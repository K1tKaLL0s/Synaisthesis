"""Early-qualification Human Gate domain objects (blueprint 08, section 15)."""

from __future__ import annotations

from dataclasses import asdict, dataclass, replace
from datetime import datetime
from typing import Any

from synaisthesis.domain.engineering import (
    EngineeringArchitectureReviewDecision,
    EngineeringDeliveryAcceptanceDecision,
    EngineeringGateType,
    EngineeringProfileChoice,
    FormalManuscriptDecision,
    PrototypeExecutionAuthorizationDecision,
)
from synaisthesis.domain.enums import (
    EarlyFormalizationReviewDecision,
    EngineeringConceptReviewDecision,
    EngineeringRouteDecision,
    FormalizationFeasibilityDecision,
    GateStatus,
    NoveltyResearchDecision,
    NoveltyStatus,
    PriorArtCoverageStatus,
    ProvenanceType,
    QualificationGateType,
    QualifiedNextTarget,
    ResearchRoute,
)
from synaisthesis.domain.errors import DomainError
from synaisthesis.domain.event import canonicalize
from synaisthesis.domain.novelty import LowNoveltyOverride
from synaisthesis.domain.qualification import is_user_actor


def _canonical_payload(value: Any) -> dict[str, Any]:
    payload = canonicalize(value)
    if not isinstance(payload, dict):
        raise TypeError("gate payload must canonicalize to an object")
    return payload


def allowed_decisions_for_gate(gate_type: QualificationGateType) -> tuple[str, ...]:
    """Return the legal decision strings for one qualification gate (03A/08)."""
    if gate_type is QualificationGateType.ENGINEERING_ROUTE_DECISION:
        return tuple(member.value for member in EngineeringRouteDecision)
    if gate_type is QualificationGateType.FORMALIZATION_FEASIBILITY_DECISION:
        return tuple(member.value for member in FormalizationFeasibilityDecision)
    if gate_type is QualificationGateType.EARLY_FORMALIZATION_REVIEW:
        return tuple(member.value for member in EarlyFormalizationReviewDecision)
    if gate_type is QualificationGateType.EARLY_ENGINEERING_CONCEPT_REVIEW:
        return tuple(member.value for member in EngineeringConceptReviewDecision)
    if gate_type is QualificationGateType.LOW_NOVELTY_RESEARCH_DECISION:
        return tuple(member.value for member in NoveltyResearchDecision)
    raise DomainError(
        f"unknown qualification gate type {gate_type.value}",
        error_code="GATE_BINDING_INVALID",
    )


def _non_empty(value: str | None) -> bool:
    return isinstance(value, str) and bool(value.strip())


@dataclass(frozen=True, slots=True)
class GateBinding:
    """Hash/route binding for one qualification Human Gate (08, section 15)."""

    gate_type: QualificationGateType
    artifact_id: str
    version: int | None
    artifact_hash: str
    input_spec_hash: str
    route: ResearchRoute | None = None
    route_selection_id: str | None = None
    coverage_status: PriorArtCoverageStatus | None = None
    novelty_total: int | None = None
    nearest_overlap_refs: tuple[str, ...] = ()
    limitations: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        missing: list[str] = []
        if not _non_empty(self.artifact_id):
            missing.append("artifact_id")
        if not _non_empty(self.artifact_hash):
            missing.append("artifact_hash")
        if not _non_empty(self.input_spec_hash):
            missing.append("input_spec_hash")
        if self.gate_type in {
            QualificationGateType.ENGINEERING_ROUTE_DECISION,
            QualificationGateType.FORMALIZATION_FEASIBILITY_DECISION,
            QualificationGateType.EARLY_FORMALIZATION_REVIEW,
            QualificationGateType.EARLY_ENGINEERING_CONCEPT_REVIEW,
        } and (self.version is None or self.version < 1):
            missing.append("version")
        if (
            self.gate_type is QualificationGateType.EARLY_FORMALIZATION_REVIEW
            and self.route is not ResearchRoute.THEORY
        ):
            missing.append("route=THEORY")
        if self.gate_type is QualificationGateType.EARLY_ENGINEERING_CONCEPT_REVIEW:
            if self.route is not ResearchRoute.ENGINEERING:
                missing.append("route=ENGINEERING")
            if not _non_empty(self.route_selection_id):
                missing.append("route_selection_id")
        if self.gate_type is QualificationGateType.LOW_NOVELTY_RESEARCH_DECISION:
            if self.route not in {ResearchRoute.THEORY, ResearchRoute.ENGINEERING}:
                missing.append("route")
            if self.coverage_status is None:
                missing.append("coverage_status")
            if self.novelty_total is None or not 0 <= self.novelty_total <= 100:
                missing.append("novelty_total")
        if missing:
            raise DomainError(
                "gate binding missing or invalid: " + ", ".join(missing),
                error_code="GATE_BINDING_INVALID",
            )

    def to_event_payload(self) -> dict[str, Any]:
        return _canonical_payload(asdict(self))


