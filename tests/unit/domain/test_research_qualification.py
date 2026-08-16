"""M2.3 domain tests: RQ0-RQ4 artifacts, feasibility, novelty, gates, migration."""

from __future__ import annotations

from dataclasses import FrozenInstanceError
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, inspect

from synaisthesis.domain.enums import (
    CapabilityStatus,
    EarlyFormalizationStatus,
    EngineeringConceptStatus,
    EngineeringRouteDecision,
    FeasibilityAssessmentStatus,
    FormalizationExecutionRoute,
    FormulaOrigin,
    GateStatus,
    NoveltyStatus,
    PredicateVerdict,
    PriorArtCoverageStatus,
    ProvenanceType,
    QualificationGateType,
    QualifiedNextTarget,
    ResearchRoute,
    RouteClassification,
)
from synaisthesis.domain.errors import DomainError
from synaisthesis.domain.event import sha256_hex
from synaisthesis.domain.gate import (
    Gate,
    GateBinding,
    allowed_decisions_for_gate,
    qualification_next_target,
)
from synaisthesis.domain.novelty import (
    ENGINEERING_NOVELTY_POLICY,
    THEORY_NOVELTY_POLICY,
    LowNoveltyOverride,
    NoveltyReview,
    NoveltyScorecard,
    calculate_conservative_novelty_score,
    route_novelty_decision,
)
from synaisthesis.domain.qualification import (
    CAPABILITY_TIER_ADVANCED,
    EVENT_NATURAL_LANGUAGE_DESIGN_READY,
    EVENT_NOVELTY_OVERRIDE_ACCEPTED,
    RQ_EVENT_TYPES,
    EarlyFormalizationBundle,
    EngineeringConceptBundle,
    EngineeringFitPredicates,
    FeasibilityPredicate,
    FormalizationCapabilityDecision,
    FormalizationCapabilityProfile,
    FormalizationFeasibilityAssessment,
    FormulaItem,
    NeighborEvidenceSet,
    PriorArtNeighbor,
    PriorArtQueryRecord,
    TheoryFitPredicates,
    UserEngineeringConceptApproval,
    UserFormalizationApproval,
    build_qualification_event,
    classify_formalization_feasibility,
    engineering_fit,
    evaluate_formalizer_capability,
    feasibility_status_for,
    predicate_merge,
    recommended_route_for,
    theory_fit,
)

REPO_ROOT = Path(__file__).resolve().parents[3]
MIGRATIONS_DIR = REPO_ROOT / "src" / "synaisthesis" / "storage" / "migrations"

NOW = datetime(2026, 8, 16, 12, 0, 0, tzinfo=UTC)


def _capability_profile(**overrides):
    base = {
        "model_profile_id": "mp-1",
        "capability_tier": CAPABILITY_TIER_ADVANCED,
        "formalization_eval_score": 90.0,
        "math_schema_valid_rate": 0.98,
        "source_citation_support": True,
        "structured_output_support": True,
        "context_budget_sufficient": True,
        "capability_evaluated_at": NOW,
        "budget_allowed": True,
        "privacy_allowed": True,
    }
    base.update(overrides)
    return FormalizationCapabilityProfile(**base)


def _pred(predicate_id: str, verdict: PredicateVerdict) -> FeasibilityPredicate:
    return FeasibilityPredicate(
        predicate_id=predicate_id,
        verdict=verdict,
        evidence_refs=("S1.core_definition", "RQ1.academic_neighbors[0]"),
    )


def _theory_predicates(verdict: PredicateVerdict = PredicateVerdict.PASS):
    return TheoryFitPredicates(
        tfo=_pred("TFO", verdict),
        tfr=_pred("TFR", verdict),
        tfc=_pred("TFC", verdict),
        tfw=_pred("TFW", verdict),
        tfp=_pred("TFP", verdict),
    )


def _engineering_predicates(verdict: PredicateVerdict = PredicateVerdict.PASS):
    return EngineeringFitPredicates(
        efs=_pred("EFS", verdict),
        efi=_pred("EFI", verdict),
        efa=_pred("EFA", verdict),
        efm=_pred("EFM", verdict),
        eff=_pred("EFF", verdict),
    )


def _scorecard(route: ResearchRoute, *, session_id: str, **scores) -> NoveltyScorecard:
    return NoveltyScorecard(
        reviewer_session_id=session_id,
        route=route,
        item_scores=scores,
    )


def _score_map(route: ResearchRoute, value: int) -> dict[str, int]:
    policy = THEORY_NOVELTY_POLICY if route is ResearchRoute.THEORY else ENGINEERING_NOVELTY_POLICY
    return {item.item_id: value for item in policy.items}


def _theory_70_scores() -> dict[str, int]:
    return {
        "T1": 4,
        "T2": 4,
        "T3": 4,
        "T4": 4,
        "A1": 3,
        "A2": 3,
        "A3": 3,
        "A4": 3,
        "A5": 3,
    }


