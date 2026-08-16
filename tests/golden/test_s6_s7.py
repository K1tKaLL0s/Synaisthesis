"""M3.1 golden tests for S6 TheoryKernel and S7 FormalizationPlan (03, S6/S7)."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config

from synaisthesis.agents.schemas import (
    FormalizationPlan,
    FormalizationPlanClaim,
    TheoryKernel,
)
from synaisthesis.application.incubation_service import (
    load_formalization_plan,
    load_theory_kernel,
    propose_formalization_plan,
    propose_theory_kernel,
)
from synaisthesis.domain.enums import (
    EarlyFormalizationStatus,
    FormulaOrigin,
    ProvenanceType,
    ResearchRoute,
)
from synaisthesis.domain.errors import DomainError
from synaisthesis.domain.qualification import (
    EarlyFormalizationBundle,
    FormulaItem,
    UserFormalizationApproval,
)
from synaisthesis.domain.stage import (
    S6_STAGE_CONTRACT,
    S7_STAGE_CONTRACT,
    StageId,
    validate_formalization_plan,
    validate_theory_kernel,
)
from synaisthesis.storage.database import init_database

NOW = datetime(2026, 8, 17, 2, 0, 0, tzinfo=UTC)
SPEC_HASH = "s" * 64
REPO_ROOT = Path(__file__).resolve().parents[2]
MIGRATIONS_DIR = REPO_ROOT / "src" / "synaisthesis" / "storage" / "migrations"


def _fresh_database(tmp_path: Path):
    db_url = f"sqlite:///{tmp_path / 's6s7.db'}"
    cfg = Config()
    cfg.set_main_option("script_location", str(MIGRATIONS_DIR))
    cfg.set_main_option("sqlalchemy.url", db_url)
    command.upgrade(cfg, "head")
    _, session_factory = init_database(db_url)
    return session_factory


def _kernel(**overrides) -> TheoryKernel:
    params = {
        "candidate_mechanism": "tr(AB)=tr(BA) 源于循环置换不变性",
        "competing_explanations": ("逐元素求和可交换假设",),
        "examples": ("A=I, B=J",),
        "counterexamples": ("非方阵形状",),
        "invariants": ("矩阵形状不变",),
        "boundaries": ("有限矩阵",),
        "predictions": ("大矩阵数值误差随规模增长",),
        "discarded_alternatives": ("逐元素求和",),
        "discard_reasons": ("不满足循环不变性",),
        "unresolved_conflicts": ("浮点实现差异",),
    }
    params.update(overrides)
    return TheoryKernel(**params)


def _bundle() -> EarlyFormalizationBundle:
    return EarlyFormalizationBundle(
        formalization_id="ef-1",
        version=1,
        research_spec_id="rs-1",
        input_spec_hash=SPEC_HASH,
        feasibility_assessment_id="fa-1",
        neighbor_evidence_set_id="nes-1",
        formalizer_profile_or_import_id="profile-1",
        notation_table=("tr: trace",),
        formula_items=(
            FormulaItem(
                formula_id="f1",
                formula_type="identity",
                latex="tr(AB)=tr(BA)",
                normalized_math_ast="trace(mul(A,B)) = trace(mul(B,A))",
                symbols_used=("A", "B"),
                source_spec_fields=("core_definition",),
                assumption_formula_ids=(),
                neighbor_refs=("n1",),
                origin=FormulaOrigin.MODEL_PROPOSAL,
                confidence=0.9,
                known_ambiguities=(),
                falsification_or_failure_formula_id="f2",
            ),
        ),
        formula_dependency_graph={"f1": ("f2",)},
        semantic_alignment_matrix=("f1 -> core_definition",),
        neighbor_difference_matrix=("f1 differs from n1",),
        uncertainty_register=(),
        plain_language_explanation=("trace is cyclic",),
        validator_results=("schema ok",),
        artifact_hash="0" * 64,
        status=EarlyFormalizationStatus.READY_FOR_USER_REVIEW,
    )


def _approved_bundle() -> tuple[EarlyFormalizationBundle, UserFormalizationApproval]:
    import dataclasses

    from synaisthesis.application.qualification_service import (
        early_formula_bundle_content_payload,
    )
    from synaisthesis.domain.event import sha256_hex

    bundle = dataclasses.replace(
        _bundle(),
        artifact_hash=sha256_hex(early_formula_bundle_content_payload(_bundle())),
        status=EarlyFormalizationStatus.READY_FOR_USER_REVIEW,
    )
    approval = UserFormalizationApproval(
        formalization_id="ef-1",
        version=1,
        formalization_hash=bundle.artifact_hash or "",
        input_spec_hash=SPEC_HASH,
        route=ResearchRoute.THEORY,
        actor=ProvenanceType.USER_DECISION,
        user_event_id="uev-ef",
        decided_at=NOW,
    )
    return bundle, approval


def _plan(**overrides) -> FormalizationPlan:
    params = {
        "object_domain": "有限矩阵 M_n",
        "symbols": ("A", "B", "tr"),
        "definitions": ("tr(M)=Σ M_ii",),
        "assumptions": ("方阵",),
        "quantifiers": ("forall",),
        "claims": (
            FormalizationPlanClaim(
                claim_id="c1",
                statement="∀A,B ∈ M_n, tr(AB)=tr(BA)",
                object_domain="有限矩阵 M_n",
                quantifiers=["forall A", "forall B"],
                falsification_witness="形状不符的非方阵输入",
            ),
        ),
        "dependency_graph": {"c1": ("def-1",)},
        "proof_paths": ("循环置换展开",),
        "counterexample_paths": ("非方阵构造",),
        "intended_tools": ("Lean 4",),
        "formalization_uncertainties": ("浮点语义",),
        "proof_candidate_artifacts": ("candidate-1.lean:PROOF_CANDIDATE",),
    }
    params.update(overrides)
    return FormalizationPlan(**params)


# ---------------------------------------------------------------------------
# Domain validators (03 S6/S7 PASS conditions)
# ---------------------------------------------------------------------------


def test_s6_s7_stage_contracts_exist():
    assert S6_STAGE_CONTRACT.stage_id is StageId.S6
    assert S6_STAGE_CONTRACT.rollback_targets == (StageId.S1, StageId.S4)
    assert S7_STAGE_CONTRACT.stage_id is StageId.S7
    assert S7_STAGE_CONTRACT.rollback_targets == (StageId.S1, StageId.S4, StageId.S6)
    assert "PROOF_CANDIDATE" in S7_STAGE_CONTRACT.human_gate_policy


def test_golden_kernel_passes_validator():
    assert validate_theory_kernel(_kernel()) == ()


def test_kernel_requires_competing_explanation():
    issues = validate_theory_kernel(_kernel(competing_explanations=[]))
    assert any("替代理论" in issue for issue in issues)


def test_kernel_preserves_counterexamples():
    issues = validate_theory_kernel(_kernel(counterexamples=[]))
    assert any("反例" in issue for issue in issues)


def test_kernel_discard_reasons_match_alternatives():
    issues = validate_theory_kernel(
        _kernel(discarded_alternatives=("A1", "A2"), discard_reasons=("r1",))
    )
    assert any("放弃理由" in issue for issue in issues)


def test_golden_plan_passes_validator():
    assert validate_formalization_plan(_plan()) == ()


def test_plan_claim_requires_domain_quantifier_witness():
    plan = _plan(
        claims=(
            FormalizationPlanClaim(
                claim_id="c1",
                statement="claim",
                object_domain="   ",
                quantifiers=[],
                falsification_witness="   ",
            ),
        )
    )
    issues = validate_formalization_plan(plan)
    assert any("对象域" in issue for issue in issues)
    assert any("量词" in issue for issue in issues)
    assert any("证伪见证" in issue for issue in issues)


def test_plan_rejects_unexplained_cycle():
    plan = _plan(dependency_graph={"a": ("b",), "b": ("a",)})
    issues = validate_formalization_plan(plan)
    assert any("无环" in issue for issue in issues)


def test_plan_accepts_explicit_self_recursion():
    plan = _plan(dependency_graph={"a": ("a",)})
    assert validate_formalization_plan(plan) == ()


def test_plan_requires_tools_or_not_applicable():
    issues = validate_formalization_plan(_plan(intended_tools=[]))
    assert any("验证工具" in issue for issue in issues)
    assert validate_formalization_plan(_plan(intended_tools=("NOT_APPLICABLE",))) == ()


# ---------------------------------------------------------------------------
# Service layer: approved-formula consumption, regression, proof candidate
# ---------------------------------------------------------------------------


def test_s6_kernel_round_trip(tmp_path):
    session_factory = _fresh_database(tmp_path)
    artifact_root = tmp_path / "artifacts"
    with session_factory() as session:
        propose_theory_kernel(
            session,
            project_id="p-1",
            kernel=_kernel(),
            artifact_root=artifact_root,
            kernel_id="kernel-1",
        )
        session.commit()
    with session_factory() as session:
        reloaded = load_theory_kernel(session, "kernel-1", artifact_root=artifact_root)
    assert reloaded == _kernel()
    assert reloaded.candidate_mechanism


def test_s7_requires_approved_early_formulas(tmp_path):
    session_factory = _fresh_database(tmp_path)
    artifact_root = tmp_path / "artifacts"
    bundle, approval = _approved_bundle()
    stale_approval = UserFormalizationApproval(
        formalization_id="ef-1",
        version=1,
        formalization_hash="0" * 64,
        input_spec_hash=SPEC_HASH,
        route=ResearchRoute.THEORY,
        actor=ProvenanceType.USER_DECISION,
        user_event_id="uev-ef",
        decided_at=NOW,
    )
    with session_factory() as session, pytest.raises(DomainError) as exc_info:
        propose_formalization_plan(
            session,
            project_id="p-1",
            plan=_plan(),
            approval=stale_approval,
            bundle=bundle,
            current_input_spec_hash=SPEC_HASH,
            artifact_root=artifact_root,
        )
    assert exc_info.value.error_code == "EARLY_FORMALIZATION_REQUIRED"


def test_s7_rejects_engineering_route_approval():
    # the domain itself refuses to build an engineering-route formalization approval
    with pytest.raises(DomainError) as exc_info:
        UserFormalizationApproval(
            formalization_id="ef-1",
            version=1,
            formalization_hash="h" * 64,
            input_spec_hash=SPEC_HASH,
            route=ResearchRoute.ENGINEERING,
            actor=ProvenanceType.USER_DECISION,
            user_event_id="uev-ef",
            decided_at=NOW,
        )
    assert exc_info.value.error_code == "INVALID_APPROVAL_ROUTE"


def test_s7_semantic_change_rolls_back_to_s1_s4(tmp_path):
    session_factory = _fresh_database(tmp_path)
    artifact_root = tmp_path / "artifacts"
    bundle, approval = _approved_bundle()
    with session_factory() as session, pytest.raises(DomainError) as exc_info:
        propose_formalization_plan(
            session,
            project_id="p-1",
            plan=_plan(),
            approval=approval,
            bundle=bundle,
            current_input_spec_hash="t" * 64,  # S1/S4 hash drifted
            artifact_root=artifact_root,
        )
    assert exc_info.value.error_code == "SEMANTIC_REGRESSION_REQUIRED"


def test_s7_plan_round_trip(tmp_path):
    session_factory = _fresh_database(tmp_path)
    artifact_root = tmp_path / "artifacts"
    bundle, approval = _approved_bundle()
    plan = _plan()
    with session_factory() as session:
        propose_formalization_plan(
            session,
            project_id="p-1",
            plan=plan,
            approval=approval,
            bundle=bundle,
            current_input_spec_hash=SPEC_HASH,
            artifact_root=artifact_root,
            plan_id="plan-1",
        )
        session.commit()
    with session_factory() as session:
        reloaded = load_formalization_plan(session, "plan-1", artifact_root=artifact_root)
    assert reloaded == plan
    assert reloaded.claims[0].object_domain == "有限矩阵 M_n"
    assert reloaded.intended_tools == ["Lean 4"]


def test_s7_rejects_tool_verified_label(tmp_path):
    session_factory = _fresh_database(tmp_path)
    artifact_root = tmp_path / "artifacts"
    bundle, approval = _approved_bundle()
    plan = _plan(proof_candidate_artifacts=("candidate-1.lean:TOOL_VERIFIED",))
    with session_factory() as session, pytest.raises(DomainError) as exc_info:
        propose_formalization_plan(
            session,
            project_id="p-1",
            plan=plan,
            approval=approval,
            bundle=bundle,
            current_input_spec_hash=SPEC_HASH,
            artifact_root=artifact_root,
        )
    assert exc_info.value.error_code == "PROOF_CANDIDATE_REQUIRED"
