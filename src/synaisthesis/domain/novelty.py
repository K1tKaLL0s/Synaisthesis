"""Route-specific novelty scoring and routing (blueprint 03A, sections 8-9)."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import asdict, dataclass
from datetime import datetime
from types import MappingProxyType
from typing import Any

from synaisthesis.domain.enums import (
    NoveltyScoreComponent,
    NoveltyStatus,
    PriorArtCoverageStatus,
    ProvenanceType,
    QualificationGateType,
    QualifiedNextTarget,
    ResearchRoute,
)
from synaisthesis.domain.errors import DomainError
from synaisthesis.domain.event import canonicalize, sha256_hex
from synaisthesis.domain.qualification import is_user_actor

POLICY_VERSION = "03A.V1"


def _canonical_payload(value: Any) -> dict[str, Any]:
    payload = canonicalize(value)
    if not isinstance(payload, dict):
        raise TypeError("novelty payload must canonicalize to an object")
    return payload


@dataclass(frozen=True, slots=True)
class NoveltyScoreItem:
    """One weighted novelty item (03A, sections 8.2/8.3)."""

    item_id: str
    component: NoveltyScoreComponent
    weight: int

    @property
    def max_score(self) -> int:
        return self.weight * 5


@dataclass(frozen=True, slots=True)
class NoveltyPolicy:
    """A route-locked score policy. Theory and engineering are not interchangeable."""

    route: ResearchRoute
    policy_version: str
    items: tuple[NoveltyScoreItem, ...]

    @property
    def item_ids(self) -> frozenset[str]:
        return frozenset(item.item_id for item in self.items)

    @property
    def max_total(self) -> int:
        return sum(item.max_score for item in self.items)


THEORY_NOVELTY_POLICY = NoveltyPolicy(
    route=ResearchRoute.THEORY,
    policy_version=POLICY_VERSION,
    items=(
        NoveltyScoreItem("T1", NoveltyScoreComponent.THEORY, 3),
        NoveltyScoreItem("T2", NoveltyScoreComponent.THEORY, 3),
        NoveltyScoreItem("T3", NoveltyScoreComponent.THEORY, 2),
        NoveltyScoreItem("T4", NoveltyScoreComponent.THEORY, 2),
        NoveltyScoreItem("A1", NoveltyScoreComponent.APPLICATION, 3),
        NoveltyScoreItem("A2", NoveltyScoreComponent.APPLICATION, 2),
        NoveltyScoreItem("A3", NoveltyScoreComponent.APPLICATION, 2),
        NoveltyScoreItem("A4", NoveltyScoreComponent.APPLICATION, 2),
        NoveltyScoreItem("A5", NoveltyScoreComponent.APPLICATION, 1),
    ),
)

ENGINEERING_NOVELTY_POLICY = NoveltyPolicy(
    route=ResearchRoute.ENGINEERING,
    policy_version=POLICY_VERSION,
    items=(
        NoveltyScoreItem("E1", NoveltyScoreComponent.ENGINEERING, 3),
        NoveltyScoreItem("E2", NoveltyScoreComponent.ENGINEERING, 3),
        NoveltyScoreItem("E3", NoveltyScoreComponent.ENGINEERING, 2),
        NoveltyScoreItem("E4", NoveltyScoreComponent.ENGINEERING, 2),
        NoveltyScoreItem("E5", NoveltyScoreComponent.ENGINEERING, 2),
        NoveltyScoreItem("EA1", NoveltyScoreComponent.ENGINEERING_APPLICATION, 2),
        NoveltyScoreItem("EA2", NoveltyScoreComponent.ENGINEERING_APPLICATION, 2),
        NoveltyScoreItem("EA3", NoveltyScoreComponent.ENGINEERING_APPLICATION, 2),
        NoveltyScoreItem("EA4", NoveltyScoreComponent.ENGINEERING_APPLICATION, 2),
    ),
)


def novelty_policy_for(route: ResearchRoute) -> NoveltyPolicy:
    if route is ResearchRoute.THEORY:
        return THEORY_NOVELTY_POLICY
    if route is ResearchRoute.ENGINEERING:
        return ENGINEERING_NOVELTY_POLICY
    raise DomainError(f"unknown novelty route {route!r}", error_code="NOVELTY_ROUTE_MISMATCH")


def _immutable_scores(scores: Mapping[str, int]) -> Mapping[str, int]:
    return MappingProxyType(dict(scores))


@dataclass(frozen=True, slots=True)
class NoveltyScorecard:
    """One reviewer's initial item ratings, each in {0,1,2,3,4,5} (03A, section 8.1)."""

    reviewer_session_id: str
    route: ResearchRoute
    item_scores: Mapping[str, int]

    def __post_init__(self) -> None:
        policy = novelty_policy_for(self.route)
        scores = dict(self.item_scores)
        if set(scores) != policy.item_ids:
            raise DomainError(
                "scorecard item ids do not match the route policy",
                error_code="NOVELTY_SCORECARD_INVALID",
            )
        for item_id, rating in scores.items():
            if isinstance(rating, bool) or not isinstance(rating, int) or not 0 <= rating <= 5:
                raise DomainError(
                    f"score for {item_id} must be an integer in [0, 5]",
                    error_code="NOVELTY_SCORECARD_INVALID",
                )
        object.__setattr__(self, "item_scores", _immutable_scores(scores))

    def to_event_payload(self) -> dict[str, Any]:
        return _canonical_payload(
            {
                "reviewer_session_id": self.reviewer_session_id,
                "route": self.route,
                "item_scores": dict(self.item_scores),
            }
        )


