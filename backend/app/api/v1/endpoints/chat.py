from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.models.user import User
from app.models.company import Company
from app.models.chat import ChatMessage
from app.schemas.schemas import ChatAskRequest, ChatAskResponse, ChatMessageOut
from app.services.ai_service import answer_chat_question
from app.api.v1.endpoints.auth import get_current_user
from app.core.rate_limit import limiter

router = APIRouter(prefix="/chat", tags=["chat"])

MAX_HISTORY_TURNS = 10  # keep prompt size sane; trim oldest turns beyond this


@router.post("/ask", response_model=ChatAskResponse)
@limiter.limit("15/minute")
def ask(
    request: Request,
    payload: ChatAskRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    company = None
    if payload.company_id:
        company = db.query(Company).filter(Company.id == payload.company_id).first()
        if not company:
            raise HTTPException(status_code=404, detail="Company not found")

    # Load recent history for this user, oldest first, capped
    past_messages = (
        db.query(ChatMessage)
        .filter(ChatMessage.user_id == current_user.id)
        .order_by(ChatMessage.created_at.desc())
        .limit(MAX_HISTORY_TURNS * 2)
        .all()
    )
    past_messages.reverse()
    conversation_history = [{"role": m.role, "content": m.content} for m in past_messages]

    answer = answer_chat_question(
        conversation_history=conversation_history,
        latest_question=payload.message,
        relevant_company=company,
    )

    user_msg = ChatMessage(
        user_id=current_user.id,
        role="user",
        content=payload.message,
        referenced_company_id=company.id if company else None,
    )
    assistant_msg = ChatMessage(
        user_id=current_user.id,
        role="assistant",
        content=answer,
        referenced_company_id=company.id if company else None,
    )
    db.add_all([user_msg, assistant_msg])
    db.commit()

    # Return only the newly created response turn (user_msg + assistant_msg) rather than fetching full history
    recent_turn = [user_msg, assistant_msg]

    return ChatAskResponse(
        answer=answer,
        history=[ChatMessageOut.model_validate(m) for m in recent_turn],
    )



from fastapi import Query

@router.get("/history", response_model=list[ChatMessageOut])
def get_history(
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Lists chat history for current user with server-side pagination."""
    messages = (
        db.query(ChatMessage)
        .filter(ChatMessage.user_id == current_user.id)
        .order_by(ChatMessage.created_at.asc())
        .offset(offset)
        .limit(limit)
        .all()
    )
    return messages

