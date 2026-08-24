import uuid
from datetime import datetime

from sqlalchemy import Column, String, DateTime, ForeignKey, JSON, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.db.database import Base


class PrepPlan(Base):
    """A generated day-wise plan. `tasks` stores structured JSON so the UI can render
    checklists/progress bars instead of free text — see docs/ai_plan_prompt.md for the
    exact schema Claude is asked to return.
    """
    __tablename__ = "prep_plans"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    target_company_id = Column(UUID(as_uuid=True), ForeignKey("companies.id"), nullable=True)

    days_total = Column(Integer, nullable=False)
    tasks = Column(JSON, nullable=False)   # [{day, topic, task, source_url, reason, done}, ...]
    progress_percent = Column(Integer, default=0)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User", back_populates="prep_plans")
