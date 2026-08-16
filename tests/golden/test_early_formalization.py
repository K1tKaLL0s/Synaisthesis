"""M2.5 golden tests for RQ2M early formalization."""

from __future__ import annotations

from dataclasses import replace
from datetime import UTC, datetime
from pathlib import Path

import pytest

from synaisthesis.agents.schemas import MechanismSketch, NaturalLanguageSpec, ResearchScopeSpec
from synaisthesis.application.qualification_service import (
    assess_formalization_feasibility_from_matrices,
    build_early_formula_bundle,
    early_formula_bundle_content_payload,
    open_early_formalization_review,
    resolve_early_formalization_review,
    validate_early_formula_bundle,
)
from synaisthesis.domain.enums import (
    EarlyFormalizationReviewDecision,
    EarlyFormalizationStatus,
    PredicateVerdict,
    PriorArtCoverageStatus,
    ProvenanceType,
    QualificationGateType,
    ResearchRoute,
)
from synaisthesis.domain.errors import DomainError
from synaisthesis.domain.event import sha256_hex
from synaisthesis.domain.qualification import (
    EngineeringFitPredicates,
    FeasibilityPredicate,
    FeasibilityPredicateMatrix,
    FormalizationCapabilityProfile,
    NeighborEvidenceSet,
    TheoryFitPredicates,
)

NOW = datetime(2026, 8, 16, 20, 0, 0, tzinfo=UTC)
REPO_ROOT = Path(__file__).resolve().parents[2]
PROMPTS_DIR = REPO_ROOT / "src" / "synaisthesis" / "prompts" / "formalization"

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


def _pred(predicate_id: str, verdict: PredicateVerdict) -> FeasibilityPredicate:
    return FeasibilityPredicate(
        predicate_id=predicate_id,
        verdict=verdict,
        evidence_refs=(f"S1.{predicate_id.lower()}",),
    )


def _matrix():
    return FeasibilityPredicateMatrix(
        theory=TheoryFitPredicates(
            tfo=_pred("TFO", PredicateVerdict.PASS),
            tfr=_pred("TFR", PredicateVerdict.PASS),
            tfc=_pred("TFC", PredicateVerdict.PASS),
            tfw=_pred("TFW", PredicateVerdict.PASS),
            tfp=_pred("TFP", PredicateVerdict.PASS),
        ),
        engineering=EngineeringFitPredicates(
            efs=_pred("EFS", PredicateVerdict.FAIL),
            efi=_pred("EFI", PredicateVerdict.FAIL),
            efa=_pred("EFA", PredicateVerdict.FAIL),
            efm=_pred("EFM", PredicateVerdict.FAIL),
            eff=_pred("EFF", PredicateVerdict.FAIL),
        ),
    )


def _assessment():
    matrix = _matrix()
    return assess_formalization_feasibility_from_matrices(
        assessment_id="fa-1",
        version=1,
        research_spec_id="rs-1",
        input_spec_hash="a" * 64,
        neighbor_evidence_set_id="ps-1",
        assessor_session_ids=("session-early", "session-engineering"),
        early_matrix=matrix,
        engineering_matrix=matrix,
        public_explanation=("pure theory fit",),
    )


