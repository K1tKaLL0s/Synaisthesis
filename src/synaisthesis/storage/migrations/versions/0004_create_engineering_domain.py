"""create engineering workflow domain tables

Revision ID: 0004
Revises: 0003
Create Date: 2026-08-17
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0004"
down_revision: str | None = "0003"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "engineering_workflow_runs",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("project_id", sa.String(), nullable=False),
        sa.Column("engineering_concept_id", sa.String(), nullable=False),
        sa.Column("stage_id", sa.String(), nullable=False),
        sa.Column("input_artifact_ids", sa.JSON(), nullable=False),
        sa.Column("output_artifact_id", sa.String(), nullable=True),
        sa.Column("output_hash", sa.String(), nullable=True),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("gate_id", sa.String(), nullable=True),
        sa.Column("started_at", sa.DateTime(), nullable=False),
        sa.Column("ended_at", sa.DateTime(), nullable=True),
    )

    op.create_table(
        "engineering_requirements",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("project_id", sa.String(), nullable=False),
        sa.Column("baseline_version", sa.Integer(), nullable=False),
        sa.Column("requirement_key", sa.String(), nullable=False),
        sa.Column("requirement_type", sa.String(), nullable=False),
        sa.Column("statement", sa.String(), nullable=False),
        sa.Column("source_refs_artifact_id", sa.String(), nullable=True),
        sa.Column("priority", sa.String(), nullable=False),
        sa.Column("measurement_method", sa.String(), nullable=True),
        sa.Column("unit", sa.String(), nullable=True),
        sa.Column("threshold", sa.String(), nullable=True),
        sa.Column("tolerance", sa.String(), nullable=True),
        sa.Column("verification_method", sa.String(), nullable=False),
        sa.Column("acceptance_criterion", sa.String(), nullable=False),
        sa.Column("owner", sa.String(), nullable=False),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("content_hash", sa.String(), nullable=False),
    )

    op.create_table(
        "engineering_trace_edges",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("project_id", sa.String(), nullable=False),
        sa.Column("from_type", sa.String(), nullable=False),
        sa.Column("from_id", sa.String(), nullable=False),
        sa.Column("relation", sa.String(), nullable=False),
        sa.Column("to_type", sa.String(), nullable=False),
        sa.Column("to_id", sa.String(), nullable=False),
        sa.Column("baseline_version", sa.Integer(), nullable=False),
        sa.Column("evidence_artifact_id", sa.String(), nullable=True),
    )

    op.create_table(
        "engineering_manuscripts",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("project_id", sa.String(), nullable=False),
        sa.Column("manuscript_type", sa.String(), nullable=False),
        sa.Column("evidence_tier", sa.String(), nullable=False),
        sa.Column("master_artifact_id", sa.String(), nullable=False),
        sa.Column("master_version", sa.Integer(), nullable=False),
        sa.Column("master_hash", sa.String(), nullable=False),
        sa.Column("claim_evidence_matrix_artifact_id", sa.String(), nullable=True),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("content_hash", sa.String(), nullable=False),
        sa.Column("supersedes_id", sa.String(), nullable=True),
    )


def downgrade() -> None:
    op.drop_table("engineering_manuscripts")
    op.drop_table("engineering_trace_edges")
    op.drop_table("engineering_requirements")
    op.drop_table("engineering_workflow_runs")
