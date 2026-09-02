import uuid
from collections import defaultdict

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.models.company import Company, LearningResource
from app.models.user import User, QuizResult
from app.models.prep_plan import PrepPlan
from sqlalchemy.orm.attributes import flag_modified
from app.schemas.schemas import PrepPlanGenerateRequest, PrepPlanOut, TaskStatusUpdate
from app.models.readiness import ReadinessScore
from app.services.readiness_service import compute_readiness_score


from app.api.v1.endpoints.auth import get_current_user

router = APIRouter(prefix="/prep-plan", tags=["prep-plan"])


@router.patch("/{plan_id}/tasks/{task_index}", response_model=PrepPlanOut)
def update_task_status(
    plan_id: uuid.UUID,
    task_index: int,
    payload: TaskStatusUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):

    """Updates completion status of a specific task in a prep plan and recalculates progress server-side."""
    plan = db.query(PrepPlan).filter(PrepPlan.id == plan_id).first()
    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found")
    if plan.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not your prep plan")

    tasks = list(plan.tasks or [])
    if task_index < 0 or task_index >= len(tasks):
        raise HTTPException(status_code=404, detail="Task index out of range")

    task = dict(tasks[task_index])

    if payload.completed is not None:
        task["completed"] = payload.completed
        task["status"] = "completed" if payload.completed else "planned"
    if payload.status is not None:
        task["status"] = payload.status
        task["completed"] = (payload.status == "completed")

    tasks[task_index] = task
    plan.tasks = tasks
    flag_modified(plan, "tasks")

    # Recalculate progress percent server-side
    total_tasks = len(tasks)
    completed_count = sum(1 for t in tasks if t.get("completed") is True or t.get("status") == "completed")
    plan.progress_percent = round((completed_count / total_tasks) * 100) if total_tasks > 0 else 0

    db.commit()
    db.refresh(plan)

    # Recompute readiness immediately so prep plan progress updates Company Preparation readiness
    readiness_result = compute_readiness_score(current_user.id, db)
    db.add(ReadinessScore(
        user_id=current_user.id,
        composite_score=readiness_result["composite_score"],
        data_status=readiness_result["data_status"],
        algorithm_version=readiness_result["algorithm_version"],
        breakdown=readiness_result["breakdown"],
    ))
    db.commit()

    return plan

from app.services.ai_service import generate_prep_plan
from app.core.rate_limit import limiter



@router.post("/generate", response_model=PrepPlanOut)
@limiter.limit("5/minute")
def generate_plan(
    request: Request,
    payload: PrepPlanGenerateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    company = db.query(Company).filter(Company.id == payload.target_company_id).first()
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")

    quiz_results = db.query(QuizResult).filter(QuizResult.user_id == current_user.id).all()
    if not quiz_results:
        raise HTTPException(
            status_code=400,
            detail="Take the diagnostic quiz first so we know your weak subjects",
        )

    subjects = {q.subject for q in quiz_results}
    resources = db.query(LearningResource).filter(LearningResource.subject.in_(subjects)).all()
    resources_by_subject = defaultdict(list)
    for r in resources:
        resources_by_subject[r.subject].append({"title": r.title, "url": r.url})

    tasks = generate_prep_plan(
        company=company,
        quiz_results=quiz_results,
        days_total=payload.days_total,
        resources_by_subject=dict(resources_by_subject),
    )

    plan = PrepPlan(
        user_id=current_user.id,
        target_company_id=company.id,
        days_total=payload.days_total,
        tasks=tasks,
        progress_percent=0,
    )
    db.add(plan)
    db.commit()
    db.refresh(plan)
    return plan


from typing import Optional

@router.get("/latest", response_model=PrepPlanOut)
def get_latest_plan(
    company_id: Optional[uuid.UUID] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Most recent prep plan for the logged-in student (optionally scoped to company_id)."""
    query = db.query(PrepPlan).filter(PrepPlan.user_id == current_user.id)
    if company_id:
        query = query.filter(PrepPlan.target_company_id == company_id)
    plan = query.order_by(PrepPlan.created_at.desc()).first()
    if not plan:
        raise HTTPException(status_code=404, detail="No prep plan yet")
    return plan


@router.get("/{plan_id}", response_model=PrepPlanOut)
def get_plan(
    plan_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    plan = db.query(PrepPlan).filter(PrepPlan.id == plan_id).first()
    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found")
    if plan.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not your prep plan")
    return plan


from app.schemas.schemas import PlanCustomizeRequest, PlanCustomizeResponse
from app.services.ai_service import customize_plan_with_ai

@router.post("/{plan_id}/customize", response_model=PlanCustomizeResponse)
@limiter.limit("10/minute")
def customize_prep_plan(
    request: Request,
    plan_id: uuid.UUID,
    payload: PlanCustomizeRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Conversational AI chatbot endpoint to customize a student's day-wise prep plan."""
    plan = db.query(PrepPlan).filter(PrepPlan.id == plan_id).first()
    if not plan:
        raise HTTPException(status_code=404, detail="Prep plan not found")
    if plan.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not your prep plan")

    company = None
    if plan.target_company_id:
        company = db.query(Company).filter(Company.id == plan.target_company_id).first()

    student_profile = {
        "name": current_user.name,
        "branch": current_user.branch,
        "grad_year": current_user.grad_year,
    }

    ai_res = customize_plan_with_ai(
        plan_type="prep_plan",
        current_plan_data={"days_total": plan.days_total, "tasks": plan.tasks, "progress_percent": plan.progress_percent},
        user_message=payload.message,
        conversation_history=payload.conversation_history,
        student_profile=student_profile,
        company_name=company.name if company else None,
    )

    if ai_res.get("plan_modified") and ai_res.get("updated_plan_data"):
        updated_data = ai_res["updated_plan_data"]
        if isinstance(updated_data, list):
            plan.tasks = updated_data
        elif isinstance(updated_data, dict):
            if "tasks" in updated_data and isinstance(updated_data["tasks"], list):
                plan.tasks = updated_data["tasks"]
            if "days_total" in updated_data:
                try:
                    plan.days_total = int(updated_data["days_total"])
                except (ValueError, TypeError):
                    pass

        # Recalculate progress percent server-side
        tasks = list(plan.tasks or [])
        total_tasks = len(tasks)
        completed_count = sum(1 for t in tasks if isinstance(t, dict) and (t.get("completed") is True or t.get("status") == "completed"))
        plan.progress_percent = round((completed_count / total_tasks) * 100) if total_tasks > 0 else 0

        flag_modified(plan, "tasks")
        db.commit()
        db.refresh(plan)

    return PlanCustomizeResponse(
        explanation=ai_res.get("explanation", "Prep plan processing complete."),
        plan_modified=bool(ai_res.get("plan_modified")),
        prep_plan=plan,
    )

