"""Early research qualification application service (blueprint 07, section 3).

M2.4 scope: orchestrate synchronous prior-art providers into an immutable
NeighborEvidenceSet, with deterministic deduplication, sorting, ranking and
coverage validation. No database, artifact store, event stream or network I/O
is performed here yet; those capabilities arrive in later storage tasks.
"""

from __future__ import annotations

from collections.abc import Callable, Sequence
from dataclasses import dataclass, replace
from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

from synaisthesis.agents.auditor import NoveltyAuditor
from synaisthesis.agents.early_formalizer import (
    EarlyFormalizer,
    build_formula_items,
    validate_formula_items,
)
from synaisthesis.agents.engineering_feasibility_assessor import (
    EngineeringFeasibilityAssessor,
    build_engineering_concept_bundle,
    engineering_concept_content_payload,
)
from synaisthesis.agents.novelty_reviewer import NoveltyReviewer
from synaisthesis.agents.schemas import MechanismSketch, NaturalLanguageSpec, ResearchScopeSpec
from synaisthesis.application.novelty_service import (
    novelty_next_target,
    open_low_novelty_research_gate,
    start_novelty_review,
)
from synaisthesis.domain.enums import (
    CapabilityStatus,
    EarlyFormalizationStatus,
    EngineeringConceptStatus,
    EngineeringRouteDecision,
    FormalizationExecutionRoute,
    PriorArtCoverageStatus,
    ProvenanceType,
    QualificationGateType,
    QualifiedNextTarget,
    ResearchRoute,
)
from synaisthesis.domain.errors import DomainError
from synaisthesis.domain.event import sha256_hex
from synaisthesis.domain.gate import Gate, GateBinding
from synaisthesis.domain.novelty import NoveltyReview, novelty_policy_for
from synaisthesis.domain.qualification import (
    EarlyFormalizationBundle,
    EngineeringConceptBundle,
    EngineeringRouteSelection,
    FeasibilityPredicateMatrix,
    FormalizationCapabilityDecision,
    FormalizationCapabilityProfile,
    FormalizationFeasibilityAssessment,
    NeighborEvidenceSet,
    UserEngineeringConceptApproval,
    UserFormalizationApproval,
    classify_formalization_feasibility,
    engineering_fit,
    evaluate_formalizer_capability,
    merge_feasibility_matrices,
    theory_fit,
)
from synaisthesis.providers.prior_art.base import (
    PriorArtProvider,
    PriorArtQueryRequest,
    ProviderNeighborRecord,
)
from synaisthesis.providers.prior_art.normalization import (
    deduplicate_provider_records,
    metadata_receipts,
    sort_provider_records,
    to_prior_art_neighbor,
)

MIN_ACADEMIC_SOURCE_CLASSES = 3
MIN_ENGINEERING_SOURCE_CLASSES = 2
MIN_ACADEMIC_NEIGHBORS = 5
MIN_ENGINEERING_NEIGHBORS = 3
MIN_MATURITY_EVIDENCE_REFS = 2


def _provider_record_kind(record: ProviderNeighborRecord) -> str:
    return record.kind


def _collect_provider_records(
    *,
    academic_providers: Sequence[PriorArtProvider],
    engineering_providers: Sequence[PriorArtProvider],
    queries: tuple[PriorArtQueryRequest, ...],
) -> tuple[list[ProviderNeighborRecord], list[ProviderNeighborRecord], list[str]]:
    academic_records: list[ProviderNeighborRecord] = []
    engineering_records: list[ProviderNeighborRecord] = []
    failures: list[str] = []
    for request in queries:
        providers = academic_providers if request.kind == "academic" else engineering_providers
        if not providers:
            failures.append(f"{request.kind} query has no configured provider")
            continue
        for provider in providers:
            try:
                records = provider.search(request.query)
            except Exception as exc:  # noqa: BLE001 - provider boundary must fail closed
                failures.append(
                    f"provider {getattr(provider, 'source_name', provider)!r} "
                    f"failed with {type(exc).__name__}"
                )
                continue
            for record in records:
                if record.kind != request.kind:
                    failures.append(
                        f"provider {getattr(provider, 'source_name', provider)!r} "
                        f"returned {record.kind!r} record for {request.kind!r} query"
                    )
                    continue
                if request.kind == "academic":
                    academic_records.append(record)
                else:
                    engineering_records.append(record)
    return academic_records, engineering_records, failures


def validate_prior_art_coverage(
    *,
    academic_records: tuple[ProviderNeighborRecord, ...],
    engineering_records: tuple[ProviderNeighborRecord, ...],
    queries: tuple[PriorArtQueryRequest, ...],
    now: datetime | None = None,
) -> tuple[PriorArtCoverageStatus, tuple[str, ...]]:
    """Validate the RQ1 minimum coverage gate (03A, section 3.3).

    Returns COMPLETE only when every default minimum is met. Any deficiency is
    reported as a deterministic blocker tuple and mapped to PARTIAL.
    """
    del now  # reserved for provider freshness checks in later real-provider tasks
    blockers: list[str] = []

    query_kinds = {request.kind for request in queries}
    if "academic" not in query_kinds:
        blockers.append("缺少学术查询方向：必须从 S1/S4 字段分别派生学术查询")
    if "engineering" not in query_kinds:
        blockers.append("缺少工程查询方向：必须从 S1/S4 字段分别派生工程查询")

    academic_sources = {record.provider_name for record in academic_records}
    engineering_sources = {record.provider_name for record in engineering_records}
    if len(academic_sources) < MIN_ACADEMIC_SOURCE_CLASSES:
        blockers.append(
            f"学术来源类别不足：需要至少 {MIN_ACADEMIC_SOURCE_CLASSES} 类，"
            f"当前 {len(academic_sources)} 类"
        )
    if len(engineering_sources) < MIN_ENGINEERING_SOURCE_CLASSES:
        blockers.append(
            f"工程来源类别不足：需要至少 {MIN_ENGINEERING_SOURCE_CLASSES} 类，"
            f"当前 {len(engineering_sources)} 类"
        )

    if len(academic_records) < MIN_ACADEMIC_NEIGHBORS:
        blockers.append(
            f"学术近邻数量不足：去重后需要至少 {MIN_ACADEMIC_NEIGHBORS} 个，"
            f"当前 {len(academic_records)} 个"
        )
    if len(engineering_records) < MIN_ENGINEERING_NEIGHBORS:
        blockers.append(
            f"工程近邻数量不足：去重后需要至少 {MIN_ENGINEERING_NEIGHBORS} 个，"
            f"当前 {len(engineering_records)} 个"
        )

    for record in academic_records + engineering_records:
        if not record.stable_identifier.strip() and not (
            record.canonical_url and record.canonical_url.strip()
        ):
            blockers.append(f"近邻 {record.stable_identifier!r} 缺少可稳定解析的标识符或 URL")
        if not record.metadata_verified:
            blockers.append(f"近邻 {record.stable_identifier!r} metadata_verified=false")
        if record.accessed_at is None:
            blockers.append(f"近邻 {record.stable_identifier!r} 缺少访问时间")
        if (
            _provider_record_kind(record) == "engineering"
            and len(record.maturity_evidence_refs) < MIN_MATURITY_EVIDENCE_REFS
        ):
            blockers.append(
                f"工程近邻 {record.stable_identifier!r} 成熟度证据不足："
                f"至少需要 {MIN_MATURITY_EVIDENCE_REFS} 条引用"
            )

    status = PriorArtCoverageStatus.COMPLETE if not blockers else PriorArtCoverageStatus.PARTIAL
    return status, tuple(blockers)


