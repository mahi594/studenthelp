import uuid
from datetime import datetime

from sqlalchemy import Column, String, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.db.database import Base


class Application(Base):
    """Tracks a student's application status for a curated company - lets the
    UI show 'Applied' vs 'Not applied' next to each company/apply link.
    One row per (user, company) pair - re-marking just updates status/timestamp."""
    __tablename__ = "applications"
    __table_args__ = (UniqueConstraint("user_id", "company_id", name="uq_user_company_application"),)

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    company_id = Column(UUID(as_uuid=True), ForeignKey("companies.id"), nullable=False)

    status = Column(String, nullable=False, default="not_applied")
    # "not_applied" | "applied" | "interviewing" | "offered" | "rejected"

    applied_at = Column(DateTime, nullable=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User", back_populates="applications")
    company = relationship("Company")