def _engineering_70_scores() -> dict[str, int]:
    return {
        "E1": 5,
        "E2": 5,
        "E3": 4,
        "E4": 4,
        "E5": 4,
        "EA1": 4,
        "EA2": 4,
        "EA3": 0,
        "EA4": 0,
    }


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------


def test_new_enums_reject_unknown_values():
    for enum_cls, value in (
        (FormalizationExecutionRoute, "PLATFORM_ADVANCED_FORMALIZER"),
        (ResearchRoute, "THEORY"),
        (CapabilityStatus, "CAPABILITY_READY"),
        (PriorArtCoverageStatus, "COMPLETE"),
        (PredicateVerdict, "PASS"),
        (RouteClassification, "HYBRID_FIT"),
        (FeasibilityAssessmentStatus, "THEORY_OR_HYBRID_FIT"),
        (QualificationGateType, "ENGINEERING_ROUTE_DECISION"),
        (QualifiedNextTarget, "S5"),
    ):
        assert enum_cls.parse(value, field="test") == enum_cls(value)
        with pytest.raises(DomainError):
            enum_cls.parse("NOT_A_REAL_VALUE", field="test")


# ---------------------------------------------------------------------------
# RQ0 capability
# ---------------------------------------------------------------------------


def test_rq0_capability_gate_thresholds_and_expiry():
    status, blockers = evaluate_formalizer_capability(_capability_profile(), evaluated_at=NOW)
    assert status is CapabilityStatus.CAPABILITY_READY
    assert blockers == ()

    below_score = _capability_profile(formalization_eval_score=79.999)
    status, blockers = evaluate_formalizer_capability(below_score, evaluated_at=NOW)
    assert status is CapabilityStatus.CAPABILITY_UNAVAILABLE
    assert any("formalization_eval_score" in blocker for blocker in blockers)

    no_citations = _capability_profile(source_citation_support=False)
    assert (
        evaluate_formalizer_capability(no_citations, evaluated_at=NOW)[0]
        is CapabilityStatus.CAPABILITY_UNAVAILABLE
    )
    no_structured = _capability_profile(structured_output_support=False)
    assert (
        evaluate_formalizer_capability(no_structured, evaluated_at=NOW)[0]
        is CapabilityStatus.CAPABILITY_UNAVAILABLE
    )

    expired = _capability_profile(capability_evaluated_at=NOW - timedelta(days=91))
    assert (
        evaluate_formalizer_capability(expired, evaluated_at=NOW)[0]
        is CapabilityStatus.CAPABILITY_UNAVAILABLE
    )
    assert (
        evaluate_formalizer_capability(_capability_profile(budget_allowed=False), evaluated_at=NOW)[
            0
        ]
        is CapabilityStatus.BLOCKED_BUDGET
    )
    assert (
        evaluate_formalizer_capability(
            _capability_profile(privacy_allowed=False), evaluated_at=NOW
        )[0]
        is CapabilityStatus.BLOCKED_PRIVACY
    )


def test_rq0_capability_decision_is_immutable():
    decision = FormalizationCapabilityDecision(
        decision_id="cd-1",
        project_id="p-1",
        research_spec_id="rs-1",
        route=FormalizationExecutionRoute.PLATFORM_ADVANCED_FORMALIZER,
        model_profile_id="mp-1",
        capability_evidence_refs=("artifact:cap-eval",),
        input_spec_hash="a" * 64,
        budget_snapshot_id=None,
        privacy_policy_snapshot_id=None,
        status=CapabilityStatus.CAPABILITY_READY,
        blocker=None,
    )
    with pytest.raises(FrozenInstanceError):
        decision.status = CapabilityStatus.BLOCKED_BUDGET  # type: ignore[misc]
    payload = decision.to_event_payload()
    assert payload["decision_id"] == "cd-1"
    assert payload["route"] == "PLATFORM_ADVANCED_FORMALIZER"


# ---------------------------------------------------------------------------
# RQ1 artifact
# ---------------------------------------------------------------------------


