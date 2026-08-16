"""create early research qualification domain tables

Revision ID: 0002
Revises: 0001
Create Date: 2026-08-16
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0002"
down_revision: str | None = "0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "research_specs",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("project_id", sa.String(), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("s1_natural_language_spec", sa.JSON(), nullable=False),
        sa.Column("s4_scope_spec", sa.JSON(), nullable=True),
        sa.Column("user_confirmed", sa.Boolean(), nullable=False),
        sa.Column("confirmed_at", sa.DateTime(), nullable=True),
        sa.Column("content_hash", sa.String(), nullable=False),
    )

    op.create_table(
        "model_profiles",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("provider", sa.String(), nullable=False),
        sa.Column("model", sa.String(), nullable=False),
        sa.Column("family", sa.String(), nullable=False),
        sa.Column("reasoning_tier", sa.String(), nullable=False),
        sa.Column("structured_output_support", sa.Boolean(), nullable=False),
        sa.Column("cost_profile", sa.JSON(), nullable=False),
        sa.Column("privacy_profile", sa.JSON(), nullable=False),
        sa.Column("enabled", sa.Boolean(), nullable=False),
    )

    op.create_table(
        "formalization_capability_decisions",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("project_id", sa.String(), nullable=False),
        sa.Column("research_spec_id", sa.String(), nullable=False),
        sa.Column("route", sa.String(), nullable=False),
        sa.Column("model_profile_id", sa.String(), nullable=True),
        sa.Column("capability_evidence_artifact_id", sa.String(), nullable=True),
        sa.Column("input_spec_hash", sa.String(), nullable=False),
        sa.Column("budget_snapshot_id", sa.String(), nullable=True),
        sa.Column("privacy_policy_snapshot_id", sa.String(), nullable=True),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("blocker", sa.String(), nullable=True),
    )

    op.create_table(
        "prior_art_searches",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("project_id", sa.String(), nullable=False),
        sa.Column("research_spec_id", sa.String(), nullable=False),
        sa.Column("input_spec_hash", sa.String(), nullable=False),
        sa.Column("query_records_artifact_id", sa.String(), nullable=True),
        sa.Column("academic_neighbor_count", sa.Integer(), nullable=False),
        sa.Column("engineering_neighbor_count", sa.Integer(), nullable=False),
        sa.Column("patent_neighbor_count", sa.Integer(), nullable=False),
        sa.Column("coverage_status", sa.String(), nullable=False),
        sa.Column("coverage_blockers_artifact_id", sa.String(), nullable=True),
        sa.Column("artifact_hash", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )

    op.create_table(
        "prior_art_neighbors",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column(
            "search_id",
            sa.String(),
            sa.ForeignKey("prior_art_searches.id"),
            nullable=False,
        ),
        sa.Column("neighbor_type", sa.String(), nullable=False),
        sa.Column("stable_identifier", sa.String(), nullable=False),
        sa.Column("canonical_url", sa.String(), nullable=True),
        sa.Column("metadata_artifact_id", sa.String(), nullable=True),
        sa.Column("metadata_verified", sa.Boolean(), nullable=False),
        sa.Column("maturity_evidence_artifact_id", sa.String(), nullable=True),
        sa.Column("theory_proximity", sa.Float(), nullable=True),
        sa.Column("application_proximity", sa.Float(), nullable=True),
        sa.Column("similarity_evidence_artifact_id", sa.String(), nullable=True),
        sa.Column("rank", sa.Integer(), nullable=False),
    )

    op.create_table(
        "formalization_feasibility_assessments",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("project_id", sa.String(), nullable=False),
        sa.Column("research_spec_id", sa.String(), nullable=False),
        sa.Column("prior_art_search_id", sa.String(), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("input_spec_hash", sa.String(), nullable=False),
        sa.Column("assessor_session_ids_artifact_id", sa.String(), nullable=True),
        sa.Column("theory_predicates_artifact_id", sa.String(), nullable=True),
        sa.Column("engineering_predicates_artifact_id", sa.String(), nullable=True),
        sa.Column("route_classification", sa.String(), nullable=False),
        sa.Column("recommended_route", sa.String(), nullable=True),
        sa.Column("missing_information_artifact_id", sa.String(), nullable=True),
        sa.Column("artifact_hash", sa.String(), nullable=False),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("supersedes_id", sa.String(), nullable=True),
    )

    op.create_table(
        "engineering_route_selections",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("project_id", sa.String(), nullable=False),
        sa.Column("feasibility_assessment_id", sa.String(), nullable=False),
        sa.Column("decision", sa.String(), nullable=False),
        sa.Column("user_actor_id", sa.String(), nullable=False),
        sa.Column("decision_event_id", sa.String(), nullable=False),
        sa.Column("bound_assessment_hash", sa.String(), nullable=False),
        sa.Column("input_spec_hash", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )

    op.create_table(
        "early_formalizations",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("project_id", sa.String(), nullable=False),
        sa.Column("research_spec_id", sa.String(), nullable=False),
        sa.Column("prior_art_search_id", sa.String(), nullable=False),
        sa.Column("capability_decision_id", sa.String(), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("input_spec_hash", sa.String(), nullable=False),
        sa.Column("formula_bundle_artifact_id", sa.String(), nullable=True),
        sa.Column("formula_bundle_hash", sa.String(), nullable=True),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("supersedes_id", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )

    op.create_table(
        "engineering_concepts",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("project_id", sa.String(), nullable=False),
        sa.Column("research_spec_id", sa.String(), nullable=False),
        sa.Column("feasibility_assessment_id", sa.String(), nullable=False),
        sa.Column("route_selection_id", sa.String(), nullable=False),
        sa.Column("prior_art_search_id", sa.String(), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("input_spec_hash", sa.String(), nullable=False),
        sa.Column("concept_bundle_artifact_id", sa.String(), nullable=True),
        sa.Column("concept_bundle_hash", sa.String(), nullable=True),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("supersedes_id", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )

    op.create_table(
        "novelty_reviews",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("project_id", sa.String(), nullable=False),
        sa.Column("route", sa.String(), nullable=False),
        sa.Column("subject_artifact_type", sa.String(), nullable=False),
        sa.Column("subject_artifact_id", sa.String(), nullable=False),
        sa.Column("prior_art_search_id", sa.String(), nullable=False),
        sa.Column("policy_version", sa.String(), nullable=False),
        sa.Column("coverage_status", sa.String(), nullable=False),
        sa.Column("theory_score", sa.Integer(), nullable=True),
        sa.Column("application_score", sa.Integer(), nullable=True),
        sa.Column("engineering_score", sa.Integer(), nullable=True),
        sa.Column("engineering_application_score", sa.Integer(), nullable=True),
        sa.Column("novelty_total", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("scorecard_artifact_id", sa.String(), nullable=True),
        sa.Column("artifact_hash", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )

    op.create_table(
        "novelty_score_items",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column(
            "novelty_review_id",
            sa.String(),
            sa.ForeignKey("novelty_reviews.id"),
            nullable=False,
        ),
        sa.Column("reviewer_session_id", sa.String(), nullable=False),
        sa.Column("criterion_id", sa.String(), nullable=False),
        sa.Column("rating", sa.Integer(), nullable=False),
        sa.Column("weight", sa.Integer(), nullable=False),
        sa.Column("evidence_refs_artifact_id", sa.String(), nullable=True),
        sa.Column("rationale_artifact_id", sa.String(), nullable=True),
    )

    op.create_table(
        "human_gates",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("project_id", sa.String(), nullable=False),
        sa.Column("run_id", sa.String(), nullable=True),
        sa.Column("gate_type", sa.String(), nullable=False),
        sa.Column("reason", sa.String(), nullable=True),
        sa.Column("semantic_diff_artifact_id", sa.String(), nullable=True),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("decision", sa.String(), nullable=True),
        sa.Column("resolved_at", sa.DateTime(), nullable=True),
    )


def downgrade() -> None:
    op.drop_table("human_gates")
    op.drop_table("novelty_score_items")
    op.drop_table("novelty_reviews")
    op.drop_table("engineering_concepts")
    op.drop_table("early_formalizations")
    op.drop_table("engineering_route_selections")
    op.drop_table("formalization_feasibility_assessments")
    op.drop_table("prior_art_neighbors")
    op.drop_table("prior_art_searches")
    op.drop_table("formalization_capability_decisions")
    op.drop_table("model_profiles")
    op.drop_table("research_specs")
