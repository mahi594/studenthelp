import uuid
from datetime import datetime

from sqlalchemy import Column, String, DateTime, ForeignKey, Text, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.db.database import Base


class Resume(Base):
    __tablename__ = "resumes"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)

    file_url = Column(String, nullable=False)         # S3/R2 URL of uploaded PDF (may be a presigned URL - see storage_key)
    storage_key = Column(String, nullable=True)        # the S3/R2 object key - use this to regenerate a fresh
                                                         # presigned URL once file_url expires (see storage_service.py)
    parsed_text = Column(Text, nullable=True)          # raw extracted text
    parsed_json = Column(JSON, nullable=True)           # structured: sections, skills, projects

    target_company_id = Column(UUID(as_uuid=True), ForeignKey("companies.id"), nullable=True)
    match_result = Column(JSON, nullable=True)          # AI-generated: {score, missing_keywords, suggestions}

    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="resumes")
