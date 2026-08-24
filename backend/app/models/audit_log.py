import uuid
from datetime import datetime

from sqlalchemy import Column, String, DateTime, JSON, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.db.database import Base


class AuditLog(Base):
    """Institutional Audit Log for tracking key actions per institution.
    
    Stores non-sensitive operational logs (e.g. TPO login, student view,
    intervention creation, CSV exports, company verification).
    NEVER store passwords, tokens, JWTs, or resume text here.
    """
    __tablename__ = "audit_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    institution_id = Column(UUID(as_uuid=True), ForeignKey("institutions.id"), nullable=False, index=True)
    actor_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    
    action = Column(String, nullable=False, index=True)       # e.g. "tpo_login", "csv_export", "intervention_create"
    resource_type = Column(String, nullable=False)           # e.g. "student", "intervention", "export", "company"
    resource_id = Column(String, nullable=True)             # UUID or identifier string of target resource
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    metadata_json = Column(JSON, nullable=True)             # non-sensitive context metadata

    institution = relationship("Institution")
    actor = relationship("User")