def neighbor_evidence_content_payload(evidence: NeighborEvidenceSet) -> dict[str, object]:
    """Return the hash-covered semantic payload (artifact_hash excluded)."""
    payload = evidence.to_event_payload()
    payload.pop("artifact_hash", None)
    return payload


def run_prior_art_search(
    *,
    academic_providers: Sequence[PriorArtProvider],
    engineering_providers: Sequence[PriorArtProvider],
    queries: tuple[PriorArtQueryRequest, ...],
    research_spec_id: str,
    input_spec_hash: str,
    search_id: str | None = None,
    unsearched_areas: tuple[str, ...] = (),
    inclusion_exclusion_log: str = "",
    now: datetime | None = None,
) -> NeighborEvidenceSet:
    """Run a synchronous fake/real prior-art search and return RQ1 evidence.

    Provider output is quarantined as data only, deduplicated by stable
    identifier/URL, sorted by route-specific proximity and ranked from 1.
    Provider failures produce FAILED_PROVIDER; data deficiencies produce
    PARTIAL; only a fully passing coverage gate produces COMPLETE.
    """
    ordered_queries = tuple(sorted(queries, key=lambda item: item.query.query_id))
    academic_records, engineering_records, failures = _collect_provider_records(
        academic_providers=academic_providers,
        engineering_providers=engineering_providers,
        queries=ordered_queries,
    )

    academic_unique = deduplicate_provider_records(tuple(academic_records))
    engineering_unique = deduplicate_provider_records(tuple(engineering_records))
    academic_sorted = sort_provider_records(academic_unique, kind="academic")
    engineering_sorted = sort_provider_records(engineering_unique, kind="engineering")
    academic_neighbors = tuple(
        to_prior_art_neighbor(record, rank=index)
        for index, record in enumerate(academic_sorted, start=1)
    )
    engineering_neighbors = tuple(
        to_prior_art_neighbor(record, rank=index)
        for index, record in enumerate(engineering_sorted, start=1)
    )

    coverage_status, coverage_blockers = validate_prior_art_coverage(
        academic_records=academic_unique,
        engineering_records=engineering_unique,
        queries=ordered_queries,
        now=now,
    )
    blockers = list(coverage_blockers)
    if failures:
        coverage_status = PriorArtCoverageStatus.FAILED_PROVIDER
        blockers = failures + blockers

    if search_id is None:
        search_id = "prior-art:" + sha256_hex(
            {
                "research_spec_id": research_spec_id,
                "input_spec_hash": input_spec_hash,
                "query_ids": [item.query.query_id for item in ordered_queries],
                "academic_ids": [item.stable_identifier for item in academic_sorted],
                "engineering_ids": [item.stable_identifier for item in engineering_sorted],
            }
        )

    evidence = NeighborEvidenceSet(
        search_id=search_id,
        research_spec_id=research_spec_id,
        input_spec_hash=input_spec_hash,
        query_records=tuple(item.query for item in ordered_queries),
        academic_neighbors=academic_neighbors,
        engineering_neighbors=engineering_neighbors,
        standards_and_reference_architectures=(),
        patent_neighbors=(),
        metadata_verification_receipts=metadata_receipts(academic_unique + engineering_unique),
        inclusion_exclusion_log=inclusion_exclusion_log,
        unsearched_areas=unsearched_areas,
        coverage_status=coverage_status,
        coverage_blockers=tuple(blockers),
        artifact_hash="0" * 64,
    )
    return replace(
        evidence,
        artifact_hash=sha256_hex(neighbor_evidence_content_payload(evidence)),
    )


def assess_formalization_feasibility_from_matrices(
    *,
    assessment_id: str,
    version: int,
    research_spec_id: str,
    input_spec_hash: str,
    neighbor_evidence_set_id: str,
    assessor_session_ids: tuple[str, ...],
    early_matrix: FeasibilityPredicateMatrix,
    engineering_matrix: FeasibilityPredicateMatrix,
    public_explanation: tuple[str, ...],
) -> FormalizationFeasibilityAssessment:
    """Merge two assessor matrices conservatively and freeze an RQ2F assessment."""
    merged, disagreements = merge_feasibility_matrices(early_matrix, engineering_matrix)
    classification = classify_formalization_feasibility(
        theory_fit(merged.theory),
        engineering_fit(merged.engineering),
    )
    missing_information = tuple(
        f"{predicate.predicate_id}=UNKNOWN"
        for predicate in merged.theory.as_tuple() + merged.engineering.as_tuple()
        if predicate.verdict.value == "UNKNOWN"
    )
    return FormalizationFeasibilityAssessment.create(
        assessment_id=assessment_id,
        version=version,
        research_spec_id=research_spec_id,
        input_spec_hash=input_spec_hash,
        neighbor_evidence_set_id=neighbor_evidence_set_id,
        assessor_session_ids=assessor_session_ids,
        theory_predicates=merged.theory.as_tuple(),
        engineering_predicates=merged.engineering.as_tuple(),
        disagreements=disagreements,
        missing_information=missing_information,
        route_classification=classification,
        public_explanation=public_explanation,
    )


