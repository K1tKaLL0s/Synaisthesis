"""M2.5B golden tests for RQ2E engineering concept formalization."""

from __future__ import annotations

from dataclasses import replace
from datetime import UTC, datetime

import pytest

from synaisthesis.agents.engineering_feasibility_assessor import (
    build_engineering_concept_bundle,
)
from synaisthesis.agents.schemas import MechanismSketch, NaturalLanguageSpec, ResearchScopeSpec
from synaisthesis.application.qualification_service import (
    assess_formalization_feasibility_from_matrices,
    validate_engineering_concept_bundle,
)
from synaisthesis.domain.enums import (
    EngineeringConceptStatus,
    EngineeringRouteDecision,
    PredicateVerdict,
    PriorArtCoverageStatus,
)
from synaisthesis.domain.errors import DomainError
from synaisthesis.domain.qualification import (
    EngineeringFitPredicates,
    EngineeringRouteSelection,
    FeasibilityPredicate,
    FeasibilityPredicateMatrix,
    NeighborEvidenceSet,
    TheoryFitPredicates,
)

NOW = datetime(2026, 8, 16, 22, 0, 0, tzinfo=UTC)

S1 = NaturalLanguageSpec(
    core_definition="trace is cyclic for compatible matrices",
    positive_examples=["tr(AB)=tr(BA)"],
    non_examples=["det(AB)=det(A)det(B)"],
    boundary_conditions=["A,B multiplicable"],
    object_candidates=["matrix", "trace"],
    ambiguous_terms=[],
    explicit_non_goals=["determinants"],
    expected_functions=["compute trace invariant"],
    target_applications=["numerical linear algebra"],
    intended_users=["researchers"],
    operational_constraints=["finite matrices"],
    success_metrics=["latency", "accuracy"],
)
S2 = MechanismSketch(
    inputs=["A", "B"],
    state_change="compute tr(AB), tr(BA)",
    outputs=["trace values"],
    invariants=["tr(AB)=tr(BA)"],
    failure_conditions=["non-multiplicable inputs"],
    causal_claims=["cyclic permutation"],
    merely_descriptive_relations=[],
    uncertainty_register=[],
)
S4 = ResearchScopeSpec(
    main_question="boundary of trace cyclic invariance",
    object_domain="finite matrices",
    non_goals=["determinants"],
    nearest_neighbor_difference="transpose counterexamples",
    central_claims=["tr(AB)=tr(BA)"],
    evidence_requirements=["proof for multiplicable matrices"],
    failure_learning_plan="revisit S1/S3 on failure",
    engineering_relevance="trace computation libraries",
    stop_conditions=["all claims refuted"],
)
EVIDENCE = NeighborEvidenceSet(
    search_id="ps-1",
    research_spec_id="rs-1",
    input_spec_hash="a" * 64,
    query_records=(),
    academic_neighbors=(),
    engineering_neighbors=(),
    standards_and_reference_architectures=(),
    patent_neighbors=(),
    metadata_verification_receipts=(),
    inclusion_exclusion_log="",
    unsearched_areas=(),
    coverage_status=PriorArtCoverageStatus.COMPLETE,
    coverage_blockers=(),
    artifact_hash="b" * 64,
)


def _pred(predicate_id: str, verdict: PredicateVerdict) -> FeasibilityPredicate:
    return FeasibilityPredicate(predicate_id, verdict, evidence_refs=(f"S1.{predicate_id}",))


