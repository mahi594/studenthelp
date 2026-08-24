import uuid
from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, Integer, JSON, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.db.database import Base


class ReadinessScore(Base):
    """A snapshot of a student's composite placement-readiness score (0-100),
    recomputed periodically (e.g. after new quiz results or a resume update)
    so it's a TREND over time, not a one-off number. This is what the TPO
    dashboard aggregates across a batch to flag students needing help early.

    `breakdown` stores the component scores that fed into the composite, e.g.
    {"quiz_mastery": 62, "resume_match": 80, "components_used": ["quiz", "resume"]}
    so the trend line can be explained, not just shown as a black-box number.
    """
    __tablename__ = "readiness_scores"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)

    # Nullable: a snapshot can be taken while the student still has too
    # little data for a meaningful composite (data_status="insufficient").
    # The row is still saved (for the trend line / audit trail) but the API
    # must render "Readiness score unavailable" rather than a number.
    composite_score = Column(Integer, nullable=True)  # 0-100, or None if insufficient data
    data_status = Column(String, default="sufficient", nullable=False)  # "sufficient" | "insufficient"
    algorithm_version = Column(String, default="v1", nullable=False)
    breakdown = Column(JSON, nullable=False)

    computed_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="readiness_scores")
