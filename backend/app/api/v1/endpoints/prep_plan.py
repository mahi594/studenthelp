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


@router.get("/latest", response_model=PrepPlanOut)
def get_latest_plan(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Most recent prep plan for the logged-in student - drives the dashboard
    'this week' teaser. Must be registered before /{plan_id} below, or
    FastAPI would try to parse 'latest' as a plan_id UUID and 422."""
    plan = (
        db.query(PrepPlan)
        .filter(PrepPlan.user_id == current_user.id)
        .order_by(PrepPlan.created_at.desc())
        .first()
    )
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