def _capability(**overrides):
    base = {
        "model_profile_id": "mp-1",
        "capability_tier": "ADVANCED",
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


def _rehash(bundle):
    return replace(
        bundle,
        artifact_hash=sha256_hex(early_formula_bundle_content_payload(bundle)),
    )


def _golden_bundle():
    return build_early_formula_bundle(
        capability_profile=_capability(),
        feasibility_assessment=_assessment(),
        spec=GOLDEN_S1,
        mechanism=GOLDEN_S2,
        scope=GOLDEN_S4,
        evidence=GOLDEN_EVIDENCE,
        formalizer_session_id="session-early",
        formalization_id="ef-1",
        version=1,
        now=NOW,
    )


def test_capability_gate_blocks_bundle_build():
    with pytest.raises(DomainError) as exc_info:
        build_early_formula_bundle(
            capability_profile=_capability(formalization_eval_score=70.0),
            feasibility_assessment=_assessment(),
            spec=GOLDEN_S1,
            mechanism=GOLDEN_S2,
            scope=GOLDEN_S4,
            evidence=GOLDEN_EVIDENCE,
            formalizer_session_id="session-early",
            now=NOW,
        )
    assert exc_info.value.error_code == "FORMALIZER_CAPABILITY_UNAVAILABLE"


def test_golden_bundle_covers_required_formula_types_and_is_candidate():
    bundle = _golden_bundle()
    assert bundle.status is EarlyFormalizationStatus.EARLY_FORMALIZATION_CANDIDATE
    formula_types = {item.formula_type for item in bundle.formula_items}
    assert {
        "OBJECT_DOMAIN",
        "ASSUMPTION",
        "CORE_CLAIM",
        "FAILURE_WITNESS",
        "THEORY_APPLICATION_MAP",
    } <= formula_types
    core_claim = next(item for item in bundle.formula_items if item.formula_type == "CORE_CLAIM")
    assert "\\" in core_claim.latex


def test_golden_bundle_validates_clean():
    bundle = _golden_bundle()
    status, issues = validate_early_formula_bundle(bundle)
    assert status is EarlyFormalizationStatus.EARLY_FORMALIZATION_CANDIDATE
    assert issues == ()
    assert sha256_hex(early_formula_bundle_content_payload(bundle)) == bundle.artifact_hash


def test_undefined_symbol_is_rejected():
    bundle = _golden_bundle()
    broken_formula = replace(bundle.formula_items[0], symbols_used=("Z",))
    broken = _rehash(replace(bundle, formula_items=(broken_formula,) + bundle.formula_items[1:]))
    status, issues = validate_early_formula_bundle(broken)
    assert status is EarlyFormalizationStatus.SCHEMA_INVALID
    assert any("Z" in issue for issue in issues)


def test_dependency_cycle_is_rejected():
    bundle = _golden_bundle()
    broken = _rehash(
        replace(
            bundle,
            formula_dependency_graph={"f1": ("f2",), "f2": ("f1",)},
        )
    )
    status, issues = validate_early_formula_bundle(broken)
    assert status is EarlyFormalizationStatus.SCHEMA_INVALID
    assert any("环" in issue or "cycle" in issue for issue in issues)


def test_core_claim_without_failure_formula_is_incomplete():
    bundle = _golden_bundle()
    broken_items = tuple(
        replace(item, falsification_or_failure_formula_id="")
        if item.formula_type == "CORE_CLAIM"
        else item
        for item in bundle.formula_items
    )
    status, issues = validate_early_formula_bundle(
        _rehash(replace(bundle, formula_items=broken_items))
    )
    assert status is EarlyFormalizationStatus.FORMULA_COVERAGE_INCOMPLETE
    assert any("失败" in issue or "failure" in issue for issue in issues)


def test_natural_language_core_claim_is_semantic_gap():
    bundle = _golden_bundle()
    broken_items = tuple(
        replace(
            item,
            latex="核心主张就是迹循环性质成立。",
            falsification_or_failure_formula_id="f-failure",
        )
        if item.formula_type == "CORE_CLAIM"
        else item
        for item in bundle.formula_items
    )
    status, issues = validate_early_formula_bundle(
        _rehash(replace(bundle, formula_items=broken_items))
    )
    assert status is EarlyFormalizationStatus.SEMANTIC_GAP
    assert any("公式" in issue for issue in issues)


def test_hash_mismatch_is_detected():
    bundle = replace(_golden_bundle(), artifact_hash="0" * 64)
    status, issues = validate_early_formula_bundle(bundle)
    assert status is EarlyFormalizationStatus.SCHEMA_INVALID
    assert any("artifact_hash" in issue for issue in issues)


def test_review_gate_binds_hash_and_requires_real_user():
    bundle = _golden_bundle()
    gate = open_early_formalization_review(bundle=bundle, gate_id="g-review")
    assert gate.gate_type is QualificationGateType.EARLY_FORMALIZATION_REVIEW
    assert gate.binding.artifact_hash == bundle.artifact_hash
    assert gate.binding.input_spec_hash == bundle.input_spec_hash
    assert gate.binding.route is ResearchRoute.THEORY

    with pytest.raises(DomainError) as exc_info:
        resolve_early_formalization_review(
            gate=gate,
            decision=EarlyFormalizationReviewDecision.APPROVE.value,
            actor=ProvenanceType.ASSISTANT_PROPOSAL,
            user_event_id="model-event",
            current_bundle_hash=bundle.artifact_hash,
            at=NOW,
        )
    assert exc_info.value.error_code == "CONFIRMATION_REQUIRES_USER_EVENT"

    resolved, approval = resolve_early_formalization_review(
        gate=gate,
        decision=EarlyFormalizationReviewDecision.APPROVE.value,
        actor=ProvenanceType.USER_DECISION,
        user_event_id="uev-approve",
        current_bundle_hash=bundle.artifact_hash,
        at=NOW,
    )
    assert resolved.decision == "APPROVE"
    assert approval is not None
    assert approval.route is ResearchRoute.THEORY
    assert approval.formalization_hash == bundle.artifact_hash


def test_stale_bundle_hash_blocks_review():
    bundle = _golden_bundle()
    gate = open_early_formalization_review(bundle=bundle, gate_id="g-review")
    with pytest.raises(DomainError) as exc_info:
        resolve_early_formalization_review(
            gate=gate,
            decision=EarlyFormalizationReviewDecision.APPROVE.value,
            actor=ProvenanceType.USER_DECISION,
            user_event_id="uev-stale",
            current_bundle_hash="c" * 64,
            at=NOW,
        )
    assert exc_info.value.error_code == "STALE_FORMALIZATION_BINDING"


def test_prompt_asset_has_required_sections():
    content = (PROMPTS_DIR / "early_formalization.md").read_text(encoding="utf-8")
    assert "prompt_key: early_formalization" in content
    assert "version: 1.0.0" in content
    assert "禁止行为" in content
    assert "OBJECT_DOMAIN" in content
    assert "CORE_CLAIM" in content