@dataclass(frozen=True, slots=True)
class Gate:
    """An immutable Human Gate record (06 human_gates, 08 section 15)."""

    gate_id: str
    project_id: str
    gate_type: QualificationGateType
    binding: GateBinding
    status: GateStatus = GateStatus.OPEN
    reason: str = ""
    decision: str | None = None
    resolved_at: datetime | None = None

    def __post_init__(self) -> None:
        if self.binding.gate_type is not self.gate_type:
            raise DomainError(
                "gate_type and binding.gate_type must match",
                error_code="GATE_BINDING_INVALID",
            )
        if self.status is GateStatus.RESOLVED and self.decision is None:
            raise DomainError(
                "a resolved gate must have a decision",
                error_code="GATE_BINDING_INVALID",
            )

    def resolve(
        self,
        *,
        decision: str,
        actor: ProvenanceType,
        user_event_id: str,
        at: datetime,
    ) -> Gate:
        """Return a RESOLVED copy; only a real user event may decide."""
        if self.status is not GateStatus.OPEN:
            raise DomainError(
                f"gate {self.gate_id!r} is already {self.status.value}",
                error_code="CONFLICT",
            )
        if not is_user_actor(actor):
            raise DomainError(
                f"gate resolution requires a real user event; got actor={actor.value}",
                error_code="CONFIRMATION_REQUIRES_USER_EVENT",
            )
        allowed = allowed_decisions_for_gate(self.gate_type)
        if decision not in allowed:
            raise DomainError(
                f"decision {decision!r} is not legal for {self.gate_type.value}; "
                f"allowed: {', '.join(allowed)}",
                error_code="INVALID_GATE_DECISION",
            )
        return replace(
            self,
            status=GateStatus.RESOLVED,
            decision=decision,
            resolved_at=at,
        )

    def to_event_payload(self) -> dict[str, Any]:
        return _canonical_payload(asdict(self))


def qualification_next_target(
    *,
    route: ResearchRoute,
    novelty_status: NoveltyStatus,
    override: LowNoveltyOverride | None = None,
    review_artifact_hash: str | None = None,
) -> QualifiedNextTarget:
    """Return the only legal downstream target after early qualification.

    Automatic pass requires the exact route-matched qualified status. A
    USER_OVERRIDDEN_BELOW_THRESHOLD status only advances when a real user
    override binds the same route and current review hash.
    """
    if route is ResearchRoute.THEORY and novelty_status is NoveltyStatus.NOVELTY_QUALIFIED:
        return QualifiedNextTarget.S5
    if (
        route is ResearchRoute.ENGINEERING
        and novelty_status is NoveltyStatus.ENGINEERING_NOVELTY_QUALIFIED
    ):
        return QualifiedNextTarget.ENG0

    if (
        novelty_status is NoveltyStatus.USER_OVERRIDDEN_BELOW_THRESHOLD
        and override is not None
        and override.route is route
        and _non_empty(review_artifact_hash)
        and override.review_artifact_hash == review_artifact_hash
    ):
        if route is ResearchRoute.THEORY:
            return QualifiedNextTarget.S5
        if route is ResearchRoute.ENGINEERING:
            return QualifiedNextTarget.ENG0

    raise DomainError(
        "early research qualification has not passed; S5/ENG0 transition is blocked",
        error_code="EARLY_QUALIFICATION_REQUIRED",
        required_user_action="先完成并绑定当前 route 的 RQ3/RQ4 用户决定",
    )


# ---------------------------------------------------------------------------
# Engineering workflow gates (03B, sections 7.4/9.1/11.4/12.2/13.3)
# ---------------------------------------------------------------------------


def engineering_allowed_decisions_for_gate(
    gate_type: EngineeringGateType,
) -> tuple[str, ...]:
    """Return the legal decision strings for one engineering workflow gate."""
    if gate_type is EngineeringGateType.ENGINEERING_ARCHITECTURE_REVIEW:
        return tuple(member.value for member in EngineeringArchitectureReviewDecision)
    if gate_type is EngineeringGateType.PROTOTYPE_EXECUTION_AUTHORIZATION:
        return tuple(member.value for member in PrototypeExecutionAuthorizationDecision)
    if gate_type is EngineeringGateType.FORMAL_MANUSCRIPT_DECISION:
        return tuple(member.value for member in FormalManuscriptDecision)
    if gate_type is EngineeringGateType.PUBLICATION_PROFILE_SELECTION:
        return tuple(member.value for member in EngineeringProfileChoice)
    if gate_type is EngineeringGateType.ENGINEERING_DELIVERY_ACCEPTANCE:
        return tuple(member.value for member in EngineeringDeliveryAcceptanceDecision)
    raise DomainError(
        f"unknown engineering gate type {gate_type.value}",
        error_code="GATE_BINDING_INVALID",
    )


