"""add must_change_password to users (admin temp password flow)

Revision ID: 7a3f9c2e1d44
Revises: 4b614a020e3f
Create Date: 2026-08-18 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "7a3f9c2e1d44"
down_revision: Union[str, None] = "4b614a020e3f"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column("must_change_password", sa.Boolean(), nullable=False, server_default=sa.false()),
    )
    # Drop the server_default after backfilling existing rows - keeps the
    # column's Python-level default (in the model) as the single source of
    # truth going forward, same pattern as email_verified before it.
    op.alter_column("users", "must_change_password", server_default=None)


def downgrade() -> None:
    op.drop_column("users", "must_change_password")
