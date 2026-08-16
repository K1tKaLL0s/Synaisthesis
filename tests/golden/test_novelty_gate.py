"""M2.6 golden tests for low-novelty research gate and 69/70 routing."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from synaisthesis.agents.auditor import NoveltyAuditor
from synaisthesis.agents.novelty_reviewer import NoveltyReviewer
from synaisthesis.application.novelty_service import (
    open_low_novelty_research_gate,
    resolve_low_novelty_research_decision,
    start_novelty_review,
)
from synaisthesis.domain.enums import (
    GateStatus,
    NoveltyResearchDecision,
    NoveltyStatus,
    PriorArtCoverageStatus,
    ProvenanceType,
    QualificationGateType,
    ResearchRoute,
)
from synaisthesis.domain.errors import DomainError
from synaisthesis.domain.novelty import THEORY_NOVELTY_POLICY

NOW = datetime(2026, 8, 17, 1, 0, 0, tzinfo=UTC)


def _theory_scores(value: int = 4) -> dict[str, int]:
    return {item.item_id: value for item in THEORY_NOVELTY_POLICY.items}


def _review():
    scores = {
        "T1": 4,
        "T2": 4,
        "T3": 4,
        "T4": 4,
        "A1": 3,
        "A2": 3,
        "A3": 3,
        "A4": 3,
        "A5": 2,
    }
    primary = NoveltyReviewer.create(
        session_id="s1",
        route=ResearchRoute.THEORY,
        model_family="family-a",
        scores=scores,
    )
    auditor = NoveltyAuditor.create(
        session_id="s2",
        route=ResearchRoute.THEORY,
        model_family="family-b",
        scores=scores,
    )
    return start_novelty_review(
        review_id="nr-golden",
        project_id="p-1",
        route=ResearchRoute.THEORY,
        policy_version=THEORY_NOVELTY_POLICY.policy_version,
        subject_artifact_type="EarlyFormalizationBundle",
        subject_artifact_id="ef-1",
        subject_artifact_hash="f" * 64,
        neighbor_evidence_set_id="ps-1",
        primary_reviewer=primary,
        auditor_reviewer=auditor,
        coverage_status=PriorArtCoverageStatus.COMPLETE,
        nearest_overlap_refs=("n-1",),
        strongest_difference_refs=("n-2",),
        limitations=("patents unsearched",),
        at=NOW,
    )


def test_69_opens_low_novelty_gate():
    # all scores 3: 3*(3+3+2+2) + 3*(3+2+2+2+1) = 30+30=60, not 69.
    # Use mixed map for exact 69: T-items 4, A-items 3 except A5=2.
    scores = {
        "T1": 4,
        "T2": 4,
        "T3": 4,
        "T4": 4,
        "A1": 3,
        "A2": 3,
        "A3": 3,
        "A4": 3,
        "A5": 2,
    }
    primary = NoveltyReviewer.create(
        session_id="s1", route=ResearchRoute.THEORY, model_family="family-a", scores=scores
    )
    auditor = NoveltyAuditor.create(
        session_id="s2", route=ResearchRoute.THEORY, model_family="family-b", scores=scores
    )
    review = start_novelty_review(
        review_id="nr-69",
        project_id="p-1",
        route=ResearchRoute.THEORY,
        policy_version=THEORY_NOVELTY_POLICY.policy_version,
        subject_artifact_type="EarlyFormalizationBundle",
        subject_artifact_id="ef-1",
        subject_artifact_hash="f" * 64,
        neighbor_evidence_set_id="ps-1",
        primary_reviewer=primary,
        auditor_reviewer=auditor,
        coverage_status=PriorArtCoverageStatus.COMPLETE,
        nearest_overlap_refs=("n-1",),
        strongest_difference_refs=("n-2",),
        limitations=(),
        at=NOW,
    )
    assert review.novelty_total == 69
    assert review.status is NoveltyStatus.NOVELTY_RESEARCH_REQUIRED
    gate = open_low_novelty_research_gate(review=review, gate_id="g-low")
    assert gate.gate_type is QualificationGateType.LOW_NOVELTY_RESEARCH_DECISION
    assert gate.binding.artifact_hash == review.artifact_hash
    assert gate.binding.novelty_total == 69
    assert gate.binding.route is ResearchRoute.THEORY


def test_model_actor_cannot_resolve_low_novelty_gate():
    review = _review()
    gate = open_low_novelty_research_gate(review=review, gate_id="g-low")
    with pytest.raises(DomainError) as exc_info:
        resolve_low_novelty_research_decision(
            gate=gate,
            decision=NoveltyResearchDecision.CONTINUE_WITH_RECORDED_OVERRIDE.value,
            actor=ProvenanceType.ASSISTANT_PROPOSAL,
            user_event_id="model-event",
            current_review_hash=review.artifact_hash,
            at=NOW,
        )
    assert exc_info.value.error_code == "CONFIRMATION_REQUIRES_USER_EVENT"


def test_user_override_creates_bound_override():
    review = _review()
    gate = open_low_novelty_research_gate(review=review, gate_id="g-low")
    resolved, override = resolve_low_novelty_research_decision(
        gate=gate,
        decision=NoveltyResearchDecision.CONTINUE_WITH_RECORDED_OVERRIDE.value,
        actor=ProvenanceType.USER_DECISION,
        user_event_id="uev-override",
        current_review_hash=review.artifact_hash,
        at=NOW,
    )
    assert resolved.status is GateStatus.RESOLVED
    assert override is not None
    assert override.review_artifact_hash == review.artifact_hash
    assert override.route is ResearchRoute.THEORY


def test_stale_review_hash_blocks_override():
    review = _review()
    gate = open_low_novelty_research_gate(review=review, gate_id="g-low")
    with pytest.raises(DomainError) as exc_info:
        resolve_low_novelty_research_decision(
            gate=gate,
            decision=NoveltyResearchDecision.CONTINUE_WITH_RECORDED_OVERRIDE.value,
            actor=ProvenanceType.USER_DECISION,
            user_event_id="uev-stale",
            current_review_hash="0" * 64,
            at=NOW,
        )
    assert exc_info.value.error_code == "STALE_NOVELTY_BINDING"
