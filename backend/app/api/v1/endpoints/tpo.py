import csv
import io
import uuid
from statistics import mean
from typing import Optional, List
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.orm import Session

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
    page_size = max(1, min(page_size, 100))  # sensible max page size

    query = db.query(User).filter(User.role == "student")
    query = scope_to_institution(query, User, current_user)
    if branch:
        query = query.filter(User.branch == branch)
    if grad_year:
        query = query.filter(User.grad_year == grad_year)
    if target_company_id:
        # target_company_ids is a JSON array column - filtering it in SQL is
        # dialect-specific (Postgres JSON containment vs SQLite), so this one
        # is applied in Python below alongside the other computed filters.
        pass

    students = query.all()

    # Bulk-fetch each student's latest readiness score and interview
    # attempt status in 2 queries total, rather than one query per student
    # (N+1) - matters once a college has hundreds/thousands of students.
    student_ids = [s.id for s in students]
    latest_score_rows: dict = {}
    if student_ids:
        rows = (
            db.query(ReadinessScore)
            .filter(ReadinessScore.user_id.in_(student_ids))
            .order_by(ReadinessScore.computed_at.desc())
            .all()
        )
        for row in rows:
            if row.user_id not in latest_score_rows:
                latest_score_rows[row.user_id] = row

    interviewed_ids = set()
    if student_ids:
        from app.models.mock_interview import MockInterviewSession
        interviewed_ids = {
            row.user_id
            for row in db.query(MockInterviewSession.user_id)
            .filter(MockInterviewSession.user_id.in_(student_ids), MockInterviewSession.status == "completed")
            .distinct()
            .all()
        }

    def matches_filters(student: User, score_row) -> bool:
        composite = score_row.composite_score if score_row else None
        breakdown = score_row.breakdown if score_row else {}

        if cgpa_min is not None or cgpa_max is not None:
            try:
                cgpa_val = float(student.cgpa) if student.cgpa else None
            except (TypeError, ValueError):
                cgpa_val = None
            if cgpa_val is None:
                return False
            if cgpa_min is not None and cgpa_val < cgpa_min:
                return False
            if cgpa_max is not None and cgpa_val > cgpa_max:
                return False

        if readiness_min is not None and (composite is None or composite < readiness_min):
            return False
        if readiness_max is not None and (composite is None or composite > readiness_max):
            return False

        if risk_category and compute_risk_category(composite) != risk_category:
            return False

        if assessment_status == "assessed" and composite is None:
            return False
        if assessment_status == "not_assessed" and composite is not None:
            return False

        if interview_status == "attempted" and student.id not in interviewed_ids:
            return False
        if interview_status == "not_attempted" and student.id in interviewed_ids:
            return False

        if target_company_id and target_company_id not in (student.target_company_ids or []):
            return False

        if skill_topic:
            dim_score = breakdown.get(skill_topic) if breakdown else None
            weaknesses = breakdown.get("top_weaknesses", []) if breakdown else []
            # "Weak in this skill" = it's one of their identified top
            # weaknesses, OR they scored below the risk threshold on it.
            is_weak = (dim_score is not None and dim_score < LOW_READINESS_THRESHOLD)
            if not is_weak and not any(skill_topic.lower() in w.lower() for w in weaknesses):
                return False

        return True

    summaries = []
    scores_for_average = []
    branch_scores: dict = {}

    for student in students:
        score_row = latest_score_rows.get(student.id)
        if not matches_filters(student, score_row):
            continue

        composite = score_row.composite_score if score_row else None
        risk = compute_risk_category(composite)

        summaries.append(
            StudentReadinessSummary(
                user_id=student.id,
                name=student.name,
                email=student.email,
                branch=student.branch,
                grad_year=student.grad_year,
                latest_composite_score=composite,
                flagged_low_readiness=(composite is not None and composite < LOW_READINESS_THRESHOLD),
                risk_category=risk,
            )
        )

        if composite is not None:
            scores_for_average.append(composite)
            if student.branch:
                branch_scores.setdefault(student.branch, []).append(composite)

    flagged = [s for s in summaries if s.flagged_low_readiness]

    branch_breakdown = [
        BranchBreakdown(
            branch=branch_name,
            average_score=round(mean(scores), 1),
            student_count=len(scores),
        )
        for branch_name, scores in branch_scores.items()
    ]

    # Pagination applies to the returned student list only - the aggregate
    # widgets above (total_students, batch_average_score, branch_breakdown,
    # flagged_students) are computed over the FULL filtered set, not just
    # the current page, since a TPO expects "average readiness" to mean the
    # whole filtered cohort, not just the 20 rows currently on screen.
    total_matching = len(summaries)
    total_pages = max(1, (total_matching + page_size - 1) // page_size)
    start = (page - 1) * page_size
    page_students = summaries[start : start + page_size]

    return TpoDashboardOut(
        total_students=len(students),
        students_with_score=len(scores_for_average),
        batch_average_score=round(mean(scores_for_average), 1) if scores_for_average else None,
        low_readiness_threshold=LOW_READINESS_THRESHOLD,
        flagged_students=flagged,
        branch_breakdown=branch_breakdown,
        all_students=page_students,
        total_matching=total_matching,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
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

    # IDOR / cross-tenant guard: every targeted student must actually be a
    # student the current TPO is authorized to see (i.e. belongs to the same
    # institution). Reject the whole request rather than silently dropping
    # students the caller shouldn't have been able to name in the first
    # place - that would let a TPO probe which IDs are valid students at
    # another institution.
    if target_ids:
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

