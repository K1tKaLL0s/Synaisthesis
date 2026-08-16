"""M2.4A unit tests for dual RQ2F assessment and conservative aggregation."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from synaisthesis.agents.early_formalizer import EarlyFormalizer
from synaisthesis.agents.engineering_feasibility_assessor import EngineeringFeasibilityAssessor
from synaisthesis.agents.schemas import MechanismSketch, NaturalLanguageSpec, ResearchScopeSpec
from synaisthesis.application.qualification_service import (
    assess_formalization_feasibility,
    assess_formalization_feasibility_from_matrices,
)
from synaisthesis.domain.enums import (
    FeasibilityAssessmentStatus,
    PredicateVerdict,
    PriorArtCoverageStatus,
    ResearchRoute,
    RouteClassification,
)
from synaisthesis.domain.errors import DomainError
from synaisthesis.domain.qualification import (
    EngineeringFitPredicates,
    FeasibilityPredicate,
    FeasibilityPredicateMatrix,
    NeighborEvidenceSet,
    TheoryFitPredicates,
    merge_feasibility_matrices,
)

NOW = datetime(2026, 8, 16, 18, 0, 0, tzinfo=UTC)


def _pred(predicate_id: str, verdict: PredicateVerdict) -> FeasibilityPredicate:
    return FeasibilityPredicate(
        predicate_id=predicate_id,
        verdict=verdict,
        evidence_refs=(f"S1.{predicate_id.lower()}", "RQ1.neighbor[0]"),
    )


def _theory(verdict: PredicateVerdict) -> TheoryFitPredicates:
    return TheoryFitPredicates(
        tfo=_pred("TFO", verdict),
        tfr=_pred("TFR", verdict),
        tfc=_pred("TFC", verdict),
        tfw=_pred("TFW", verdict),
        tfp=_pred("TFP", verdict),
    )


def _engineering(verdict: PredicateVerdict) -> EngineeringFitPredicates:
    return EngineeringFitPredicates(
        efs=_pred("EFS", verdict),
        efi=_pred("EFI", verdict),
        efa=_pred("EFA", verdict),
        efm=_pred("EFM", verdict),
        eff=_pred("EFF", verdict),
    )


def _matrix(theory_verdict: PredicateVerdict, engineering_verdict: PredicateVerdict):
    return FeasibilityPredicateMatrix(
        theory=_theory(theory_verdict),
        engineering=_engineering(engineering_verdict),
    )


def _assessment(
    theory_verdict: PredicateVerdict,
    engineering_verdict: PredicateVerdict,
    *,
    assessment_id: str = "fa-1",
):
    return assess_formalization_feasibility_from_matrices(
        assessment_id=assessment_id,
        version=1,
        research_spec_id="rs-1",
        input_spec_hash="a" * 64,
        neighbor_evidence_set_id="ps-1",
        assessor_session_ids=("session-early", "session-engineering"),
        early_matrix=_matrix(theory_verdict, engineering_verdict),
        engineering_matrix=_matrix(theory_verdict, engineering_verdict),
        public_explanation=("theory and engineering materials evaluated",),
    )


GOLDEN_S1 = NaturalLanguageSpec(
    core_definition="迹是方阵对角元之和，tr(AB)=tr(BA) 对可相乘方阵成立。",
    positive_examples=["tr(AB)=tr(BA)"],
    non_examples=["det(AB)=det(A)det(B)"],
    boundary_conditions=["A、B 必须可相乘"],
    object_candidates=["方阵", "迹"],
    ambiguous_terms=[],
    explicit_non_goals=["不研究行列式"],
    expected_functions=["证明循环性质"],
    target_applications=["数值线性代数"],
    intended_users=["研究者"],
    operational_constraints=["有限维实/复方阵"],
    success_metrics=["形式化证明覆盖循环性质"],
)

GOLDEN_S2 = MechanismSketch(
    inputs=["方阵 A", "方阵 B"],
    state_change="取 AB 与 BA 的迹",
    outputs=["tr(AB)", "tr(BA)"],
    invariants=["tr(AB)=tr(BA)"],
    failure_conditions=["不可相乘时无定义"],
    causal_claims=["循环置换使迹不变"],
    merely_descriptive_relations=["样本中交换与迹相关"],
    uncertainty_register=["转置对称性未定"],
)

GOLDEN_S4 = ResearchScopeSpec(
    main_question="迹的循环不变性在什么边界条件下保持？",
    object_domain="有限维实/复方阵",
    non_goals=["不研究行列式"],
    nearest_neighbor_difference="明确转置反例边界",
    central_claims=["tr(AB)=tr(BA)"],
    evidence_requirements=["给出方阵可相乘时的证明"],
    failure_learning_plan="反例不成立则回 S1/S3",
    engineering_relevance="迹的数值计算",
    stop_conditions=["中心主张被推翻时停止"],
)

GOLDEN_EVIDENCE = NeighborEvidenceSet(
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


def test_feasibility_predicate_requires_evidence_refs():
    with pytest.raises(DomainError) as exc_info:
        FeasibilityPredicate(
            predicate_id="TFO",
            verdict=PredicateVerdict.PASS,
            evidence_refs=(),
        )
    assert exc_info.value.error_code == "FEASIBILITY_PREDICATE_EVIDENCE_REQUIRED"


def test_merge_uses_fail_over_unknown_over_pass_for_every_predicate():
    first = _matrix(PredicateVerdict.PASS, PredicateVerdict.PASS)
    second = _matrix(PredicateVerdict.FAIL, PredicateVerdict.FAIL)
    merged, disagreements = merge_feasibility_matrices(first, second)
    assert all(
        predicate.verdict is PredicateVerdict.FAIL
        for predicate in merged.theory.as_tuple() + merged.engineering.as_tuple()
    )
    assert len(disagreements) == 10

    second_unknown = _matrix(PredicateVerdict.UNKNOWN, PredicateVerdict.UNKNOWN)
    merged, _ = merge_feasibility_matrices(first, second_unknown)
    assert all(
        predicate.verdict is PredicateVerdict.UNKNOWN
        for predicate in merged.theory.as_tuple() + merged.engineering.as_tuple()
    )


def test_unknown_never_makes_fit_true():
    unknown_assessment = _assessment(PredicateVerdict.UNKNOWN, PredicateVerdict.PASS)
    assert unknown_assessment.route_classification is RouteClassification.INCONCLUSIVE
    assert unknown_assessment.status is FeasibilityAssessmentStatus.FEASIBILITY_INCONCLUSIVE
    assert unknown_assessment.recommended_route is None


def test_fixed_truth_table_and_assessment_fields():
    cases = (
        (
            PredicateVerdict.PASS,
            PredicateVerdict.PASS,
            RouteClassification.HYBRID_FIT,
            FeasibilityAssessmentStatus.THEORY_OR_HYBRID_FIT,
            ResearchRoute.THEORY,
        ),
        (
            PredicateVerdict.PASS,
            PredicateVerdict.FAIL,
            RouteClassification.PURE_THEORY_FIT,
            FeasibilityAssessmentStatus.THEORY_OR_HYBRID_FIT,
            ResearchRoute.THEORY,
        ),
        (
            PredicateVerdict.FAIL,
            PredicateVerdict.PASS,
            RouteClassification.ENGINEERING_PROJECT_CANDIDATE,
            FeasibilityAssessmentStatus.ENGINEERING_ROUTE_DECISION_REQUIRED,
            ResearchRoute.ENGINEERING,
        ),
        (
            PredicateVerdict.FAIL,
            PredicateVerdict.FAIL,
            RouteClassification.NEITHER_CURRENTLY_FIT,
            FeasibilityAssessmentStatus.FORMALIZATION_FEASIBILITY_USER_DECISION_REQUIRED,
            None,
        ),
    )
    for theory_verdict, engineering_verdict, classification, status, route in cases:
        assessment = _assessment(theory_verdict, engineering_verdict)
        assert assessment.route_classification is classification
        assert assessment.status is status
        assert assessment.recommended_route is route


def test_early_formalizer_returns_all_pass_for_complete_golden_inputs():
    session = EarlyFormalizer.create(
        session_id="session-early",
        spec=GOLDEN_S1,
        mechanism=GOLDEN_S2,
        scope=GOLDEN_S4,
        evidence=GOLDEN_EVIDENCE,
    )
    matrix = session.assess(GOLDEN_S1, GOLDEN_S2, GOLDEN_S4, GOLDEN_EVIDENCE)
    assert all(
        predicate.verdict is PredicateVerdict.PASS
        for predicate in matrix.theory.as_tuple() + matrix.engineering.as_tuple()
    )
    assert session.role == "EARLY_FORMALIZER"


def test_engineering_assessor_returns_all_pass_and_separate_context_hash():
    early = EarlyFormalizer.create(
        session_id="session-early",
        spec=GOLDEN_S1,
        mechanism=GOLDEN_S2,
        scope=GOLDEN_S4,
        evidence=GOLDEN_EVIDENCE,
    )
    engineering = EngineeringFeasibilityAssessor.create(
        session_id="session-engineering",
        spec=GOLDEN_S1,
        mechanism=GOLDEN_S2,
        scope=GOLDEN_S4,
        evidence=GOLDEN_EVIDENCE,
    )
    assert engineering.role == "ENGINEERING_FEASIBILITY_ASSESSOR"
    assert early.isolated_context_hash != engineering.isolated_context_hash
    matrix = engineering.assess(GOLDEN_S1, GOLDEN_S2, GOLDEN_S4, GOLDEN_EVIDENCE)
    assert all(
        predicate.verdict is PredicateVerdict.PASS
        for predicate in matrix.theory.as_tuple() + matrix.engineering.as_tuple()
    )


def test_structural_assessor_does_not_default_pass_on_missing_material():
    broken_s1 = GOLDEN_S1.model_copy(update={"success_metrics": []})
    broken_scope = GOLDEN_S4.model_copy(update={"stop_conditions": []})
    early = EarlyFormalizer.create(
        session_id="session-early",
        spec=broken_s1,
        mechanism=GOLDEN_S2,
        scope=broken_scope,
        evidence=GOLDEN_EVIDENCE,
    )
    matrix = early.assess(broken_s1, GOLDEN_S2, broken_scope, GOLDEN_EVIDENCE)
    verdicts = {
        predicate.predicate_id: predicate.verdict
        for predicate in matrix.theory.as_tuple() + matrix.engineering.as_tuple()
    }
    assert verdicts["TFW"] in {PredicateVerdict.FAIL, PredicateVerdict.UNKNOWN}
    assert verdicts["EFM"] in {PredicateVerdict.FAIL, PredicateVerdict.UNKNOWN}
    assert PredicateVerdict.PASS not in {
        verdicts["TFW"],
        verdicts["EFM"],
    }


def test_high_level_assessment_merges_two_sessions():
    early = EarlyFormalizer.create(
        session_id="session-early",
        spec=GOLDEN_S1,
        mechanism=GOLDEN_S2,
        scope=GOLDEN_S4,
        evidence=GOLDEN_EVIDENCE,
    )
    engineering = EngineeringFeasibilityAssessor.create(
        session_id="session-engineering",
        spec=GOLDEN_S1,
        mechanism=GOLDEN_S2,
        scope=GOLDEN_S4,
        evidence=GOLDEN_EVIDENCE,
    )
    assessment = assess_formalization_feasibility(
        assessment_id="fa-1",
        version=1,
        research_spec_id="rs-1",
        input_spec_hash="a" * 64,
        neighbor_evidence_set_id="ps-1",
        early_formalizer=early,
        engineering_assessor=engineering,
        spec=GOLDEN_S1,
        mechanism=GOLDEN_S2,
        scope=GOLDEN_S4,
        evidence=GOLDEN_EVIDENCE,
        public_explanation=("theory and engineering materials evaluated",),
    )
    assert assessment.route_classification is RouteClassification.HYBRID_FIT
    assert assessment.assessor_session_ids == ("session-early", "session-engineering")