def assess_formalization_feasibility(
    *,
    assessment_id: str,
    version: int,
    research_spec_id: str,
    input_spec_hash: str,
    neighbor_evidence_set_id: str,
    early_formalizer: EarlyFormalizer,
    engineering_assessor: EngineeringFeasibilityAssessor,
    spec: NaturalLanguageSpec,
    mechanism: MechanismSketch,
    scope: ResearchScopeSpec,
    evidence: NeighborEvidenceSet,
    public_explanation: tuple[str, ...],
) -> FormalizationFeasibilityAssessment:
    """Run two isolated RQ2F assessor sessions and merge their matrices."""
    return assess_formalization_feasibility_from_matrices(
        assessment_id=assessment_id,
        version=version,
        research_spec_id=research_spec_id,
        input_spec_hash=input_spec_hash,
        neighbor_evidence_set_id=neighbor_evidence_set_id,
        assessor_session_ids=(
            early_formalizer.session_id,
            engineering_assessor.session_id,
        ),
        early_matrix=early_formalizer.assess(spec, mechanism, scope, evidence),
        engineering_matrix=engineering_assessor.assess(spec, mechanism, scope, evidence),
        public_explanation=public_explanation,
    )


def open_formalization_feasibility_gate(
    *,
    assessment: FormalizationFeasibilityAssessment,
    gate_id: str,
) -> Gate | None:
    """Open only the RQ2F Gate required by the fixed route classification."""
    gate_type: QualificationGateType | None = None
    if assessment.route_classification.value == "ENGINEERING_PROJECT_CANDIDATE":
        gate_type = QualificationGateType.ENGINEERING_ROUTE_DECISION
    elif assessment.route_classification.value in {
        "NEITHER_CURRENTLY_FIT",
        "INCONCLUSIVE",
    }:
        gate_type = QualificationGateType.FORMALIZATION_FEASIBILITY_DECISION
    if gate_type is None:
        return None
    return Gate(
        gate_id=gate_id,
        project_id=assessment.research_spec_id,
        gate_type=gate_type,
        binding=GateBinding(
            gate_type=gate_type,
            artifact_id=assessment.assessment_id,
            version=assessment.version,
            artifact_hash=assessment.artifact_hash,
            input_spec_hash=assessment.input_spec_hash,
        ),
        reason=assessment.route_classification.value,
    )


def _check_current_binding(
    *,
    gate: Gate,
    current_input_spec_hash: str,
) -> None:
    if gate.binding.input_spec_hash != current_input_spec_hash:
        raise DomainError(
            "current S1/S4 hash does not match the gate binding",
            error_code="STALE_FEASIBILITY_BINDING",
        )


def resolve_engineering_route_decision(
    *,
    gate: Gate,
    decision: str,
    actor: ProvenanceType,
    user_event_id: str,
    current_input_spec_hash: str,
    at: datetime,
    selection_id: str | None = None,
) -> tuple[Gate, EngineeringRouteSelection | None]:
    """Resolve ENGINEERING_ROUTE_DECISION; only TRY_ENGINEERING_PROJECT creates a selection."""
    if gate.gate_type is not QualificationGateType.ENGINEERING_ROUTE_DECISION:
        raise DomainError(
            f"gate type {gate.gate_type.value} cannot resolve an engineering route decision",
            error_code="GATE_TYPE_MISMATCH",
        )
    _check_current_binding(gate=gate, current_input_spec_hash=current_input_spec_hash)
    resolved = gate.resolve(
        decision=decision,
        actor=actor,
        user_event_id=user_event_id,
        at=at,
    )
    if decision != EngineeringRouteDecision.TRY_ENGINEERING_PROJECT.value:
        return resolved, None
    selection = EngineeringRouteSelection(
        id=selection_id or uuid4().hex,
        project_id=gate.project_id,
        feasibility_assessment_id=gate.binding.artifact_id,
        decision=EngineeringRouteDecision.TRY_ENGINEERING_PROJECT,
        user_actor_id=actor.value,
        decision_event_id=user_event_id,
        bound_assessment_hash=gate.binding.artifact_hash,
        input_spec_hash=gate.binding.input_spec_hash,
        created_at=at,
    )
    return resolved, selection


def resolve_formalization_feasibility_decision(
    *,
    gate: Gate,
    decision: str,
    actor: ProvenanceType,
    user_event_id: str,
    current_input_spec_hash: str,
    at: datetime,
) -> Gate:
    """Resolve FORMALIZATION_FEASIBILITY_DECISION with current-hash binding."""
    if gate.gate_type is not QualificationGateType.FORMALIZATION_FEASIBILITY_DECISION:
        raise DomainError(
            f"gate type {gate.gate_type.value} cannot resolve a formalization feasibility decision",
            error_code="GATE_TYPE_MISMATCH",
        )
    _check_current_binding(gate=gate, current_input_spec_hash=current_input_spec_hash)
    return gate.resolve(
        decision=decision,
        actor=actor,
        user_event_id=user_event_id,
        at=at,
    )


def early_formula_bundle_content_payload(bundle: EarlyFormalizationBundle) -> dict[str, object]:
    """Return the hash-covered RQ2M content (derived fields excluded)."""
    payload = bundle.to_event_payload()
    for key in ("artifact_hash", "status", "validator_results"):
        payload.pop(key, None)
    return payload