@dataclass(frozen=True, slots=True)
class ConservativeNoveltyScores:
    """Item-wise min aggregation and the route-specific component totals."""

    conservative_item_scores: Mapping[str, int]
    theory_score: int | None
    application_score: int | None
    engineering_score: int | None
    engineering_application_score: int | None
    novelty_total: int


@dataclass(frozen=True, slots=True)
class NoveltyRouteDecision:
    """Deterministic RQ4 routing result (03A, section 8.4)."""

    status: NoveltyStatus
    gate_type: QualificationGateType | None
    next_target: QualifiedNextTarget | None
    blockers: tuple[str, ...] = ()


def calculate_conservative_novelty_score(
    *,
    route: ResearchRoute,
    primary: NoveltyScorecard,
    auditor: NoveltyScorecard,
) -> ConservativeNoveltyScores:
    """Apply q_i = min(primary_i, auditor_i) under the route-locked policy."""
    policy = novelty_policy_for(route)
    if primary.route is not route or auditor.route is not route:
        raise DomainError(
            "novelty scorecards and requested route do not match",
            error_code="NOVELTY_ROUTE_MISMATCH",
        )
    conservative = {
        item.item_id: min(primary.item_scores[item.item_id], auditor.item_scores[item.item_id])
        for item in policy.items
    }

    def component_total(component: NoveltyScoreComponent) -> int:
        return sum(
            item.weight * conservative[item.item_id]
            for item in policy.items
            if item.component is component
        )

    if route is ResearchRoute.THEORY:
        theory_score = component_total(NoveltyScoreComponent.THEORY)
        application_score = component_total(NoveltyScoreComponent.APPLICATION)
        engineering_score = None
        engineering_application_score = None
        novelty_total = theory_score + application_score
    else:
        theory_score = None
        application_score = None
        engineering_score = component_total(NoveltyScoreComponent.ENGINEERING)
        engineering_application_score = component_total(
            NoveltyScoreComponent.ENGINEERING_APPLICATION
        )
        novelty_total = engineering_score + engineering_application_score

    return ConservativeNoveltyScores(
        conservative_item_scores=_immutable_scores(conservative),
        theory_score=theory_score,
        application_score=application_score,
        engineering_score=engineering_score,
        engineering_application_score=engineering_application_score,
        novelty_total=novelty_total,
    )


