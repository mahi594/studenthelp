"""
Weekly cadence jobs: nudge students who haven't taken a subject's quiz in
the last 7 days, and auto-generate a fresh 7-day prep plan for students who
have both quiz history and a target company set, so the "weekly quiz -> new
plan" loop the product is built around actually runs on its own instead of
requiring the student to remember to do it manually.

Both jobs are deliberately conservative and per-student fault-isolated: one
student's AI-generation failure (bad prompt, quota, etc) is caught and
logged, not allowed to abort the whole run for everyone else. See the
scheduler wiring in main.py for how often these fire.
"""
import logging
from collections import defaultdict
from datetime import datetime, timedelta

from sqlalchemy.orm import Session

from app.models.user import User, QuizResult
from app.models.company import Company, LearningResource
from app.models.prep_plan import PrepPlan
from app.models.notification import Notification
from app.services.ai_service import generate_prep_plan
from app.services.notification_service import notify
from app.services.email_service import send_email, is_email_configured

logger = logging.getLogger(__name__)

WEEKLY_QUIZ_SUBJECTS = ["DSA", "DBMS", "OS", "Aptitude", "CN", "OOP"]
QUIZ_CADENCE_DAYS = 7
PREP_PLAN_DAYS_TOTAL = 7  # a weekly plan matches the weekly quiz/notification cadence


def _latest_quiz_by_subject(db: Session, user_id) -> dict:
    latest = {}
    results = (
        db.query(QuizResult)
        .filter(QuizResult.user_id == user_id)
        .order_by(QuizResult.taken_at.desc())
        .all()
    )
    for r in results:
        if r.subject not in latest:
            latest[r.subject] = r
    return latest


def send_weekly_quiz_reminders(db: Session) -> int:
    """Notifies every student who has at least one subject due (never taken,
    or 7+ days since last attempt). One notification per student per run,
    listing which subjects are due, rather than one per subject - keeps it
    to a single weekly nudge instead of up to 6."""
    students = db.query(User).filter(User.role == "student").all()
    now = datetime.utcnow()
    sent = 0

    for student in students:
        latest = _latest_quiz_by_subject(db, student.id)
        due_subjects = []
        for subject in WEEKLY_QUIZ_SUBJECTS:
            last = latest.get(subject)
            if not last or now >= last.taken_at + timedelta(days=QUIZ_CADENCE_DAYS):
                due_subjects.append(subject)

        if not due_subjects:
            continue

        # Don't double-send if the job has already run this week for this student.
        week_start = now - timedelta(days=QUIZ_CADENCE_DAYS)
        already_sent = (
            db.query(Notification)
            .filter(
                Notification.user_id == student.id,
                Notification.type == "weekly_quiz_reminder",
                Notification.created_at >= week_start,
            )
            .first()
        )
        if already_sent:
            continue

        subjects_list = ", ".join(due_subjects)
        notify(
            db,
            user_id=student.id,
            type="weekly_quiz_reminder",
            title="Your weekly quiz is ready",
            body=f"Time to check in on: {subjects_list}. Ten questions each - it feeds your prep plan and roadmap.",
            link="/quiz",
        )
        sent += 1

        # Best-effort email nudge, in addition to the in-app notification -
        # a weekly cadence is easy to miss if the student isn't already in
        # the app. Never let an email failure block the notification itself
        # (already added to the session above) or the rest of the run.
        if is_email_configured():
            try:
                send_email(
                    student.email,
                    "Your weekly quiz is ready",
                    f"Hi {student.name},\n\nTime to check in on: {subjects_list}.\n\n"
                    f"Ten questions each - your score feeds your LeetCode recommendations and next prep plan.\n\n"
                    f"Take it here: {_frontend_url()}/quiz",
                )
            except Exception:
                logger.exception("Weekly quiz reminder email failed for user %s", student.id)

    db.commit()
    return sent


def generate_weekly_prep_plans(db: Session) -> int:
    """For students with both quiz history and at least one target company
    set, regenerates a 7-day prep plan and notifies them. Skips students
    without a target company (prep plans are company-specific here - see
    PrepPlanGenerateRequest) rather than guessing one for them."""
    students = (
        db.query(User)
        .filter(User.role == "student")
        .filter(User.target_company_ids.isnot(None))
        .all()
    )

    generated = 0
    for student in students:
        if not student.target_company_ids:
            continue

        quiz_results = db.query(QuizResult).filter(QuizResult.user_id == student.id).all()
        if not quiz_results:
            continue  # nothing to base a plan on yet

        # Only regenerate weekly - skip if this student already got one in the last 7 days.
        recent_plan = (
            db.query(PrepPlan)
            .filter(PrepPlan.user_id == student.id)
            .order_by(PrepPlan.created_at.desc())
            .first()
        )
        if recent_plan and recent_plan.created_at >= datetime.utcnow() - timedelta(days=QUIZ_CADENCE_DAYS):
            continue

        company = db.query(Company).filter(Company.id == student.target_company_ids[0]).first()
        if not company:
            continue

        subjects = {q.subject for q in quiz_results}
        resources = db.query(LearningResource).filter(LearningResource.subject.in_(subjects)).all()
        resources_by_subject = defaultdict(list)
        for r in resources:
            resources_by_subject[r.subject].append({"title": r.title, "url": r.url})

        try:
            tasks = generate_prep_plan(
                company=company,
                quiz_results=quiz_results,
                days_total=PREP_PLAN_DAYS_TOTAL,
                resources_by_subject=dict(resources_by_subject),
            )
        except Exception:
            # AI quota/outage etc - don't let one student's failure break the
            # rest of the run; they'll be picked up again next week.
            logger.exception("Weekly prep plan generation failed for user %s", student.id)
            continue

        plan = PrepPlan(
            user_id=student.id,
            target_company_id=company.id,
            days_total=PREP_PLAN_DAYS_TOTAL,
            tasks=tasks,
            progress_percent=0,
        )
        db.add(plan)
        notify(
            db,
            user_id=student.id,
            type="prep_plan_ready",
            title="This week's prep plan is ready",
            body=f"A fresh 7-day plan for {company.name}, based on your latest quiz scores.",
            link="/prep-plan",
        )
        generated += 1

        if is_email_configured():
            try:
                send_email(
                    student.email,
                    "This week's prep plan is ready",
                    f"Hi {student.name},\n\nA fresh 7-day prep plan for {company.name} is ready, "
                    f"based on your latest quiz scores.\n\nView it here: {_frontend_url()}/prep-plan",
                )
            except Exception:
                logger.exception("Weekly prep plan email failed for user %s", student.id)

    db.commit()
    return generated


def _frontend_url() -> str:
    from app.core.config import settings
    return settings.FRONTEND_URL.rstrip("/")
