"""M3.2 integration tests for S8 readiness attack, S9 open questions, S10 handoff."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config

from synaisthesis.agents.schemas import (
    HandoffTask,
    OpenQuestionRecord,
    OpenQuestionRegistry,
    PreFreezeAttackReport,
    ResearchHandoffBundle,
)
from synaisthesis.application.incubation_service import (
    load_open_question_registry,
    load_prefreeze_attack_report,
    load_research_handoff_bundle,
    propose_open_question_registry,
    propose_prefreeze_attack_report,
    propose_research_handoff_bundle,
)
from synaisthesis.domain.enums import NoveltyStatus, ResearchRoute
from synaisthesis.domain.errors import DomainError
from synaisthesis.domain.stage import (
    S8_STAGE_CONTRACT,
    S9_STAGE_CONTRACT,
    S10_STAGE_CONTRACT,
    StageId,
    validate_open_question_registry,
    validate_prefreeze_attack_report,
    validate_research_handoff_bundle,
)
from synaisthesis.orchestration.nodes.incubator_nodes import (
    s8_readiness_attack_node,
    s10_handoff_node,
)
from synaisthesis.storage.database import init_database

NOW = datetime(2026, 8, 17, 2, 0, 0, tzinfo=UTC)
REVIEW_HASH = "r" * 64
REPO_ROOT = Path(__file__).resolve().parents[2]
MIGRATIONS_DIR = REPO_ROOT / "src" / "synaisthesis" / "storage" / "migrations"


def _fresh_database(tmp_path: Path):
    db_url = f"sqlite:///{tmp_path / 's8s10.db'}"
    cfg = Config()
    cfg.set_main_option("script_location", str(MIGRATIONS_DIR))
    cfg.set_main_option("sqlalchemy.url", db_url)
    command.upgrade(cfg, "head")
    _, session_factory = init_database(db_url)
    return session_factory


def _report(**overrides) -> PreFreezeAttackReport:
    params = {
        "attack_rounds": 2,
        "internal_attacks": ("内部攻击：浮点边界失败",),
        "external_attacks": ("独立外部攻击：量词风险",),
        "obvious_counterexamples": ("非方阵",),
        "boundary_failures": ("浮点下界",),
        "definition_holes": ("trace 定义域",),
        "quantifier_risks": ("∀ 缺少形状约束",),
        "tool_feasibility": ("Lean 可表达",),
        "claim_atomicity": ("c1 原子",),
        "recommended_split": ("拆分 c1/c2",),
        "freeze_readiness": True,
        "critical_issues_resolved": True,
        "critical_issues_blocked": False,
        "rollback_targets": ("S1", "S7"),
    }
    params.update(overrides)
    return PreFreezeAttackReport(**params)


def _registry(**overrides) -> OpenQuestionRegistry:
    params = {
        "registry_id": "oq-1",
        "entries": (
            OpenQuestionRecord(
                question_id="q1",
                statement="浮点实现下 tr(AB)=tr(BA) 的误差界",
                origin="AI_GENERATED",
                why_open="浮点语义未形式化",
                known_failed_attempts=["逐项比较失败"],
                falsification_path="构造病态矩阵",
                next_action="形式化误差模型",
                dependency_claims=["c1"],
                status="OPEN",
            ),
        ),
    }
    params.update(overrides)
    return OpenQuestionRegistry(**params)


def _handoff(**overrides) -> ResearchHandoffBundle:
    params = {
        "frozen_terms": ("trace", "cyclic invariant"),
        "evidence_summary": ("tr(AB)=tr(BA) 由最小案例验证 @s5-1",),
        "current_versions": {"S5": "s5-1", "S7": "plan-1"},
        "open_questions": ("q1",),
        "downstream_tasks": (
            HandoffTask(
                task_id="t1",
                title="Lean 形式化",
                track="proof",
                input="S7 plan",
                output="proof candidate",
                threshold="kernel accepted",
            ),
        ),
        "verification_thresholds": ("Lean kernel 接受",),
        "proof_track": ("t1",),
        "experiment_track": ("数值稳定性实验",),
        "engineering_track": (),
        "writing_track": ("母稿章节",),
        "artifact_manifest": ("s5-1", "plan-1"),
        "unresolved_gates": (),
    }
    params.update(overrides)
    return ResearchHandoffBundle(**params)


# ---------------------------------------------------------------------------
# Stage contracts and domain validators
# ---------------------------------------------------------------------------


def test_s8_s10_stage_contracts():
    assert S8_STAGE_CONTRACT.stage_id is StageId.S8
    assert "十轮 Council" in S8_STAGE_CONTRACT.human_gate_policy
    assert S8_STAGE_CONTRACT.rollback_targets == (
        StageId.S1,
        StageId.S4,
        StageId.S6,
        StageId.S7,
    )
    assert S9_STAGE_CONTRACT.stage_id is StageId.S9
    assert S10_STAGE_CONTRACT.stage_id is StageId.S10
    assert "RQ4M" in S10_STAGE_CONTRACT.human_gate_policy


def test_golden_report_passes_validator():
    assert validate_prefreeze_attack_report(_report()) == ()


def test_s8_never_allows_ten_round_council():
    # schema layer rejects 10 rounds outright
    with pytest.raises(ValueError):
        _report(attack_rounds=10)
    # domain validator also rejects it when reached with a bypassed schema
    bypassed = PreFreezeAttackReport.model_construct(
        **{**_report().model_dump(), "attack_rounds": 10}
    )
    issues = validate_prefreeze_attack_report(bypassed)
    assert any("十轮" in issue for issue in issues)


def test_s8_requires_internal_and_external_attacks():
    issues = validate_prefreeze_attack_report(_report(internal_attacks=(), external_attacks=("x",)))
    assert any("内部攻击" in issue for issue in issues)
    issues = validate_prefreeze_attack_report(_report(internal_attacks=("x",), external_attacks=()))
    assert any("独立外部攻击" in issue for issue in issues)


def test_s8_freeze_requires_critical_resolution_or_block():
    issues = validate_prefreeze_attack_report(
        _report(critical_issues_resolved=False, critical_issues_blocked=False)
    )
    assert any("Critical" in issue for issue in issues)
    # explicitly blocked critical issues are allowed, but freeze requires resolution
    blocked = _report(
        critical_issues_resolved=False,
        critical_issues_blocked=True,
        freeze_readiness=False,
    )
    assert validate_prefreeze_attack_report(blocked) == ()


def test_s9_validator_preserves_ai_generated_marker():
    assert validate_open_question_registry(_registry()) == ()
    registry = _registry(
        entries=(
            OpenQuestionRecord(
                question_id="q1",
                statement="s",
                origin="AI_GENERATED",
                why_open="w",
                known_failed_attempts=["f"],
                falsification_path="p",
                next_action="n",
                dependency_claims=[],
                status="OPEN",
            ),
        )
    )
    assert registry.entries[0].origin == "AI_GENERATED"


def test_s9_rejects_unknown_origin():
    issues = validate_open_question_registry(
        _registry(
            entries=(
                OpenQuestionRecord(
                    question_id="q1",
                    statement="s",
                    origin="HALLUCINATED",
                    why_open="w",
                    known_failed_attempts=["f"],
                    falsification_path="p",
                    next_action="n",
                    dependency_claims=[],
                    status="OPEN",
                ),
            )
        )
    )
    assert any("来源" in issue for issue in issues)


def test_s10_validator_rejects_unattributed_evidence():
    issues = validate_research_handoff_bundle(_handoff(evidence_summary=("没有来源的证据",)))
    assert any("未归属" in issue for issue in issues)


def test_s10_validator_requires_task_io_threshold():
    issues = validate_research_handoff_bundle(
        _handoff(
            downstream_tasks=(
                HandoffTask(
                    task_id="t1",
                    title="t",
                    track="proof",
                    input="   ",
                    output="   ",
                    threshold="   ",
                ),
            )
        )
    )
    assert any("缺少 input" in issue for issue in issues)
    assert any("缺少 output" in issue for issue in issues)
    assert any("缺少 threshold" in issue for issue in issues)


# ---------------------------------------------------------------------------
# Service layer
# ---------------------------------------------------------------------------


def test_s8_report_round_trip(tmp_path):
    session_factory = _fresh_database(tmp_path)
    artifact_root = tmp_path / "artifacts"
    report = _report()
    with session_factory() as session:
        propose_prefreeze_attack_report(
            session,
            project_id="p-1",
            report=report,
            artifact_root=artifact_root,
            report_id="attack-1",
        )
        session.commit()
    with session_factory() as session:
        reloaded = load_prefreeze_attack_report(session, "attack-1", artifact_root=artifact_root)
    assert reloaded == report
    assert reloaded.attack_rounds == 2


def test_s9_registry_round_trip(tmp_path):
    session_factory = _fresh_database(tmp_path)
    artifact_root = tmp_path / "artifacts"
    registry = _registry()
    with session_factory() as session:
        propose_open_question_registry(
            session,
            project_id="p-1",
            registry=registry,
            artifact_root=artifact_root,
        )
        session.commit()
    with session_factory() as session:
        reloaded = load_open_question_registry(session, "oq-1", artifact_root=artifact_root)
    assert reloaded == registry
    assert reloaded.entries[0].origin == "AI_GENERATED"


def test_s10_maturity_gate_rejects_engineering_route(tmp_path):
    session_factory = _fresh_database(tmp_path)
    artifact_root = tmp_path / "artifacts"
    with session_factory() as session, pytest.raises(DomainError) as exc_info:
        propose_research_handoff_bundle(
            session,
            project_id="p-1",
            bundle=_handoff(),
            qualification_route=ResearchRoute.ENGINEERING,
            novelty_status=NoveltyStatus.ENGINEERING_NOVELTY_QUALIFIED,
            qualification_review_hash=REVIEW_HASH,
            artifact_root=artifact_root,
        )
    assert exc_info.value.error_code == "EARLY_QUALIFICATION_REQUIRED"


def test_s10_maturity_gate_rejects_unqualified_theory(tmp_path):
    session_factory = _fresh_database(tmp_path)
    artifact_root = tmp_path / "artifacts"
    with session_factory() as session, pytest.raises(DomainError) as exc_info:
        propose_research_handoff_bundle(
            session,
            project_id="p-1",
            bundle=_handoff(),
            qualification_route=ResearchRoute.THEORY,
            novelty_status=NoveltyStatus.NOVELTY_RESEARCH_REQUIRED,
            qualification_review_hash=REVIEW_HASH,
            artifact_root=artifact_root,
        )
    assert exc_info.value.error_code == "EARLY_QUALIFICATION_REQUIRED"


def test_s10_handoff_round_trip_with_qualified_theory(tmp_path):
    session_factory = _fresh_database(tmp_path)
    artifact_root = tmp_path / "artifacts"
    bundle = _handoff()
    with session_factory() as session:
        propose_research_handoff_bundle(
            session,
            project_id="p-1",
            bundle=bundle,
            qualification_route=ResearchRoute.THEORY,
            novelty_status=NoveltyStatus.NOVELTY_QUALIFIED,
            qualification_review_hash=REVIEW_HASH,
            artifact_root=artifact_root,
            bundle_id="handoff-1",
        )
        session.commit()
    with session_factory() as session:
        reloaded = load_research_handoff_bundle(session, "handoff-1", artifact_root=artifact_root)
    assert reloaded == bundle
    assert reloaded.downstream_tasks[0].threshold == "kernel accepted"


def test_nodes_enforce_same_preconditions(tmp_path):
    session_factory = _fresh_database(tmp_path)
    artifact_root = tmp_path / "artifacts"
    with session_factory() as session:
        s8_readiness_attack_node(
            session,
            project_id="p-1",
            report=_report(),
            artifact_root=artifact_root,
        )
        with pytest.raises(DomainError) as exc_info:
            s10_handoff_node(
                session,
                project_id="p-1",
                bundle=_handoff(),
                qualification_route=ResearchRoute.ENGINEERING,
                novelty_status=NoveltyStatus.ENGINEERING_NOVELTY_QUALIFIED,
                qualification_review_hash=REVIEW_HASH,
                artifact_root=artifact_root,
            )
    assert exc_info.value.error_code == "EARLY_QUALIFICATION_REQUIRED"
