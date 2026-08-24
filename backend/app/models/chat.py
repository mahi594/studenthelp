import uuid
from datetime import datetime

from sqlalchemy import Column, String, DateTime, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.db.database import Base


class ChatMessage(Base):
    """One turn in the student's conversation with the placement Q&A bot.
    Stored per-user so the bot has memory of the conversation and so admins
    can later audit what the AI has been telling students (quality control)."""
    __tablename__ = "chat_messages"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)

    role = Column(String, nullable=False)   # "user" | "assistant"
    content = Column(Text, nullable=False)
    referenced_company_id = Column(UUID(as_uuid=True), ForeignKey("companies.id"), nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="chat_messages")
