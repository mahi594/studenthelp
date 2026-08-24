"""institutions + interventions tables, tenant isolation, honest readiness/intervention data

Adds two tables that existed as SQLAlchemy models but were NEVER migrated
(institutions, interventions) - on a real alembic-managed database, every
TPO/intervention endpoint would have failed with "relation does not exist".
Also adds:
  - users.institution_id (FK -> institutions.id): the actual tenant-scope
    column every TPO query now filters on.
  - interventions.institution_id + sample-size columns (eligible_count,
    pre_assessed_count, reassessed_count), so intervention impact is always
    shown with its sample size and is never fabricated.
  - readiness_scores.composite_score becomes nullable, and
    readiness_scores.data_status is added, so an "insufficient data" state
    can be stored honestly instead of a fabricated 0 or default score.

Revision ID: 9d2a1f4c7b3e
Revises: 7a3f9c2e1d44
Create Date: 2026-08-22 00:00:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "9d2a1f4c7b3e"
down_revision: Union[str, None] = "7a3f9c2e1d44"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ---- institutions (was model-only; never migrated) ----
    op.create_table(
        "institutions",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("domain", sa.String(), nullable=True),
        sa.Column("logo_url", sa.String(), nullable=True),
        sa.Column("primary_color", sa.String(), nullable=True),
        sa.Column("placement_cell_name", sa.String(), nullable=True),
        sa.Column("academic_year", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_institutions_name"), "institutions", ["name"], unique=True)

    # ---- users.institution_id (was model-only; never migrated) ----
    op.add_column("users", sa.Column("institution_id", postgresql.UUID(as_uuid=True), nullable=True))
    op.create_foreign_key(
        "fk_users_institution_id", "users", "institutions", ["institution_id"], ["id"]
    )
    # must_change_password exists on the model but wasn't confirmed present -
    # guard with a checkfirst-style pattern via batch alter is unnecessary
    # here since 7a3f9c2e1d44 already added it; left untouched.

    # ---- interventions (was model-only; never migrated) ----
    op.create_table(
        "interventions",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("title", sa.String(), nullable=False),
        sa.Column("skill_topic", sa.String(), nullable=False),
        sa.Column("intervention_type", sa.String(), nullable=True),
        sa.Column("target_branch", sa.String(), nullable=True),
        sa.Column("target_student_ids", sa.JSON(), nullable=False),
        sa.Column("status", sa.String(), nullable=True),
        sa.Column("pre_avg_score", sa.Integer(), nullable=True),
        sa.Column("post_avg_score", sa.Integer(), nullable=True),
        sa.Column("improvement_delta", sa.Integer(), nullable=True),
        sa.Column("eligible_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("pre_assessed_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("reassessed_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("institution_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("created_by_user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("completed_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["institution_id"], ["institutions.id"]),
        sa.ForeignKeyConstraint(["created_by_user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    # ---- readiness_scores: honest insufficient-data state ----
    op.alter_column("readiness_scores", "composite_score", existing_type=sa.Integer(), nullable=True)
    op.add_column(
        "readiness_scores",
        sa.Column("data_status", sa.String(), nullable=False, server_default="sufficient"),
    )


def downgrade() -> None:
    op.drop_column("readiness_scores", "data_status")
    op.alter_column("readiness_scores", "composite_score", existing_type=sa.Integer(), nullable=False)

    op.drop_table("interventions")

    op.drop_constraint("fk_users_institution_id", "users", type_="foreignkey")
    op.drop_column("users", "institution_id")

    op.drop_index(op.f("ix_institutions_name"), table_name="institutions")
    op.drop_table("institutions")
