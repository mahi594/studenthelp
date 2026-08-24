import uuid
from datetime import datetime

from sqlalchemy import Column, String, DateTime, JSON, ForeignKey, Integer, Boolean
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from sqlalchemy.orm import relationship


from app.db.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=False, index=True)
    hashed_password = Column(String, nullable=False)

    branch = Column(String, nullable=True)          # e.g. "CSE"
    grad_year = Column(Integer, nullable=True)       # e.g. 2027
    cgpa = Column(String, nullable=True)

    role = Column(String, nullable=False, default="student")  # "student" | "admin" | "tpo_admin"
    college_name = Column(String, nullable=True)  # used to scope the TPO dashboard
    institution_id = Column(UUID(as_uuid=True), ForeignKey("institutions.id"), nullable=True)
    email_verified = Column(Boolean, nullable=False, default=False)

    # True for admin/tpo_admin accounts created via /admin/create-admin with a
    # system-generated temp password. Forces a password change (see
    # /auth/change-password) before a full-access token is ever issued -
    # see get_current_user_for_password_change in auth.py for enforcement.
    must_change_password = Column(Boolean, nullable=False, default=False)

    # NOTE: the initial migration (f1b54c101efb) created this column as a
    # real Postgres ARRAY(UUID), not JSON - the model previously said
    # `Column(JSON, ...)`, which happened to work against SQLite (used by
    # the test suite's Base.metadata.create_all(), which builds tables FROM
    # the model rather than from Alembic) but silently broke every single
    # user insert against a real, migration-built Postgres database
    # ("malformed array literal" from psycopg2). Fixed to match the actual
    # migrated schema instead of changing the schema, since ARRAY(UUID) is
    # the correct/existing type and no data migration is needed.
    # `.with_variant(JSON(), "sqlite")` keeps the test suite's SQLite
    # fallback path working when a real Postgres test database isn't
    # reachable - it is not the source of truth, Postgres is.
    target_company_ids = Column(ARRAY(UUID(as_uuid=True)).with_variant(JSON(), "sqlite"), default=list)


    leetcode_username = Column(String, nullable=True)
    leetcode_daily_goal = Column(Integer, nullable=False, default=1)
    leetcode_total_solved = Column(Integer, nullable=False, default=0)
    leetcode_easy_solved = Column(Integer, nullable=False, default=0)
    leetcode_medium_solved = Column(Integer, nullable=False, default=0)
    leetcode_hard_solved = Column(Integer, nullable=False, default=0)
    leetcode_streak = Column(Integer, nullable=False, default=0)
    leetcode_last_solved_date = Column(String, nullable=True)

    created_at = Column(DateTime, default=lambda: datetime.utcnow())

    quiz_results = relationship("QuizResult", back_populates="user", cascade="all, delete-orphan")
    resumes = relationship("Resume", back_populates="user", cascade="all, delete-orphan")
    prep_plans = relationship("PrepPlan", back_populates="user", cascade="all, delete-orphan")
    roadmaps = relationship("Roadmap", back_populates="user", cascade="all, delete-orphan")
    chat_messages = relationship(
        "ChatMessage", back_populates="user", cascade="all, delete-orphan",
        order_by="ChatMessage.created_at",
    )
    readiness_scores = relationship(
        "ReadinessScore", back_populates="user", cascade="all, delete-orphan",
        order_by="ReadinessScore.computed_at",
    )
    applications = relationship("Application", back_populates="user", cascade="all, delete-orphan")
    mock_interview_sessions = relationship(
        "MockInterviewSession", back_populates="user", cascade="all, delete-orphan"
    )
    leetcode_logs = relationship(
        "LeetCodeLog", back_populates="user", cascade="all, delete-orphan", order_by="LeetCodeLog.solved_at.desc()"
    )
    institution = relationship("Institution", back_populates="users")



class QuizResult(Base):
    """Stores diagnostic quiz outcome per subject — this is the 'skill signal' feeding the plan generator."""
    __tablename__ = "quiz_results"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    subject = Column(String, nullable=False)   # e.g. "DSA", "DBMS", "OS", "Aptitude"
    score_percent = Column(Integer, nullable=False)
    taken_at = Column(DateTime, default=lambda: datetime.utcnow())

    user = relationship("User", back_populates="quiz_results")
