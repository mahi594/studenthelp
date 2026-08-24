import uuid
from datetime import datetime

from sqlalchemy import Column, String, DateTime, ForeignKey, Boolean, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.db.database import Base


class Notification(Base):
    """In-app notification for a user. Kept deliberately simple (no push/email
    delivery) - `type` + `link` let the frontend route to the relevant page
    when clicked, without needing a notification-type-specific schema."""
    __tablename__ = "notifications"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)

    type = Column(String, nullable=False)   # e.g. "quiz_approved", "readiness_flagged", "qa_reply", "application_update"
    title = Column(String, nullable=False)
    body = Column(Text, nullable=True)
    link = Column(String, nullable=True)    # relative frontend path, e.g. "/applications"

    is_read = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User")
