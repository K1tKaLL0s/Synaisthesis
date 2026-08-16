"""ENG0-ENG10 engineering workflow domain (blueprint 03B).

This module owns the engineering-route workflow: stable stage identifiers,
delivery/artifact statuses, the ENG0 entry precondition (03B section 1.1),
immutable stage artifacts (Mission/ConOps/TradeStudy/Blueprint/Roadmap), the
engineering event catalog and the deterministic regression mapping (03B
section 14).  Milestone enums live here (not in ``domain/enums.py``) because
M2.8's contract restricts ``domain/enums.py``; see ``domain/enums.py``
module docstring for the milestone-ownership convention.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import asdict, dataclass, replace
from datetime import datetime
from typing import Any

from synaisthesis.domain.enums import (
    NoveltyStatus,
    ResearchRoute,
    StrictStrEnum,
)
from synaisthesis.domain.errors import DomainError
from synaisthesis.domain.event import DomainEvent, canonicalize, sha256_hex
from synaisthesis.domain.novelty import LowNoveltyOverride
from synaisthesis.domain.qualification import (
    EngineeringRouteSelection,
    UserEngineeringConceptApproval,
)

# ---------------------------------------------------------------------------
# Stable enumerations
# ---------------------------------------------------------------------------


class EngineeringStageId(StrictStrEnum):
    """Engineering workflow stages ENG0-ENG10 (03B, section 2)."""

    ENG0 = "ENG0"
    ENG1 = "ENG1"
    ENG2 = "ENG2"
    ENG3 = "ENG3"
    ENG4 = "ENG4"
    ENG5 = "ENG5"
    ENG6 = "ENG6"
    ENG7 = "ENG7"
    ENG8 = "ENG8"
    ENG9 = "ENG9"
    ENG10 = "ENG10"


class EngineeringArtifactStatus(StrictStrEnum):
    """Lifecycle of one immutable engineering artifact (03B, section 14)."""

    ACTIVE = "ACTIVE"
    APPROVED = "APPROVED"
    BLOCKED = "BLOCKED"
    SUPERSEDED = "SUPERSEDED"
    NEEDS_REGRESSION = "NEEDS_REGRESSION"
    RETRACTED = "RETRACTED"


class EngineeringDeliveryMode(StrictStrEnum):
    """ENG0 charter delivery mode (03B, section 3.2) and ENG6 split (9.1)."""

    BLUEPRINT_ONLY = "BLUEPRINT_ONLY"
    BUILD_AND_EVALUATE_UNDECIDED = "BUILD_AND_EVALUATE_UNDECIDED"
    BUILD_AND_EVALUATE = "BUILD_AND_EVALUATE"


class EngineeringDeliveryStatus(StrictStrEnum):
    """Authoritative ``engineering_delivery_status`` values (06, section 9)."""

    NOT_STARTED = "NOT_STARTED"
    MISSION_BASELINING = "MISSION_BASELINING"
    CONOPS_DEFINING = "CONOPS_DEFINING"
    REQUIREMENTS_BASELINING = "REQUIREMENTS_BASELINING"
    TRADE_STUDY_RUNNING = "TRADE_STUDY_RUNNING"
    ARCHITECTURE_DESIGNING = "ARCHITECTURE_DESIGNING"
    ARCHITECTURE_USER_REVIEW = "ARCHITECTURE_USER_REVIEW"
    BLUEPRINT_BUILDING = "BLUEPRINT_BUILDING"
    BLUEPRINT_GAP = "BLUEPRINT_GAP"
    BLUEPRINT_ONLY = "BLUEPRINT_ONLY"
    BUILD_AUTHORIZATION_REQUIRED = "BUILD_AUTHORIZATION_REQUIRED"
    VERIFYING = "VERIFYING"
    VALIDATING = "VALIDATING"
    APPLICATION_ROADMAP_BUILDING = "APPLICATION_ROADMAP_BUILDING"
    MASTER_MANUSCRIPT_BUILDING = "MASTER_MANUSCRIPT_BUILDING"
    ENGINEERING_MASTER_MANUSCRIPT_AUDITING = "ENGINEERING_MASTER_MANUSCRIPT_AUDITING"
    ENGINEERING_MASTER_MANUSCRIPT_READY = "ENGINEERING_MASTER_MANUSCRIPT_READY"
    FORMAL_MANUSCRIPT_DECISION_REQUIRED = "FORMAL_MANUSCRIPT_DECISION_REQUIRED"
    MASTER_ONLY_DELIVERED = "MASTER_ONLY_DELIVERED"
    MASTER_REVISION_REQUIRED = "MASTER_REVISION_REQUIRED"
    FORMAL_MANUSCRIPT_PAUSED = "FORMAL_MANUSCRIPT_PAUSED"
    PUBLICATION_PROFILE_REQUIRED = "PUBLICATION_PROFILE_REQUIRED"
    VENUE_MANUSCRIPT_BUILDING = "VENUE_MANUSCRIPT_BUILDING"
    FORMAL_MANUSCRIPT_DRAFT = "FORMAL_MANUSCRIPT_DRAFT"
    FORMAL_MANUSCRIPT_READY = "FORMAL_MANUSCRIPT_READY"
    ARXIV_PACKAGE_READY = "ARXIV_PACKAGE_READY"
    DELIVERY_AUDITING = "DELIVERY_AUDITING"
    ENGINEERING_DELIVERY_CANDIDATE = "ENGINEERING_DELIVERY_CANDIDATE"
    ENGINEERING_DELIVERY_READY = "ENGINEERING_DELIVERY_READY"
    BLOCKED_ENGINEERING_DELIVERY = "BLOCKED_ENGINEERING_DELIVERY"
    NEEDS_REGRESSION = "NEEDS_REGRESSION"
    SUPERSEDED = "SUPERSEDED"


class EngineeringChangeKind(StrictStrEnum):
    """Change kinds with a fixed earliest rollback point (03B, section 14)."""

    S1_S4_CORE_SEMANTICS = "S1_S4_CORE_SEMANTICS"
    NEIGHBOR_CHANGED_NOVELTY = "NEIGHBOR_CHANGED_NOVELTY"
    STAKEHOLDER_OR_CONOPS = "STAKEHOLDER_OR_CONOPS"
    REQUIREMENT_OR_THRESHOLD = "REQUIREMENT_OR_THRESHOLD"
    TECHNOLOGY_ROUTE_OR_MAJOR_DEPENDENCY = "TECHNOLOGY_ROUTE_OR_MAJOR_DEPENDENCY"
    PUBLIC_INTERFACE_OR_DATA_OR_SECURITY_BOUNDARY = "PUBLIC_INTERFACE_OR_DATA_OR_SECURITY_BOUNDARY"
    BLUEPRINT_GAP_FOUND = "BLUEPRINT_GAP_FOUND"
    IMPLEMENTATION_FALSIFIES_ARCHITECTURE = "IMPLEMENTATION_FALSIFIES_ARCHITECTURE"
    NEW_EXPERIMENTAL_RESULTS = "NEW_EXPERIMENTAL_RESULTS"
    MASTER_MANUSCRIPT_CLAIMS = "MASTER_MANUSCRIPT_CLAIMS"
    VENUE_GUIDANCE_UPDATE = "VENUE_GUIDANCE_UPDATE"
    EVIDENCE_REVOCATION_OR_LICENSE = "EVIDENCE_REVOCATION_OR_LICENSE"


class EngineeringGateType(StrictStrEnum):
    """Human Gates opened by the engineering workflow (03B sections 7.4/9.1/11.4/12.2/13.3)."""

    ENGINEERING_ARCHITECTURE_REVIEW = "ENGINEERING_ARCHITECTURE_REVIEW"
    PROTOTYPE_EXECUTION_AUTHORIZATION = "PROTOTYPE_EXECUTION_AUTHORIZATION"
    FORMAL_MANUSCRIPT_DECISION = "FORMAL_MANUSCRIPT_DECISION"
    PUBLICATION_PROFILE_SELECTION = "PUBLICATION_PROFILE_SELECTION"
    ENGINEERING_DELIVERY_ACCEPTANCE = "ENGINEERING_DELIVERY_ACCEPTANCE"


class EngineeringArchitectureReviewDecision(StrictStrEnum):
    """Legal ENGINEERING_ARCHITECTURE_REVIEW choices (03B, section 7.4)."""

    APPROVE_BASELINE = "APPROVE_BASELINE"
    REQUEST_REVISION = "REQUEST_REVISION"
    RETURN_TO_TRADE_STUDY = "RETURN_TO_TRADE_STUDY"
    REVISE_REQUIREMENTS = "REVISE_REQUIREMENTS"
    PAUSE = "PAUSE"
    ARCHIVE = "ARCHIVE"


class PrototypeExecutionAuthorizationDecision(StrictStrEnum):
    """Legal PROTOTYPE_EXECUTION_AUTHORIZATION choices (03B, section 9.1)."""

    AUTHORIZE = "AUTHORIZE"
    REJECT = "REJECT"
    REQUEST_REVISION = "REQUEST_REVISION"
    PAUSE = "PAUSE"


class FormalManuscriptDecision(StrictStrEnum):
    """Legal FORMAL_MANUSCRIPT_DECISION choices (03B, section 11.4)."""

    KEEP_MASTER_ONLY = "KEEP_MASTER_ONLY"
    WRITE_FORMAL_MANUSCRIPT = "WRITE_FORMAL_MANUSCRIPT"
    REVISE_MASTER = "REVISE_MASTER"
    PAUSE = "PAUSE"


class EngineeringProfileChoice(StrictStrEnum):
    """Built-in engineering publication profiles (03B, section 12.1)."""

    ENG_IEEE_TSE = "ENG_IEEE_TSE"
    ENG_ACM_TOSEM = "ENG_ACM_TOSEM"
    ENG_EMSE = "ENG_EMSE"
    ENG_JSS = "ENG_JSS"
    ENG_ARXIV_PREPRINT = "ENG_ARXIV_PREPRINT"
    JOSS_RESEARCH_SOFTWARE = "JOSS_RESEARCH_SOFTWARE"
    NATURE_PORTFOLIO_METHODS_OR_SOFTWARE = "NATURE_PORTFOLIO_METHODS_OR_SOFTWARE"
    CUSTOM_VENUE = "CUSTOM_VENUE"


class EngineeringDeliveryAcceptanceDecision(StrictStrEnum):
    """Legal ENGINEERING_DELIVERY_ACCEPTANCE choices (03B, section 13.3)."""

    ACCEPT = "ACCEPT"
    REQUEST_CHANGES = "REQUEST_CHANGES"
    PAUSE = "PAUSE"


class ApplicationHorizon(StrictStrEnum):
    """Application direction time horizon (03B, section 10.1)."""

    NOW = "NOW"
    NEXT = "NEXT"
    LATER = "LATER"
    RESEARCH_ONLY = "RESEARCH_ONLY"


# ---------------------------------------------------------------------------
# Event catalog
# ---------------------------------------------------------------------------

ENGINEERING_EVENT_TYPES: frozenset[str] = frozenset(
    {
        "EngineeringStageOpened",
        "EngineeringArtifactCreated",
        "EngineeringScopeChangeOpened",
        "EngineeringStageBlocked",
        "EngineeringRegressionDetected",
        "EngineeringGateOpened",
        "EngineeringGateResolved",
    }
)

EVENT_ENGINEERING_STAGE_OPENED = "EngineeringStageOpened"
EVENT_ENGINEERING_ARTIFACT_CREATED = "EngineeringArtifactCreated"
EVENT_ENGINEERING_SCOPE_CHANGE_OPENED = "EngineeringScopeChangeOpened"
EVENT_ENGINEERING_STAGE_BLOCKED = "EngineeringStageBlocked"
EVENT_ENGINEERING_REGRESSION_DETECTED = "EngineeringRegressionDetected"
EVENT_ENGINEERING_GATE_OPENED = "EngineeringGateOpened"
EVENT_ENGINEERING_GATE_RESOLVED = "EngineeringGateResolved"


def build_engineering_event(
    event_type: str,
    *,
    aggregate_type: str,
    aggregate_id: str,
    payload: dict[str, Any],
    sequence: int,
) -> DomainEvent:
    """Build an immutable engineering DomainEvent with a stable event hash."""
    if event_type not in ENGINEERING_EVENT_TYPES:
        raise DomainError(
            f"unknown engineering event type {event_type!r}",
            error_code="UNKNOWN_EVENT_TYPE",
        )
    return DomainEvent(
        aggregate_type=aggregate_type,
        aggregate_id=aggregate_id,
        event_type=event_type,
        payload=payload,
        sequence=sequence,
    )


# ---------------------------------------------------------------------------
# Shared artifact helpers
# ---------------------------------------------------------------------------


def _canonical_payload(value: Any) -> dict[str, Any]:
    payload = canonicalize(value)
    if not isinstance(payload, dict):
        raise TypeError("engineering payload must canonicalize to an object")
    return payload


def ensure_artifact_hash(*, content_payload: Mapping[str, Any], artifact_hash: str) -> None:
    """Fail closed when artifact_hash does not cover the semantic content."""
    expected = sha256_hex(content_payload)
    if artifact_hash != expected:
        raise DomainError(
            "artifact_hash does not match the artifact content",
            error_code="ARTIFACT_HASH_MISMATCH",
        )


def finalize_artifact_hash(artifact: Any, *, field: str = "artifact_hash") -> None:
    """Auto-compute the hash field, or verify a caller-provided value.

    Every engineering artifact's hash field must equal the SHA-256 of its
    canonical semantic content; a provided mismatching hash fails closed.
    """
    expected = sha256_hex(artifact.content_payload())
    current = getattr(artifact, field)
    if current is not None and current != expected:
        raise DomainError(
            f"{field} does not match the artifact content",
            error_code="ARTIFACT_HASH_MISMATCH",
        )
    object.__setattr__(artifact, field, expected)


def superseded(artifact: Any) -> Any:
    """Return an immutable SUPERSEDED copy; history is never overwritten."""
    if not hasattr(artifact, "status"):
        raise TypeError("superseded() requires an artifact with a status field")
    return replace(artifact, status=EngineeringArtifactStatus.SUPERSEDED)


# ---------------------------------------------------------------------------
# Stage / delivery-status mapping
# ---------------------------------------------------------------------------

STAGE_ORDER: tuple[EngineeringStageId, ...] = tuple(EngineeringStageId)

DELIVERY_STATUS_FOR_STAGE: Mapping[EngineeringStageId, EngineeringDeliveryStatus] = {
    EngineeringStageId.ENG0: EngineeringDeliveryStatus.MISSION_BASELINING,
    EngineeringStageId.ENG1: EngineeringDeliveryStatus.CONOPS_DEFINING,
    EngineeringStageId.ENG2: EngineeringDeliveryStatus.REQUIREMENTS_BASELINING,
    EngineeringStageId.ENG3: EngineeringDeliveryStatus.TRADE_STUDY_RUNNING,
    EngineeringStageId.ENG4: EngineeringDeliveryStatus.ARCHITECTURE_DESIGNING,
    EngineeringStageId.ENG5: EngineeringDeliveryStatus.BLUEPRINT_BUILDING,
    EngineeringStageId.ENG6: EngineeringDeliveryStatus.VERIFYING,
    EngineeringStageId.ENG7: EngineeringDeliveryStatus.APPLICATION_ROADMAP_BUILDING,
    EngineeringStageId.ENG8: EngineeringDeliveryStatus.MASTER_MANUSCRIPT_BUILDING,
    EngineeringStageId.ENG9: EngineeringDeliveryStatus.VENUE_MANUSCRIPT_BUILDING,
    EngineeringStageId.ENG10: EngineeringDeliveryStatus.DELIVERY_AUDITING,
}


def engineering_next_stage(stage: EngineeringStageId) -> EngineeringStageId | None:
    """Return the next stage in ENG0..ENG10 order; None at ENG10."""
    position = STAGE_ORDER.index(stage)
    if position + 1 >= len(STAGE_ORDER):
        return None
    return STAGE_ORDER[position + 1]


def delivery_status_for_stage(stage: EngineeringStageId) -> EngineeringDeliveryStatus:
    """Return the deterministic delivery status for a stage (06, section 9)."""
    return DELIVERY_STATUS_FOR_STAGE[stage]


# ---------------------------------------------------------------------------
# ENG0 entry precondition (03B, section 1.1)
# ---------------------------------------------------------------------------


def eng0_entry_blockers(
    *,
    bound_input_spec_hash: str,
    current_input_spec_hash: str,
    route_selection: EngineeringRouteSelection | None,
    concept_approval: UserEngineeringConceptApproval | None,
    concept_hash: str | None,
    novelty_status: NoveltyStatus,
    novelty_review_hash: str | None,
    override: LowNoveltyOverride | None,
    open_gate_types: tuple[str, ...] = (),
) -> tuple[str, ...]:
    """Return structured blockers; empty tuple means ENG0 may be created.

    Implements 03B section 1.1: every condition must hold; a natural-language
    remark can never bypass a blocker.
    """
    blockers: list[str] = []
    if not bound_input_spec_hash or bound_input_spec_hash != current_input_spec_hash:
        blockers.append(
            "S1/S4 hash 已变化，必须重新资格化（当前 input_spec_hash 与绑定 hash 不一致）"
        )
    if route_selection is None:
        blockers.append("缺少 EngineeringRouteSelection，工程路线未由用户选择")
    elif route_selection.decision.value != "TRY_ENGINEERING_PROJECT":
        blockers.append(
            "EngineeringRouteSelection.decision 不是 TRY_ENGINEERING_PROJECT，工程路线未由用户选择"
        )
    if concept_approval is None:
        blockers.append("RQ3E 尚未批准当前 EngineeringConceptBundle")
    else:
        if concept_approval.route is not ResearchRoute.ENGINEERING:
            blockers.append("RQ3E 概念审批未绑定 ENGINEERING route")
        if not concept_hash or concept_approval.concept_hash != concept_hash:
            blockers.append("RQ3E 审批的 concept hash 与当前 bundle 不一致")
        if (
            route_selection is not None
            and concept_approval.route_selection_id != route_selection.id
        ):
            blockers.append("RQ3E 审批未绑定当前 route selection")
    if novelty_status is NoveltyStatus.ENGINEERING_NOVELTY_QUALIFIED:
        if not novelty_review_hash:
            blockers.append("缺少 novelty review hash，无法验证 RQ4E 绑定")
    elif (
        novelty_status is NoveltyStatus.USER_OVERRIDDEN_BELOW_THRESHOLD
        and override is not None
        and override.route is ResearchRoute.ENGINEERING
        and novelty_review_hash
        and override.review_artifact_hash == novelty_review_hash
    ):
        pass
    else:
        blockers.append(
            "RQ4E 未达到 ENGINEERING_NOVELTY_QUALIFIED 且无绑定当前 review hash 的用户 override"
        )
    unresolved = [gate for gate in open_gate_types if gate]
    if unresolved:
        blockers.append(
            "存在未解决的隐私/伦理/监管/付费/安全 Gate：" + ", ".join(sorted(unresolved))
        )
    return tuple(blockers)


# ---------------------------------------------------------------------------
# ENG0 — EngineeringMissionCharter (03B, section 3)
# ---------------------------------------------------------------------------

SCOPE_KEYS: tuple[str, ...] = (
    "object_domain",
    "intended_users",
    "core_functions",
    "data_classification",
    "engineering_goals",
)


def charter_scope_changes(
    *,
    baseline_scope: Mapping[str, Any],
    charter_scope: Mapping[str, Any],
    proposed_additions: tuple[str, ...],
) -> tuple[str, ...]:
    """Detect object-domain/user/core-function/data/engineering-goal changes.

    03B section 3.3: model-added content must live in proposed_additions and
    must not be mixed into the baseline; any core-function addition that is
    not recorded as a proposed addition is a scope change.
    """
    changed: list[str] = []
    for key in SCOPE_KEYS:
        baseline = canonicalize(baseline_scope.get(key))
        charter = canonicalize(charter_scope.get(key))
        if key == "core_functions":
            baseline_set = set(baseline or [])
            charter_set = set(charter or [])
            added = charter_set - baseline_set
            if added and not any(addition in proposed_additions for addition in added):
                changed.append(key)
            continue
        if baseline != charter:
            changed.append(key)
    return tuple(changed)


@dataclass(frozen=True, slots=True)
class EngineeringMissionCharter:
    """ENG0 output (03B, section 3.2); immutable once created."""

    charter_id: str
    version: int
    project_id: str
    source_artifact_hashes: tuple[str, ...]
    problem_statement: str
    stakeholders: tuple[str, ...]
    intended_users: tuple[str, ...]
    operational_context: str
    system_of_interest_boundary: str
    objectives: tuple[str, ...]
    non_goals: tuple[str, ...]
    success_metrics: tuple[str, ...]
    constraints: tuple[str, ...]
    assumptions: tuple[str, ...]
    regulatory_security_ethics_flags: tuple[str, ...]
    delivery_mode: EngineeringDeliveryMode
    baseline_scope: dict[str, Any]
    charter_scope: dict[str, Any]
    proposed_additions: tuple[str, ...]
    artifact_hash: str | None = None
    status: EngineeringArtifactStatus = EngineeringArtifactStatus.ACTIVE
    created_at: datetime | None = None

    def __post_init__(self) -> None:
        if self.delivery_mode not in {
            EngineeringDeliveryMode.BLUEPRINT_ONLY,
            EngineeringDeliveryMode.BUILD_AND_EVALUATE_UNDECIDED,
        }:
            raise DomainError(
                "ENG0 charter delivery_mode must be BLUEPRINT_ONLY or BUILD_AND_EVALUATE_UNDECIDED",
                error_code="ENGINEERING_DELIVERY_MODE_INVALID",
            )
        changes = charter_scope_changes(
            baseline_scope=self.baseline_scope,
            charter_scope=self.charter_scope,
            proposed_additions=self.proposed_additions,
        )
        if changes:
            raise DomainError(
                "charter introduces unrecorded scope changes: "
                + ", ".join(changes)
                + "；必须打开 ENGINEERING_SCOPE_CHANGE",
                error_code="ENGINEERING_SCOPE_CHANGE",
            )
        finalize_artifact_hash(self)

    def content_payload(self) -> dict[str, Any]:
        payload = asdict(self)
        payload.pop("artifact_hash", None)
        payload.pop("status", None)
        return _canonical_payload(payload)

    def to_event_payload(self) -> dict[str, Any]:
        return _canonical_payload(asdict(self))


# ---------------------------------------------------------------------------
# ENG1 — OperationalConceptBundle (03B, section 4)
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class OperationalScenario:
    """One ConOps scenario (03B, section 4.1)."""

    scenario_id: str
    expected_function_refs: tuple[str, ...]
    stakeholder_role_refs: tuple[str, ...]
    precondition: str
    trigger: str
    main_flow: tuple[str, ...]
    alternate_flow: tuple[str, ...]
    postcondition: str
    external_dependency_refs: tuple[str, ...] = ()
    trust_zone: str | None = None

    def __post_init__(self) -> None:
        if not self.scenario_id.strip() or not self.precondition.strip():
            raise DomainError(
                "scenario requires scenario_id and precondition",
                error_code="CONOPS_INVALID",
            )


@dataclass(frozen=True, slots=True)
class ExternalDependency:
    """One external system/data dependency (03B, section 4.1/4.2)."""

    dependency_id: str
    owner: str
    failure_mode: str
    fallback: str


@dataclass(frozen=True, slots=True)
class StakeholderEntry:
    """Stakeholder map entry with responsibility boundary (03B, section 4.1)."""

    stakeholder_id: str
    role: str | None
    responsibility_boundary: str
    is_operator: bool
    intended_user_refs: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class OperationalConceptBundle:
    """ENG1 output (03B, section 4.1)."""

    conops_id: str
    version: int
    project_id: str
    charter_id: str
    input_spec_hash: str
    charter_hash: str
    stakeholder_map: tuple[StakeholderEntry, ...]
    scenarios: tuple[OperationalScenario, ...]
    system_context: str
    external_systems: tuple[ExternalDependency, ...]
    data_sources: tuple[ExternalDependency, ...]
    trust_boundaries: tuple[str, ...]
    human_intervention_points: tuple[str, ...]
    environment_assumptions: tuple[str, ...]
    quality_requirements: tuple[str, ...]
    unresolved_issues: tuple[str, ...]
    decision_owners: tuple[str, ...]
    expected_functions: tuple[str, ...]
    intended_user_ids: tuple[str, ...]
    intent_refs: tuple[str, ...]
    artifact_hash: str | None = None
    status: EngineeringArtifactStatus = EngineeringArtifactStatus.ACTIVE
    created_at: datetime | None = None

    def __post_init__(self) -> None:
        finalize_artifact_hash(self)

    def content_payload(self) -> dict[str, Any]:
        payload = asdict(self)
        payload.pop("artifact_hash", None)
        payload.pop("status", None)
        return _canonical_payload(payload)

    def to_event_payload(self) -> dict[str, Any]:
        return _canonical_payload(asdict(self))


def conops_blockers(bundle: OperationalConceptBundle) -> tuple[str, ...]:
    """Return ENG1 pass-criteria blockers (03B, section 4.2)."""
    blockers: list[str] = []
    function_to_scenarios: dict[str, int] = {}
    for scenario in bundle.scenarios:
        for function_ref in scenario.expected_function_refs:
            function_to_scenarios[function_ref] = function_to_scenarios.get(function_ref, 0) + 1
    for function in bundle.expected_functions:
        if function_to_scenarios.get(function, 0) < 1:
            blockers.append(f"expected function {function!r} 没有场景")
    user_to_role: dict[str, bool] = {}
    for stakeholder in bundle.stakeholder_map:
        for user_ref in stakeholder.intended_user_refs:
            user_to_role[user_ref] = (
                user_to_role.get(user_ref, False)
                or (stakeholder.role is not None and bool(stakeholder.role.strip()))
                or not stakeholder.is_operator
            )
    for user_id in bundle.intended_user_ids:
        if not user_to_role.get(user_id, False):
            blockers.append(f"intended user {user_id!r} 未映射角色且未标为非操作者")
    for dependency in (*bundle.external_systems, *bundle.data_sources):
        if not dependency.owner.strip() or not dependency.failure_mode.strip():
            blockers.append(
                f"external dependency {dependency.dependency_id!r} 缺 owner/failure mode"
            )
        if not dependency.fallback.strip():
            blockers.append(f"external dependency {dependency.dependency_id!r} 缺 fallback")
    for scenario in bundle.scenarios:
        for _dependency_ref in scenario.external_dependency_refs:
            if not scenario.trust_zone:
                blockers.append(f"scenario {scenario.scenario_id!r} 的外部动作未标注 trust zone")
    return tuple(blockers)


# ---------------------------------------------------------------------------
# ENG3 — reference set and trade study (03B, section 6)
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class EngineeringReference:
    """One deep-search reference (03B, section 6.1)."""

    stable_identifier: str
    reference_type: str
    canonical_url: str
    evidence_refs: tuple[str, ...]
    maturity_claims: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class EngineeringReferenceSet:
    """ENG3 reference output (03B, section 6.3)."""

    reference_set_id: str
    version: int
    project_id: str
    requirements_baseline_id: str
    references: tuple[EngineeringReference, ...]
    artifact_hash: str | None = None
    status: EngineeringArtifactStatus = EngineeringArtifactStatus.ACTIVE
    created_at: datetime | None = None

    def __post_init__(self) -> None:
        finalize_artifact_hash(self)

    def content_payload(self) -> dict[str, Any]:
        payload = asdict(self)
        payload.pop("artifact_hash", None)
        payload.pop("status", None)
        return _canonical_payload(payload)

    def to_event_payload(self) -> dict[str, Any]:
        return _canonical_payload(asdict(self))


@dataclass(frozen=True, slots=True)
class TradeStudyOption:
    """One candidate technical route (03B, section 6.2)."""

    option_id: str
    name: str
    covers_requirements: tuple[str, ...]
    key_components: tuple[str, ...]
    dependencies: tuple[str, ...]
    interfaces: tuple[str, ...]
    data_paths: tuple[str, ...]
    performance_predictions: dict[str, Any]
    reliability_predictions: dict[str, Any]
    security_predictions: dict[str, Any]
    maintainability_predictions: dict[str, Any]
    scalability_predictions: dict[str, Any]
    implementation_complexity: str
    personnel_effort: str
    timeline_cost_infrastructure: str
    license_supply_chain_risks: tuple[str, ...]
    prototype_spike_suggestions: tuple[str, ...]
    unknowns: tuple[str, ...]
    evidence_confidence: str
    normalized_criterion_scores: dict[str, float]


@dataclass(frozen=True, slots=True)
class OptionTradeStudy:
    """ENG3 trade study with the frozen weighting formula (03B, section 6.2)."""

    study_id: str
    version: int
    project_id: str
    requirements_baseline_id: str
    critical_requirement_ids: tuple[str, ...]
    criteria: tuple[str, ...]
    weights: dict[str, float]
    weights_derivation_ref: str
    options: tuple[TradeStudyOption, ...]
    eliminated_option_ids: tuple[str, ...]
    artifact_hash: str | None = None
    status: EngineeringArtifactStatus = EngineeringArtifactStatus.ACTIVE
    created_at: datetime | None = None

    def __post_init__(self) -> None:
        if not self.criteria or not self.options:
            raise DomainError(
                "trade study requires at least one criterion and one option",
                error_code="TRADE_STUDY_INVALID",
            )
        if set(self.weights) != set(self.criteria):
            raise DomainError(
                "weights must cover exactly the criteria set",
                error_code="TRADE_STUDY_INVALID",
            )
        total = sum(self.weights.values())
        if abs(total - 1.0) > 1e-9:
            raise DomainError(
                f"weights must sum to 1 (got {total})",
                error_code="TRADE_STUDY_INVALID",
            )
        for option in self.options:
            if set(option.normalized_criterion_scores) != set(self.criteria):
                raise DomainError(
                    f"option {option.option_id!r} scores do not cover all criteria",
                    error_code="TRADE_STUDY_INVALID",
                )
            for score in option.normalized_criterion_scores.values():
                if not 0.0 <= score <= 1.0:
                    raise DomainError(
                        f"option {option.option_id!r} has out-of-range score {score}",
                        error_code="TRADE_STUDY_INVALID",
                    )
        finalize_artifact_hash(self)

    def content_payload(self) -> dict[str, Any]:
        payload = asdict(self)
        payload.pop("artifact_hash", None)
        payload.pop("status", None)
        return _canonical_payload(payload)

    def to_event_payload(self) -> dict[str, Any]:
        return _canonical_payload(asdict(self))

    def weighted_score(self, option_id: str) -> float:
        """Fixed formula score = Σ w_j × normalized_score (03B, section 6.2)."""
        option = next(
            (candidate for candidate in self.options if candidate.option_id == option_id),
            None,
        )
        if option is None:
            raise DomainError(
                f"unknown trade study option {option_id!r}",
                error_code="TRADE_STUDY_INVALID",
            )
        return sum(
            self.weights[criterion] * option.normalized_criterion_scores[criterion]
            for criterion in self.criteria
        )

    def eligible_ranking(self) -> tuple[str, ...]:
        """Rank eligible options (never hard-eliminated ones) by weighted score."""
        ranked = sorted(
            (
                option
                for option in self.options
                if option.option_id not in self.eliminated_option_ids
            ),
            key=lambda option: self.weighted_score(option.option_id),
            reverse=True,
        )
        return tuple(option.option_id for option in ranked)


def trade_study_blockers(study: OptionTradeStudy, requirements_baseline_id: str) -> tuple[str, ...]:
    """Return hard-elimination blockers (03B, section 6.2).

    An option that does not cover every critical requirement is eliminated and
    never participates in weighted compensation; this can never be repaired by
    a high score.
    """
    blockers: list[str] = []
    if study.requirements_baseline_id != requirements_baseline_id:
        blockers.append("trade study 未绑定当前 Requirements Baseline")
    eliminated: list[str] = []
    for option in study.options:
        if not set(study.critical_requirement_ids).issubset(set(option.covers_requirements)):
            eliminated.append(option.option_id)
    expected = set(eliminated)
    recorded = set(study.eliminated_option_ids)
    if expected != recorded:
        blockers.append(
            "硬淘汰集合不一致：必须淘汰 "
            + ", ".join(sorted(expected))
            + "（记录为 "
            + ", ".join(sorted(recorded))
            + "）"
        )
    if eliminated and study.eligible_ranking() and study.eligible_ranking()[0] in eliminated:
        blockers.append("被淘汰方案不得参与加权补偿或成为推荐")
    return tuple(blockers)


@dataclass(frozen=True, slots=True)
class TechnologySelectionRecord:
    """ENG3 selected route record, hash-bound to its trade study (03B, section 6.3)."""

    selection_id: str
    study_id: str
    study_hash: str
    selected_option_id: str
    rationale: str
    created_at: datetime

    def __post_init__(self) -> None:
        if not self.selected_option_id.strip() or not self.rationale.strip():
            raise DomainError(
                "selection requires option id and rationale",
                error_code="TRADE_STUDY_INVALID",
            )

    def to_event_payload(self) -> dict[str, Any]:
        return _canonical_payload(asdict(self))


@dataclass(frozen=True, slots=True)
class RejectedOptionLog:
    """ENG3 rejected options with reasons (03B, section 6.3)."""

    study_id: str
    rejected_options: tuple[tuple[str, str], ...]  # (option_id, reason)

    def to_event_payload(self) -> dict[str, Any]:
        return _canonical_payload(asdict(self))


def validate_technology_selection(
    record: TechnologySelectionRecord, study: OptionTradeStudy
) -> tuple[str, ...]:
    """Block selection when the study hash changed (frozen-weights rule)."""
    if record.study_id != study.study_id or record.study_hash != study.artifact_hash:
        return ("TechnologySelectionRecord 绑定的 trade study hash 已变化，旧选择失效",)
    if record.selected_option_id in study.eliminated_option_ids:
        return ("被硬淘汰的方案不得被选择",)
    return ()


# ---------------------------------------------------------------------------
# ENG5 — MechanicalEngineeringBlueprint (03B, section 8)
# ---------------------------------------------------------------------------

#: Wording that makes a mechanical task non-mechanical (03B, sections 8.2/16.8).
BLUEPRINT_VAGUE_PATTERNS: tuple[str, ...] = (
    "适当修改",
    "完善相关",
    "视情况",
    "相关代码",
    "尽量",
    "酌情",
)


@dataclass(frozen=True, slots=True)
class EngineeringWorkUnitContract:
    """One atomic mechanical task (03B, section 8.2)."""

    task_id: str
    unique_objective: str
    authoritative_inputs: tuple[str, ...]
    preconditions_gates_environment: tuple[str, ...]
    allowed_files: tuple[str, ...]
    forbidden_files: tuple[str, ...]
    io_contracts: tuple[str, ...]
    invariants: tuple[str, ...]
    step_actions: tuple[str, ...]
    errors_boundaries_compat_rollback: tuple[str, ...]
    focused_tests: tuple[str, ...]
    full_checks: tuple[str, ...]
    acceptance_criteria: tuple[str, ...]
    stop_escalation_conditions: tuple[str, ...]
    delivery_format: str

    def __post_init__(self) -> None:
        if not self.task_id.strip() or not self.unique_objective.strip():
            raise DomainError(
                "work unit requires task_id and unique objective",
                error_code="WORK_UNIT_INVALID",
            )
        for field_name in ("step_actions", "acceptance_criteria"):
            for item in getattr(self, field_name):
                if any(pattern in item for pattern in BLUEPRINT_VAGUE_PATTERNS):
                    raise DomainError(
                        f"work unit {self.task_id!r} {field_name} 含模糊措辞：{item!r}",
                        error_code="WORK_UNIT_INVALID",
                    )

    def to_event_payload(self) -> dict[str, Any]:
        return _canonical_payload(asdict(self))


@dataclass(frozen=True, slots=True)
class MechanicalEngineeringBlueprint:
    """ENG5 output (03B, section 8.1)."""

    blueprint_id: str
    version: int
    project_id: str
    architecture_baseline_id: str
    architecture_hash: str
    project_tree: dict[str, str]
    file_level_changes: dict[str, tuple[str, ...]]
    modules_and_symbols: dict[str, tuple[str, ...]]
    dependency_lock_policy: str
    config_secret_env_policy: str
    data_migration_rollback_policy: str
    runtime_flow_specs: dict[str, str]
    non_functional_requirements: tuple[str, ...]
    command_templates: dict[str, str]
    traceability: dict[str, tuple[str, ...]]
    risk_register: tuple[str, ...]
    stop_and_escalation_conditions: tuple[str, ...]
    pending_generated_artifacts: tuple[str, ...]
    work_units: tuple[EngineeringWorkUnitContract, ...]
    artifact_hash: str | None = None
    status: EngineeringArtifactStatus = EngineeringArtifactStatus.ACTIVE
    created_at: datetime | None = None

    def __post_init__(self) -> None:
        finalize_artifact_hash(self)

    def content_payload(self) -> dict[str, Any]:
        payload = asdict(self)
        payload.pop("artifact_hash", None)
        payload.pop("status", None)
        return _canonical_payload(payload)

    def to_event_payload(self) -> dict[str, Any]:
        return _canonical_payload(asdict(self))


def blueprint_completeness_blockers(
    blueprint: MechanicalEngineeringBlueprint,
    *,
    requirements_total: int,
    requirements_to_design: int,
    requirements_to_task: int,
    critical_requirements_total: int,
    critical_requirements_to_test: int,
    public_interfaces_total: int,
    public_interfaces_with_schema: int,
    unresolved_product_decisions: int,
    unresolved_architecture_decisions: int,
    broken_diagram_references: int,
) -> tuple[str, ...]:
    """Return Blueprint Completeness Gate blockers (03B, section 8.3)."""
    blockers: list[str] = []
    if requirements_total <= 0 or requirements_total != requirements_to_design:
        blockers.append(
            f"requirements_traced_to_design 未达 100%"
            f"（{requirements_to_design}/{requirements_total}）"
        )
    if requirements_total != requirements_to_task:
        blockers.append(
            f"requirements_traced_to_task 未达 100%（{requirements_to_task}/{requirements_total}）"
        )
    if (
        critical_requirements_total <= 0
        or critical_requirements_total != critical_requirements_to_test
    ):
        blockers.append(
            f"critical_requirements_traced_to_test 未达 100%"
            f"（{critical_requirements_to_test}/{critical_requirements_total}）"
        )
    if public_interfaces_total != public_interfaces_with_schema:
        blockers.append(
            f"public_interfaces_with_schema 未达 100%"
            f"（{public_interfaces_with_schema}/{public_interfaces_total}）"
        )
    if unresolved_product_decisions > 0:
        blockers.append(f"unresolved_product_decisions={unresolved_product_decisions}")
    if unresolved_architecture_decisions > 0:
        blockers.append(f"unresolved_architecture_decisions={unresolved_architecture_decisions}")
    if broken_diagram_references > 0:
        blockers.append(f"broken_diagram_references={broken_diagram_references}")
    tasks_without_stop = [
        unit.task_id for unit in blueprint.work_units if not unit.stop_escalation_conditions
    ]
    if tasks_without_stop:
        blockers.append("tasks_with_stop_condition 未达 100%：" + ", ".join(tasks_without_stop))
    return tuple(blockers)


# ---------------------------------------------------------------------------
# ENG7 — applications and extensions (03B, section 10)
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class ApplicationDirection:
    """One application direction (03B, section 10.1)."""

    direction_id: str
    users_stakeholders: tuple[str, ...]
    problem_and_scenarios: str
    required_capabilities: tuple[str, ...]
    current_coverage: str
    conditions: tuple[str, ...]
    measurable_value_metrics: tuple[str, ...]
    adoption_barriers: tuple[str, ...]
    failure_modes: tuple[str, ...]
    evidence_tier: str
    horizon: ApplicationHorizon

    def __post_init__(self) -> None:
        if not self.measurable_value_metrics:
            raise DomainError(
                f"application direction {self.direction_id!r} 缺少可测量价值指标",
                error_code="APPLICATION_DIRECTION_INVALID",
            )
        if not self.adoption_barriers or not self.failure_modes:
            raise DomainError(
                f"application direction {self.direction_id!r} 缺少采用障碍/失败模式",
                error_code="APPLICATION_DIRECTION_INVALID",
            )
        if not self.evidence_tier.strip():
            raise DomainError(
                f"application direction {self.direction_id!r} 缺少证据等级",
                error_code="APPLICATION_DIRECTION_INVALID",
            )

    def to_event_payload(self) -> dict[str, Any]:
        return _canonical_payload(asdict(self))


@dataclass(frozen=True, slots=True)
class ExtensionRoadmapItem:
    """One future extension (03B, section 10.2)."""

    extension_id: str
    goal: str
    non_goals: tuple[str, ...]
    trigger_conditions: tuple[str, ...]
    affected_refs: tuple[str, ...]
    compatibility_migration_strategy: str
    dependencies: tuple[str, ...]
    risk_cost_level: str
    reversibility: str
    adr_or_task_suggestion: str
    no_premature_coupling_rationale: str

    def __post_init__(self) -> None:
        if not self.goal.strip() or not self.no_premature_coupling_rationale.strip():
            raise DomainError(
                f"extension {self.extension_id!r} 缺少目标或不得提前耦合的理由",
                error_code="EXTENSION_ROADMAP_INVALID",
            )

    def to_event_payload(self) -> dict[str, Any]:
        return _canonical_payload(asdict(self))


@dataclass(frozen=True, slots=True)
class ApplicationDirectionPortfolio:
    """ENG7 application portfolio (03B, section 10.1)."""

    portfolio_id: str
    version: int
    project_id: str
    directions: tuple[ApplicationDirection, ...]
    artifact_hash: str | None = None
    status: EngineeringArtifactStatus = EngineeringArtifactStatus.ACTIVE
    created_at: datetime | None = None

    def __post_init__(self) -> None:
        finalize_artifact_hash(self)

    def content_payload(self) -> dict[str, Any]:
        payload = asdict(self)
        payload.pop("artifact_hash", None)
        payload.pop("status", None)
        return _canonical_payload(payload)

    def to_event_payload(self) -> dict[str, Any]:
        return _canonical_payload(asdict(self))


@dataclass(frozen=True, slots=True)
class ExtensionRoadmap:
    """ENG7 extension roadmap (03B, section 10.2)."""

    roadmap_id: str
    version: int
    project_id: str
    items: tuple[ExtensionRoadmapItem, ...]
    artifact_hash: str | None = None
    status: EngineeringArtifactStatus = EngineeringArtifactStatus.ACTIVE
    created_at: datetime | None = None

    def __post_init__(self) -> None:
        finalize_artifact_hash(self)

    def content_payload(self) -> dict[str, Any]:
        payload = asdict(self)
        payload.pop("artifact_hash", None)
        payload.pop("status", None)
        return _canonical_payload(payload)

    def to_event_payload(self) -> dict[str, Any]:
        return _canonical_payload(asdict(self))


# ---------------------------------------------------------------------------
# Regression (03B, section 14)
# ---------------------------------------------------------------------------

#: Deterministic earliest rollback point per change kind (GAP-1: 03B lists
#: alternative rollback points for some rows; the domain picks the earliest
#: conservative stage and records it here).
EARLIEST_ROLLBACK: Mapping[EngineeringChangeKind, EngineeringStageId | None] = {
    EngineeringChangeKind.S1_S4_CORE_SEMANTICS: None,  # 回 RQ1/RQ2F（工作流之外）
    EngineeringChangeKind.NEIGHBOR_CHANGED_NOVELTY: None,  # 回 RQ4E（工作流之外）
    EngineeringChangeKind.STAKEHOLDER_OR_CONOPS: EngineeringStageId.ENG1,
    EngineeringChangeKind.REQUIREMENT_OR_THRESHOLD: EngineeringStageId.ENG2,
    EngineeringChangeKind.TECHNOLOGY_ROUTE_OR_MAJOR_DEPENDENCY: EngineeringStageId.ENG3,
    EngineeringChangeKind.PUBLIC_INTERFACE_OR_DATA_OR_SECURITY_BOUNDARY: (EngineeringStageId.ENG4),
    EngineeringChangeKind.BLUEPRINT_GAP_FOUND: EngineeringStageId.ENG4,
    EngineeringChangeKind.IMPLEMENTATION_FALSIFIES_ARCHITECTURE: EngineeringStageId.ENG3,
    EngineeringChangeKind.NEW_EXPERIMENTAL_RESULTS: EngineeringStageId.ENG6,
    EngineeringChangeKind.MASTER_MANUSCRIPT_CLAIMS: EngineeringStageId.ENG8,
    EngineeringChangeKind.VENUE_GUIDANCE_UPDATE: EngineeringStageId.ENG9,
    EngineeringChangeKind.EVIDENCE_REVOCATION_OR_LICENSE: EngineeringStageId.ENG6,
}


@dataclass(frozen=True, slots=True)
class EngineeringRegressionResult:
    """Deterministic regression decision (03B, section 14; 06 NEEDS_REGRESSION)."""

    requires_regression: bool
    requires_reentry: bool
    earliest_rollback_stage: EngineeringStageId | None
    changed_kinds: tuple[EngineeringChangeKind, ...]
    status: EngineeringDeliveryStatus = EngineeringDeliveryStatus.NEEDS_REGRESSION


def engineering_regression_check(
    changed_kinds: tuple[EngineeringChangeKind, ...],
) -> EngineeringRegressionResult:
    """Map changed inputs to the earliest rollback stage (03B, section 14)."""
    if not changed_kinds:
        return EngineeringRegressionResult(
            requires_regression=False,
            requires_reentry=False,
            earliest_rollback_stage=None,
            changed_kinds=(),
            status=EngineeringDeliveryStatus.NOT_STARTED,
        )
    stages = [EARLIEST_ROLLBACK[kind] for kind in changed_kinds if kind in EARLIEST_ROLLBACK]
    reentry = any(
        kind
        in {
            EngineeringChangeKind.S1_S4_CORE_SEMANTICS,
            EngineeringChangeKind.NEIGHBOR_CHANGED_NOVELTY,
        }
        for kind in changed_kinds
    )
    workflow_stages = [stage for stage in stages if stage is not None]
    earliest = (
        min(workflow_stages, key=lambda stage: STAGE_ORDER.index(stage))
        if workflow_stages
        else None
    )
    return EngineeringRegressionResult(
        requires_regression=True,
        requires_reentry=reentry,
        earliest_rollback_stage=earliest,
        changed_kinds=tuple(changed_kinds),
    )


def artifact_needs_regression(artifact: Any) -> Any:
    """Mark an immutable artifact NEEDS_REGRESSION (history is preserved)."""
    if not hasattr(artifact, "status"):
        raise TypeError("artifact_needs_regression() requires a status field")
    return replace(artifact, status=EngineeringArtifactStatus.NEEDS_REGRESSION)


__all__ = [
    "BLUEPRINT_VAGUE_PATTERNS",
    "DELIVERY_STATUS_FOR_STAGE",
    "EARLIEST_ROLLBACK",
    "ENGINEERING_EVENT_TYPES",
    "EVENT_ENGINEERING_ARTIFACT_CREATED",
    "EVENT_ENGINEERING_GATE_OPENED",
    "EVENT_ENGINEERING_GATE_RESOLVED",
    "EVENT_ENGINEERING_REGRESSION_DETECTED",
    "EVENT_ENGINEERING_SCOPE_CHANGE_OPENED",
    "EVENT_ENGINEERING_STAGE_BLOCKED",
    "EVENT_ENGINEERING_STAGE_OPENED",
    "SCOPE_KEYS",
    "STAGE_ORDER",
    "ApplicationDirection",
    "ApplicationDirectionPortfolio",
    "ApplicationHorizon",
    "EngineeringArtifactStatus",
    "EngineeringChangeKind",
    "EngineeringDeliveryAcceptanceDecision",
    "EngineeringDeliveryMode",
    "EngineeringDeliveryStatus",
    "EngineeringGateType",
    "EngineeringMissionCharter",
    "EngineeringProfileChoice",
    "EngineeringReference",
    "EngineeringReferenceSet",
    "EngineeringRegressionResult",
    "EngineeringStageId",
    "EngineeringWorkUnitContract",
    "EngineeringArchitectureReviewDecision",
    "ExtensionRoadmap",
    "ExtensionRoadmapItem",
    "ExternalDependency",
    "FormalManuscriptDecision",
    "MechanicalEngineeringBlueprint",
    "OperationalConceptBundle",
    "OperationalScenario",
    "OptionTradeStudy",
    "PrototypeExecutionAuthorizationDecision",
    "RejectedOptionLog",
    "StakeholderEntry",
    "TechnologySelectionRecord",
    "TradeStudyOption",
    "artifact_needs_regression",
    "blueprint_completeness_blockers",
    "build_engineering_event",
    "charter_scope_changes",
    "conops_blockers",
    "delivery_status_for_stage",
    "eng0_entry_blockers",
    "finalize_artifact_hash",
    "engineering_next_stage",
    "engineering_regression_check",
    "ensure_artifact_hash",
    "superseded",
    "trade_study_blockers",
    "validate_technology_selection",
]
