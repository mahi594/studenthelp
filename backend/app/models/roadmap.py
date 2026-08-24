import uuid
from datetime import datetime

from sqlalchemy import Column, String, DateTime, ForeignKey, JSON, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.db.database import Base


class Roadmap(Base):
    """A longer-horizon roadmap (semester/months-wise), re-generated periodically
    as the student's quiz performance changes over time. Distinct from `PrepPlan`,
    which is a short, company-specific countdown plan (days, not months).

    `phases` structure (JSON): [
      {
        "phase": "Semester 3 / Months 1-2",
        "focus_subjects": ["DSA basics", "Aptitude foundations"],
        "milestones": ["Solve 50 easy DSA problems", "Complete 1 mock aptitude test"],
        "reason": "why this phase now, referencing current performance trend"
      }, ...
    ]
    """
    __tablename__ = "roadmaps"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)

    horizon_months = Column(Integer, nullable=False)   # e.g. 6, 12, 24
    phases = Column(JSON, nullable=False)
    target_company_ids = Column(JSON, nullable=True)
    target_company_names = Column(JSON, nullable=True)
    based_on_quiz_snapshot = Column(JSON, nullable=True)  # quiz scores at generation time, for audit/trend comparison

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User", back_populates="roadmaps")

