"""Early research qualification application service (blueprint 07, section 3).

M2.4 scope: orchestrate synchronous prior-art providers into an immutable
NeighborEvidenceSet, with deterministic deduplication, sorting, ranking and
coverage validation. No database, artifact store, event stream or network I/O
is performed here yet; those capabilities arrive in later storage tasks.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import replace
from datetime import UTC, datetime
from uuid import uuid4

from synaisthesis.agents.early_formalizer import (
    EarlyFormalizer,
    build_formula_items,
    validate_formula_items,
)
from synaisthesis.agents.engineering_feasibility_assessor import (
    EngineeringFeasibilityAssessor,
    engineering_concept_content_payload,
)
from synaisthesis.agents.schemas import MechanismSketch, NaturalLanguageSpec, ResearchScopeSpec
from synaisthesis.domain.enums import (
    EarlyFormalizationStatus,
    EngineeringConceptStatus,
    EngineeringRouteDecision,
    PriorArtCoverageStatus,
    ProvenanceType,
    QualificationGateType,
    ResearchRoute,
)
from synaisthesis.domain.errors import DomainError
from synaisthesis.domain.event import sha256_hex
from synaisthesis.domain.gate import Gate, GateBinding
from synaisthesis.domain.qualification import (
    EarlyFormalizationBundle,
    EngineeringConceptBundle,
    EngineeringRouteSelection,
    FeasibilityPredicateMatrix,
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


__all__ = [
    "MIN_ACADEMIC_NEIGHBORS",
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
    "run_prior_art_search",
    "validate_prior_art_coverage",
]