def build_early_formula_bundle(
    *,
    capability_profile: FormalizationCapabilityProfile,
    feasibility_assessment: FormalizationFeasibilityAssessment,
    spec: NaturalLanguageSpec,
    mechanism: MechanismSketch,
    scope: ResearchScopeSpec,
    evidence: NeighborEvidenceSet,
    formalizer_session_id: str,
    formalization_id: str | None = None,
    version: int = 1,
    now: datetime | None = None,
) -> EarlyFormalizationBundle:
    """Build an RQ2M bundle; capability-gate failure blocks construction.

    The bundle is always a CANDIDATE. Invalid formula material fails closed
    here and never reaches a caller as a malformed bundle.
    """
    capability_status, blockers = evaluate_formalizer_capability(
        capability_profile,
        evaluated_at=now or datetime.now(UTC),
    )
    if capability_status.value != "CAPABILITY_READY":
        raise DomainError(
            "formalizer capability gate failed: " + "; ".join(blockers),
            error_code="FORMALIZER_CAPABILITY_UNAVAILABLE",
        )
    formula_items = build_formula_items(
        spec=spec,
        mechanism=mechanism,
        scope=scope,
        evidence=evidence,
    )
    notation_table = (
        "X: object domain element",
        "Y: output object",
        "A: core assumption predicate",
        "C: core conclusion predicate",
        "I: invariant predicate",
        "s: state",
        "u: control input",
        "theta: parameters",
        "M: theory model space",
        "Aspace: application space",
        "O: verification obligations",
    )
    dependency_graph = {
        "f-io-map": ("f-assumption",),
        "f-state": ("f-assumption",),
        "f-invariant": ("f-assumption",),
        "f-core-claim": ("f-assumption", "f-failure-witness"),
        "f-objective": ("f-assumption",),
        "f-failure-witness": ("f-assumption",),
    }
    bundle = EarlyFormalizationBundle(
        formalization_id=formalization_id or uuid4().hex,
        version=version,
        research_spec_id=feasibility_assessment.research_spec_id,
        input_spec_hash=feasibility_assessment.input_spec_hash,
        feasibility_assessment_id=feasibility_assessment.assessment_id,
        neighbor_evidence_set_id=evidence.search_id,
        formalizer_profile_or_import_id=capability_profile.model_profile_id,
        notation_table=notation_table,
        formula_items=formula_items,
        formula_dependency_graph=dependency_graph,
        semantic_alignment_matrix=(
            "S1.core_definition -> f-core-claim",
            "S4.object_domain -> f-object-domain",
            "S4.central_claims -> f-core-claim",
            "S4.evidence_requirements -> f-verification",
        ),
        neighbor_difference_matrix=(f"{scope.nearest_neighbor_difference} -> f-core-claim",),
        uncertainty_register=tuple(mechanism.uncertainty_register),
        plain_language_explanation=("bundle is a formalization candidate, not a proof",),
        validator_results=(),
        artifact_hash="0" * 64,
        status=EarlyFormalizationStatus.EARLY_FORMALIZATION_CANDIDATE,
    )
    issues = validate_formula_items(
        formula_items=bundle.formula_items,
        notation_table=bundle.notation_table,
        formula_dependency_graph=bundle.formula_dependency_graph,
    )
    if issues:
        raise DomainError(
            "RQ2M bundle invalid: " + "; ".join(issues),
            error_code="FORMULA_BUNDLE_INVALID",
        )
    return replace(
        bundle,
        artifact_hash=sha256_hex(early_formula_bundle_content_payload(bundle)),
    )


def validate_early_formula_bundle(
    bundle: EarlyFormalizationBundle,
) -> tuple[EarlyFormalizationStatus, tuple[str, ...]]:
    """Validate an RQ2M bundle and map issues to a deterministic status."""
    expected_hash = sha256_hex(early_formula_bundle_content_payload(bundle))
    if bundle.artifact_hash != expected_hash:
        return (
            EarlyFormalizationStatus.SCHEMA_INVALID,
            ("artifact_hash 与 bundle 内容不一致",),
        )
    issues = validate_formula_items(
        formula_items=bundle.formula_items,
        notation_table=bundle.notation_table,
        formula_dependency_graph=bundle.formula_dependency_graph,
    )
    if not issues:
        return EarlyFormalizationStatus.EARLY_FORMALIZATION_CANDIDATE, ()
    if any("不是 LaTeX" in issue for issue in issues):
        return EarlyFormalizationStatus.SEMANTIC_GAP, issues
    if any("缺少失败" in issue or "缺少必需" in issue or "缺少源" in issue for issue in issues):
        return EarlyFormalizationStatus.FORMULA_COVERAGE_INCOMPLETE, issues
    return EarlyFormalizationStatus.SCHEMA_INVALID, issues


def open_early_formalization_review(
    *,
    bundle: EarlyFormalizationBundle,
    gate_id: str,
) -> Gate:
    """Open EARLY_FORMALIZATION_REVIEW bound to formula/spec hash."""
    return Gate(
        gate_id=gate_id,
        project_id=bundle.research_spec_id,
        gate_type=QualificationGateType.EARLY_FORMALIZATION_REVIEW,
        binding=GateBinding(
            gate_type=QualificationGateType.EARLY_FORMALIZATION_REVIEW,
            artifact_id=bundle.formalization_id,
            version=bundle.version,
            artifact_hash=bundle.artifact_hash,
            input_spec_hash=bundle.input_spec_hash,
            route=ResearchRoute.THEORY,
        ),
    )


def resolve_early_formalization_review(
    *,
    gate: Gate,
    decision: str,
    actor: ProvenanceType,
    user_event_id: str,
    current_bundle_hash: str,
    at: datetime,
) -> tuple[Gate, UserFormalizationApproval | None]:
    """Resolve EARLY_FORMALIZATION_REVIEW; APPROVE records a user approval."""
    if gate.gate_type is not QualificationGateType.EARLY_FORMALIZATION_REVIEW:
        raise DomainError(
            f"gate type {gate.gate_type.value} cannot resolve a formalization review",
            error_code="GATE_TYPE_MISMATCH",
        )
    if gate.binding.artifact_hash != current_bundle_hash:
        raise DomainError(
            "current formula bundle hash does not match the review binding",
            error_code="STALE_FORMALIZATION_BINDING",
        )
    resolved = gate.resolve(
        decision=decision,
        actor=actor,
        user_event_id=user_event_id,
        at=at,
    )
    if decision != "APPROVE":
        return resolved, None
    approval = UserFormalizationApproval(
        formalization_id=gate.binding.artifact_id,
        version=gate.binding.version or 0,
        formalization_hash=gate.binding.artifact_hash,
        input_spec_hash=gate.binding.input_spec_hash,
        route=ResearchRoute.THEORY,
        actor=actor,
        user_event_id=user_event_id,
        decided_at=at,
    )
    return resolved, approval


