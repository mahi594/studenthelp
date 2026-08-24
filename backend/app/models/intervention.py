import uuid
from datetime import datetime

from sqlalchemy import Column, String, DateTime, ForeignKey, JSON, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.db.database import Base


class Intervention(Base):
    """An institutional placement cell intervention created by TPO admins to
    remediate identified skill gaps (e.g. a 7-day DSA Workshop for struggling students).
    Tracks student enrollment, pre-intervention baseline score, post-intervention score,
    and measured impact (+X points improvement).
    """
    __tablename__ = "interventions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = Column(String, nullable=False)
    skill_topic = Column(String, nullable=False)  # "DSA", "Communication", "Aptitude", "DBMS", "OS"
    intervention_type = Column(String, default="workshop")  # "workshop" | "assignment" | "mock_test"
    target_branch = Column(String, nullable=True)

    target_student_ids = Column(JSON, nullable=False, default=list)  # list of UUID strings
    status = Column(String, default="active")  # "active" | "completed"

    # pre_avg_score / post_avg_score are ONLY ever set from real ReadinessScore
    # rows for the target students. They are nullable and MUST stay null when
    # no student in target_student_ids has a readiness score yet - never
    # backfilled with an assumed/fabricated number. See tpo.py for the
    # enforcement of this rule.
    pre_avg_score = Column(Integer, nullable=True)
    post_avg_score = Column(Integer, nullable=True)
    improvement_delta = Column(Integer, nullable=True)

    # Sample sizes behind pre_avg_score / post_avg_score, so the UI can show
    # "Reassessed: 61 / 87" instead of implying every target student was
    # measured.
    eligible_count = Column(Integer, nullable=False, default=0)
    pre_assessed_count = Column(Integer, nullable=False, default=0)
    reassessed_count = Column(Integer, nullable=False, default=0)

    # Tenant scope: which institution this intervention belongs to. Set once
    # at creation from the creating TPO's institution and never changed -
    # this is what every TPO-facing query below filters on.
    institution_id = Column(UUID(as_uuid=True), ForeignKey("institutions.id"), nullable=True)

    created_by_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)

    created_by = relationship("User")