def route_novelty_decision(
    *,
    review_valid: bool,
    coverage_status: PriorArtCoverageStatus,
    route: ResearchRoute,
    primary: NoveltyScorecard,
    auditor: NoveltyScorecard,
) -> NoveltyRouteDecision:
    """Apply the fixed RQ4 router: 70 auto-continue, 69/invalid opens user gate."""
    scores = calculate_conservative_novelty_score(
        route=route,
        primary=primary,
        auditor=auditor,
    )
    if not review_valid or coverage_status is not PriorArtCoverageStatus.COMPLETE:
        blockers = []
        if not review_valid:
            blockers.append("Novelty Review 无效（前置条件不满足）")
        if coverage_status is not PriorArtCoverageStatus.COMPLETE:
            blockers.append(f"RQ1 coverage_status={coverage_status.value}，不得自动通行")
        return NoveltyRouteDecision(
            status=NoveltyStatus.INCONCLUSIVE,
            gate_type=QualificationGateType.LOW_NOVELTY_RESEARCH_DECISION,
            next_target=None,
            blockers=tuple(blockers),
        )

    if scores.novelty_total >= 70:
        if route is ResearchRoute.THEORY:
            return NoveltyRouteDecision(
                status=NoveltyStatus.NOVELTY_QUALIFIED,
                gate_type=None,
                next_target=QualifiedNextTarget.S5,
            )
        return NoveltyRouteDecision(
            status=NoveltyStatus.ENGINEERING_NOVELTY_QUALIFIED,
            gate_type=None,
            next_target=QualifiedNextTarget.ENG0,
        )

    return NoveltyRouteDecision(
        status=NoveltyStatus.NOVELTY_RESEARCH_REQUIRED,
        gate_type=QualificationGateType.LOW_NOVELTY_RESEARCH_DECISION,
        next_target=None,
        blockers=(f"novelty_total={scores.novelty_total} < 70",),
    )


