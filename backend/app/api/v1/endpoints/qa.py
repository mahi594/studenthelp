import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.orm import Session, joinedload

from app.db.database import get_db
from app.models.user import User
from app.models.company import Company
from app.models.qa import QAQuestion, QAAnswer
from app.schemas.schemas import (
    QAQuestionCreate,
    QAQuestionListOut,
    QAQuestionDetailOut,
    QAAnswerCreate,
    QAAnswerOut,
)
from app.api.v1.endpoints.auth import get_current_user, get_current_admin_user
from app.services.notification_service import notify
from app.core.rate_limit import limiter

router = APIRouter(prefix="/qa", tags=["qa"])


@router.get("/questions", response_model=list[QAQuestionListOut])
def list_questions(
    company_id: uuid.UUID | None = Query(None),
    tag: str | None = Query(None),
    db: Session = Depends(get_db),
):
    query = (
        db.query(QAQuestion)
        .options(joinedload(QAQuestion.author), joinedload(QAQuestion.answers))
        .filter(QAQuestion.is_hidden == False)  # noqa: E712
    )
    if company_id:
        query = query.filter(QAQuestion.company_id == company_id)
    if tag:
        query = query.filter(QAQuestion.tags.any(tag))

    return query.order_by(QAQuestion.created_at.desc()).limit(100).all()


@router.get("/questions/{question_id}", response_model=QAQuestionDetailOut)
def get_question(question_id: uuid.UUID, db: Session = Depends(get_db)):
    question = (
        db.query(QAQuestion)
        .options(joinedload(QAQuestion.author), joinedload(QAQuestion.answers).joinedload(QAAnswer.author))
        .filter(QAQuestion.id == question_id, QAQuestion.is_hidden == False)  # noqa: E712
        .first()
    )
    if not question:
        raise HTTPException(status_code=404, detail="Question not found")

    # Hide moderated answers from the response without touching the DB rows
    question.answers = [a for a in question.answers if not a.is_hidden]
    return question


@router.post("/questions", response_model=QAQuestionDetailOut)
@limiter.limit("10/minute")
def create_question(
    request: Request,
    payload: QAQuestionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if payload.company_id:
        company = db.query(Company).filter(Company.id == payload.company_id).first()
        if not company:
            raise HTTPException(status_code=404, detail="Company not found")

    question = QAQuestion(
        author_id=current_user.id,
        company_id=payload.company_id,
        title=payload.title,
        body=payload.body,
        tags=payload.tags,
    )
    db.add(question)
    db.commit()
    db.refresh(question)
    return question


@router.post("/questions/{question_id}/answers", response_model=QAAnswerOut)
@limiter.limit("20/minute")
def answer_question(
    request: Request,
    question_id: uuid.UUID,
    payload: QAAnswerCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    question = db.query(QAQuestion).filter(QAQuestion.id == question_id).first()
    if not question:
        raise HTTPException(status_code=404, detail="Question not found")

    answer = QAAnswer(question_id=question.id, author_id=current_user.id, body=payload.body)
    db.add(answer)

    # Notify the question's author, unless they're answering their own question
    if question.author_id != current_user.id:
        notify(
            db,
            user_id=question.author_id,
            type="qa_reply",
            title=f"{current_user.name} answered your question",
            body=question.title,
            link=f"/community/{question.id}",
        )

    db.commit()
    db.refresh(answer)
    return answer


@router.post("/answers/{answer_id}/upvote", response_model=QAAnswerOut)
def upvote_answer(
    answer_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Simple increment - no per-user upvote tracking/idempotency in this
    version, so the same user can upvote more than once. Fine for a first
    pass; add a qa_upvotes join table if abuse becomes a real problem."""
    answer = db.query(QAAnswer).filter(QAAnswer.id == answer_id).first()
    if not answer:
        raise HTTPException(status_code=404, detail="Answer not found")

    answer.upvotes += 1
    db.commit()
    db.refresh(answer)
    return answer


@router.delete("/questions/{question_id}")
def hide_question(
    question_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin_user),
):
    """Admin moderation: soft-delete (hide) rather than a hard delete, so
    it's recoverable and doesn't orphan answer notifications already sent."""
    question = db.query(QAQuestion).filter(QAQuestion.id == question_id).first()
    if not question:
        raise HTTPException(status_code=404, detail="Question not found")

    question.is_hidden = True
    db.commit()
    return {"message": "Question hidden"}


@router.delete("/answers/{answer_id}")
def hide_answer(
    answer_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin_user),
):
    answer = db.query(QAAnswer).filter(QAAnswer.id == answer_id).first()
    if not answer:
        raise HTTPException(status_code=404, detail="Answer not found")

    answer.is_hidden = True
    db.commit()
    return {"message": "Answer hidden"}
