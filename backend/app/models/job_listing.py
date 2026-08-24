import uuid
from datetime import datetime

from sqlalchemy import Column, String, DateTime, Text
from sqlalchemy.dialects.postgresql import UUID

from app.db.database import Base


class JobListing(Base):
    """A live job opening fetched from an external jobs API (Adzuna).

    Deliberately separate from `Company` — this table is live/temporary data
    (openings that come and go), not the verified/curated interview-process
    facts (rounds, questions) that live in `Company`/`Round`. If a listing's
    company later gets a full curated profile, `matched_company_id` can be
    set to link them (nullable - most listings won't have a curated match).
    """
    __tablename__ = "job_listings"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    source = Column(String, default="adzuna")   # which jobs API this came from
    external_id = Column(String, nullable=False, unique=True)  # dedupe key from the source API

    company_name = Column(String, nullable=False, index=True)
    role_title = Column(String, nullable=False)
    location = Column(String, nullable=True)
    description_snippet = Column(Text, nullable=True)
    apply_url = Column(String, nullable=False)   # direct apply link

    posted_at = Column(DateTime, nullable=True)
    expires_at = Column(DateTime, nullable=False)  # auto-cleanup deletes past this
    fetched_at = Column(DateTime, default=datetime.utcnow)
