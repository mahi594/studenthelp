import csv
import io
import uuid
from statistics import mean
from typing import Optional, List
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy import func, and_, cast, Float, String
from sqlalchemy.orm import Session, aliased

from app.db.database import get_db
from app.models.user import User, QuizResult
from app.models.readiness import ReadinessScore
from app.models.intervention import Intervention
from app.models.company import Company
from app.models.application import Application
from app.models.resume import Resume
from app.models.prep_plan import PrepPlan
from app.schemas.schemas import (
    TpoDashboardOut,
    StudentReadinessSummary,
    BranchBreakdown,
    InterventionCreate,
    InterventionOut,
    TpoStudentDetailOut,
    TpoStudentAssessmentEntry,
    TpoStudentTargetCompany,
    TpoStudentPreparation,
    TpoStudentMockInterview,
    TpoStudentInterventionEntry,
)
from app.api.v1.endpoints.auth import get_current_tpo_or_admin_user

router = APIRouter(prefix="/tpo", tags=["tpo"])

LOW_READINESS_THRESHOLD = 50  # composite_score below this gets flagged


def scope_to_institution(query, model, current_user: User):
    """Applies tenant isolation to a TPO-facing query.

    - tpo_admin accounts are always scoped to their own institution_id.
      A tpo_admin with no institution_id (should not normally happen - see
      admin.create_admin) is refused rather than silently shown everyone's
      data.
    - "admin" accounts are the platform's own global/content admins (they
      also approve quiz questions, etc.) and are not tied to a single
      institution, so they are allowed to see across institutions. This is a
      deliberate, narrow exception for the platform operator role - it is
      NOT available to tpo_admin, which is the role actual college
      placement-cell staff use.

    `model` must have an `institution_id` column.
    """
    if current_user.role == "admin":
        return query
    if current_user.role == "tpo_admin":
        if current_user.institution_id is None:
            raise HTTPException(
                status_code=403,
                detail="This TPO account is not linked to an institution. Contact your platform admin.",
            )
        return query.filter(model.institution_id == current_user.institution_id)
    # Should be unreachable - get_current_tpo_or_admin_user already restricts
    # to these two roles - but fail closed rather than open just in case.
    raise HTTPException(status_code=403, detail="TPO or admin access required")


def _latest_scores_by_student(db: Session, student_ids: List[str], after: "datetime | None" = None):
    """Returns {student_id_str: composite_score} using only each student's
    MOST RECENT ReadinessScore row (optionally restricted to snapshots taken
    strictly after `after`). Using the latest score per student - rather
    than averaging every historical snapshot ever recorded - is what makes
    pre/post intervention comparisons meaningful instead of double-counting
    old data as if it were fresh reassessment.
    """
    if not student_ids:
        return {}
    ids = [uuid.UUID(sid) for sid in student_ids]
    query = db.query(ReadinessScore).filter(
        ReadinessScore.user_id.in_(ids),
        ReadinessScore.composite_score.isnot(None),
    )
    if after is not None:
        query = query.filter(ReadinessScore.computed_at > after)
    rows = query.order_by(ReadinessScore.computed_at.desc()).all()

    latest: dict = {}
    for row in rows:
        key = str(row.user_id)
        if key not in latest:  # rows are newest-first, so first hit per user wins
            latest[key] = row.composite_score
    return latest


def compute_risk_category(score: Optional[int]) -> str:
    if score is None:
        return "Not Assessed"
    if score < 50:
        return "Needs Significant Support"
    if score < 65:
        return "Needs Attention"
    if score < 80:
        return "On Track"
    return "Interview Ready"