@dataclass(frozen=True, slots=True)
class NoveltyReview:
    """RQ4 output (03A, section 8.5), built only through create()."""

    review_id: str
    project_id: str
    route: ResearchRoute
    policy_version: str
    subject_artifact_type: str
    subject_artifact_id: str
    subject_artifact_hash: str
    neighbor_evidence_set_id: str
    reviewer_session_ids: tuple[str, ...]
    reviewer_scorecards: tuple[NoveltyScorecard, ...]
    conservative_item_scores: Mapping[str, int]
    theory_score: int | None
    application_score: int | None
    engineering_score: int | None
    engineering_application_score: int | None
    novelty_total: int
    coverage_status: PriorArtCoverageStatus
    status: NoveltyStatus
    nearest_overlap_refs: tuple[str, ...]
    strongest_difference_refs: tuple[str, ...]
    limitations: tuple[str, ...]
    artifact_hash: str
    created_at: datetime

    def __post_init__(self) -> None:
        policy = novelty_policy_for(self.route)
        if self.policy_version != policy.policy_version:
            raise DomainError(
                "policy_version does not match the route policy",
                error_code="NOVELTY_POLICY_MISMATCH",
            )
        if self.route is ResearchRoute.THEORY:
            expected_none = (self.engineering_score, self.engineering_application_score)
            if (
                self.theory_score is None
                or self.application_score is None
                or any(value is not None for value in expected_none)
            ):
                raise DomainError(
                    "theory review must only carry theory/application scores",
                    error_code="NOVELTY_ROUTE_MISMATCH",
                )
        else:
            expected_none = (self.theory_score, self.application_score)
            if (
                self.engineering_score is None
                or self.engineering_application_score is None
                or any(value is not None for value in expected_none)
            ):
                raise DomainError(
                    "engineering review must only carry engineering/application scores",
                    error_code="NOVELTY_ROUTE_MISMATCH",
                )
        if self.novelty_total < 0 or self.novelty_total > 100:
            raise DomainError(
                "novelty_total must be in [0, 100]",
                error_code="NOVELTY_TOTAL_INVALID",
            )
        expected_status = _review_status(
            coverage_status=self.coverage_status,
            novelty_total=self.novelty_total,
            route=self.route,
        )
        if self.status is not expected_status:
            raise DomainError(
                "NoveltyReview.status does not match the deterministic route",
                error_code="INVALID_NOVELTY_STATUS",
            )
        expected_hash = sha256_hex(self.content_payload())
        if self.artifact_hash != expected_hash:
            raise DomainError(
                "artifact_hash does not match the review content",
                error_code="ARTIFACT_HASH_MISMATCH",
            )
        object.__setattr__(
            self,
            "conservative_item_scores",
            _immutable_scores(self.conservative_item_scores),
        )

    @classmethod
    def create(
        cls,
        *,
        review_id: str,
        project_id: str,
        route: ResearchRoute,
        policy_version: str,
        subject_artifact_type: str,
        subject_artifact_id: str,
        subject_artifact_hash: str,
        neighbor_evidence_set_id: str,
        reviewer_session_ids: tuple[str, ...],
        primary_scorecard: NoveltyScorecard,
        auditor_scorecard: NoveltyScorecard,
        coverage_status: PriorArtCoverageStatus,
        nearest_overlap_refs: tuple[str, ...],
        strongest_difference_refs: tuple[str, ...],
        limitations: tuple[str, ...],
        created_at: datetime,
    ) -> NoveltyReview:
        """Build an immutable review with computed scores, status and hash."""
        policy = novelty_policy_for(route)
        if policy_version != policy.policy_version:
            raise DomainError(
                "policy_version does not match the route policy",
                error_code="NOVELTY_POLICY_MISMATCH",
            )
        scores = calculate_conservative_novelty_score(
            route=route,
            primary=primary_scorecard,
            auditor=auditor_scorecard,
        )
        decision = route_novelty_decision(
            review_valid=True,
            coverage_status=coverage_status,
            route=route,
            primary=primary_scorecard,
            auditor=auditor_scorecard,
        )
        content = {
            "review_id": review_id,
            "project_id": project_id,
            "route": route.value,
            "policy_version": policy_version,
            "subject_artifact_type": subject_artifact_type,
            "subject_artifact_id": subject_artifact_id,
            "subject_artifact_hash": subject_artifact_hash,
            "neighbor_evidence_set_id": neighbor_evidence_set_id,
            "reviewer_session_ids": list(reviewer_session_ids),
            "reviewer_scorecards": [
                scorecard.to_event_payload() for scorecard in (primary_scorecard, auditor_scorecard)
            ],
            "conservative_item_scores": dict(scores.conservative_item_scores),
            "theory_score": scores.theory_score,
            "application_score": scores.application_score,
            "engineering_score": scores.engineering_score,
            "engineering_application_score": scores.engineering_application_score,
            "novelty_total": scores.novelty_total,
            "coverage_status": coverage_status.value,
            "status": decision.status.value,
            "nearest_overlap_refs": list(nearest_overlap_refs),
            "strongest_difference_refs": list(strongest_difference_refs),
            "limitations": list(limitations),
            "created_at": created_at.isoformat(),
        }
        return cls(
            review_id=review_id,
            project_id=project_id,
            route=route,
            policy_version=policy_version,
            subject_artifact_type=subject_artifact_type,
            subject_artifact_id=subject_artifact_id,
            subject_artifact_hash=subject_artifact_hash,
            neighbor_evidence_set_id=neighbor_evidence_set_id,
            reviewer_session_ids=reviewer_session_ids,
            reviewer_scorecards=(primary_scorecard, auditor_scorecard),
            conservative_item_scores=scores.conservative_item_scores,
            theory_score=scores.theory_score,
            application_score=scores.application_score,
            engineering_score=scores.engineering_score,
            engineering_application_score=scores.engineering_application_score,
            novelty_total=scores.novelty_total,
            coverage_status=coverage_status,
            status=decision.status,
            nearest_overlap_refs=nearest_overlap_refs,
            strongest_difference_refs=strongest_difference_refs,
            limitations=limitations,
            artifact_hash=sha256_hex(content),
            created_at=created_at,
        )

    def content_payload(self) -> dict[str, Any]:
        """Return the hash-covered semantic content (artifact_hash excluded)."""
        return _canonical_payload(self._payload_dict(include_artifact_hash=False))

    def to_event_payload(self) -> dict[str, Any]:
        return _canonical_payload(self._payload_dict(include_artifact_hash=True))

    def _payload_dict(self, *, include_artifact_hash: bool) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "review_id": self.review_id,
            "project_id": self.project_id,
            "route": self.route,
            "policy_version": self.policy_version,
            "subject_artifact_type": self.subject_artifact_type,
            "subject_artifact_id": self.subject_artifact_id,
            "subject_artifact_hash": self.subject_artifact_hash,
            "neighbor_evidence_set_id": self.neighbor_evidence_set_id,
            "reviewer_session_ids": self.reviewer_session_ids,
            "reviewer_scorecards": [
                scorecard.to_event_payload() for scorecard in self.reviewer_scorecards
            ],
            "conservative_item_scores": dict(self.conservative_item_scores),
            "theory_score": self.theory_score,
            "application_score": self.application_score,
            "engineering_score": self.engineering_score,
            "engineering_application_score": self.engineering_application_score,
            "novelty_total": self.novelty_total,
            "coverage_status": self.coverage_status,
            "status": self.status,
            "nearest_overlap_refs": self.nearest_overlap_refs,
            "strongest_difference_refs": self.strongest_difference_refs,
            "limitations": self.limitations,
            "created_at": self.created_at,
        }
        if include_artifact_hash:
            payload["artifact_hash"] = self.artifact_hash
        return payload


