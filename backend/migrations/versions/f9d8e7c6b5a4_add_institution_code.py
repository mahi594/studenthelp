"""add code column to institutions table for onboarding

Revision ID: f9d8e7c6b5a4
Revises: e8c9d0a1b2c3
Create Date: 2026-08-25 00:00:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "f9d8e7c6b5a4"
down_revision: Union[str, None] = "e8c9d0a1b2c3"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("institutions", sa.Column("code", sa.String(), nullable=True))
    op.create_index(op.f("ix_institutions_code"), "institutions", ["code"], unique=True)


def downgrade() -> None:
    op.drop_index(op.f("ix_institutions_code"), table_name="institutions")
    op.drop_column("institutions", "code")