@router.get("/dashboard", response_model=TpoDashboardOut)
def get_tpo_dashboard(
    branch: Optional[str] = None,
    grad_year: Optional[int] = None,
    cgpa_min: Optional[float] = None,
    cgpa_max: Optional[float] = None,
    readiness_min: Optional[int] = None,
    readiness_max: Optional[int] = None,
    risk_category: Optional[str] = None,
    assessment_status: Optional[str] = None,  # "assessed" | "not_assessed"
    interview_status: Optional[str] = None,  # "attempted" | "not_attempted"
    target_company_id: Optional[uuid.UUID] = None,
    skill_topic: Optional[str] = None,  # dimension key: dsa/cs_fundamentals/aptitude/communication/resume/interview/company_prep
    page: int = 1,
    page_size: int = 20,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_tpo_or_admin_user),
):
    page = max(1, page)
    page_size = max(1, min(page_size, 100))

    # Base query count for total students in current institution
    total_institution_query = db.query(User).filter(User.role == "student")
    total_institution_query = scope_to_institution(total_institution_query, User, current_user)
    total_institution_students = total_institution_query.count()

    # Subquery for each student's latest ReadinessScore (max computed_at)
    latest_score_subq = (
        db.query(
            ReadinessScore.user_id.label("user_id"),
            func.max(ReadinessScore.computed_at).label("max_date")
        )
        .group_by(ReadinessScore.user_id)
        .subquery()
    )

    score_alias = aliased(ReadinessScore)
    query = db.query(User, score_alias).filter(User.role == "student")
    query = scope_to_institution(query, User, current_user)
    query = query.outerjoin(latest_score_subq, User.id == latest_score_subq.c.user_id)\
                 .outerjoin(
                     score_alias,
                     and_(
                         score_alias.user_id == latest_score_subq.c.user_id,
                         score_alias.computed_at == latest_score_subq.c.max_date
                     )
                 )

    if branch:
        query = query.filter(User.branch == branch)
    if grad_year:
        query = query.filter(User.grad_year == grad_year)

    if cgpa_min is not None:
        query = query.filter(cast(User.cgpa, Float) >= cgpa_min)
    if cgpa_max is not None:
        query = query.filter(cast(User.cgpa, Float) <= cgpa_max)

    if readiness_min is not None:
        query = query.filter(score_alias.composite_score >= readiness_min)
    if readiness_max is not None:
        query = query.filter(score_alias.composite_score <= readiness_max)

    if risk_category:
        if risk_category == "high":
            query = query.filter(and_(score_alias.composite_score.isnot(None), score_alias.composite_score < LOW_READINESS_THRESHOLD))
        elif risk_category == "moderate":
            query = query.filter(and_(score_alias.composite_score >= LOW_READINESS_THRESHOLD, score_alias.composite_score < 70))
        elif risk_category == "low":
            query = query.filter(score_alias.composite_score >= 70)
        elif risk_category == "not_assessed":
            query = query.filter(score_alias.composite_score.is_(None))

    if assessment_status == "assessed":
        query = query.filter(score_alias.composite_score.isnot(None))
    elif assessment_status == "not_assessed":
        query = query.filter(score_alias.composite_score.is_(None))

    if interview_status == "attempted":
        from app.models.mock_interview import MockInterviewSession
        attempted_subq = db.query(MockInterviewSession.user_id).filter(MockInterviewSession.status == "completed").subquery()
        query = query.filter(User.id.in_(attempted_subq))
    elif interview_status == "not_attempted":
        from app.models.mock_interview import MockInterviewSession
        attempted_subq = db.query(MockInterviewSession.user_id).filter(MockInterviewSession.status == "completed").subquery()
        query = query.filter(User.id.notin_(attempted_subq))

    if target_company_id:
        target_str = str(target_company_id)
        query = query.filter(cast(User.target_company_ids, String).contains(target_str))

    if skill_topic:
        skill_str = skill_topic.lower()
        query = query.filter(cast(score_alias.breakdown, String).ilike(f"%{skill_str}%"))

    # SQL COUNT over full filtered set
    total_matching = query.count()
    total_pages = max(1, (total_matching + page_size - 1) // page_size)

    # Calculate aggregate stats using SQL aggregations over full filtered set
    avg_score_scalar = query.with_entities(func.avg(score_alias.composite_score)).scalar()
    average_readiness_score = round(float(avg_score_scalar), 1) if avg_score_scalar is not None else None

    flagged_students_count = query.with_entities(func.count(User.id)).filter(
        and_(score_alias.composite_score.isnot(None), score_alias.composite_score < LOW_READINESS_THRESHOLD)
    ).scalar() or 0

    branch_stats_rows = query.with_entities(
        User.branch,
        func.avg(score_alias.composite_score),
        func.count(User.id)
    ).filter(score_alias.composite_score.isnot(None))\
     .group_by(User.branch).all()

    branch_breakdown = [
        BranchBreakdown(
            branch=b_name or "Unknown",
            average_score=round(float(b_avg), 1) if b_avg is not None else 0.0,
            student_count=b_count,
        )
        for b_name, b_avg, b_count in branch_stats_rows if b_name
    ]

    # SQL LIMIT and OFFSET for paginated student rows ONLY (returns at most page_size rows)
    paged_rows = (
        query.order_by(User.name.asc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )

    paged_summaries = []
    paged_flagged = []
    for user_obj, score_obj in paged_rows:
        comp = score_obj.composite_score if score_obj else None
        risk = compute_risk_category(comp)
        summary = StudentReadinessSummary(
            user_id=user_obj.id,
            name=user_obj.name,
            email=user_obj.email,
            branch=user_obj.branch,
            grad_year=user_obj.grad_year,
            latest_composite_score=comp,
            flagged_low_readiness=(comp is not None and comp < LOW_READINESS_THRESHOLD),
            risk_category=risk,
        )
        paged_summaries.append(summary)
    flagged_rows = (
        query.filter(
            and_(
                score_alias.composite_score.isnot(None),
                score_alias.composite_score < LOW_READINESS_THRESHOLD,
            )
        )
        .order_by(User.name.asc())
        .limit(50)
        .all()
    )
    all_flagged_summaries = [
        StudentReadinessSummary(
            user_id=u.id,
            name=u.name,
            email=u.email,
            branch=u.branch,
            grad_year=u.grad_year,
            latest_composite_score=s.composite_score if s else None,
            flagged_low_readiness=True,
            risk_category=compute_risk_category(s.composite_score if s else None),
        )
        for u, s in flagged_rows
    ]

    return TpoDashboardOut(
        institution_name=current_user.institution_name if hasattr(current_user, "institution_name") else None,
        total_students=total_institution_students,
        students_with_score=total_matching,
        batch_average_score=average_readiness_score,
        low_readiness_threshold=LOW_READINESS_THRESHOLD,
        filtered_students_count=total_matching,
        total_matching=total_matching,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
        flagged_students_count=flagged_students_count,
        average_readiness_score=average_readiness_score,
        branch_breakdown=branch_breakdown,
        all_students=paged_summaries,
        students=paged_summaries,
        flagged_students=all_flagged_summaries,
    )




@router.get("/students/{student_id}", response_model=TpoStudentDetailOut)
def get_student_detail(
    student_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_tpo_or_admin_user),
):
    """Full TPO-facing student profile (Phase 7). Institution-scoped like
    everything else in this file - a TPO can only open a detail page for a
    student in their own institution. Never returns password/hash/tokens -
    this queries specific columns/models, it never serializes the raw User
    ORM object."""
    student_query = db.query(User).filter(User.id == student_id, User.role == "student")
    student_query = scope_to_institution(student_query, User, current_user)
    student = student_query.first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")

    # --- Readiness + trend ---
    score_rows = (
        db.query(ReadinessScore)
        .filter(ReadinessScore.user_id == student.id)
        .order_by(ReadinessScore.computed_at.asc())
        .all()
    )
    latest = score_rows[-1] if score_rows else None
    composite = latest.composite_score if latest else None
    trend = [
        {"date": row.computed_at, "composite_score": row.composite_score}
        for row in score_rows
    ]

    # --- Assessment history ---
    quiz_rows = (
        db.query(QuizResult)
        .filter(QuizResult.user_id == student.id)
        .order_by(QuizResult.taken_at.desc())
        .all()
    )
    assessment_history = [
        TpoStudentAssessmentEntry(date=q.taken_at, subject=q.subject, score_percent=q.score_percent)
        for q in quiz_rows
    ]

    # --- Target companies (with real resume-match data only, no fabrication) ---
    target_companies = []
    company_ids = student.target_company_ids or []
    if company_ids:
        companies = db.query(Company).filter(Company.id.in_(company_ids)).all()
        applications = {
            a.company_id: a
            for a in db.query(Application).filter(
                Application.user_id == student.id, Application.company_id.in_(company_ids)
            ).all()
        }
        for company in companies:
            resume = (
                db.query(Resume)
                .filter(
                    Resume.user_id == student.id,
                    Resume.target_company_id == company.id,
                    Resume.match_result.isnot(None),
                )
                .order_by(Resume.created_at.desc())
                .first()
            )
            match_percent = None
            match_note = "No resume matched to this company yet."
            if resume and resume.match_result:
                match_percent = resume.match_result.get("match_score_percent")
                if match_percent is not None:
                    match_note = "AI-generated resume match - not a guaranteed outcome."

            app_row = applications.get(company.id)
            target_companies.append(
                TpoStudentTargetCompany(
                    company_id=company.id,
                    name=company.name,
                    roles=company.roles or [],
                    application_status=app_row.status if app_row else None,
                    resume_match_percent=match_percent,
                    resume_match_note=match_note,
                )
            )

    # --- Preparation plan (latest) ---
    latest_plan = (
        db.query(PrepPlan)
        .filter(PrepPlan.user_id == student.id)
        .order_by(PrepPlan.created_at.desc())
        .first()
    )
    if latest_plan:
        plan_company = db.query(Company).filter(Company.id == latest_plan.target_company_id).first() if latest_plan.target_company_id else None
        preparation = TpoStudentPreparation(
            has_plan=True,
            target_company_name=plan_company.name if plan_company else None,
            days_total=latest_plan.days_total,
            progress_percent=latest_plan.progress_percent,
            created_at=latest_plan.created_at,
        )
    else:
        preparation = TpoStudentPreparation(has_plan=False)

    # --- Mock interviews ---
    from app.models.mock_interview import MockInterviewSession
    interview_rows = (
        db.query(MockInterviewSession)
        .filter(MockInterviewSession.user_id == student.id, MockInterviewSession.status == "completed")
        .order_by(MockInterviewSession.completed_at.desc())
        .all()
    )
    mock_interviews = [
        TpoStudentMockInterview(
            date=row.completed_at,
            overall_score=row.overall_score,
            strengths=(row.feedback or {}).get("strengths", []),
            improvements=(row.feedback or {}).get("improvements", []),
            is_ai_generated_feedback=True,
        )
        for row in interview_rows
    ]

    # --- Interventions targeting this student ---
    intervention_rows = (
        db.query(Intervention)
        .filter(Intervention.institution_id == student.institution_id)
        .all()
    )
    interventions = [
        TpoStudentInterventionEntry(
            id=item.id,
            title=item.title,
            status=item.status,
            pre_avg_score=item.pre_avg_score,
            post_avg_score=item.post_avg_score,
            improvement_delta=item.improvement_delta,
        )
        for item in intervention_rows
        if str(student.id) in (item.target_student_ids or [])
    ]

    return TpoStudentDetailOut(
        user_id=student.id,
        name=student.name,
        email=student.email,
        branch=student.branch,
        grad_year=student.grad_year,
        cgpa=student.cgpa,
        composite_score=composite,
        data_status=latest.data_status if latest else "insufficient",
        algorithm_version=latest.algorithm_version if latest else "v1",
        breakdown=latest.breakdown if latest else {},
        risk_category=compute_risk_category(composite),
        readiness_trend=trend,
        assessment_history=assessment_history,
        target_companies=target_companies,
        preparation=preparation,
        mock_interviews=mock_interviews,
        interventions=interventions,
    )


@router.post("/interventions", response_model=InterventionOut)
def create_intervention(
    payload: InterventionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_tpo_or_admin_user),
):
    target_ids = [str(sid) for sid in payload.target_student_ids]
    has_criteria = bool(
        payload.target_branch
        or payload.target_grad_year
        or payload.target_readiness_min is not None
        or payload.target_readiness_max is not None
        or payload.target_risk
        or payload.target_company_id
    )

    if not target_ids and not has_criteria:
        raise HTTPException(
            status_code=400,
            detail="Provide targeting criteria or select at least one student.",
        )

    if not target_ids:
        # MODE A: Server-side criteria eligibility query across entire institution
        latest_score_subq = (
            db.query(
                ReadinessScore.user_id.label("user_id"),
                func.max(ReadinessScore.computed_at).label("max_date")
            )
            .group_by(ReadinessScore.user_id)
            .subquery()
        )
        score_alias = aliased(ReadinessScore)
        student_query = db.query(User).filter(User.role == "student")
        student_query = scope_to_institution(student_query, User, current_user)
        student_query = student_query.outerjoin(latest_score_subq, User.id == latest_score_subq.c.user_id)\
                                     .outerjoin(
                                         score_alias,
                                         and_(
                                             score_alias.user_id == latest_score_subq.c.user_id,
                                             score_alias.computed_at == latest_score_subq.c.max_date
                                         )
                                     )

        if payload.target_branch:
            student_query = student_query.filter(User.branch == payload.target_branch)
        if payload.target_grad_year:
            student_query = student_query.filter(User.grad_year == payload.target_grad_year)
        if payload.target_readiness_min is not None:
            student_query = student_query.filter(score_alias.composite_score >= payload.target_readiness_min)
        if payload.target_readiness_max is not None:
            student_query = student_query.filter(score_alias.composite_score <= payload.target_readiness_max)
        if payload.target_risk:
            if payload.target_risk == "high":
                student_query = student_query.filter(and_(score_alias.composite_score.isnot(None), score_alias.composite_score < LOW_READINESS_THRESHOLD))
            elif payload.target_risk == "moderate":
                student_query = student_query.filter(and_(score_alias.composite_score >= LOW_READINESS_THRESHOLD, score_alias.composite_score < 70))
            elif payload.target_risk == "low":
                student_query = student_query.filter(score_alias.composite_score >= 70)
        if payload.target_company_id:
            target_str = str(payload.target_company_id)
            student_query = student_query.filter(cast(User.target_company_ids, String).contains(target_str))

        eligible_students = student_query.all()
        target_ids = [str(s.id) for s, _sc in eligible_students] if eligible_students and isinstance(eligible_students[0], tuple) else [str(s.id) for s in eligible_students]
    else:
        # IDOR / cross-tenant guard: every targeted student must belong to authorized institution
        student_query = db.query(User).filter(
            User.id.in_([uuid.UUID(sid) for sid in target_ids]),
            User.role == "student",
        )
        student_query = scope_to_institution(student_query, User, current_user)
        authorized_students = student_query.all()
        if len(authorized_students) != len(set(target_ids)):
            raise HTTPException(
                status_code=403,
                detail="One or more target students are not in your institution.",
            )


    # Baseline: each target student's most recent readiness score as of
    # right now. Students with no score yet simply aren't counted - pre_avg
    # is never guessed.
    pre_scores_by_student = _latest_scores_by_student(db, target_ids)
    pre_scores = list(pre_scores_by_student.values())
    pre_avg = round(mean(pre_scores)) if pre_scores else None

    intervention = Intervention(
        title=payload.title,
        skill_topic=payload.skill_topic,
        intervention_type=payload.intervention_type,
        target_branch=payload.target_branch,
        target_student_ids=target_ids,
        status="active",
        pre_avg_score=pre_avg,
        eligible_count=len(target_ids),
        pre_assessed_count=len(pre_scores),
        institution_id=current_user.institution_id,  # None for a platform "admin"; a real institution for tpo_admin
        created_by_user_id=current_user.id,
    )
    db.add(intervention)
    db.commit()
    db.refresh(intervention)

    return _to_intervention_out(intervention)