def test_rq1_neighbor_evidence_set_fields_and_immutability():
    evidence = NeighborEvidenceSet(
        search_id="ps-1",
        research_spec_id="rs-1",
        input_spec_hash="b" * 64,
        query_records=(
            PriorArtQueryRecord(
                query_id="q-1",
                original_text="trace cyclic property",
                generated_from=("S1.core_definition", "S2.causal_claims"),
                provider="OpenAlex",
                time_range="2015-2026",
                filters=("type:article",),
                page_count=1,
                result_count=25,
                executed_at=NOW,
            ),
        ),
        academic_neighbors=(
            PriorArtNeighbor(
                neighbor_id="n-1",
                neighbor_type="ACADEMIC",
                stable_identifier="openalex:W123",
                canonical_url="https://example.org/w123",
                metadata_verified=True,
                maturity_evidence_refs=(),
                theory_proximity=3.2,
                application_proximity=1.1,
                similarity_evidence_refs=("artifact:n-1",),
                rank=1,
            ),
        ),
        engineering_neighbors=(),
        standards_and_reference_architectures=("ISO-1",),
        patent_neighbors=(),
        metadata_verification_receipts=("openalex:receipt-1",),
        inclusion_exclusion_log="included one academic neighbor",
        unsearched_areas=("patents",),
        coverage_status=PriorArtCoverageStatus.PARTIAL,
        coverage_blockers=("engineering source count < 2",),
        artifact_hash="c" * 64,
    )
    assert evidence.coverage_status is PriorArtCoverageStatus.PARTIAL
    assert evidence.academic_neighbors[0].theory_proximity == 3.2
    with pytest.raises(FrozenInstanceError):
        evidence.coverage_status = PriorArtCoverageStatus.COMPLETE  # type: ignore[misc]


# ---------------------------------------------------------------------------
# RQ2F feasibility
# ---------------------------------------------------------------------------


def test_predicate_merge_uses_fail_over_unknown_over_pass():
    assert predicate_merge(PredicateVerdict.PASS, PredicateVerdict.PASS) is PredicateVerdict.PASS
    assert (
        predicate_merge(PredicateVerdict.UNKNOWN, PredicateVerdict.PASS) is PredicateVerdict.UNKNOWN
    )
    assert predicate_merge(PredicateVerdict.FAIL, PredicateVerdict.UNKNOWN) is PredicateVerdict.FAIL
    assert predicate_merge(PredicateVerdict.UNKNOWN, PredicateVerdict.FAIL) is PredicateVerdict.FAIL


def test_fit_functions_treat_unknown_as_not_true():
    assert theory_fit(_theory_predicates(PredicateVerdict.PASS)) is True
    assert engineering_fit(_engineering_predicates(PredicateVerdict.PASS)) is True

    theory_with_unknown = TheoryFitPredicates(
        tfo=_pred("TFO", PredicateVerdict.PASS),
        tfr=_pred("TFR", PredicateVerdict.PASS),
        tfc=_pred("TFC", PredicateVerdict.UNKNOWN),
        tfw=_pred("TFW", PredicateVerdict.PASS),
        tfp=_pred("TFP", PredicateVerdict.PASS),
    )
    assert theory_fit(theory_with_unknown) is None
    engineering_with_fail = EngineeringFitPredicates(
        efs=_pred("EFS", PredicateVerdict.PASS),
        efi=_pred("EFI", PredicateVerdict.PASS),
        efa=_pred("EFA", PredicateVerdict.PASS),
        efm=_pred("EFM", PredicateVerdict.FAIL),
        eff=_pred("EFF", PredicateVerdict.PASS),
    )
    assert engineering_fit(engineering_with_fail) is False


def test_feasibility_classification_truth_table_and_derived_fields():
    assert classify_formalization_feasibility(True, True) is RouteClassification.HYBRID_FIT
    assert classify_formalization_feasibility(True, False) is RouteClassification.PURE_THEORY_FIT
    assert (
        classify_formalization_feasibility(False, True)
        is RouteClassification.ENGINEERING_PROJECT_CANDIDATE
    )
    assert (
        classify_formalization_feasibility(False, False)
        is RouteClassification.NEITHER_CURRENTLY_FIT
    )
    assert classify_formalization_feasibility(None, True) is RouteClassification.INCONCLUSIVE
    assert classify_formalization_feasibility(True, None) is RouteClassification.INCONCLUSIVE

    assert (
        feasibility_status_for(RouteClassification.ENGINEERING_PROJECT_CANDIDATE)
        is FeasibilityAssessmentStatus.ENGINEERING_ROUTE_DECISION_REQUIRED
    )
    assert recommended_route_for(RouteClassification.PURE_THEORY_FIT) is ResearchRoute.THEORY
    assert recommended_route_for(RouteClassification.INCONCLUSIVE) is None