def validate_engineering_concept_bundle(
    bundle: EngineeringConceptBundle,
) -> tuple[EngineeringConceptStatus, tuple[str, ...]]:
    """Validate an RQ2E concept candidate and map issues deterministically."""
    issues: list[str] = []
    forbidden_terms = ("IMPLEMENTED", "VALIDATED", "PRODUCTION_READY", "NOVEL")
    inspected_text = " ".join(
        (
            *bundle.plain_language_explanation,
            *bundle.requirement_predicates,
            *bundle.quality_metric_formulas,
        )
    )
    for term in forbidden_terms:
        if term in inspected_text:
            issues.append(f"概念 bundle 包含越权状态 {term}")

    if not bundle.input_output_contracts:
        issues.append("缺少 input_output_contracts")
    if not bundle.state_transition_formulas:
        issues.append("缺少 state_transition_formulas")
    if not bundle.requirement_predicates:
        issues.append("缺少 requirement_predicates")
    if not bundle.quality_metric_formulas:
        issues.append("缺少 quality_metric_formulas")
    if bundle.architecture_graph_candidate.get("type") != "component_graph":
        issues.append("architecture_graph_candidate 缺少 component_graph type")
    if not bundle.verification_obligations:
        issues.append("缺少 verification_obligations")
    for requirement in bundle.requirement_predicates:
        requirement_id = requirement.split(":", 1)[0].strip()
        trace = bundle.traceability_relation.get(requirement_id)
        if not isinstance(trace, tuple) or len(trace) < 2:
            issues.append(f"requirement {requirement_id} 缺少 design/verification trace")

    if issues:
        if any("越权状态" in issue for issue in issues):
            return EngineeringConceptStatus.SCHEMA_INVALID, tuple(issues)
        return EngineeringConceptStatus.REQUIREMENT_COVERAGE_INCOMPLETE, tuple(issues)

    expected_hash = sha256_hex(engineering_concept_content_payload(bundle))
    if bundle.artifact_hash != expected_hash:
        return EngineeringConceptStatus.SCHEMA_INVALID, ("artifact_hash 与 bundle 内容不一致",)
    return EngineeringConceptStatus.ENGINEERING_CONCEPT_CANDIDATE, ()


def open_early_engineering_concept_review(
    *,
    bundle: EngineeringConceptBundle,
    gate_id: str,
) -> Gate:
    """Open EARLY_ENGINEERING_CONCEPT_REVIEW bound to concept/route/spec hash."""
    return Gate(
        gate_id=gate_id,
        project_id=bundle.research_spec_id,
        gate_type=QualificationGateType.EARLY_ENGINEERING_CONCEPT_REVIEW,
        binding=GateBinding(
            gate_type=QualificationGateType.EARLY_ENGINEERING_CONCEPT_REVIEW,
            artifact_id=bundle.concept_id,
            version=bundle.version,
            artifact_hash=bundle.artifact_hash,
            input_spec_hash=bundle.input_spec_hash,
            route=ResearchRoute.ENGINEERING,
            route_selection_id=bundle.route_selection_id,
        ),
    )


def resolve_early_engineering_concept_review(
    *,
    gate: Gate,
    decision: str,
    actor: ProvenanceType,
    user_event_id: str,
    current_concept_hash: str,
    at: datetime,
) -> tuple[Gate, UserEngineeringConceptApproval | None]:
    """Resolve EARLY_ENGINEERING_CONCEPT_REVIEW; APPROVE records approval."""
    if gate.gate_type is not QualificationGateType.EARLY_ENGINEERING_CONCEPT_REVIEW:
        raise DomainError(
            f"gate type {gate.gate_type.value} cannot resolve an engineering concept review",
            error_code="GATE_TYPE_MISMATCH",
        )
    if gate.binding.artifact_hash != current_concept_hash:
        raise DomainError(
            "current concept hash does not match the review binding",
            error_code="STALE_CONCEPT_BINDING",
        )
    resolved = gate.resolve(
        decision=decision,
        actor=actor,
        user_event_id=user_event_id,
        at=at,
    )
    if decision != "APPROVE":
        return resolved, None
    approval = UserEngineeringConceptApproval(
        concept_id=gate.binding.artifact_id,
        version=gate.binding.version or 0,
        concept_hash=gate.binding.artifact_hash,
        route_selection_id=gate.binding.route_selection_id or "",
        input_spec_hash=gate.binding.input_spec_hash,
        route=ResearchRoute.ENGINEERING,
        actor=actor,
        user_event_id=user_event_id,
        decided_at=at,
    )
    return resolved, approval


# ---------------------------------------------------------------------------
# M13.3 — route-aware RQ0-RQ4 qualification pipeline (19 §5 M13.3)
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class QualificationRun:
    """One deterministic RQ0→RQ4 run with every stage artifact kept."""

    run_id: str
    project_id: str
    research_spec_id: str
    input_spec_hash: str
    capability_decision: FormalizationCapabilityDecision
    evidence: NeighborEvidenceSet
    feasibility_assessment: FormalizationFeasibilityAssessment
    route: ResearchRoute | None
    route_selection: EngineeringRouteSelection | None
    formula_bundle: EarlyFormalizationBundle | None
    concept_bundle: EngineeringConceptBundle | None
    user_formalization_approval: UserFormalizationApproval | None
    user_engineering_concept_approval: UserEngineeringConceptApproval | None
    novelty_review: NoveltyReview | None
    next_target: QualifiedNextTarget | None
    user_gate: Gate | None
    created_at: datetime