def _assessment():
    matrix = FeasibilityPredicateMatrix(
        theory=TheoryFitPredicates(
            tfo=_pred("TFO", PredicateVerdict.FAIL),
            tfr=_pred("TFR", PredicateVerdict.FAIL),
            tfc=_pred("TFC", PredicateVerdict.FAIL),
            tfw=_pred("TFW", PredicateVerdict.FAIL),
            tfp=_pred("TFP", PredicateVerdict.FAIL),
        ),
        engineering=EngineeringFitPredicates(
            efs=_pred("EFS", PredicateVerdict.PASS),
            efi=_pred("EFI", PredicateVerdict.PASS),
            efa=_pred("EFA", PredicateVerdict.PASS),
            efm=_pred("EFM", PredicateVerdict.PASS),
            eff=_pred("EFF", PredicateVerdict.PASS),
        ),
    )
    return assess_formalization_feasibility_from_matrices(
        assessment_id="fa-1",
        version=1,
        research_spec_id="rs-1",
        input_spec_hash="a" * 64,
        neighbor_evidence_set_id="ps-1",
        assessor_session_ids=("s-early", "s-eng"),
        early_matrix=matrix,
        engineering_matrix=matrix,
        public_explanation=("engineering project candidate",),
    )


def _selection(assessment=None, **overrides):
    assessment = assessment or _assessment()
    base = {
        "id": "ers-1",
        "project_id": "rs-1",
        "feasibility_assessment_id": assessment.assessment_id,
        "decision": EngineeringRouteDecision.TRY_ENGINEERING_PROJECT,
        "user_actor_id": "USER_DECISION",
        "decision_event_id": "uev-1",
        "bound_assessment_hash": assessment.artifact_hash,
        "input_spec_hash": assessment.input_spec_hash,
        "created_at": NOW,
    }
    base.update(overrides)
    return EngineeringRouteSelection(**base)


def _bundle(**overrides):
    base = {
        "route_selection": _selection(),
        "feasibility_assessment": _assessment(),
        "spec": S1,
        "mechanism": S2,
        "scope": S4,
        "evidence": EVIDENCE,
        "assessor_session_id": "s-eng",
        "concept_id": "ec-1",
        "version": 1,
        "at": NOW,
    }
    base.update(overrides)
    return build_engineering_concept_bundle(**base)


def test_non_try_route_selection_is_blocked():
    with pytest.raises(DomainError) as exc_info:
        _bundle(route_selection=_selection(decision=EngineeringRouteDecision.PAUSE))
    assert exc_info.value.error_code == "ENGINEERING_ROUTE_DECISION_REQUIRED"


def test_stale_route_selection_hash_is_blocked():
    assessment = _assessment()
    with pytest.raises(DomainError) as exc_info:
        _bundle(
            feasibility_assessment=assessment,
            route_selection=_selection(assessment, bound_assessment_hash="0" * 64),
        )
    assert exc_info.value.error_code == "STALE_ROUTE_SELECTION"


def test_golden_bundle_has_complete_engineering_material_and_is_candidate():
    bundle = _bundle()
    assert bundle.status is EngineeringConceptStatus.ENGINEERING_CONCEPT_CANDIDATE
    assert bundle.input_output_contracts
    assert bundle.state_transition_formulas
    assert bundle.requirement_predicates
    assert bundle.quality_metric_formulas
    assert bundle.unresolved_thresholds
    assert bundle.architecture_graph_candidate["type"]
    assert bundle.traceability_relation
    assert bundle.verification_obligations
    status, issues = validate_engineering_concept_bundle(bundle)
    assert status is EngineeringConceptStatus.ENGINEERING_CONCEPT_CANDIDATE
    assert issues == ()


def test_forbidden_implemented_or_novel_status_is_rejected():
    bundle = replace(_bundle(), status=EngineeringConceptStatus.SUPERSEDED)
    bundle = replace(
        bundle,
        plain_language_explanation=("concept is IMPLEMENTED and NOVEL",),
    )
    status, issues = validate_engineering_concept_bundle(bundle)
    assert status is EngineeringConceptStatus.SCHEMA_INVALID
    assert any("IMPLEMENTED" in issue or "NOVEL" in issue for issue in issues)


def test_requirement_without_design_or_verification_trace_is_rejected():
    bundle = replace(_bundle(), traceability_relation={})
    status, issues = validate_engineering_concept_bundle(bundle)
    assert status is EngineeringConceptStatus.REQUIREMENT_COVERAGE_INCOMPLETE
    assert any("trace" in issue or "追踪" in issue for issue in issues)