def _review_status(
    *,
    coverage_status: PriorArtCoverageStatus,
    novelty_total: int,
    route: ResearchRoute,
) -> NoveltyStatus:
    if coverage_status is not PriorArtCoverageStatus.COMPLETE:
        return NoveltyStatus.INCONCLUSIVE
    if novelty_total >= 70:
        if route is ResearchRoute.THEORY:
            return NoveltyStatus.NOVELTY_QUALIFIED
        return NoveltyStatus.ENGINEERING_NOVELTY_QUALIFIED
    return NoveltyStatus.NOVELTY_RESEARCH_REQUIRED


@dataclass(frozen=True, slots=True)
class LowNoveltyOverride:
    """A real user low-novelty continue decision, bound to one review hash."""

    review_id: str
    route: ResearchRoute
    review_artifact_hash: str
    actor: ProvenanceType
    user_event_id: str
    decided_at: datetime

    def __post_init__(self) -> None:
        if not is_user_actor(self.actor):
            raise DomainError(
                f"low-novelty override requires a real user event; got actor={self.actor.value}",
                error_code="CONFIRMATION_REQUIRES_USER_EVENT",
            )

    def to_event_payload(self) -> dict[str, Any]:
        return _canonical_payload(asdict(self))


__all__ = [
    "ENGINEERING_NOVELTY_POLICY",
    "POLICY_VERSION",
    "THEORY_NOVELTY_POLICY",
    "ConservativeNoveltyScores",
    "LowNoveltyOverride",
    "NoveltyPolicy",
    "NoveltyReview",
    "NoveltyRouteDecision",
    "NoveltyScoreItem",
    "NoveltyScorecard",
    "calculate_conservative_novelty_score",
    "novelty_policy_for",
    "route_novelty_decision",
]
