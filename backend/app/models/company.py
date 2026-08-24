import uuid
from datetime import datetime

from sqlalchemy import Column, String, DateTime, JSON, ForeignKey, Integer, Text, Boolean
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from sqlalchemy.orm import relationship

from app.db.database import Base


class Company(Base):
    __tablename__ = "companies"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False, index=True)
    # NOTE: these are real Postgres ARRAY(String) columns in the actual
    # migration (f1b54c101efb), not JSON - see the identical note on
    # User.target_company_ids for why this drift existed and how it was
    # found (it broke every company insert against real Postgres with
    # "malformed array literal"). `.with_variant(JSON(), "sqlite")` keeps
    # the test suite's SQLite fallback working.
    roles = Column(ARRAY(String).with_variant(JSON(), "sqlite"), default=list)          # e.g. ["SDE-1", "Analyst"]
    tags = Column(ARRAY(String).with_variant(JSON(), "sqlite"), default=list)            # e.g. ["product-based", "core"]

    # Resume filter criteria
    min_cgpa = Column(String, nullable=True)
    preferred_branches = Column(ARRAY(String).with_variant(JSON(), "sqlite"), default=list)
    resume_keywords = Column(ARRAY(String).with_variant(JSON(), "sqlite"), default=list)  # skills/keywords they filter for

    apply_url = Column(String, nullable=True)  # direct link to the application/careers page, set by admin

    is_curated_verified = Column(Boolean, default=False)   # true once an admin/senior has confirmed the data
    source_type = Column(String, default="placement_cell")  # "placement_cell" | "alumni_report" | "ai_recommended"
    verified_by = Column(String, nullable=True)  # e.g., "Placement Cell Head"
    verified_at = Column(DateTime, nullable=True)
    confidence = Column(String, default="High")  # "High" | "Medium" | "Low"
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    rounds = relationship("Round", back_populates="company", cascade="all, delete-orphan", order_by="Round.order_index")


class Round(Base):
    """One stage in a company's hiring process, e.g. OA, Tech1, Tech2, HR."""
    __tablename__ = "rounds"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id = Column(UUID(as_uuid=True), ForeignKey("companies.id"), nullable=False)

    order_index = Column(Integer, nullable=False)   # sequence in the process
    round_type = Column(String, nullable=False)      # "OA" | "Technical" | "HR" | "System Design"
    subjects_tested = Column(ARRAY(String).with_variant(JSON(), "sqlite"), default=list)  # e.g. ["DSA", "DBMS"]
    difficulty = Column(String, nullable=True)        # "Easy" | "Medium" | "Hard"
    notes = Column(Text, nullable=True)

    company = relationship("Company", back_populates="rounds")
    questions = relationship("Question", back_populates="round", cascade="all, delete-orphan")


class Question(Base):
    """A real (curated) or AI-generated practice question tied to a round/subject."""
    __tablename__ = "questions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    round_id = Column(UUID(as_uuid=True), ForeignKey("rounds.id"), nullable=True)  # nullable: subject-only practice Qs

    subject = Column(String, nullable=False)
    difficulty = Column(String, nullable=True)
    tags = Column(ARRAY(String).with_variant(JSON(), "sqlite"), default=list)
    text = Column(Text, nullable=False)
    answer_or_hint = Column(Text, nullable=True)

    source = Column(String, default="curated")   # "curated" | "ai_generated" | "senior_submitted"
    submitted_by = Column(String, nullable=True)   # attribution for trust, e.g. senior's name/batch

    round = relationship("Round", back_populates="questions")


class LearningResource(Base):
    """Curated (admin-picked) source per subject/topic — not raw AI suggestions."""
    __tablename__ = "learning_resources"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    subject = Column(String, nullable=False)
    topic = Column(String, nullable=False)
    title = Column(String, nullable=False)
    url = Column(String, nullable=False)
    resource_type = Column(String, default="video")  # "video" | "article" | "notes" | "playlist"
    rank = Column(Integer, default=1)   # lower = higher priority/best recommendation