def test_feasibility_assessment_is_immutable_and_derived_fields_are_validated():
    assessment = FormalizationFeasibilityAssessment.create(
        assessment_id="fa-1",
        version=1,
        research_spec_id="rs-1",
        input_spec_hash="d" * 64,
        neighbor_evidence_set_id="ps-1",
        assessor_session_ids=("session-theory", "session-engineering"),
        theory_predicates=tuple(_theory_predicates().as_tuple()),
        engineering_predicates=tuple(_engineering_predicates(PredicateVerdict.PASS).as_tuple()),
        disagreements=(),
        missing_information=(),
        route_classification=RouteClassification.PURE_THEORY_FIT,
        public_explanation=("适合纯理论构造", "工程材料不足"),
    )
    assert assessment.status is FeasibilityAssessmentStatus.THEORY_OR_HYBRID_FIT
    assert assessment.recommended_route is ResearchRoute.THEORY
    assert sha256_hex(assessment.content_payload()) == assessment.artifact_hash
    with pytest.raises(FrozenInstanceError):
        assessment.status = FeasibilityAssessmentStatus.FEASIBILITY_INCONCLUSIVE  # type: ignore[misc]

    with pytest.raises(DomainError):
        FormalizationFeasibilityAssessment.create(
            assessment_id="fa-bad",
            version=1,
            research_spec_id="rs-1",
            input_spec_hash="d" * 64,
            neighbor_evidence_set_id="ps-1",
            assessor_session_ids=(),
            theory_predicates=tuple(_theory_predicates().as_tuple()),
            engineering_predicates=tuple(_engineering_predicates().as_tuple()),
            disagreements=(),
            missing_information=(),
            route_classification=RouteClassification.HYBRID_FIT,
            public_explanation=tuple(f"explanation-{index}" for index in range(13)),
        )


# ---------------------------------------------------------------------------
# RQ2M / RQ2E / RQ3 records
# ---------------------------------------------------------------------------


def test_rq2m_rq2e_rq3_records_are_immutable_and_model_actor_cannot_approve():
    formula = FormulaItem(
        formula_id="f-1",
        formula_type="CORE_CLAIM",
        latex=r"\forall A,B,\ \mathrm{tr}(AB)=\mathrm{tr}(BA)",
        normalized_math_ast=None,
        symbols_used=("A", "B"),
        source_spec_fields=("S1.core_definition",),
        assumption_formula_ids=("f-2",),
        neighbor_refs=("n-1",),
        origin=FormulaOrigin.DERIVED,
        confidence=0.8,
        known_ambiguities=(),
        falsification_or_failure_formula_id="f-3",
    )
    bundle = EarlyFormalizationBundle(
        formalization_id="ef-1",
        version=1,
        research_spec_id="rs-1",
        input_spec_hash="e" * 64,
        feasibility_assessment_id="fa-1",
        neighbor_evidence_set_id="ps-1",
        formalizer_profile_or_import_id="mp-1",
        notation_table=("A: square matrix", "B: square matrix"),
        formula_items=(formula,),
        formula_dependency_graph={"f-1": ("f-2",)},
        semantic_alignment_matrix=("S1.core_definition->f-1",),
        neighbor_difference_matrix=("n-1 differs in transpose boundary",),
        uncertainty_register=("trace transpose symmetry unresolved",),
        plain_language_explanation=("the trace of a product is cyclic",),
        validator_results=("symbols closed",),
        artifact_hash="f" * 64,
        status=EarlyFormalizationStatus.EARLY_FORMALIZATION_CANDIDATE,
    )
    concept = EngineeringConceptBundle(
        concept_id="ec-1",
        version=1,
        research_spec_id="rs-1",
        input_spec_hash="e" * 64,
        route_selection_id="ers-1",
        feasibility_assessment_id="fa-1",
        neighbor_evidence_set_id="ps-1",
        notation_table=("X: input", "Y: output"),
        system_boundary_model={"actors": ("user",), "external_systems": ()},
        actors_and_use_cases=("user computes trace",),
        input_output_contracts=("F: X*C -> Y",),
        state_transition_formulas=("s'=T(s,u,e)",),
        requirement_predicates=("R1: output is trace",),
        quality_metric_formulas=("Q1: latency < 1s",),
        architecture_graph_candidate={"vertices": ("compute",), "edges": ()},
        traceability_relation={"R1": ("D1", "V1")},
        verification_obligations=("V1: test trace output",),
        neighbor_difference_matrix=("engineering neighbor differs in API",),
        assumptions_and_constraints=("finite matrices",),
        unresolved_thresholds=(),
        plain_language_explanation=("engineering concept candidate",),
        artifact_hash="aa" * 32,
        status=EngineeringConceptStatus.ENGINEERING_CONCEPT_CANDIDATE,
    )

    with pytest.raises(FrozenInstanceError):
        bundle.status = EarlyFormalizationStatus.READY_FOR_USER_REVIEW  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        concept.status = EngineeringConceptStatus.READY_FOR_USER_REVIEW  # type: ignore[misc]

    approval = UserFormalizationApproval(
        formalization_id="ef-1",
        version=1,
        formalization_hash="f" * 64,
        input_spec_hash="e" * 64,
        route=ResearchRoute.THEORY,
        actor=ProvenanceType.USER_DECISION,
        user_event_id="uev-approve",
        decided_at=NOW,
    )
    assert approval.route is ResearchRoute.THEORY
    with pytest.raises(DomainError):
        UserFormalizationApproval(
            formalization_id="ef-1",
            version=1,
            formalization_hash="f" * 64,
            input_spec_hash="e" * 64,
            route=ResearchRoute.THEORY,
            actor=ProvenanceType.ASSISTANT_PROPOSAL,
            user_event_id="model-event",
            decided_at=NOW,
        )
    with pytest.raises(DomainError):
        UserEngineeringConceptApproval(
            concept_id="ec-1",
            version=1,
            concept_hash="aa" * 32,
            route_selection_id="ers-1",
            input_spec_hash="e" * 64,
            route=ResearchRoute.ENGINEERING,
            actor=ProvenanceType.ASSISTANT_PROPOSAL,
            user_event_id="model-event",
            decided_at=NOW,
        )


