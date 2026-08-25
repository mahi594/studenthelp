"""add qa_upvotes table for single upvote enforcement

Revision ID: a1b2c3d4e5f6
Revises: f9d8e7c6b5a4
Create Date: 2026-08-25 01:00:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "a1b2c3d4e5f6"
down_revision: Union[str, None] = "f9d8e7c6b5a4"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "qa_upvotes",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("answer_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("qa_answers.id"), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.UniqueConstraint("user_id", "answer_id", name="uq_user_answer_upvote"),
    )


def downgrade() -> None:
    op.drop_table("qa_upvotes")
