import uuid
from datetime import datetime

from sqlalchemy import Column, String, DateTime, ForeignKey, Text, Integer, Boolean, JSON
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from sqlalchemy.orm import relationship

from app.db.database import Base


class QAQuestion(Base):
    """A student-posted question in the community Q&A. Optionally tagged to
    a company (e.g. "Anyone interviewed at Razorpay recently?") so it can
    surface alongside that company's curated prep content."""
    __tablename__ = "qa_questions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    author_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    company_id = Column(UUID(as_uuid=True), ForeignKey("companies.id"), nullable=True)

    title = Column(String, nullable=False)
    body = Column(Text, nullable=False)
    # Real Postgres ARRAY(String) in the migration, not JSON - same drift
    # class as User.target_company_ids/Company.roles, see those for why.
    tags = Column(ARRAY(String).with_variant(JSON(), "sqlite"), default=list)

    is_hidden = Column(Boolean, nullable=False, default=False)  # admin moderation


    created_at = Column(DateTime, default=datetime.utcnow)

    author = relationship("User")
    company = relationship("Company")
    answers = relationship(
        "QAAnswer", back_populates="question", cascade="all, delete-orphan",
        order_by="QAAnswer.created_at",
    )

    @property
    def author_name(self) -> str:
        return self.author.name

    @property
    def answer_count(self) -> int:
        return len([a for a in self.answers if not a.is_hidden])


class QAAnswer(Base):
    __tablename__ = "qa_answers"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    question_id = Column(UUID(as_uuid=True), ForeignKey("qa_questions.id"), nullable=False)
    author_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)

    body = Column(Text, nullable=False)
    upvotes = Column(Integer, nullable=False, default=0)
    is_hidden = Column(Boolean, nullable=False, default=False)  # admin moderation

    created_at = Column(DateTime, default=datetime.utcnow)

    question = relationship("QAQuestion", back_populates="answers")
    author = relationship("User")

    @property
    def author_name(self) -> str:
        return self.author.name
