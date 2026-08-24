import uuid

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.models.user import User, QuizResult
from app.models.company import Company
from app.models.roadmap import Roadmap
from app.schemas.schemas import RoadmapGenerateRequest, RoadmapOut
from app.services.ai_service import generate_roadmap
from app.api.v1.endpoints.auth import get_current_user
from app.core.rate_limit import limiter

router = APIRouter(prefix="/roadmap", tags=["roadmap"])


@router.post("/generate", response_model=RoadmapOut)
@limiter.limit("3/minute")
def generate(
    request: Request,
    payload: RoadmapGenerateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    quiz_results = db.query(QuizResult).filter(QuizResult.user_id == current_user.id).all()
    if not quiz_results:
        raise HTTPException(
            status_code=400,
            detail="Take the diagnostic quiz first so the roadmap reflects your actual performance",
        )

    companies = []
    if payload.target_company_ids:
        companies = db.query(Company).filter(Company.id.in_(payload.target_company_ids)).all()

    company_names = [c.name for c in companies]
    company_ids_str = [str(c.id) for c in companies]

    phases = generate_roadmap(
        quiz_results=quiz_results,
        horizon_months=payload.horizon_months,
        target_company_names=company_names,
    )

    roadmap = Roadmap(
        user_id=current_user.id,
        horizon_months=payload.horizon_months,
        phases=phases,
        target_company_ids=company_ids_str,
        target_company_names=company_names,
        based_on_quiz_snapshot=[
            {"subject": q.subject, "score_percent": q.score_percent} for q in quiz_results
        ],
    )
    db.add(roadmap)
    db.commit()
    db.refresh(roadmap)
    return roadmap



@router.get("/{roadmap_id}", response_model=RoadmapOut)
def get_roadmap(
    roadmap_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # Was previously unauthenticated with no ownership check at all - any
    # caller could read any student's roadmap (readiness weaknesses, plan
    # details) just by guessing/enumerating a UUID. Now requires auth and is
    # scoped to the requester's own roadmap.
    roadmap = (
        db.query(Roadmap)
        .filter(Roadmap.id == roadmap_id, Roadmap.user_id == current_user.id)
        .first()
    )
    if not roadmap:
        raise HTTPException(status_code=404, detail="Roadmap not found")
    return roadmap


@router.get("/user/latest", response_model=RoadmapOut)
def get_latest_roadmap(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Fetch the most recently generated roadmap - re-generate periodically
    (e.g. every time new quiz results come in) to keep it performance-driven."""
    roadmap = (
        db.query(Roadmap)
        .filter(Roadmap.user_id == current_user.id)
        .order_by(Roadmap.created_at.desc())
        .first()
    )
    if not roadmap:
        raise HTTPException(status_code=404, detail="No roadmap generated yet")
    return roadmap
