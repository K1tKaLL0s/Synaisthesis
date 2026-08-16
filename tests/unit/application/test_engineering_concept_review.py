"""M2.5B unit tests for EARLY_ENGINEERING_CONCEPT_REVIEW gate."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from synaisthesis.agents.engineering_feasibility_assessor import (
    build_engineering_concept_bundle,
)
from synaisthesis.agents.schemas import MechanismSketch, NaturalLanguageSpec, ResearchScopeSpec
from synaisthesis.application.qualification_service import (
    assess_formalization_feasibility_from_matrices,
    open_early_engineering_concept_review,
    resolve_early_engineering_concept_review,
)
from synaisthesis.domain.enums import (
    EngineeringConceptReviewDecision,
    EngineeringRouteDecision,
    GateStatus,
    PredicateVerdict,
    PriorArtCoverageStatus,
    ProvenanceType,
    QualificationGateType,
    ResearchRoute,
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

NOW = datetime(2026, 8, 16, 23, 0, 0, tzinfo=UTC)


def _base_materials():
    spec = NaturalLanguageSpec(
        core_definition="trace cyclic",
        positive_examples=["tr(AB)=tr(BA)"],
        non_examples=["det"],
        boundary_conditions=["multiplicable"],
        object_candidates=["matrix"],
        ambiguous_terms=[],
        explicit_non_goals=["det"],
        expected_functions=["compute"],
        target_applications=["numerics"],
        intended_users=["researchers"],
        operational_constraints=["finite"],
        success_metrics=["accuracy"],
    )
    mechanism = MechanismSketch(
        inputs=["A", "B"],
        state_change="compute trace",
        outputs=["trace"],
        invariants=["tr(AB)=tr(BA)"],
        failure_conditions=["bad shapes"],
        causal_claims=[],
        merely_descriptive_relations=[],
        uncertainty_register=[],
    )
    scope = ResearchScopeSpec(
        main_question="trace boundary",
        object_domain="finite matrices",
        non_goals=["det"],
        nearest_neighbor_difference="transpose",
        central_claims=["tr(AB)=tr(BA)"],
        evidence_requirements=["proof"],
        failure_learning_plan="revisit",
        engineering_relevance="libraries",
        stop_conditions=["refuted"],
    )
    evidence = NeighborEvidenceSet(
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
    return spec, mechanism, scope, evidence


def _feasibility():
    spec, _, _, evidence = _base_materials()
    matrix = FeasibilityPredicateMatrix(
        theory=TheoryFitPredicates(
            *[
                FeasibilityPredicate(
                    predicate_id=name,
                    verdict=PredicateVerdict.FAIL,
                    evidence_refs=("S1",),
                )
                for name in ("TFO", "TFR", "TFC", "TFW", "TFP")
            ]
        ),
        engineering=EngineeringFitPredicates(
            *[
                FeasibilityPredicate(
                    predicate_id=name,
                    verdict=PredicateVerdict.PASS,
                    evidence_refs=("S1", "RQ1"),
                )
                for name in ("EFS", "EFI", "EFA", "EFM", "EFF")
            ]
        ),
    )
    return (
        assess_formalization_feasibility_from_matrices(
            assessment_id="fa-1",
            version=1,
            research_spec_id="rs-1",
            input_spec_hash=evidence.input_spec_hash,
            neighbor_evidence_set_id=evidence.search_id,
            assessor_session_ids=("s-early", "s-eng"),
            early_matrix=matrix,
            engineering_matrix=matrix,
            public_explanation=("engineering candidate",),
        ),
        evidence,
    )


def _concept():
    spec, mechanism, scope, evidence = _base_materials()
    assessment, _ = _feasibility()
    selection = EngineeringRouteSelection(
        id="ers-1",
        project_id="rs-1",
        feasibility_assessment_id=assessment.assessment_id,
        decision=EngineeringRouteDecision.TRY_ENGINEERING_PROJECT,
        user_actor_id="USER_DECISION",
        decision_event_id="uev-1",
        bound_assessment_hash=assessment.artifact_hash,
        input_spec_hash=assessment.input_spec_hash,
        created_at=NOW,
    )
    return build_engineering_concept_bundle(
        route_selection=selection,
        feasibility_assessment=assessment,
        spec=spec,
        mechanism=mechanism,
        scope=scope,
        evidence=evidence,
        assessor_session_id="s-eng",
        concept_id="ec-1",
        version=1,
        at=NOW,
    )


def test_review_gate_binds_concept_route_and_spec_hash():
    bundle = _concept()
    gate = open_early_engineering_concept_review(bundle=bundle, gate_id="g-review")
    assert gate.gate_type is QualificationGateType.EARLY_ENGINEERING_CONCEPT_REVIEW
    assert gate.binding.artifact_hash == bundle.artifact_hash
    assert gate.binding.route_selection_id == bundle.route_selection_id
    assert gate.binding.input_spec_hash == bundle.input_spec_hash
    assert gate.binding.route is ResearchRoute.ENGINEERING


def test_model_actor_cannot_approve_engineering_concept():
    bundle = _concept()
    gate = open_early_engineering_concept_review(bundle=bundle, gate_id="g-review")
    with pytest.raises(DomainError) as exc_info:
        resolve_early_engineering_concept_review(
            gate=gate,
            decision=EngineeringConceptReviewDecision.APPROVE.value,
            actor=ProvenanceType.ASSISTANT_PROPOSAL,
            user_event_id="model-event",
            current_concept_hash=bundle.artifact_hash,
            at=NOW,
        )
    assert exc_info.value.error_code == "CONFIRMATION_REQUIRES_USER_EVENT"


def test_user_approve_records_engineering_concept_approval():
    bundle = _concept()
    gate = open_early_engineering_concept_review(bundle=bundle, gate_id="g-review")
    resolved, approval = resolve_early_engineering_concept_review(
        gate=gate,
        decision=EngineeringConceptReviewDecision.APPROVE.value,
        actor=ProvenanceType.USER_DECISION,
        user_event_id="uev-approve",
        current_concept_hash=bundle.artifact_hash,
        at=NOW,
    )
    assert resolved.status is GateStatus.RESOLVED
    assert approval is not None
    assert approval.concept_hash == bundle.artifact_hash
    assert approval.route is ResearchRoute.ENGINEERING
    assert approval.route_selection_id == bundle.route_selection_id


def test_stale_concept_hash_blocks_review():
    bundle = _concept()
    gate = open_early_engineering_concept_review(bundle=bundle, gate_id="g-review")
    with pytest.raises(DomainError) as exc_info:
        resolve_early_engineering_concept_review(
            gate=gate,
            decision=EngineeringConceptReviewDecision.APPROVE.value,
            actor=ProvenanceType.USER_DECISION,
            user_event_id="uev-stale",
            current_concept_hash="0" * 64,
            at=NOW,
        )
    assert exc_info.value.error_code == "STALE_CONCEPT_BINDING"
