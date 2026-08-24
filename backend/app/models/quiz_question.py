import uuid
from datetime import datetime

from sqlalchemy import Column, String, DateTime, ForeignKey, JSON, Integer, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.db.database import Base


class QuizQuestion(Base):
    """A quiz question, AI-generated per company/subject but gated behind
    admin approval before students can ever see it (`status`). This mirrors
    the same curated-trust principle used for company data: AI drafts, a
    human verifies before it goes live.

    `options` is a JSON list of strings, e.g. ["O(n)", "O(n^2)", "O(log n)", "O(1)"].
    `correct_option_index` points into that list - never sent to students
    before they answer (see the schema used for the student-facing GET).
    """
    __tablename__ = "quiz_questions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id = Column(UUID(as_uuid=True), ForeignKey("companies.id"), nullable=True)  # null = general/subject-only

    subject = Column(String, nullable=False)
    difficulty = Column(String, nullable=True)
    question_text = Column(Text, nullable=False)
    options = Column(JSON, nullable=False)
    correct_option_index = Column(Integer, nullable=False)
    explanation = Column(Text, nullable=True)

    status = Column(String, nullable=False, default="pending_approval")
    # "pending_approval" | "approved" | "rejected"

    generated_by = Column(String, default="ai")  # "ai" | "admin"
    reviewed_by_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    reviewed_at = Column(DateTime, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)

    company = relationship("Company")
