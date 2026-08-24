import uuid
from datetime import datetime

from sqlalchemy import Column, String, DateTime, ForeignKey, JSON, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.db.database import Base


class MockInterviewSession(Base):
    """An AI-conducted mock interview. `transcript` is a JSON list of turns:
    [{"role": "interviewer"|"candidate", "content": "..."}], built up as the
    student answers each question. Once finished, `overall_score` and
    `feedback` are filled in - this becomes the third input to the Readiness
    Score (see readiness_service.py).

    Company-specific calibration follows the same curated-facts rule as
    everywhere else: if `company_id` is set, the interviewer AI is only told
    that company's curated round/subject data, never invents company facts.
    """
    __tablename__ = "mock_interview_sessions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    company_id = Column(UUID(as_uuid=True), ForeignKey("companies.id"), nullable=True)

    role_or_subject = Column(String, nullable=False)  # e.g. "SDE-1" or "DSA" if no company chosen
    transcript = Column(JSON, nullable=False, default=list)
    status = Column(String, nullable=False, default="in_progress")  # "in_progress" | "completed"

    overall_score = Column(Integer, nullable=True)   # 0-100, filled in on completion
    feedback = Column(JSON, nullable=True)             # {"strengths": [...], "improvements": [...]}

    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)

    user = relationship("User", back_populates="mock_interview_sessions")
