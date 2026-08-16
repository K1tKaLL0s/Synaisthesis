"""Early research qualification domain objects (blueprint 03A, M2.3).

This module defines the RQ0-RQ3 artifact records, deterministic feasibility
logic, and the stable event catalog. It is deliberately persistence-free and
provider-free: no SQLAlchemy, Alembic, pydantic or HTTP imports are allowed
here. Later milestones add services, assessors, providers and repositories.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
from typing import Any, cast

from synaisthesis.domain.enums import (
    CapabilityStatus,
    EarlyFormalizationStatus,
    EngineeringConceptStatus,
    EngineeringRouteDecision,
    FeasibilityAssessmentStatus,
    FormalizationExecutionRoute,
    FormulaOrigin,
    PredicateVerdict,
    PriorArtCoverageStatus,
    ProvenanceType,
    ResearchRoute,
    RouteClassification,
)
from synaisthesis.domain.errors import DomainError
from synaisthesis.domain.event import DomainEvent, canonicalize, sha256_hex

CAPABILITY_TIER_ADVANCED = "ADVANCED"
CAPABILITY_EVAL_TTL_DAYS = 90
MAX_PUBLIC_EXPLANATION_ITEMS = 12

EVENT_NATURAL_LANGUAGE_DESIGN_READY = "NaturalLanguageDesignReady"
EVENT_FORMALIZATION_CAPABILITY_SELECTED = "FormalizationCapabilitySelected"
EVENT_NEIGHBOR_SEARCH_COMPLETED = "NeighborSearchCompleted"
EVENT_FORMALIZATION_FEASIBILITY_ASSESSED = "FormalizationFeasibilityAssessed"
EVENT_ENGINEERING_ROUTE_DECISION_OPENED = "EngineeringRouteDecisionOpened"
EVENT_ENGINEERING_ROUTE_SELECTED = "EngineeringRouteSelected"
EVENT_EARLY_FORMALIZATION_CREATED = "EarlyFormalizationCreated"
EVENT_ENGINEERING_CONCEPT_CREATED = "EngineeringConceptCreated"
EVENT_EARLY_FORMALIZATION_REVIEW_OPENED = "EarlyFormalizationReviewOpened"
EVENT_EARLY_ENGINEERING_CONCEPT_REVIEW_OPENED = "EarlyEngineeringConceptReviewOpened"
EVENT_EARLY_FORMALIZATION_APPROVED = "EarlyFormalizationApproved"
EVENT_EARLY_ENGINEERING_CONCEPT_APPROVED = "EarlyEngineeringConceptApproved"
EVENT_NOVELTY_REVIEW_STARTED = "NoveltyReviewStarted"
EVENT_NOVELTY_REVIEW_SCORED = "NoveltyReviewScored"
EVENT_NOVELTY_THRESHOLD_PASSED = "NoveltyThresholdPassed"
EVENT_ENGINEERING_NOVELTY_THRESHOLD_PASSED = "EngineeringNoveltyThresholdPassed"
EVENT_NOVELTY_RESEARCH_DECISION_OPENED = "NoveltyResearchDecisionOpened"
EVENT_NOVELTY_RESEARCH_REQUESTED = "NoveltyResearchRequested"
EVENT_NOVELTY_OVERRIDE_ACCEPTED = "NoveltyOverrideAccepted"

RQ_EVENT_TYPES = frozenset(
    {
        EVENT_NATURAL_LANGUAGE_DESIGN_READY,
        EVENT_FORMALIZATION_CAPABILITY_SELECTED,
        EVENT_NEIGHBOR_SEARCH_COMPLETED,
        EVENT_FORMALIZATION_FEASIBILITY_ASSESSED,
        EVENT_ENGINEERING_ROUTE_DECISION_OPENED,
        EVENT_ENGINEERING_ROUTE_SELECTED,
        EVENT_EARLY_FORMALIZATION_CREATED,
        EVENT_ENGINEERING_CONCEPT_CREATED,
        EVENT_EARLY_FORMALIZATION_REVIEW_OPENED,
        EVENT_EARLY_ENGINEERING_CONCEPT_REVIEW_OPENED,
        EVENT_EARLY_FORMALIZATION_APPROVED,
        EVENT_EARLY_ENGINEERING_CONCEPT_APPROVED,
        EVENT_NOVELTY_REVIEW_STARTED,
        EVENT_NOVELTY_REVIEW_SCORED,
        EVENT_NOVELTY_THRESHOLD_PASSED,
        EVENT_ENGINEERING_NOVELTY_THRESHOLD_PASSED,
        EVENT_NOVELTY_RESEARCH_DECISION_OPENED,
        EVENT_NOVELTY_RESEARCH_REQUESTED,
        EVENT_NOVELTY_OVERRIDE_ACCEPTED,
    }
)


def _canonical_payload(value: Any) -> dict[str, Any]:
    payload = canonicalize(value)
    if not isinstance(payload, dict):
        raise TypeError("domain artifact payload must canonicalize to an object")
    return cast(dict[str, Any], payload)


def is_user_actor(actor: ProvenanceType) -> bool:
    """Return True only for real user provenance (03A/08 human-decision rule)."""
    return actor in {ProvenanceType.USER_INPUT, ProvenanceType.USER_DECISION}


def _require_user_actor(actor: ProvenanceType) -> None:
    if not is_user_actor(actor):
        raise DomainError(
            f"decision requires a real user event; got actor={actor.value}",
            error_code="CONFIRMATION_REQUIRES_USER_EVENT",
        )


# ---------------------------------------------------------------------------
# RQ0 — capability
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class ModelProfile:
    """Model profile fields from blueprint 06, section 1 (model_profiles)."""

    id: str
    provider: str
    model: str
    family: str
    reasoning_tier: str
    structured_output_support: bool
    cost_profile: dict[str, Any]
    privacy_profile: dict[str, Any]
    enabled: bool

    def to_event_payload(self) -> dict[str, Any]:
        return _canonical_payload(asdict(self))


@dataclass(frozen=True, slots=True)
class FormalizationCapabilityProfile:
    """Capability evidence needed by the RQ0 gate (03A, section 2.2)."""

    model_profile_id: str
    capability_tier: str
    formalization_eval_score: float
    math_schema_valid_rate: float
    source_citation_support: bool
    structured_output_support: bool
    context_budget_sufficient: bool
    capability_evaluated_at: datetime
    capability_ttl_days: int = CAPABILITY_EVAL_TTL_DAYS
    budget_allowed: bool = True
    privacy_allowed: bool = True


def evaluate_formalizer_capability(
    profile: FormalizationCapabilityProfile,
    *,
    evaluated_at: datetime,
) -> tuple[CapabilityStatus, tuple[str, ...]]:
    """Evaluate the RQ0 capability gate (03A, section 2.2).

    Returns CAPABILITY_READY with an empty blocker list only when every
    threshold passes and the capability evidence has not expired. A missing
    budget/privacy authorization has its own status; all other failures are
    CAPABILITY_UNAVAILABLE with machine-readable blocker text.
    """
    if not profile.budget_allowed:
        return CapabilityStatus.BLOCKED_BUDGET, ("当前调用预算不允许 Early Formalizer 执行",)
    if not profile.privacy_allowed:
        return CapabilityStatus.BLOCKED_PRIVACY, ("当前隐私策略不允许 Early Formalizer 执行",)

    blockers: list[str] = []
    if profile.capability_tier != CAPABILITY_TIER_ADVANCED:
        blockers.append(f"capability_tier 必须为 {CAPABILITY_TIER_ADVANCED}")
    if profile.formalization_eval_score < 80.0:
        blockers.append("formalization_eval_score 必须 >= 80/100")
    if profile.math_schema_valid_rate < 0.95:
        blockers.append("math_schema_valid_rate 必须 >= 0.95")
    if not profile.source_citation_support:
        blockers.append("必须支持来源引用")
    if not profile.structured_output_support:
        blockers.append("必须支持结构化输出")
    if not profile.context_budget_sufficient:
        blockers.append("上下文预算必须能容纳 S1/S4、检索证据集与输出 Schema")
    age = evaluated_at - profile.capability_evaluated_at
    if age > timedelta(days=profile.capability_ttl_days):
        blockers.append("能力评估记录已过期")
    if blockers:
        return CapabilityStatus.CAPABILITY_UNAVAILABLE, tuple(blockers)
    return CapabilityStatus.CAPABILITY_READY, ()


@dataclass(frozen=True, slots=True)
class FormalizationCapabilityDecision:
    """RQ0 output (03A, section 2.3)."""

    decision_id: str
    project_id: str
    research_spec_id: str
    route: FormalizationExecutionRoute
    model_profile_id: str | None
    capability_evidence_refs: tuple[str, ...]
    input_spec_hash: str
    budget_snapshot_id: str | None
    privacy_policy_snapshot_id: str | None
    status: CapabilityStatus
    blocker: str | None

    def to_event_payload(self) -> dict[str, Any]:
        return _canonical_payload(asdict(self))


# ---------------------------------------------------------------------------
# RQ1 — neighbor evidence
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class PriorArtQueryRecord:
    """One RQ1 query record (03A, section 3.2)."""

    query_id: str
    original_text: str
    generated_from: tuple[str, ...]
    provider: str
    time_range: str
    filters: tuple[str, ...]
    page_count: int | None
    result_count: int | None
    executed_at: datetime | None

    def to_event_payload(self) -> dict[str, Any]:
        return _canonical_payload(asdict(self))


@dataclass(frozen=True, slots=True)
class PriorArtNeighbor:
    """One RQ1 neighbor (03A, section 3.4 and 06 prior_art_neighbors)."""

    neighbor_id: str
    neighbor_type: str
    stable_identifier: str
    canonical_url: str | None
    metadata_verified: bool
    maturity_evidence_refs: tuple[str, ...]
    theory_proximity: float | None
    application_proximity: float | None
    similarity_evidence_refs: tuple[str, ...]
    rank: int | None

    def to_event_payload(self) -> dict[str, Any]:
        return _canonical_payload(asdict(self))


@dataclass(frozen=True, slots=True)
class NeighborEvidenceSet:
    """RQ1 output (03A, section 3.5)."""

    search_id: str
    research_spec_id: str
    input_spec_hash: str
    query_records: tuple[PriorArtQueryRecord, ...]
    academic_neighbors: tuple[PriorArtNeighbor, ...]
    engineering_neighbors: tuple[PriorArtNeighbor, ...]
    standards_and_reference_architectures: tuple[str, ...]
    patent_neighbors: tuple[str, ...]
    metadata_verification_receipts: tuple[str, ...]
    inclusion_exclusion_log: str
    unsearched_areas: tuple[str, ...]
    coverage_status: PriorArtCoverageStatus
    coverage_blockers: tuple[str, ...]
    artifact_hash: str

    def to_event_payload(self) -> dict[str, Any]:
        return _canonical_payload(asdict(self))


# ---------------------------------------------------------------------------
# RQ2F — formalization feasibility
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class FeasibilityPredicate:
    """A single T*/E* predicate with evidence references (03A, section 4)."""

    predicate_id: str
    verdict: PredicateVerdict
    evidence_refs: tuple[str, ...]

    def to_event_payload(self) -> dict[str, Any]:
        return _canonical_payload(asdict(self))


@dataclass(frozen=True, slots=True)
class TheoryFitPredicates:
    """TFO/TFR/TFC/TFW/TFP matrix (03A, section 4.2)."""

    tfo: FeasibilityPredicate
    tfr: FeasibilityPredicate
    tfc: FeasibilityPredicate
    tfw: FeasibilityPredicate
    tfp: FeasibilityPredicate

    def as_tuple(self) -> tuple[FeasibilityPredicate, ...]:
        return (self.tfo, self.tfr, self.tfc, self.tfw, self.tfp)


@dataclass(frozen=True, slots=True)
class EngineeringFitPredicates:
    """EFS/EFI/EFA/EFM/EFF matrix (03A, section 4.3)."""

    efs: FeasibilityPredicate
    efi: FeasibilityPredicate
    efa: FeasibilityPredicate
    efm: FeasibilityPredicate
    eff: FeasibilityPredicate

    def as_tuple(self) -> tuple[FeasibilityPredicate, ...]:
        return (self.efs, self.efi, self.efa, self.efm, self.eff)


def predicate_merge(left: PredicateVerdict, right: PredicateVerdict) -> PredicateVerdict:
    """Conservative predicate merge: FAIL > UNKNOWN > PASS (03A, section 4.4)."""
    rank = {PredicateVerdict.PASS: 0, PredicateVerdict.UNKNOWN: 1, PredicateVerdict.FAIL: 2}
    return left if rank[left] >= rank[right] else right


def _fit(predicates: tuple[FeasibilityPredicate, ...]) -> bool | None:
    verdicts = [predicate.verdict for predicate in predicates]
    if PredicateVerdict.FAIL in verdicts:
        return False
    if PredicateVerdict.UNKNOWN in verdicts:
        return None
    return True


def theory_fit(predicates: TheoryFitPredicates) -> bool | None:
    """theory_fit = TFO ∧ TFR ∧ TFC ∧ TFW ∧ TFP (UNKNOWN never true)."""
    return _fit(predicates.as_tuple())


def engineering_fit(predicates: EngineeringFitPredicates) -> bool | None:
    """engineering_fit = EFS ∧ EFI ∧ EFA ∧ EFM ∧ EFF (UNKNOWN never true)."""
    return _fit(predicates.as_tuple())


def classify_formalization_feasibility(
    theory_fit: bool | None,
    engineering_fit: bool | None,
) -> RouteClassification:
    """Apply the fixed RQ2F truth table (03A, section 4.4)."""
    if theory_fit is None or engineering_fit is None:
        return RouteClassification.INCONCLUSIVE
    if theory_fit and engineering_fit:
        return RouteClassification.HYBRID_FIT
    if theory_fit:
        return RouteClassification.PURE_THEORY_FIT
    if engineering_fit:
        return RouteClassification.ENGINEERING_PROJECT_CANDIDATE
    return RouteClassification.NEITHER_CURRENTLY_FIT


def feasibility_status_for(
    classification: RouteClassification,
) -> FeasibilityAssessmentStatus:
    """Derive the assessment status from route classification (M2.3 GAP-2)."""
    if classification is RouteClassification.HYBRID_FIT:
        return FeasibilityAssessmentStatus.THEORY_OR_HYBRID_FIT
    if classification is RouteClassification.PURE_THEORY_FIT:
        return FeasibilityAssessmentStatus.THEORY_OR_HYBRID_FIT
    if classification is RouteClassification.ENGINEERING_PROJECT_CANDIDATE:
        return FeasibilityAssessmentStatus.ENGINEERING_ROUTE_DECISION_REQUIRED
    if classification is RouteClassification.NEITHER_CURRENTLY_FIT:
        return FeasibilityAssessmentStatus.FORMALIZATION_FEASIBILITY_USER_DECISION_REQUIRED
    return FeasibilityAssessmentStatus.FEASIBILITY_INCONCLUSIVE


def recommended_route_for(classification: RouteClassification) -> ResearchRoute | None:
    """Derive the recommended research route (M2.3 GAP-2)."""
    if classification in {
        RouteClassification.HYBRID_FIT,
        RouteClassification.PURE_THEORY_FIT,
    }:
        return ResearchRoute.THEORY
    if classification is RouteClassification.ENGINEERING_PROJECT_CANDIDATE:
        return ResearchRoute.ENGINEERING
    return None


@dataclass(frozen=True, slots=True)
class FormalizationFeasibilityAssessment:
    """RQ2F output (03A, section 4.5).

    status and recommended_route are derived from route_classification; create()
    computes them and the artifact hash. Direct construction with mismatched
    derived fields fails closed.
    """

    assessment_id: str
    version: int
    research_spec_id: str
    input_spec_hash: str
    neighbor_evidence_set_id: str
    assessor_session_ids: tuple[str, ...]
    theory_predicates: tuple[FeasibilityPredicate, ...]
    engineering_predicates: tuple[FeasibilityPredicate, ...]
    disagreements: tuple[str, ...]
    missing_information: tuple[str, ...]
    route_classification: RouteClassification
    public_explanation: tuple[str, ...]
    artifact_hash: str
    status: FeasibilityAssessmentStatus
    recommended_route: ResearchRoute | None

    def __post_init__(self) -> None:
        if len(self.public_explanation) > MAX_PUBLIC_EXPLANATION_ITEMS:
            raise DomainError(
                "public_explanation 最多 12 条",
                error_code="FEASIBILITY_EXPLANATION_TOO_LONG",
            )
        expected_status = feasibility_status_for(self.route_classification)
        if self.status is not expected_status:
            raise DomainError(
                f"status {self.status.value} 与 route_classification "
                f"{self.route_classification.value} 不一致",
                error_code="INVALID_FEASIBILITY_STATUS",
            )
        expected_route = recommended_route_for(self.route_classification)
        if self.recommended_route is not expected_route:
            raise DomainError(
                "recommended_route 与 route_classification 不一致",
                error_code="INVALID_FEASIBILITY_ROUTE",
            )
        expected_hash = sha256_hex(self.content_payload())
        if self.artifact_hash != expected_hash:
            raise DomainError(
                "artifact_hash 与 assessment 内容不一致",
                error_code="ARTIFACT_HASH_MISMATCH",
            )

    @classmethod
    def create(
        cls,
        *,
        assessment_id: str,
        version: int,
        research_spec_id: str,
        input_spec_hash: str,
        neighbor_evidence_set_id: str,
        assessor_session_ids: tuple[str, ...],
        theory_predicates: tuple[FeasibilityPredicate, ...],
        engineering_predicates: tuple[FeasibilityPredicate, ...],
        disagreements: tuple[str, ...],
        missing_information: tuple[str, ...],
        route_classification: RouteClassification,
        public_explanation: tuple[str, ...],
    ) -> FormalizationFeasibilityAssessment:
        """Create an assessment with derived status/route and artifact hash."""
        content = {
            "assessment_id": assessment_id,
            "version": version,
            "research_spec_id": research_spec_id,
            "input_spec_hash": input_spec_hash,
            "neighbor_evidence_set_id": neighbor_evidence_set_id,
            "assessor_session_ids": list(assessor_session_ids),
            "theory_predicates": [predicate.to_event_payload() for predicate in theory_predicates],
            "engineering_predicates": [
                predicate.to_event_payload() for predicate in engineering_predicates
            ],
            "disagreements": list(disagreements),
            "missing_information": list(missing_information),
            "route_classification": route_classification.value,
            "public_explanation": list(public_explanation),
        }
        return cls(
            assessment_id=assessment_id,
            version=version,
            research_spec_id=research_spec_id,
            input_spec_hash=input_spec_hash,
            neighbor_evidence_set_id=neighbor_evidence_set_id,
            assessor_session_ids=assessor_session_ids,
            theory_predicates=theory_predicates,
            engineering_predicates=engineering_predicates,
            disagreements=disagreements,
            missing_information=missing_information,
            route_classification=route_classification,
            public_explanation=public_explanation,
            artifact_hash=sha256_hex(content),
            status=feasibility_status_for(route_classification),
            recommended_route=recommended_route_for(route_classification),
        )

    def content_payload(self) -> dict[str, Any]:
        """Return the hash-covered semantic content (derived fields excluded)."""
        payload = asdict(self)
        for key in ("artifact_hash", "status", "recommended_route"):
            payload.pop(key, None)
        return _canonical_payload(payload)

    def to_event_payload(self) -> dict[str, Any]:
        return _canonical_payload(asdict(self))


@dataclass(frozen=True, slots=True)
class EngineeringRouteSelection:
    """Derived record created only by a real user ENGINEERING_ROUTE_DECISION."""

    id: str
    project_id: str
    feasibility_assessment_id: str
    decision: EngineeringRouteDecision
    user_actor_id: str
    decision_event_id: str
    bound_assessment_hash: str
    input_spec_hash: str
    created_at: datetime

    def to_event_payload(self) -> dict[str, Any]:
        return _canonical_payload(asdict(self))


# ---------------------------------------------------------------------------
# RQ2M — early formalization
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class FormulaItem:
    """One formula item (03A, section 5.3)."""

    formula_id: str
    formula_type: str
    latex: str
    normalized_math_ast: str | None
    symbols_used: tuple[str, ...]
    source_spec_fields: tuple[str, ...]
    assumption_formula_ids: tuple[str, ...]
    neighbor_refs: tuple[str, ...]
    origin: FormulaOrigin
    confidence: float | None
    known_ambiguities: tuple[str, ...]
    falsification_or_failure_formula_id: str

    def to_event_payload(self) -> dict[str, Any]:
        return _canonical_payload(asdict(self))


@dataclass(frozen=True, slots=True)
class EarlyFormalizationBundle:
    """RQ2M output (03A, section 5.2)."""

    formalization_id: str
    version: int
    research_spec_id: str
    input_spec_hash: str
    feasibility_assessment_id: str
    neighbor_evidence_set_id: str
    formalizer_profile_or_import_id: str
    notation_table: tuple[str, ...]
    formula_items: tuple[FormulaItem, ...]
    formula_dependency_graph: dict[str, tuple[str, ...]]
    semantic_alignment_matrix: tuple[str, ...]
    neighbor_difference_matrix: tuple[str, ...]
    uncertainty_register: tuple[str, ...]
    plain_language_explanation: tuple[str, ...]
    validator_results: tuple[str, ...]
    artifact_hash: str
    status: EarlyFormalizationStatus

    def to_event_payload(self) -> dict[str, Any]:
        return _canonical_payload(asdict(self))


# ---------------------------------------------------------------------------
# RQ2E — engineering concept
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class EngineeringConceptBundle:
    """RQ2E output (03A, section 6.3)."""

    concept_id: str
    version: int
    research_spec_id: str
    input_spec_hash: str
    route_selection_id: str
    feasibility_assessment_id: str
    neighbor_evidence_set_id: str
    notation_table: tuple[str, ...]
    system_boundary_model: dict[str, Any]
    actors_and_use_cases: tuple[str, ...]
    input_output_contracts: tuple[str, ...]
    state_transition_formulas: tuple[str, ...]
    requirement_predicates: tuple[str, ...]
    quality_metric_formulas: tuple[str, ...]
    architecture_graph_candidate: dict[str, Any]
    traceability_relation: dict[str, tuple[str, ...]]
    verification_obligations: tuple[str, ...]
    neighbor_difference_matrix: tuple[str, ...]
    assumptions_and_constraints: tuple[str, ...]
    unresolved_thresholds: tuple[str, ...]
    plain_language_explanation: tuple[str, ...]
    artifact_hash: str
    status: EngineeringConceptStatus

    def to_event_payload(self) -> dict[str, Any]:
        return _canonical_payload(asdict(self))


# ---------------------------------------------------------------------------
# RQ3 — user approvals
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class UserFormalizationApproval:
    """RQ3M approval; binding fields are immutable (03A, section 7.1)."""

    formalization_id: str
    version: int
    formalization_hash: str
    input_spec_hash: str
    route: ResearchRoute
    actor: ProvenanceType
    user_event_id: str
    decided_at: datetime

    def __post_init__(self) -> None:
        _require_user_actor(self.actor)
        if self.route is not ResearchRoute.THEORY:
            raise DomainError(
                "理论形式化审批必须绑定 THEORY route",
                error_code="INVALID_APPROVAL_ROUTE",
            )

    def to_event_payload(self) -> dict[str, Any]:
        return _canonical_payload(asdict(self))


@dataclass(frozen=True, slots=True)
class UserEngineeringConceptApproval:
    """RQ3E approval; binding fields are immutable (03A, section 7.2)."""

    concept_id: str
    version: int
    concept_hash: str
    route_selection_id: str
    input_spec_hash: str
    route: ResearchRoute
    actor: ProvenanceType
    user_event_id: str
    decided_at: datetime

    def __post_init__(self) -> None:
        _require_user_actor(self.actor)
        if self.route is not ResearchRoute.ENGINEERING:
            raise DomainError(
                "工程概念审批必须绑定 ENGINEERING route",
                error_code="INVALID_APPROVAL_ROUTE",
            )

    def to_event_payload(self) -> dict[str, Any]:
        return _canonical_payload(asdict(self))


# ---------------------------------------------------------------------------
# Event catalog
# ---------------------------------------------------------------------------


def build_qualification_event(
    event_type: str,
    *,
    aggregate_type: str,
    aggregate_id: str,
    payload: dict[str, Any],
    sequence: int,
) -> DomainEvent:
    """Build an immutable qualification DomainEvent with a stable event hash."""
    if event_type not in RQ_EVENT_TYPES:
        raise DomainError(
            f"unknown qualification event type {event_type!r}",
            error_code="UNKNOWN_EVENT_TYPE",
        )
    return DomainEvent(
        aggregate_type=aggregate_type,
        aggregate_id=aggregate_id,
        event_type=event_type,
        payload=payload,
        sequence=sequence,
    )


__all__ = [
    "CAPABILITY_EVAL_TTL_DAYS",
    "CAPABILITY_TIER_ADVANCED",
    "EVENT_EARLY_ENGINEERING_CONCEPT_APPROVED",
    "EVENT_EARLY_ENGINEERING_CONCEPT_REVIEW_OPENED",
    "EVENT_EARLY_FORMALIZATION_APPROVED",
    "EVENT_EARLY_FORMALIZATION_CREATED",
    "EVENT_EARLY_FORMALIZATION_REVIEW_OPENED",
    "EVENT_ENGINEERING_CONCEPT_CREATED",
    "EVENT_ENGINEERING_NOVELTY_THRESHOLD_PASSED",
    "EVENT_ENGINEERING_ROUTE_DECISION_OPENED",
    "EVENT_ENGINEERING_ROUTE_SELECTED",
    "EVENT_FORMALIZATION_CAPABILITY_SELECTED",
    "EVENT_FORMALIZATION_FEASIBILITY_ASSESSED",
    "EVENT_NEIGHBOR_SEARCH_COMPLETED",
    "EVENT_NATURAL_LANGUAGE_DESIGN_READY",
    "EVENT_NOVELTY_OVERRIDE_ACCEPTED",
    "EVENT_NOVELTY_REVIEW_SCORED",
    "EVENT_NOVELTY_REVIEW_STARTED",
    "EVENT_NOVELTY_RESEARCH_DECISION_OPENED",
    "EVENT_NOVELTY_RESEARCH_REQUESTED",
    "EVENT_NOVELTY_THRESHOLD_PASSED",
    "EngineeringConceptBundle",
    "EngineeringFitPredicates",
    "EngineeringRouteSelection",
    "EarlyFormalizationBundle",
    "FeasibilityPredicate",
    "FormalizationCapabilityDecision",
    "FormalizationCapabilityProfile",
    "FormalizationFeasibilityAssessment",
    "FormulaItem",
    "ModelProfile",
    "NeighborEvidenceSet",
    "PriorArtNeighbor",
    "PriorArtQueryRecord",
    "RQ_EVENT_TYPES",
    "TheoryFitPredicates",
    "UserEngineeringConceptApproval",
    "UserFormalizationApproval",
    "build_qualification_event",
    "classify_formalization_feasibility",
    "engineering_fit",
    "evaluate_formalizer_capability",
    "feasibility_status_for",
    "is_user_actor",
    "predicate_merge",
    "recommended_route_for",
    "theory_fit",
]