def _input_spec_hash(
    spec: NaturalLanguageSpec,
    mechanism: MechanismSketch,
    scope: ResearchScopeSpec,
) -> str:
    return sha256_hex(
        {
            "spec": spec.model_dump(mode="json"),
            "mechanism": mechanism.model_dump(mode="json"),
            "scope": scope.model_dump(mode="json"),
        }
    )


def run_qualification_pipeline(
    *,
    run_id: str | None = None,
    project_id: str,
    research_spec_id: str,
    spec: NaturalLanguageSpec,
    mechanism: MechanismSketch,
    scope: ResearchScopeSpec,
    capability_profile: FormalizationCapabilityProfile,
    academic_providers: Sequence[PriorArtProvider],
    engineering_providers: Sequence[PriorArtProvider],
    queries: tuple[PriorArtQueryRequest, ...],
    formalizer_session_id: str,
    assessor_session_id: str,
    primary_reviewer_factory: Callable[[ResearchRoute], NoveltyReviewer],
    auditor_reviewer_factory: Callable[[ResearchRoute], NoveltyAuditor],
    route_decision: str | None = None,
    review_decision: str | None = "APPROVE",
    actor: ProvenanceType = ProvenanceType.USER_DECISION,
    user_event_id: str = "user-event:qualification-pipeline",
    search_id: str | None = None,
    unsearched_areas: tuple[str, ...] = (),
    at: datetime | None = None,
) -> QualificationRun:
    """Execute route-aware RQ0→RQ4 for a real natural-language design.

    - RQ0: capability gate must be CAPABILITY_READY, else RQ0_CAPABILITY_BLOCKED.
    - RQ1: coverage must be COMPLETE, else RQ1_COVERAGE_INCOMPLETE (never auto-pass).
    - RQ2F: fixed classification; ENGINEERING_PROJECT_CANDIDATE requires the
      user's TRY_ENGINEERING_PROJECT route decision.
    - RQ2M/RQ2E -> RQ3 review -> RQ4: 70 auto-continues to S5/ENG0; below 70 or
      an unresolved gate returns the run to the user with `user_gate` set.
    """
    resolved_run_id = run_id or "qualification-" + uuid4().hex
    now = at or datetime.now(UTC)
    input_spec_hash = _input_spec_hash(spec, mechanism, scope)

    capability_status, capability_blockers = evaluate_formalizer_capability(
        capability_profile,
        evaluated_at=now,
    )
    if capability_status is not CapabilityStatus.CAPABILITY_READY:
        raise DomainError(
            "RQ0 capability gate failed: " + "; ".join(capability_blockers),
            error_code="RQ0_CAPABILITY_BLOCKED",
        )
    capability_decision = FormalizationCapabilityDecision(
        decision_id=f"{resolved_run_id}:rq0",
        project_id=project_id,
        research_spec_id=research_spec_id,
        route=FormalizationExecutionRoute.PLATFORM_ADVANCED_FORMALIZER,
        model_profile_id=capability_profile.model_profile_id,
        capability_evidence_refs=(f"model_profile:{capability_profile.model_profile_id}",),
        input_spec_hash=input_spec_hash,
        budget_snapshot_id=None,
        privacy_policy_snapshot_id=None,
        status=CapabilityStatus.CAPABILITY_READY,
        blocker=None,
    )

    evidence = run_prior_art_search(
        academic_providers=academic_providers,
        engineering_providers=engineering_providers,
        queries=queries,
        research_spec_id=research_spec_id,
        input_spec_hash=input_spec_hash,
        search_id=search_id,
        unsearched_areas=unsearched_areas,
        now=now,
    )
    if evidence.coverage_status is not PriorArtCoverageStatus.COMPLETE:
        raise DomainError(
            "RQ1 coverage incomplete, no auto qualification: "
            + "; ".join(evidence.coverage_blockers),
            error_code="RQ1_COVERAGE_INCOMPLETE",
        )

    formalizer = EarlyFormalizer.create(
        session_id=formalizer_session_id,
        spec=spec,
        mechanism=mechanism,
        scope=scope,
        evidence=evidence,
    )
    engineering_assessor = EngineeringFeasibilityAssessor.create(
        session_id=assessor_session_id,
        spec=spec,
        mechanism=mechanism,
        scope=scope,
        evidence=evidence,
    )
    assessment = assess_formalization_feasibility(
        assessment_id=f"{resolved_run_id}:rq2f",
        version=1,
        research_spec_id=research_spec_id,
        input_spec_hash=input_spec_hash,
        neighbor_evidence_set_id=evidence.search_id,
        early_formalizer=formalizer,
        engineering_assessor=engineering_assessor,
        spec=spec,
        mechanism=mechanism,
        scope=scope,
        evidence=evidence,
        public_explanation=("RQ2F 双评估保守聚合，见 feasibility_matrix",),
    )

    classification = assessment.route_classification.value
    route: ResearchRoute | None = None
    route_selection: EngineeringRouteSelection | None = None
    if classification == "ENGINEERING_PROJECT_CANDIDATE":
        gate = open_formalization_feasibility_gate(
            assessment=assessment,
            gate_id=f"{resolved_run_id}:gate-route",
        )
        if gate is None:
            raise DomainError(
                "RQ2F engineering candidate produced no route gate",
                error_code="GATE_BINDING_INVALID",
            )
        if route_decision is None:
            return QualificationRun(
                run_id=resolved_run_id,
                project_id=project_id,
                research_spec_id=research_spec_id,
                input_spec_hash=input_spec_hash,
                capability_decision=capability_decision,
                evidence=evidence,
                feasibility_assessment=assessment,
                route=None,
                route_selection=None,
                formula_bundle=None,
                concept_bundle=None,
                user_formalization_approval=None,
                user_engineering_concept_approval=None,
                novelty_review=None,
                next_target=None,
                user_gate=gate,
                created_at=now,
            )
        resolved, selection = resolve_engineering_route_decision(
            gate=gate,
            decision=route_decision,
            actor=actor,
            user_event_id=user_event_id,
            current_input_spec_hash=input_spec_hash,
            at=now,
            selection_id=f"{resolved_run_id}:route-selection",
        )
        if selection is None:
            return QualificationRun(
                run_id=resolved_run_id,
                project_id=project_id,
                research_spec_id=research_spec_id,
                input_spec_hash=input_spec_hash,
                capability_decision=capability_decision,
                evidence=evidence,
                feasibility_assessment=assessment,
                route=None,
                route_selection=None,
                formula_bundle=None,
                concept_bundle=None,
                user_formalization_approval=None,
                user_engineering_concept_approval=None,
                novelty_review=None,
                next_target=None,
                user_gate=resolved,
                created_at=now,
            )
        route = ResearchRoute.ENGINEERING
        route_selection = selection
    elif classification in {"PURE_THEORY_FIT", "HYBRID_FIT"}:
        route = ResearchRoute.THEORY
    else:
        gate = open_formalization_feasibility_gate(
            assessment=assessment,
            gate_id=f"{resolved_run_id}:gate-feasibility",
        )
        if gate is None:
            raise DomainError(
                "RQ2F inconclusive produced no feasibility gate",
                error_code="GATE_BINDING_INVALID",
            )
        return QualificationRun(
            run_id=resolved_run_id,
            project_id=project_id,
            research_spec_id=research_spec_id,
            input_spec_hash=input_spec_hash,
            capability_decision=capability_decision,
            evidence=evidence,
            feasibility_assessment=assessment,
            route=None,
            route_selection=None,
            formula_bundle=None,
            concept_bundle=None,
            user_formalization_approval=None,
            user_engineering_concept_approval=None,
            novelty_review=None,
            next_target=None,
            user_gate=gate,
            created_at=now,
        )

    formula_bundle: EarlyFormalizationBundle | None = None
    concept_bundle: EngineeringConceptBundle | None = None
    formalization_approval: UserFormalizationApproval | None = None
    concept_approval: UserEngineeringConceptApproval | None = None
    subject_artifact_type: str
    subject_artifact_id: str
    subject_artifact_hash: str

    if route is ResearchRoute.THEORY:
        formula_bundle = build_early_formula_bundle(
            capability_profile=capability_profile,
            feasibility_assessment=assessment,
            spec=spec,
            mechanism=mechanism,
            scope=scope,
            evidence=evidence,
            formalizer_session_id=formalizer_session_id,
            formalization_id=f"{resolved_run_id}:rq2m",
        )
        gate = open_early_formalization_review(
            bundle=formula_bundle,
            gate_id=f"{resolved_run_id}:gate-rq3m",
        )
        if review_decision is None:
            return QualificationRun(
                run_id=resolved_run_id,
                project_id=project_id,
                research_spec_id=research_spec_id,
                input_spec_hash=input_spec_hash,
                capability_decision=capability_decision,
                evidence=evidence,
                feasibility_assessment=assessment,
                route=route,
                route_selection=None,
                formula_bundle=formula_bundle,
                concept_bundle=None,
                user_formalization_approval=None,
                user_engineering_concept_approval=None,
                novelty_review=None,
                next_target=None,
                user_gate=gate,
                created_at=now,
            )
        resolved, formalization_approval = resolve_early_formalization_review(
            gate=gate,
            decision=review_decision,
            actor=actor,
            user_event_id=user_event_id,
            current_bundle_hash=formula_bundle.artifact_hash,
            at=now,
        )
        if formalization_approval is None:
            return QualificationRun(
                run_id=resolved_run_id,
                project_id=project_id,
                research_spec_id=research_spec_id,
                input_spec_hash=input_spec_hash,
                capability_decision=capability_decision,
                evidence=evidence,
                feasibility_assessment=assessment,
                route=route,
                route_selection=None,
                formula_bundle=formula_bundle,
                concept_bundle=None,
                user_formalization_approval=None,
                user_engineering_concept_approval=None,
                novelty_review=None,
                next_target=None,
                user_gate=resolved,
                created_at=now,
            )
        subject_artifact_type = "EarlyFormalizationBundle"
        subject_artifact_id = formula_bundle.formalization_id
        subject_artifact_hash = formula_bundle.artifact_hash
    else:
        assert route_selection is not None
        concept_bundle = build_engineering_concept_bundle(
            route_selection=route_selection,
            feasibility_assessment=assessment,
            spec=spec,
            mechanism=mechanism,
            scope=scope,
            evidence=evidence,
            assessor_session_id=assessor_session_id,
            concept_id=f"{resolved_run_id}:rq2e",
        )
        concept_status, concept_issues = validate_engineering_concept_bundle(concept_bundle)
        if concept_status is not EngineeringConceptStatus.ENGINEERING_CONCEPT_CANDIDATE:
            raise DomainError(
                "RQ2E concept bundle invalid: " + "; ".join(concept_issues),
                error_code="REQUIREMENT_COVERAGE_INCOMPLETE",
            )
        gate = open_early_engineering_concept_review(
            bundle=concept_bundle,
            gate_id=f"{resolved_run_id}:gate-rq3e",
        )
        if review_decision is None:
            return QualificationRun(
                run_id=resolved_run_id,
                project_id=project_id,
                research_spec_id=research_spec_id,
                input_spec_hash=input_spec_hash,
                capability_decision=capability_decision,
                evidence=evidence,
                feasibility_assessment=assessment,
                route=route,
                route_selection=route_selection,
                formula_bundle=None,
                concept_bundle=concept_bundle,
                user_formalization_approval=None,
                user_engineering_concept_approval=None,
                novelty_review=None,
                next_target=None,
                user_gate=gate,
                created_at=now,
            )
        resolved, concept_approval = resolve_early_engineering_concept_review(
            gate=gate,
            decision=review_decision,
            actor=actor,
            user_event_id=user_event_id,
            current_concept_hash=concept_bundle.artifact_hash,
            at=now,
        )
        if concept_approval is None:
            return QualificationRun(
                run_id=resolved_run_id,
                project_id=project_id,
                research_spec_id=research_spec_id,
                input_spec_hash=input_spec_hash,
                capability_decision=capability_decision,
                evidence=evidence,
                feasibility_assessment=assessment,
                route=route,
                route_selection=route_selection,
                formula_bundle=None,
                concept_bundle=concept_bundle,
                user_formalization_approval=None,
                user_engineering_concept_approval=None,
                novelty_review=None,
                next_target=None,
                user_gate=resolved,
                created_at=now,
            )
        subject_artifact_type = "EngineeringConceptBundle"
        subject_artifact_id = concept_bundle.concept_id
        subject_artifact_hash = concept_bundle.artifact_hash

    review = start_novelty_review(
        review_id=f"{resolved_run_id}:rq4",
        project_id=project_id,
        route=route,
        policy_version=novelty_policy_for(route).policy_version,
        subject_artifact_type=subject_artifact_type,
        subject_artifact_id=subject_artifact_id,
        subject_artifact_hash=subject_artifact_hash,
        neighbor_evidence_set_id=evidence.search_id,
        primary_reviewer=primary_reviewer_factory(route),
        auditor_reviewer=auditor_reviewer_factory(route),
        coverage_status=evidence.coverage_status,
        nearest_overlap_refs=tuple(
            neighbor.stable_identifier for neighbor in evidence.academic_neighbors[:2]
        )
        + tuple(neighbor.stable_identifier for neighbor in evidence.engineering_neighbors[:2]),
        strongest_difference_refs=(scope.nearest_neighbor_difference,),
        limitations=evidence.unsearched_areas,
        at=now,
    )
    status, next_target, gate_type = novelty_next_target(review)
    if next_target is None:
        assert gate_type is not None
        user_gate = open_low_novelty_research_gate(
            review=review,
            gate_id=f"{resolved_run_id}:gate-rq4",
        )
        assert user_gate.gate_type is gate_type
        return QualificationRun(
            run_id=resolved_run_id,
            project_id=project_id,
            research_spec_id=research_spec_id,
            input_spec_hash=input_spec_hash,
            capability_decision=capability_decision,
            evidence=evidence,
            feasibility_assessment=assessment,
            route=route,
            route_selection=route_selection,
            formula_bundle=formula_bundle,
            concept_bundle=concept_bundle,
            user_formalization_approval=formalization_approval,
            user_engineering_concept_approval=concept_approval,
            novelty_review=review,
            next_target=None,
            user_gate=user_gate,
            created_at=now,
        )
    del status
    return QualificationRun(
        run_id=resolved_run_id,
        project_id=project_id,
        research_spec_id=research_spec_id,
        input_spec_hash=input_spec_hash,
        capability_decision=capability_decision,
        evidence=evidence,
        feasibility_assessment=assessment,
        route=route,
        route_selection=route_selection,
        formula_bundle=formula_bundle,
        concept_bundle=concept_bundle,
        user_formalization_approval=formalization_approval,
        user_engineering_concept_approval=concept_approval,
        novelty_review=review,
        next_target=next_target,
        user_gate=None,
        created_at=now,
    )


