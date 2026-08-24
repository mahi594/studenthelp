import random
import uuid
from datetime import datetime, timedelta
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.models.user import User, QuizResult
from app.models.quiz_question import QuizQuestion
from app.models.notification import Notification
from app.schemas.schemas import (
    QuizResultCreate,
    QuizQuestionStudentOut,
    QuizSubmitAnswersRequest,
    QuizSubmitAnswersResponse,
    QuizResultOut,
    QuizWeeklySubjectStatus,
    LeetCodeRecommendationOut,
)
from app.api.v1.endpoints.auth import get_current_user
from app.api.v1.endpoints.leetcode import (
    SUBJECT_TO_LEETCODE_TOPICS,
    WEAK_SUBJECT_THRESHOLD,
    recommend_for_subject,
)
from app.services.notification_service import notify
from app.services.weekly_engine_service import WEEKLY_QUIZ_SUBJECTS, QUIZ_CADENCE_DAYS

router = APIRouter(prefix="/quiz", tags=["quiz"])


@router.get("/questions", response_model=List[QuizQuestionStudentOut])
def get_quiz_questions(
    subject: str,
    company_id: Optional[uuid.UUID] = None,
    limit: int = 10,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Fetch a set of admin-approved quiz questions for a subject (optionally
    calibrated to a specific company). Only `status == 'approved'` questions
    are ever returned here - correct answers are never included in this
    response, see QuizQuestionStudentOut."""
    query = db.query(QuizQuestion).filter(
        QuizQuestion.subject == subject,
        QuizQuestion.status == "approved",
    )
    if company_id:
        query = query.filter(QuizQuestion.company_id == company_id)

    questions = query.all()
    if not questions:
        raise HTTPException(
            status_code=404,
            detail=f"No approved quiz questions available yet for '{subject}'. Ask an admin to generate and approve some.",
        )

    random.shuffle(questions)
    return questions[:limit]


@router.post("/submit-answers", response_model=QuizSubmitAnswersResponse)
def submit_quiz_answers(
    payload: QuizSubmitAnswersRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Auto-grades the student's answers against the stored correct answers,
    computes a score_percent, and saves it as a QuizResult - this is what
    actually feeds the Prep Plan / Roadmap generators."""
    if not payload.answers:
        raise HTTPException(status_code=400, detail="No answers submitted")

    question_ids = [a.question_id for a in payload.answers]
    questions = db.query(QuizQuestion).filter(QuizQuestion.id.in_(question_ids)).all()
    questions_by_id = {q.id: q for q in questions}

    correct_count = 0
    question_breakdown = []
    for answer in payload.answers:
        question = questions_by_id.get(answer.question_id)
        if question:
            is_correct = (question.correct_option_index == answer.selected_option_index)
            if is_correct:
                correct_count += 1
            question_breakdown.append({
                "question_id": question.id,
                "question_text": question.question_text,
                "options": question.options,
                "selected_option_index": answer.selected_option_index,
                "correct_option_index": question.correct_option_index,
                "is_correct": is_correct,
                "explanation": question.explanation or "The correct option is based on fundamental principles of the subject.",
            })

    total = len(payload.answers)
    score_percent = round((correct_count / total) * 100) if total > 0 else 0

    result = QuizResult(
        user_id=current_user.id,
        subject=payload.subject,
        score_percent=score_percent,
    )
    db.add(result)

    # Weak-subject signal -> immediate, relevant LeetCode recommendations +
    # a notification, so the "what do I do about this score" question is
    # answered right away instead of requiring a separate visit to /leetcode.
    is_weak = score_percent < WEAK_SUBJECT_THRESHOLD
    recommended: List[dict] = []
    if is_weak:
        recommended = recommend_for_subject(payload.subject, limit=5)

        # Avoid spamming a notification every single attempt at the same
        # weak subject in one day - one nudge per subject per day is enough.
        today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        already_notified_today = (
            db.query(Notification)
            .filter(
                Notification.user_id == current_user.id,
                Notification.type == "leetcode_recommendation",
                Notification.body.ilike(f"%{payload.subject}%"),
                Notification.created_at >= today_start,
            )
            .first()
        )
        if not already_notified_today:
            notify(
                db,
                user_id=current_user.id,
                type="leetcode_recommendation",
                title=f"Practice recommendations for {payload.subject}",
                body=(
                    f"You scored {score_percent}% on {payload.subject} - here are "
                    f"{len(recommended)} LeetCode problems picked to strengthen it."
                ),
                link="/leetcode",
            )

    db.commit()

    return QuizSubmitAnswersResponse(
        subject=payload.subject,
        score_percent=score_percent,
        correct_count=correct_count,
        total_count=total,
        is_weak_subject=is_weak,
        recommended_leetcode=[LeetCodeRecommendationOut(**p) for p in recommended],
        question_breakdown=question_breakdown,
    )



@router.post("/submit")
def submit_quiz_result(
    payload: QuizResultCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Manual override: directly record a subject score without going through
    the question flow above. Kept for quick testing / bulk imports."""
    result = QuizResult(
        user_id=current_user.id,
        subject=payload.subject,
        score_percent=payload.score_percent,
    )
    db.add(result)
    db.commit()
    return {"status": "recorded"}


@router.get("/history", response_model=List[QuizResultOut])
def get_quiz_history(
    subject: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Every quiz attempt the student has made, oldest to newest - use this
    to render a per-subject score trend or a dated activity log. Optionally
    filter to a single subject (e.g. only 'DSA' attempts)."""
    query = db.query(QuizResult).filter(QuizResult.user_id == current_user.id)
    if subject:
        query = query.filter(QuizResult.subject == subject)
    return query.order_by(QuizResult.taken_at.asc()).all()


@router.get("/weekly-status", response_model=List[QuizWeeklySubjectStatus])
def get_weekly_quiz_status(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Per-subject weekly cadence: when the student last took each subject's
    quiz and whether they're due again (7+ days, or never taken). Drives the
    'due this week' badges on the quiz page and the weekly reminder job in
    weekly_engine_service.py - both read this same cadence rule."""
    latest_by_subject: dict[str, QuizResult] = {}
    results = (
        db.query(QuizResult)
        .filter(QuizResult.user_id == current_user.id)
        .order_by(QuizResult.taken_at.desc())
        .all()
    )
    for r in results:
        if r.subject not in latest_by_subject:
            latest_by_subject[r.subject] = r

    now = datetime.utcnow()
    statuses = []
    for subject in WEEKLY_QUIZ_SUBJECTS:
        last = latest_by_subject.get(subject)
        if not last:
            statuses.append(QuizWeeklySubjectStatus(subject=subject, is_due=True))
            continue

        next_eligible = last.taken_at + timedelta(days=QUIZ_CADENCE_DAYS)
        statuses.append(QuizWeeklySubjectStatus(
            subject=subject,
            last_taken_at=last.taken_at,
            last_score_percent=last.score_percent,
            next_eligible_at=next_eligible,
            is_due=now >= next_eligible,
        ))
    return statuses