# ---------------------------------------------------------------------------
# Events
# ---------------------------------------------------------------------------


def test_event_catalog_matches_03a_and_builder_is_stable():
    expected = {
        "NaturalLanguageDesignReady",
        "FormalizationCapabilitySelected",
        "NeighborSearchCompleted",
        "FormalizationFeasibilityAssessed",
        "EngineeringRouteDecisionOpened",
        "EngineeringRouteSelected",
        "EarlyFormalizationCreated",
        "EngineeringConceptCreated",
        "EarlyFormalizationReviewOpened",
        "EarlyEngineeringConceptReviewOpened",
        "EarlyFormalizationApproved",
        "EarlyEngineeringConceptApproved",
        "NoveltyReviewStarted",
        "NoveltyReviewScored",
        "NoveltyThresholdPassed",
        "EngineeringNoveltyThresholdPassed",
        "NoveltyResearchDecisionOpened",
        "NoveltyResearchRequested",
        "NoveltyOverrideAccepted",
    }
    assert expected == RQ_EVENT_TYPES
    assert EVENT_NATURAL_LANGUAGE_DESIGN_READY == "NaturalLanguageDesignReady"
    assert EVENT_NOVELTY_OVERRIDE_ACCEPTED == "NoveltyOverrideAccepted"

    event = build_qualification_event(
        EVENT_NATURAL_LANGUAGE_DESIGN_READY,
        aggregate_type="Project",
        aggregate_id="p-1",
        payload={"project_id": "p-1", "input_spec_hash": "e" * 64},
        sequence=1,
    )
    assert event.event_hash == sha256_hex(
        {
            "aggregate_type": "Project",
            "aggregate_id": "p-1",
            "event_type": EVENT_NATURAL_LANGUAGE_DESIGN_READY,
            "payload": {"project_id": "p-1", "input_spec_hash": "e" * 64},
            "sequence": 1,
            "created_at": event.created_at,
        }
    )
    with pytest.raises(DomainError) as exc_info:
        build_qualification_event(
            "NotAnRQEvent",
            aggregate_type="Project",
            aggregate_id="p-1",
            payload={},
            sequence=1,
        )
    assert exc_info.value.error_code == "UNKNOWN_EVENT_TYPE"


# ---------------------------------------------------------------------------
# Novelty policies and scoring
# ---------------------------------------------------------------------------


def test_novelty_policies_have_exact_weights_and_are_not_interchangeable():
    assert {item.item_id: item.weight for item in THEORY_NOVELTY_POLICY.items} == {
        "T1": 3,
        "T2": 3,
        "T3": 2,
        "T4": 2,
        "A1": 3,
        "A2": 2,
        "A3": 2,
        "A4": 2,
        "A5": 1,
    }
    assert {item.item_id: item.weight for item in ENGINEERING_NOVELTY_POLICY.items} == {
        "E1": 3,
        "E2": 3,
        "E3": 2,
        "E4": 2,
        "E5": 2,
        "EA1": 2,
        "EA2": 2,
        "EA3": 2,
        "EA4": 2,
    }
    assert THEORY_NOVELTY_POLICY.route is ResearchRoute.THEORY
    assert ENGINEERING_NOVELTY_POLICY.route is ResearchRoute.ENGINEERING


def test_conservative_scoring_uses_itemwise_min_and_rejects_route_mixing():
    theory_scores = _theory_70_scores()
    primary = _scorecard(ResearchRoute.THEORY, session_id="s1", **theory_scores)
    auditor = _scorecard(
        ResearchRoute.THEORY,
        session_id="s2",
        **{**theory_scores, "T1": 5},
    )
    conservative = calculate_conservative_novelty_score(
        route=ResearchRoute.THEORY,
        primary=primary,
        auditor=auditor,
    )
    assert conservative.conservative_item_scores["T1"] == 4
    assert conservative.conservative_item_scores["T2"] == 4
    assert conservative.theory_score == 40
    assert conservative.application_score == 30
    assert conservative.novelty_total == 70
    assert conservative.engineering_score is None
    assert conservative.engineering_application_score is None

    engineering_primary = _scorecard(
        ResearchRoute.ENGINEERING, session_id="s3", **_score_map(ResearchRoute.ENGINEERING, 5)
    )
    with pytest.raises(DomainError) as exc_info:
        calculate_conservative_novelty_score(
            route=ResearchRoute.THEORY,
            primary=engineering_primary,
            auditor=engineering_primary,
        )
    assert exc_info.value.error_code == "NOVELTY_ROUTE_MISMATCH"


