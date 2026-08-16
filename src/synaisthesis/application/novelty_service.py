"""Novelty review application service (blueprint 07 section 3, M2.6)."""

from __future__ import annotations

from datetime import datetime

from synaisthesis.agents.auditor import NoveltyAuditor
from synaisthesis.agents.novelty_reviewer import NoveltyReviewer
from synaisthesis.domain.enums import (
    NoveltyResearchDecision,
    NoveltyStatus,
    PriorArtCoverageStatus,
    ProvenanceType,
    QualificationGateType,
    ResearchRoute,
)
from synaisthesis.domain.errors import DomainError
from synaisthesis.domain.gate import Gate, GateBinding
from synaisthesis.domain.novelty import (
    LowNoveltyOverride,
    NoveltyReview,
)


def start_novelty_review(
    *,
    review_id: str,
    project_id: str,
    route: ResearchRoute,
    policy_version: str,
    subject_artifact_type: str,
    subject_artifact_id: str,
    subject_artifact_hash: str,
    neighbor_evidence_set_id: str,
    primary_reviewer: NoveltyReviewer,
    auditor_reviewer: NoveltyAuditor,
    coverage_status: PriorArtCoverageStatus,
    nearest_overlap_refs: tuple[str, ...],
    strongest_difference_refs: tuple[str, ...],
    limitations: tuple[str, ...],
    at: datetime,
    require_independent_families: bool = True,
) -> NoveltyReview:
    """Score with two isolated reviewers and freeze a route-locked review."""
    if primary_reviewer.route is not route or auditor_reviewer.route is not route:
        raise DomainError(
            "reviewer route does not match requested route",
            error_code="NOVELTY_ROUTE_MISMATCH",
        )
    primary_scorecard, primary_evidence = primary_reviewer.score(
        subject_artifact_id=subject_artifact_id,
        subject_artifact_hash=subject_artifact_hash,
    )
    auditor_scorecard, auditor_evidence = auditor_reviewer.score(
        subject_artifact_id=subject_artifact_id,
        subject_artifact_hash=subject_artifact_hash,
    )

    review_valid = True
    reason_lines = list(limitations)
    if primary_reviewer.session_id == auditor_reviewer.session_id:
        review_valid = False
        reason_lines.append("single reviewer session: independence violated")
    if (
        require_independent_families
        and primary_reviewer.model_family == auditor_reviewer.model_family
    ):
        review_valid = False
        reason_lines.append("reviewer model families are not independent")
    if coverage_status is not PriorArtCoverageStatus.COMPLETE:
        review_valid = False
        reason_lines.append(f"coverage_status={coverage_status.value}")
    evidence_by_item = {item.item_id: item for item in primary_evidence}
    if len(evidence_by_item) != len(primary_scorecard.item_scores):
        review_valid = False
        reason_lines.append("primary scorecard evidence incomplete")
    if len({item.item_id for item in auditor_evidence}) != len(auditor_scorecard.item_scores):
        review_valid = False
        reason_lines.append("auditor scorecard evidence incomplete")

    return NoveltyReview.create(
        review_id=review_id,
        project_id=project_id,
        route=route,
        policy_version=policy_version,
        subject_artifact_type=subject_artifact_type,
        subject_artifact_id=subject_artifact_id,
        subject_artifact_hash=subject_artifact_hash,
        neighbor_evidence_set_id=neighbor_evidence_set_id,
        reviewer_session_ids=(
            primary_reviewer.session_id,
            auditor_reviewer.session_id,
        ),
        primary_scorecard=primary_scorecard,
        auditor_scorecard=auditor_scorecard,
        coverage_status=coverage_status,
        nearest_overlap_refs=nearest_overlap_refs,
        strongest_difference_refs=strongest_difference_refs,
        limitations=tuple(reason_lines),
        created_at=at,
        review_valid=review_valid,
    )


def open_low_novelty_research_gate(
    *,
    review: NoveltyReview,
    gate_id: str,
) -> Gate:
    """Open the low-novelty user gate for non-qualifying reviews."""
    if review.status in {
        NoveltyStatus.NOVELTY_QUALIFIED,
        NoveltyStatus.ENGINEERING_NOVELTY_QUALIFIED,
    }:
        raise DomainError(
            "qualified novelty review does not require a low-novelty gate",
            error_code="NOVELTY_GATE_NOT_REQUIRED",
        )
    return Gate(
        gate_id=gate_id,
        project_id=review.project_id,
        gate_type=QualificationGateType.LOW_NOVELTY_RESEARCH_DECISION,
        binding=GateBinding(
            gate_type=QualificationGateType.LOW_NOVELTY_RESEARCH_DECISION,
            artifact_id=review.review_id,
            version=None,
            artifact_hash=review.artifact_hash,
            input_spec_hash=review.subject_artifact_hash,
            route=review.route,
            coverage_status=review.coverage_status,
            novelty_total=review.novelty_total,
            nearest_overlap_refs=review.nearest_overlap_refs,
            limitations=review.limitations,
        ),
    )


def resolve_low_novelty_research_decision(
    *,
    gate: Gate,
    decision: str,
    actor: ProvenanceType,
    user_event_id: str,
    current_review_hash: str,
    at: datetime,
) -> tuple[Gate, LowNoveltyOverride | None]:
    """Resolve LOW_NOVELTY_RESEARCH_DECISION with current review hash binding."""
    if gate.gate_type is not QualificationGateType.LOW_NOVELTY_RESEARCH_DECISION:
        raise DomainError(
            f"gate type {gate.gate_type.value} cannot resolve a low-novelty decision",
            error_code="GATE_TYPE_MISMATCH",
        )
    if gate.binding.artifact_hash != current_review_hash:
        raise DomainError(
            "current novelty review hash does not match the gate binding",
            error_code="STALE_NOVELTY_BINDING",
        )
    resolved = gate.resolve(
        decision=decision,
        actor=actor,
        user_event_id=user_event_id,
        at=at,
    )
    if decision != NoveltyResearchDecision.CONTINUE_WITH_RECORDED_OVERRIDE.value:
        return resolved, None
    route = gate.binding.route
    if route is None:
        raise DomainError(
            "low-novelty gate binding has no route",
            error_code="GATE_BINDING_INVALID",
        )
    override = LowNoveltyOverride(
        review_id=gate.binding.artifact_id,
        route=route,
        review_artifact_hash=gate.binding.artifact_hash,
        actor=actor,
        user_event_id=user_event_id,
        decided_at=at,
    )
    return resolved, override


__all__ = [
    "open_low_novelty_research_gate",
    "resolve_low_novelty_research_decision",
    "start_novelty_review",
]
