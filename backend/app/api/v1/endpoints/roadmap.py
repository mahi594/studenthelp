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


from app.schemas.schemas import PlanCustomizeRequest, PlanCustomizeResponse
from app.services.ai_service import customize_plan_with_ai
from sqlalchemy.orm.attributes import flag_modified

@router.post("/{roadmap_id}/customize", response_model=PlanCustomizeResponse)
@limiter.limit("10/minute")
def customize_roadmap(
    request: Request,
    roadmap_id: uuid.UUID,
    payload: PlanCustomizeRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Conversational AI chatbot endpoint to customize a student's active roadmap."""
    roadmap = db.query(Roadmap).filter(Roadmap.id == roadmap_id).first()
    if not roadmap:
        raise HTTPException(status_code=404, detail="Roadmap not found")
    if roadmap.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not your roadmap")

    student_profile = {
        "name": current_user.name,
        "branch": current_user.branch,
        "grad_year": current_user.grad_year,
    }

    ai_res = customize_plan_with_ai(
        plan_type="roadmap",
        current_plan_data={"horizon_months": roadmap.horizon_months, "phases": roadmap.phases},
        user_message=payload.message,
        conversation_history=payload.conversation_history,
        student_profile=student_profile,
        company_name=", ".join(roadmap.target_company_names) if roadmap.target_company_names else None,
    )

    if ai_res.get("plan_modified") and ai_res.get("updated_plan_data"):
        updated_data = ai_res["updated_plan_data"]
        if isinstance(updated_data, list):
            roadmap.phases = updated_data
        elif isinstance(updated_data, dict) and "phases" in updated_data:
            roadmap.phases = updated_data["phases"]
            if "horizon_months" in updated_data:
                try:
                    roadmap.horizon_months = int(updated_data["horizon_months"])
                except (ValueError, TypeError):
                    pass
        flag_modified(roadmap, "phases")
        db.commit()
        db.refresh(roadmap)

    return PlanCustomizeResponse(
        explanation=ai_res.get("explanation", "Roadmap processing complete."),
        plan_modified=bool(ai_res.get("plan_modified")),
        roadmap=roadmap,
    )