@dataclass(frozen=True, slots=True)
class EngineeringGateBinding:
    """Hash binding for one engineering Human Gate (03B, sections 7.4/11.4/13.3)."""

    gate_type: EngineeringGateType
    artifact_id: str
    version: int | None
    artifact_hash: str
    bound_hashes: dict[str, str]
    route: ResearchRoute = ResearchRoute.ENGINEERING

    def __post_init__(self) -> None:
        missing: list[str] = []
        if not _non_empty(self.artifact_id):
            missing.append("artifact_id")
        if not _non_empty(self.artifact_hash):
            missing.append("artifact_hash")
        if self.version is None or self.version < 1:
            missing.append("version")
        if not self.bound_hashes or any(
            not _non_empty(value) for value in self.bound_hashes.values()
        ):
            missing.append("bound_hashes")
        if self.route is not ResearchRoute.ENGINEERING:
            missing.append("route=ENGINEERING")
        if missing:
            raise DomainError(
                "engineering gate binding missing or invalid: " + ", ".join(missing),
                error_code="GATE_BINDING_INVALID",
            )

    def to_event_payload(self) -> dict[str, Any]:
        return _canonical_payload(asdict(self))


@dataclass(frozen=True, slots=True)
class EngineeringGate:
    """An immutable engineering workflow Human Gate (03B)."""

    gate_id: str
    project_id: str
    gate_type: EngineeringGateType
    binding: EngineeringGateBinding
    status: GateStatus = GateStatus.OPEN
    reason: str = ""
    decision: str | None = None
    resolved_at: datetime | None = None

    def __post_init__(self) -> None:
        if self.binding.gate_type is not self.gate_type:
            raise DomainError(
                "gate_type and binding.gate_type must match",
                error_code="GATE_BINDING_INVALID",
            )
        if self.status is GateStatus.RESOLVED and self.decision is None:
            raise DomainError(
                "a resolved gate must have a decision",
                error_code="GATE_BINDING_INVALID",
            )

    def resolve(
        self,
        *,
        decision: str,
        actor: ProvenanceType,
        user_event_id: str,
        at: datetime,
    ) -> EngineeringGate:
        """Return a RESOLVED copy; only a real user event may decide."""
        if self.status is not GateStatus.OPEN:
            raise DomainError(
                f"gate {self.gate_id!r} is already {self.status.value}",
                error_code="CONFLICT",
            )
        if not is_user_actor(actor):
            raise DomainError(
                f"gate resolution requires a real user event; got actor={actor.value}",
                error_code="CONFIRMATION_REQUIRES_USER_EVENT",
            )
        allowed = engineering_allowed_decisions_for_gate(self.gate_type)
        if decision not in allowed:
            raise DomainError(
                f"decision {decision!r} is not legal for {self.gate_type.value}; "
                f"allowed: {', '.join(allowed)}",
                error_code="INVALID_GATE_DECISION",
            )
        return replace(
            self,
            status=GateStatus.RESOLVED,
            decision=decision,
            resolved_at=at,
        )

    def to_event_payload(self) -> dict[str, Any]:
        return _canonical_payload(asdict(self))


# ---------------------------------------------------------------------------
# Claim acceptance (08, section 15: CLAIM_ACCEPTANCE; M4.2)
# ---------------------------------------------------------------------------

CLAIM_ACCEPTANCE_DECISIONS: tuple[str, ...] = ("ACCEPT", "REJECT", "PAUSE")


def claim_acceptance_allowed_decisions() -> tuple[str, ...]:
    """Legal CLAIM_ACCEPTANCE decisions (08, section 15)."""
    return CLAIM_ACCEPTANCE_DECISIONS


def assert_claim_acceptance_decision(decision: str) -> None:
    """Fail closed on an illegal claim-acceptance decision."""
    if decision not in CLAIM_ACCEPTANCE_DECISIONS:
        raise DomainError(
            f"decision {decision!r} is not legal for CLAIM_ACCEPTANCE; "
            f"allowed: {', '.join(CLAIM_ACCEPTANCE_DECISIONS)}",
            error_code="INVALID_GATE_DECISION",
        )


__all__ = [
    "CLAIM_ACCEPTANCE_DECISIONS",
    "EngineeringGate",
    "EngineeringGateBinding",
    "Gate",
    "GateBinding",
    "allowed_decisions_for_gate",
    "assert_claim_acceptance_decision",
    "claim_acceptance_allowed_decisions",
    "engineering_allowed_decisions_for_gate",
    "qualification_next_target",
]
