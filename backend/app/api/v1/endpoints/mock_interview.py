import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.rate_limit import limiter
from fastapi import Request
from app.db.database import get_db
from app.models.user import User
from app.models.company import Company
from app.models.mock_interview import MockInterviewSession
from app.models.readiness import ReadinessScore
from app.schemas.schemas import (
    MockInterviewStartRequest,
    MockInterviewRespondRequest,
    MockInterviewSessionOut,
)
from app.services.ai_service import start_mock_interview, continue_mock_interview, score_mock_interview
from app.services.readiness_service import compute_readiness_score
from app.api.v1.endpoints.auth import get_current_user

router = APIRouter(prefix="/mock-interview", tags=["mock-interview"])

MAX_TURNS = 6  # candidate answers before the session auto-suggests finishing


@router.post("/start", response_model=MockInterviewSessionOut)
@limiter.limit("5/minute")
def start_session(
    request: Request,
    payload: MockInterviewStartRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    company = None
    if payload.company_id:
        company = db.query(Company).filter(Company.id == payload.company_id).first()
        if not company:
            raise HTTPException(status_code=404, detail="Company not found")

    opening_question = start_mock_interview(company, payload.role_or_subject)

    session = MockInterviewSession(
        user_id=current_user.id,
        company_id=company.id if company else None,
        role_or_subject=payload.role_or_subject,
        transcript=[{"role": "interviewer", "content": opening_question}],
        status="in_progress",
    )
    db.add(session)
    db.commit()
    db.refresh(session)
    return session


@router.post("/{session_id}/respond", response_model=MockInterviewSessionOut)
@limiter.limit("15/minute")
def respond(
    request: Request,
    session_id: uuid.UUID,
    payload: MockInterviewRespondRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    session = (
        db.query(MockInterviewSession)
        .filter(MockInterviewSession.id == session_id, MockInterviewSession.user_id == current_user.id)
        .first()
    )
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    if session.status != "in_progress":
        raise HTTPException(status_code=400, detail="This interview session has already been completed")

    transcript = list(session.transcript)
    transcript.append({"role": "candidate", "content": payload.answer})

    next_question = continue_mock_interview(transcript, payload.answer)
    transcript.append({"role": "interviewer", "content": next_question})

    session.transcript = transcript
    db.commit()
    db.refresh(session)
    return session


@router.post("/{session_id}/finish", response_model=MockInterviewSessionOut)
@limiter.limit("5/minute")
def finish_session(
    request: Request,
    session_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Scores the full transcript and marks the session complete. Also
    recomputes the Readiness Score so the mock interview result is reflected
    immediately (see readiness_service.py - mock interview is the third
    weighted component)."""
    session = (
        db.query(MockInterviewSession)
        .filter(MockInterviewSession.id == session_id, MockInterviewSession.user_id == current_user.id)
        .first()
    )
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    if session.status != "in_progress":
        raise HTTPException(status_code=400, detail="This interview session has already been completed")

    result = score_mock_interview(session.transcript)

    session.status = "completed"
    session.overall_score = result.get("overall_score")
    session.feedback = {
        "strengths": result.get("strengths", []),
        "improvements": result.get("improvements", []),
    }
    session.completed_at = datetime.utcnow()
    db.commit()
    db.refresh(session)

    # Recompute readiness immediately so the new mock interview score counts right away
    readiness_result = compute_readiness_score(current_user.id, db)
    db.add(ReadinessScore(
        user_id=current_user.id,
        composite_score=readiness_result["composite_score"],
        data_status=readiness_result["data_status"],
        algorithm_version=readiness_result["algorithm_version"],
        breakdown=readiness_result["breakdown"],
    ))
    db.commit()

    return session


@router.get("/{session_id}", response_model=MockInterviewSessionOut)
def get_session(
    session_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    session = (
        db.query(MockInterviewSession)
        .filter(MockInterviewSession.id == session_id, MockInterviewSession.user_id == current_user.id)
        .first()
    )
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return session