def test_scorecard_rejects_missing_extra_and_out_of_range_scores():
    with pytest.raises(DomainError) as exc_info:
        _scorecard(ResearchRoute.THEORY, session_id="s1", T1=5)
    assert exc_info.value.error_code == "NOVELTY_SCORECARD_INVALID"

    with pytest.raises(DomainError) as exc_info:
        _scorecard(
            ResearchRoute.THEORY,
            session_id="s1",
            **_theory_70_scores() | {"EXTRA": 3},
        )
    assert exc_info.value.error_code == "NOVELTY_SCORECARD_INVALID"

    with pytest.raises(DomainError) as exc_info:
        _scorecard(
            ResearchRoute.THEORY,
            session_id="s1",
            **_theory_70_scores() | {"T1": 6},
        )
    assert exc_info.value.error_code == "NOVELTY_SCORECARD_INVALID"


def test_theory_route_70_and_69_boundaries():
    primary = _scorecard(ResearchRoute.THEORY, session_id="s1", **_theory_70_scores())
    auditor = _scorecard(ResearchRoute.THEORY, session_id="s2", **_theory_70_scores())

    decision = route_novelty_decision(
        review_valid=True,
        coverage_status=PriorArtCoverageStatus.COMPLETE,
        route=ResearchRoute.THEORY,
        primary=primary,
        auditor=auditor,
    )
    assert decision.status is NoveltyStatus.NOVELTY_QUALIFIED
    assert decision.gate_type is None
    assert decision.next_target is QualifiedNextTarget.S5

    scores_69 = _theory_70_scores() | {"A5": 2}
    decision = route_novelty_decision(
        review_valid=True,
        coverage_status=PriorArtCoverageStatus.COMPLETE,
        route=ResearchRoute.THEORY,
        primary=_scorecard(ResearchRoute.THEORY, session_id="s1", **scores_69),
        auditor=_scorecard(ResearchRoute.THEORY, session_id="s2", **scores_69),
    )
    assert decision.status is NoveltyStatus.NOVELTY_RESEARCH_REQUIRED
    assert decision.gate_type is QualificationGateType.LOW_NOVELTY_RESEARCH_DECISION
    assert decision.next_target is None


def test_engineering_route_70_and_69_boundaries():
    scores_70 = _engineering_70_scores()
    primary = _scorecard(ResearchRoute.ENGINEERING, session_id="s1", **scores_70)
    auditor = _scorecard(ResearchRoute.ENGINEERING, session_id="s2", **scores_70)
    decision = route_novelty_decision(
        review_valid=True,
        coverage_status=PriorArtCoverageStatus.COMPLETE,
        route=ResearchRoute.ENGINEERING,
        primary=primary,
        auditor=auditor,
    )
    assert decision.status is NoveltyStatus.ENGINEERING_NOVELTY_QUALIFIED
    assert decision.gate_type is None
    assert decision.next_target is QualifiedNextTarget.ENG0

    scores_69 = _engineering_70_scores() | {"E1": 4, "EA4": 1}
    primary = _scorecard(ResearchRoute.ENGINEERING, session_id="s1", **scores_69)
    auditor = _scorecard(ResearchRoute.ENGINEERING, session_id="s2", **scores_69)
    decision = route_novelty_decision(
        review_valid=True,
        coverage_status=PriorArtCoverageStatus.COMPLETE,
        route=ResearchRoute.ENGINEERING,
        primary=primary,
        auditor=auditor,
    )
    assert decision.status is NoveltyStatus.NOVELTY_RESEARCH_REQUIRED
    assert decision.gate_type is QualificationGateType.LOW_NOVELTY_RESEARCH_DECISION
    assert decision.next_target is None


def test_novelty_review_is_inconclusive_when_coverage_or_validity_fails():
    scores = _theory_70_scores()
    for coverage in (
        PriorArtCoverageStatus.PARTIAL,
        PriorArtCoverageStatus.FAILED_PROVIDER,
    ):
        decision = route_novelty_decision(
            review_valid=True,
            coverage_status=coverage,
            route=ResearchRoute.THEORY,
            primary=_scorecard(ResearchRoute.THEORY, session_id="s1", **scores),
            auditor=_scorecard(ResearchRoute.THEORY, session_id="s2", **scores),
        )
        assert decision.status is NoveltyStatus.INCONCLUSIVE
        assert decision.next_target is None

    decision = route_novelty_decision(
        review_valid=False,
        coverage_status=PriorArtCoverageStatus.COMPLETE,
        route=ResearchRoute.THEORY,
        primary=_scorecard(ResearchRoute.THEORY, session_id="s1", **scores),
        auditor=_scorecard(ResearchRoute.THEORY, session_id="s2", **scores),
    )
    assert decision.status is NoveltyStatus.INCONCLUSIVE
    assert decision.gate_type is QualificationGateType.LOW_NOVELTY_RESEARCH_DECISION