def qualification_export_payload(run: QualificationRun) -> dict[str, Any]:
    """M13.3 export: sources, feasibility matrix, route, formalization, scores, gate."""
    assessment = run.feasibility_assessment
    feasibility = {
        "assessment_id": assessment.assessment_id,
        "route_classification": assessment.route_classification.value,
        "theory": [predicate.to_event_payload() for predicate in assessment.theory_predicates],
        "engineering": [
            predicate.to_event_payload() for predicate in assessment.engineering_predicates
        ],
    }
    evidence = run.evidence
    sources = {
        "search_id": evidence.search_id,
        "coverage_status": evidence.coverage_status.value,
        "coverage_blockers": list(evidence.coverage_blockers),
        "query_records": [record.to_event_payload() for record in evidence.query_records],
        "academic_neighbors": [
            neighbor.to_event_payload() for neighbor in evidence.academic_neighbors
        ],
        "engineering_neighbors": [
            neighbor.to_event_payload() for neighbor in evidence.engineering_neighbors
        ],
        "metadata_verification_receipts": list(evidence.metadata_verification_receipts),
        "unsearched_areas": list(evidence.unsearched_areas),
    }
    return {
        "run_id": run.run_id,
        "project_id": run.project_id,
        "research_spec_id": run.research_spec_id,
        "input_spec_hash": run.input_spec_hash,
        "route": run.route.value if run.route else None,
        "capability": run.capability_decision.to_event_payload(),
        "sources": sources,
        "feasibility_matrix": feasibility,
        "formalization": (run.formula_bundle.to_event_payload() if run.formula_bundle else None),
        "engineering_concept": (
            run.concept_bundle.to_event_payload() if run.concept_bundle else None
        ),
        "scores": run.novelty_review.to_event_payload() if run.novelty_review else None,
        "next_target": run.next_target.value if run.next_target else None,
        "gate": run.user_gate.to_event_payload() if run.user_gate else None,
        "exported_at": run.created_at.isoformat(),
    }


__all__ = [
    "MIN_ACADEMIC_NEIGHBORS",
    "QualificationRun",
    "assess_formalization_feasibility",
    "build_early_formula_bundle",
    "open_early_engineering_concept_review",
    "resolve_early_engineering_concept_review",
    "validate_engineering_concept_bundle",
    "early_formula_bundle_content_payload",
    "open_early_formalization_review",
    "resolve_early_formalization_review",
    "validate_early_formula_bundle",
    "assess_formalization_feasibility_from_matrices",
    "open_formalization_feasibility_gate",
    "resolve_engineering_route_decision",
    "resolve_formalization_feasibility_decision",
    "MIN_ACADEMIC_SOURCE_CLASSES",
    "MIN_ENGINEERING_NEIGHBORS",
    "MIN_ENGINEERING_SOURCE_CLASSES",
    "MIN_MATURITY_EVIDENCE_REFS",
    "neighbor_evidence_content_payload",
    "qualification_export_payload",
    "run_prior_art_search",
    "run_qualification_pipeline",
    "validate_prior_art_coverage",
]