def _to_intervention_out(item: Intervention) -> InterventionOut:
    return InterventionOut(
        id=item.id,
        title=item.title,
        skill_topic=item.skill_topic,
        intervention_type=item.intervention_type,
        target_branch=item.target_branch,
        target_student_ids=[uuid.UUID(sid) for sid in (item.target_student_ids or [])],
        status=item.status,
        eligible_count=item.eligible_count or 0,
        pre_assessed_count=item.pre_assessed_count or 0,
        reassessed_count=item.reassessed_count or 0,
        pre_avg_score=item.pre_avg_score,
        post_avg_score=item.post_avg_score,
        improvement_delta=item.improvement_delta,
        created_at=item.created_at,
    )


@router.get("/interventions", response_model=List[InterventionOut])
def list_interventions(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_tpo_or_admin_user),
):
    query = db.query(Intervention).order_by(Intervention.created_at.desc())
    query = scope_to_institution(query, Intervention, current_user)
    return [_to_intervention_out(item) for item in query.all()]


def _get_authorized_intervention(intervention_id: uuid.UUID, db: Session, current_user: User) -> Intervention:
    """Fetches an intervention and enforces tenant isolation (IDOR guard).
    Returns 404 (not 403) so callers can't distinguish "doesn't exist" from
    "belongs to another institution"."""
    query = db.query(Intervention).filter(Intervention.id == intervention_id)
    query = scope_to_institution(query, Intervention, current_user)
    intervention = query.first()
    if not intervention:
        raise HTTPException(status_code=404, detail="Intervention not found")
    return intervention