def test_novelty_review_builder_computes_scores_and_hash():
    scores = _theory_70_scores()
    review = NoveltyReview.create(
        review_id="nr-1",
        project_id="p-1",
        route=ResearchRoute.THEORY,
        policy_version=THEORY_NOVELTY_POLICY.policy_version,
        subject_artifact_type="EarlyFormalizationBundle",
        subject_artifact_id="ef-1",
        subject_artifact_hash="f" * 64,
        neighbor_evidence_set_id="ps-1",
        reviewer_session_ids=("s1", "s2"),
        primary_scorecard=_scorecard(ResearchRoute.THEORY, session_id="s1", **scores),
        auditor_scorecard=_scorecard(ResearchRoute.THEORY, session_id="s2", **scores),
        coverage_status=PriorArtCoverageStatus.COMPLETE,
        nearest_overlap_refs=("n-1",),
        strongest_difference_refs=("n-2",),
        limitations=("patent area unsearched",),
        created_at=NOW,
    )
    assert review.theory_score == 40
    assert review.application_score == 30
    assert review.novelty_total == 70
    assert review.status is NoveltyStatus.NOVELTY_QUALIFIED
    assert sha256_hex(review.content_payload()) == review.artifact_hash
    with pytest.raises(FrozenInstanceError):
        review.novelty_total = 100  # type: ignore[misc]


# ---------------------------------------------------------------------------
# Gates
# ---------------------------------------------------------------------------


def test_gate_binding_requires_type_specific_fields():
    valid = GateBinding(
        gate_type=QualificationGateType.ENGINEERING_ROUTE_DECISION,
        artifact_id="fa-1",
        version=1,
        artifact_hash="a" * 64,
        input_spec_hash="e" * 64,
    )
    assert valid.route is None

    with pytest.raises(DomainError) as exc_info:
        GateBinding(
            gate_type=QualificationGateType.EARLY_FORMALIZATION_REVIEW,
            artifact_id="ef-1",
            version=1,
            artifact_hash="f" * 64,
            input_spec_hash="e" * 64,
            route=ResearchRoute.ENGINEERING,
        )
    assert exc_info.value.error_code == "GATE_BINDING_INVALID"

    with pytest.raises(DomainError) as exc_info:
        GateBinding(
            gate_type=QualificationGateType.LOW_NOVELTY_RESEARCH_DECISION,
            artifact_id="nr-1",
            version=1,
            artifact_hash="a" * 64,
            input_spec_hash="e" * 64,
            route=ResearchRoute.THEORY,
        )
    assert exc_info.value.error_code == "GATE_BINDING_INVALID"


def test_gate_resolution_requires_user_actor_and_legal_decision():
    binding = GateBinding(
        gate_type=QualificationGateType.ENGINEERING_ROUTE_DECISION,
        artifact_id="fa-1",
        version=1,
        artifact_hash="a" * 64,
        input_spec_hash="e" * 64,
    )
    gate = Gate(gate_id="g-1", project_id="p-1", gate_type=binding.gate_type, binding=binding)
    assert gate.status is GateStatus.OPEN

    with pytest.raises(DomainError) as exc_info:
        gate.resolve(
            decision=EngineeringRouteDecision.TRY_ENGINEERING_PROJECT.value,
            actor=ProvenanceType.ASSISTANT_PROPOSAL,
            user_event_id="model-event",
            at=NOW,
        )
    assert exc_info.value.error_code == "CONFIRMATION_REQUIRES_USER_EVENT"

    with pytest.raises(DomainError) as exc_info:
        gate.resolve(
            decision="NOT_A_DECISION",
            actor=ProvenanceType.USER_DECISION,
            user_event_id="uev-1",
            at=NOW,
        )
    assert exc_info.value.error_code == "INVALID_GATE_DECISION"

    resolved = gate.resolve(
        decision=EngineeringRouteDecision.TRY_ENGINEERING_PROJECT.value,
        actor=ProvenanceType.USER_DECISION,
        user_event_id="uev-1",
        at=NOW,
    )
    assert resolved.status is GateStatus.RESOLVED
    assert resolved.decision == "TRY_ENGINEERING_PROJECT"
    with pytest.raises(DomainError) as exc_info:
        resolved.resolve(
            decision=EngineeringRouteDecision.PAUSE.value,
            actor=ProvenanceType.USER_DECISION,
            user_event_id="uev-2",
            at=NOW,
        )
    assert exc_info.value.error_code == "CONFLICT"


