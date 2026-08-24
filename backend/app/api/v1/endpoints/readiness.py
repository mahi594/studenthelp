from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.models.user import User
from app.models.readiness import ReadinessScore
from app.schemas.schemas import ReadinessScoreOut
from app.services.readiness_service import compute_readiness_score
from app.api.v1.endpoints.auth import get_current_user

router = APIRouter(prefix="/readiness", tags=["readiness"])


@router.post("/compute", response_model=ReadinessScoreOut)
def compute_and_save_readiness(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Recomputes the student's composite readiness score from their current
    quiz results + resume match data, and saves a new snapshot (so the score
    is a trend over time, not overwritten). Call this after taking a quiz or
    uploading a resume to keep the trend current."""
    result = compute_readiness_score(current_user.id, db)

    score = ReadinessScore(
        user_id=current_user.id,
        composite_score=result["composite_score"],
        data_status=result["data_status"],
        algorithm_version=result["algorithm_version"],
        breakdown=result["breakdown"],
    )
    db.add(score)
    db.commit()
    db.refresh(score)
    return score


@router.get("/latest", response_model=ReadinessScoreOut)
def get_latest_readiness(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    score = (
        db.query(ReadinessScore)
        .filter(ReadinessScore.user_id == current_user.id)
        .order_by(ReadinessScore.computed_at.desc())
        .first()
    )
    if not score:
        # Compute on the fly if nothing's been saved yet, rather than 404-ing
        result = compute_readiness_score(current_user.id, db)
        score = ReadinessScore(
            user_id=current_user.id,
            composite_score=result["composite_score"],
            data_status=result["data_status"],
            algorithm_version=result["algorithm_version"],
            breakdown=result["breakdown"],
        )
        db.add(score)
        db.commit()
        db.refresh(score)
    return score


@router.get("/history", response_model=List[ReadinessScoreOut])
def get_readiness_history(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Full trend line - use this to render a chart of readiness over time."""
    return (
        db.query(ReadinessScore)
        .filter(ReadinessScore.user_id == current_user.id)
        .order_by(ReadinessScore.computed_at.asc())
        .all()
    )