@router.get("/interventions/{intervention_id}", response_model=InterventionOut)
def get_intervention(
    intervention_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_tpo_or_admin_user),
):
    intervention = _get_authorized_intervention(intervention_id, db, current_user)
    return _to_intervention_out(intervention)


from app.services.audit_log_service import log_event


@router.post("/interventions/{intervention_id}/complete", response_model=InterventionOut)
def complete_intervention(
    intervention_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_tpo_or_admin_user),
):
    intervention = _get_authorized_intervention(intervention_id, db, current_user)

    target_ids = intervention.target_student_ids or []

    post_scores_by_student = _latest_scores_by_student(db, target_ids, after=intervention.created_at)
    post_scores = list(post_scores_by_student.values())

    intervention.status = "completed"
    intervention.completed_at = datetime.utcnow()
    intervention.reassessed_count = len(post_scores)

    if post_scores:
        intervention.post_avg_score = round(mean(post_scores))
        if intervention.pre_avg_score is not None:
            intervention.improvement_delta = intervention.post_avg_score - intervention.pre_avg_score
        else:
            intervention.improvement_delta = None
    else:
        intervention.post_avg_score = None
        intervention.improvement_delta = None

    db.commit()
    db.refresh(intervention)

    log_event(
        db=db,
        actor_user=current_user,
        action="intervention_completed",
        resource_type="intervention",
        resource_id=str(intervention.id),
        metadata={"title": intervention.title, "reassessed_count": len(post_scores)},
    )

    return _to_intervention_out(intervention)