def test_allowed_decisions_for_each_qualification_gate():
    assert set(allowed_decisions_for_gate(QualificationGateType.ENGINEERING_ROUTE_DECISION)) == {
        "REVISE_FOR_THEORY",
        "TRY_ENGINEERING_PROJECT",
        "PAUSE",
        "ARCHIVE",
    }
    assert set(
        allowed_decisions_for_gate(QualificationGateType.FORMALIZATION_FEASIBILITY_DECISION)
    ) == {"REVISE_DESIGN", "RESEARCH_MORE", "PAUSE", "ARCHIVE"}
    assert set(allowed_decisions_for_gate(QualificationGateType.EARLY_FORMALIZATION_REVIEW)) == {
        "APPROVE",
        "REQUEST_REVISION",
        "RESEARCH_MORE",
        "REVISE_DESIGN",
        "REJECT",
        "PAUSE",
    }
    assert set(
        allowed_decisions_for_gate(QualificationGateType.EARLY_ENGINEERING_CONCEPT_REVIEW)
    ) == {
        "APPROVE",
        "REQUEST_REVISION",
        "RESEARCH_MORE",
        "RETURN_TO_ROUTE_DECISION",
        "REJECT",
        "PAUSE",
    }
    assert set(allowed_decisions_for_gate(QualificationGateType.LOW_NOVELTY_RESEARCH_DECISION)) == {
        "RERUN_RESEARCH",
        "REVISE_DESIGN",
        "CONTINUE_WITH_RECORDED_OVERRIDE",
        "RETURN_TO_ROUTE_DECISION",
        "ARCHIVE",
        "PAUSE",
    }


def test_unqualified_route_cannot_advance_to_s5_or_eng0():
    assert (
        qualification_next_target(
            route=ResearchRoute.THEORY,
            novelty_status=NoveltyStatus.NOVELTY_QUALIFIED,
        )
        is QualifiedNextTarget.S5
    )
    assert (
        qualification_next_target(
            route=ResearchRoute.ENGINEERING,
            novelty_status=NoveltyStatus.ENGINEERING_NOVELTY_QUALIFIED,
        )
        is QualifiedNextTarget.ENG0
    )

    for status in (
        NoveltyStatus.NOVELTY_RESEARCH_REQUIRED,
        NoveltyStatus.INCONCLUSIVE,
        NoveltyStatus.USER_OVERRIDDEN_BELOW_THRESHOLD,
    ):
        with pytest.raises(DomainError) as exc_info:
            qualification_next_target(
                route=ResearchRoute.THEORY,
                novelty_status=status,
            )
        assert exc_info.value.error_code == "EARLY_QUALIFICATION_REQUIRED"

    override = LowNoveltyOverride(
        review_id="nr-1",
        route=ResearchRoute.THEORY,
        review_artifact_hash="h" * 64,
        actor=ProvenanceType.USER_DECISION,
        user_event_id="uev-override",
        decided_at=NOW,
    )
    assert (
        qualification_next_target(
            route=ResearchRoute.THEORY,
            novelty_status=NoveltyStatus.USER_OVERRIDDEN_BELOW_THRESHOLD,
            override=override,
            review_artifact_hash="h" * 64,
        )
        is QualifiedNextTarget.S5
    )
    with pytest.raises(DomainError) as exc_info:
        qualification_next_target(
            route=ResearchRoute.ENGINEERING,
            novelty_status=NoveltyStatus.USER_OVERRIDDEN_BELOW_THRESHOLD,
            override=override,
            review_artifact_hash="h" * 64,
        )
    assert exc_info.value.error_code == "EARLY_QUALIFICATION_REQUIRED"


# ---------------------------------------------------------------------------
# Migration 0002
# ---------------------------------------------------------------------------


def _alembic_config(db_url: str) -> Config:
    cfg = Config()
    cfg.set_main_option("script_location", str(MIGRATIONS_DIR))
    cfg.set_main_option("sqlalchemy.url", db_url)
    return cfg


def test_migration_0002_upgrade_and_downgrade(tmp_path):
    db_url = f"sqlite:///{tmp_path / 'rq.db'}"
    cfg = _alembic_config(db_url)
    command.upgrade(cfg, "0002")
    inspector = inspect(create_engine(db_url))
    expected_tables = {
        "research_specs",
        "model_profiles",
        "formalization_capability_decisions",
        "prior_art_searches",
        "prior_art_neighbors",
        "formalization_feasibility_assessments",
        "engineering_route_selections",
        "early_formalizations",
        "engineering_concepts",
        "novelty_reviews",
        "novelty_score_items",
        "human_gates",
    }
    assert expected_tables <= set(inspector.get_table_names())
    columns = {column["name"] for column in inspector.get_columns("novelty_reviews")}
    assert {
        "id",
        "route",
        "theory_score",
        "application_score",
        "engineering_score",
        "engineering_application_score",
        "novelty_total",
        "status",
    } <= columns
    command.downgrade(cfg, "0001")
    inspector = inspect(create_engine(db_url))
    assert set(inspector.get_table_names()) == {"alembic_version", "artifacts", "domain_events"}
