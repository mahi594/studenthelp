import uuid
from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.models.user import User
from app.models.company import Company
from app.models.quiz_question import QuizQuestion
from app.schemas.schemas import (
    QuizGenerateRequest,
    QuizQuestionAdminOut,
    AdminCreateRequest,
    AdminCreateResponse,
)
from app.services.ai_service import generate_quiz_questions
from app.services.email_service import send_email, is_email_configured
from app.api.v1.endpoints.auth import get_current_admin_user, generate_temp_password, pwd_context
from app.core.rate_limit import limiter
from app.services.institution_service import get_or_create_institution

router = APIRouter(prefix="/admin", tags=["admin"])


@router.post("/create-admin", response_model=AdminCreateResponse)
@limiter.limit("10/minute")
def create_admin(
    request: Request,
    payload: AdminCreateRequest,
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin_user),
):
    """Admin-only. Creates a new admin or tpo_admin account with a
    system-generated temporary password and must_change_password=True - the
    new account cannot reach any page beyond the forced password-change
    screen until they set their own password (see /auth/change-password and
    the must_change_password branch in /auth/login).

    The temp password is returned once in this response and, if SMTP is
    configured, also emailed directly to the new admin - it is never stored
    or retrievable again after this call."""
    if payload.role not in ("admin", "tpo_admin"):
        raise HTTPException(status_code=400, detail="role must be 'admin' or 'tpo_admin'")

    existing = db.query(User).filter(User.email == payload.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")

    if payload.role == "tpo_admin" and not payload.college_name:
        raise HTTPException(status_code=400, detail="college_name is required for a tpo_admin account, to scope their dashboard")

    # institution_id (not just the free-text college_name) is what every
    # tenant-isolation query actually filters on - see tpo.py. Resolve/create
    # the Institution row here so a tpo_admin is never left unscoped.
    institution_id = None
    if payload.role == "tpo_admin":
        institution = get_or_create_institution(db, payload.college_name)
        institution_id = institution.id

    temp_password = generate_temp_password()

    new_admin = User(
        name=payload.name,
        email=payload.email,
        hashed_password=pwd_context.hash(temp_password),
        role=payload.role,
        college_name=payload.college_name,
        institution_id=institution_id,
        email_verified=True,  # created by an admin, not self-registered - no verification email loop needed
        must_change_password=True,
    )
    db.add(new_admin)
    db.commit()
    db.refresh(new_admin)

    email_sent = False
    if is_email_configured():
        body = f"""An admin account has been created for you on StudentHelp.

Email: {payload.email}
Temporary password: {temp_password}

Log in and you'll be asked to set your own password before you can access anything else. This temporary password will not work again after that."""
        email_sent = send_email(payload.email, "Your StudentHelp admin account", body)

    return AdminCreateResponse(
        id=new_admin.id,
        name=new_admin.name,
        email=new_admin.email,
        role=new_admin.role,
        temp_password=temp_password,
        email_sent=email_sent,
    )


@router.post("/quiz/generate", response_model=List[QuizQuestionAdminOut])
@limiter.limit("10/minute")
def generate_quiz(
    request: Request,
    payload: QuizGenerateRequest,
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin_user),
):
    """AI drafts quiz questions (optionally calibrated to a company's curated
    round data). They land as `pending_approval` - NOT visible to students
    until an admin explicitly approves each one via /admin/quiz/{id}/approve."""
    company = None
    if payload.company_id:
        company = db.query(Company).filter(Company.id == payload.company_id).first()
        if not company:
            raise HTTPException(status_code=404, detail="Company not found")

    generated = generate_quiz_questions(
        subject=payload.subject,
        num_questions=payload.num_questions,
        company=company,
    )

    questions = []
    for q in generated:
        question = QuizQuestion(
            company_id=company.id if company else None,
            subject=payload.subject,
            difficulty=q.get("difficulty"),
            question_text=q["question_text"],
            options=q["options"],
            correct_option_index=q["correct_option_index"],
            explanation=q.get("explanation"),
            status="pending_approval",
            generated_by="ai",
        )
        db.add(question)
        questions.append(question)

    db.commit()
    for q in questions:
        db.refresh(q)
    return questions


@router.get("/quiz/pending", response_model=List[QuizQuestionAdminOut])
def list_pending_quiz_questions(
    subject: Optional[str] = None,
    company_id: Optional[uuid.UUID] = None,
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin_user),
):
    query = db.query(QuizQuestion).filter(QuizQuestion.status == "pending_approval")
    if subject:
        query = query.filter(QuizQuestion.subject == subject)
    if company_id:
        query = query.filter(QuizQuestion.company_id == company_id)
    return query.all()


@router.post("/quiz/{question_id}/approve", response_model=QuizQuestionAdminOut)
def approve_quiz_question(
    question_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin_user),
):
    question = db.query(QuizQuestion).filter(QuizQuestion.id == question_id).first()
    if not question:
        raise HTTPException(status_code=404, detail="Question not found")

    question.status = "approved"
    question.reviewed_by_user_id = current_admin.id
    question.reviewed_at = datetime.utcnow()
    db.commit()
    db.refresh(question)
    return question


@router.post("/quiz/{question_id}/reject", response_model=QuizQuestionAdminOut)
def reject_quiz_question(
    question_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin_user),
):
    question = db.query(QuizQuestion).filter(QuizQuestion.id == question_id).first()
    if not question:
        raise HTTPException(status_code=404, detail="Question not found")

    question.status = "rejected"
    question.reviewed_by_user_id = current_admin.id
    question.reviewed_at = datetime.utcnow()
    db.commit()
    db.refresh(question)
    return question
