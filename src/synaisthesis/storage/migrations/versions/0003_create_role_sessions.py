"""create role_sessions table

Revision ID: 0003
Revises: 0002
Create Date: 2026-08-16
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0003"
down_revision: str | None = "0002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "role_sessions",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("run_id", sa.String(), nullable=True),
        sa.Column("round_id", sa.Integer(), nullable=True),
        sa.Column("role", sa.String(), nullable=False),
        sa.Column("model_profile_id", sa.String(), nullable=True),
        sa.Column("visibility_policy_id", sa.String(), nullable=True),
        sa.Column("isolated_context_hash", sa.String(), nullable=False),
        sa.Column("session_status", sa.String(), nullable=True),
    )


def downgrade() -> None:
    op.drop_table("role_sessions")
