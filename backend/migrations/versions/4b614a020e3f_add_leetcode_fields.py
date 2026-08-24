"""add leetcode fields

Revision ID: 4b614a020e3f
Revises: ca02351769b5
Create Date: 2026-08-12 17:27:35.393816

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "4b614a020e3f"
down_revision: Union[str, None] = "ca02351769b5"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create LeetCode logs table
    op.create_table(
        "leetcode_logs",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("problem_title", sa.String(), nullable=False),
        sa.Column("problem_slug", sa.String(), nullable=True),
        sa.Column("difficulty", sa.String(), nullable=False),
        sa.Column("topic", sa.String(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("solved_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    # Add LeetCode fields to existing users table.
    # Server defaults are important because the users table
    # already contains existing records.
    op.add_column(
        "users",
        sa.Column(
            "leetcode_username",
            sa.String(),
            nullable=True,
        ),
    )

    op.add_column(
        "users",
        sa.Column(
            "leetcode_daily_goal",
            sa.Integer(),
            nullable=False,
            server_default="1",
        ),
    )

    op.add_column(
        "users",
        sa.Column(
            "leetcode_total_solved",
            sa.Integer(),
            nullable=False,
            server_default="0",
        ),
    )

    op.add_column(
        "users",
        sa.Column(
            "leetcode_easy_solved",
            sa.Integer(),
            nullable=False,
            server_default="0",
        ),
    )

    op.add_column(
        "users",
        sa.Column(
            "leetcode_medium_solved",
            sa.Integer(),
            nullable=False,
            server_default="0",
        ),
    )

    op.add_column(
        "users",
        sa.Column(
            "leetcode_hard_solved",
            sa.Integer(),
            nullable=False,
            server_default="0",
        ),
    )

    op.add_column(
        "users",
        sa.Column(
            "leetcode_streak",
            sa.Integer(),
            nullable=False,
            server_default="0",
        ),
    )

    op.add_column(
        "users",
        sa.Column(
            "leetcode_last_solved_date",
            sa.String(),
            nullable=True,
        ),
    )


def downgrade() -> None:
    # Remove LeetCode fields from users table
    op.drop_column("users", "leetcode_last_solved_date")
    op.drop_column("users", "leetcode_streak")
    op.drop_column("users", "leetcode_hard_solved")
    op.drop_column("users", "leetcode_medium_solved")
    op.drop_column("users", "leetcode_easy_solved")
    op.drop_column("users", "leetcode_total_solved")
    op.drop_column("users", "leetcode_daily_goal")
    op.drop_column("users", "leetcode_username")

    # Remove LeetCode logs table
    op.drop_table("leetcode_logs")