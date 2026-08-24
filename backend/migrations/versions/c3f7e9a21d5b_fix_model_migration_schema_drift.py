"""fix model/migration schema drift found via real Postgres testing

Two real, previously-undetected bugs were found this session by actually
running migrations + inserts against a live PostgreSQL database (every
prior session's test suite silently used a SQLite fallback built with
`Base.metadata.create_all()`, which builds tables FROM the current models -
so model/migration drift was invisible to it):

1. Several JSON-typed SQLAlchemy model columns (User.target_company_ids,
   Company.roles/tags/preferred_branches/resume_keywords, Round.subjects_tested,
   Question.tags, QAQuestion.tags) were actually migrated as real Postgres
   ARRAY columns back in f1b54c101efb. Every insert against those columns
   failed on Postgres with "malformed array literal". The MODELS were fixed
   to match the ALREADY-MIGRATED schema (no data migration needed here -
   this file only adds the columns below).

2. Company.source_type / verified_by / verified_at / confidence exist on the
   model (support for Phase 10's Verified/Student-Reported/AI-Recommended
   distinction) but were never actually migrated - added here.

Revision ID: c3f7e9a21d5b
Revises: 9d2a1f4c7b3e
Create Date: 2026-08-23 12:00:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "c3f7e9a21d5b"
down_revision: Union[str, None] = "9d2a1f4c7b3e"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("companies", sa.Column("source_type", sa.String(), nullable=True, server_default="placement_cell"))
    op.add_column("companies", sa.Column("verified_by", sa.String(), nullable=True))
    op.add_column("companies", sa.Column("verified_at", sa.DateTime(), nullable=True))
    op.add_column("companies", sa.Column("confidence", sa.String(), nullable=True, server_default="High"))

    # readiness_scores.algorithm_version exists on the ReadinessScore model
    # (and was already being read/written by app code, including the
    # Phase 4 "algorithm_version" work from an earlier session) but was
    # NEVER actually migrated - only found now that inserts are being run
    # against a real migrated Postgres database instead of SQLite's
    # create_all(). Every readiness computation would have failed outright
    # in a real deployment before this fix.
    op.add_column("readiness_scores", sa.Column("algorithm_version", sa.String(), nullable=True, server_default="v1"))

    # roadmaps.target_company_ids / target_company_names: same story - used
    # by app/api/v1/endpoints/roadmap.py on every roadmap generation, never
    # migrated. Every POST /roadmap/generate would fail on real Postgres.
    op.add_column("roadmaps", sa.Column("target_company_ids", sa.JSON(), nullable=True))
    op.add_column("roadmaps", sa.Column("target_company_names", sa.JSON(), nullable=True))


def downgrade() -> None:
    op.drop_column("roadmaps", "target_company_names")
    op.drop_column("roadmaps", "target_company_ids")
    op.drop_column("readiness_scores", "algorithm_version")
    op.drop_column("companies", "confidence")
    op.drop_column("companies", "verified_at")
    op.drop_column("companies", "verified_by")
    op.drop_column("companies", "source_type")