@router.get("/export")
def export_tpo_report(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_tpo_or_admin_user),
):
    log_event(
        db=db,
        actor_user=current_user,
        action="csv_export",
        resource_type="export",
        resource_id=None,
        metadata={"institution_name": current_user.institution.name if current_user.institution else "All"},
    )
    query = db.query(User).filter(User.role == "student")
    query = scope_to_institution(query, User, current_user)
    students = query.all()
    output = io.StringIO()
    writer = csv.writer(output)
    
    institution_name = current_user.institution.name if current_user.institution else "All Institutions (platform admin)"
    export_date = datetime.utcnow().strftime("%Y-%m-%d")
    writer.writerow([f"Institution: {institution_name}", f"Exported: {export_date}"])
    writer.writerow([])

    writer.writerow([
        "Student ID", "Name", "Email", "Branch", "Grad Year", "CGPA",
        "Overall Readiness", "DSA", "CS Fundamentals", "Aptitude", "Communication",
        "Resume", "Interview", "Company Preparation",

        "Risk Category", "Assessment Status", "Flagged Low Readiness",
    ])

    for student in students:
        latest_score = (
            db.query(ReadinessScore)
            .filter(ReadinessScore.user_id == student.id)
            .order_by(ReadinessScore.computed_at.desc())
            .first()
        )
        breakdown = latest_score.breakdown if latest_score else {}
        components_used = set(breakdown.get("components_used", [])) if breakdown else set()

        def dim(key: str):
            """Only report a dimension value if that dimension was actually
            part of the composite for this student - never print a score for
            a dimension with no underlying data."""
            if key in components_used:
                return breakdown.get(key, "")
            return "Not Assessed"

        score_val = latest_score.composite_score if latest_score else "Not Assessed"
        risk = compute_risk_category(latest_score.composite_score if latest_score else None)
        flagged = "Yes" if (latest_score and latest_score.composite_score < LOW_READINESS_THRESHOLD) else "No"
        assessment_status = "Assessed" if latest_score else "Not Assessed"

        writer.writerow([
            str(student.id),
            student.name,
            student.email,
            student.branch or "",
            student.grad_year or "",
            student.cgpa or "",
            score_val,
            dim("dsa"), dim("cs_fundamentals"), dim("aptitude"), dim("communication"),
            dim("resume"), dim("interview"), dim("company_prep"),
            risk,
            assessment_status,
            flagged,
        ])

    csv_content = output.getvalue()
    return Response(
        content=csv_content,
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=tpo_placement_readiness_report_{export_date}.csv"},
    )

