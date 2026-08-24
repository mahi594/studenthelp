import uuid
from datetime import datetime

from sqlalchemy import Column, String, DateTime, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.db.database import Base


class LeetCodeLog(Base):
    """Stores individual LeetCode problems solved/logged by students."""
    __tablename__ = "leetcode_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)

    problem_title = Column(String, nullable=False)
    problem_slug = Column(String, nullable=True)
    difficulty = Column(String, nullable=False, default="Easy")  # "Easy" | "Medium" | "Hard"
    topic = Column(String, nullable=True, default="General")     # e.g. "Arrays", "DP", "Trees", "Graphs"
    notes = Column(Text, nullable=True)

    solved_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="leetcode_logs")
