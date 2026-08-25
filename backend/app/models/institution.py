import uuid
from datetime import datetime

from sqlalchemy import Column, String, DateTime, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.db.database import Base


class Institution(Base):
    """Represents a college / university institution using StudentHelp."""
    __tablename__ = "institutions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False, unique=True, index=True)
    code = Column(String, nullable=True, unique=True, index=True)  # e.g. DEMO2026 for student onboarding
    domain = Column(String, nullable=True)  # e.g., "college.edu" for auto-tenant assignment

    logo_url = Column(String, nullable=True)
    primary_color = Column(String, default="#4f46e5")
    placement_cell_name = Column(String, default="Training & Placement Cell")
    academic_year = Column(String, default="2026-2027")

    created_at = Column(DateTime, default=datetime.utcnow)

    users = relationship("User", back_populates="institution")
