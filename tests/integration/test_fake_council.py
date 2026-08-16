"""M7.1 integration tests for the Fake council state graph (03 section 2)."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config

from synaisthesis.application.council_service import (
    advance_council_round,
    create_council_run,
    load_council_run_state,
    pause_council_run,
    recover_council_run_from_checkpoint,
    resume_council_run,
    start_council_run,
)
from synaisthesis.domain.enums import ProgressKind
from synaisthesis.domain.errors import DomainError
from synaisthesis.domain.isolation import CouncilRun, CouncilRunStatus
from synaisthesis.orchestration.checkpointing import load_council_checkpoint
from synaisthesis.orchestration.graph_builder import (
    PLAN_KIND_CHECKPOINT,
    PLAN_KIND_COMPLETE,
    PLAN_KIND_MATURITY_GATE,
    PLAN_KIND_ROUND,
    build_round_plan,
    pause_resume_edges,
)
from synaisthesis.orchestration.nodes.council_nodes import (
    council_pause_node,
    council_recover_node,
    council_resume_node,
    council_round_node,
)
from synaisthesis.orchestration.state import (
    can_continue_after_maturity_gate,
    checkpoint_due,
    is_valid_round,
    maturity_gate_due,
    next_round_target,
)
from synaisthesis.storage.database import init_database

NOW = datetime(2026, 8, 17, 2, 0, 0, tzinfo=UTC)
REPO_ROOT = Path(__file__).resolve().parents[2]
MIGRATIONS_DIR = REPO_ROOT / "src" / "synaisthesis" / "storage" / "migrations"


def _fresh_database(tmp_path: Path):
    db_url = f"sqlite:///{tmp_path / 'council.db'}"
    cfg = Config()
    cfg.set_main_option("script_location", str(MIGRATIONS_DIR))
    cfg.set_main_option("sqlalchemy.url", db_url)
    command.upgrade(cfg, "head")
    _, session_factory = init_database(db_url)
    return session_factory


def _create_and_start(session_factory, artifact_root: Path, rounds: int = 10) -> CouncilRun:
    with session_factory() as session:
        run = create_council_run(
            session,
            project_id="p-1",
            claim_contract_id="cc-1",
            configured_rounds=rounds,
            primary_model_profile_id="mp-1",
            auditor_model_profile_id="mp-2",
            delegation_policy_id="dp-1",
            budget_policy_id="bp-1",
            artifact_root=artifact_root,
            run_id="run-1",
        )
        running = start_council_run(session, project_id="p-1", run=run, artifact_root=artifact_root)
        session.commit()
    return running


def _advance(
    session_factory,
    artifact_root: Path,
    run: CouncilRun,
    *,
    restatement: bool = False,
    **overrides,
) -> CouncilRun:
    params = {
        "progress_kind": ProgressKind.MECHANISM,
        "produced_new_artifact_or_diff": True,
        "public_rationale": "new evidence",
        "unresolved_items": ("counterexample search",),
        "is_restatement": restatement,
    }
    params.update(overrides)
    with session_factory() as session:
        advanced = advance_council_round(
            session,
            project_id="p-1",
            run=run,
            artifact_root=artifact_root,
            **params,
        )
        session.commit()
    return advanced


# ---------------------------------------------------------------------------
# Effective-round rules (03, section 2)
# ---------------------------------------------------------------------------


def test_valid_round_requires_all_five_conditions():
    assert is_valid_round(
        progress_kind=ProgressKind.MECHANISM,
        produced_new_artifact_or_diff=True,
        public_rationale="r",
        unresolved_items=("x",),
        is_restatement=False,
    ) == (True, ())
    valid, blockers = is_valid_round(
        progress_kind=None,
        produced_new_artifact_or_diff=False,
        public_rationale="",
        unresolved_items=(),
        is_restatement=True,
    )
    assert valid is False
    assert len(blockers) == 5


def test_invalid_round_is_not_counted(tmp_path):
    session_factory = _fresh_database(tmp_path)
    artifact_root = tmp_path / "artifacts"
    run = _create_and_start(session_factory, artifact_root)
    with session_factory() as session, pytest.raises(DomainError) as exc_info:
        advance_council_round(
            session,
            project_id="p-1",
            run=run,
            progress_kind=ProgressKind.MECHANISM,
            produced_new_artifact_or_diff=False,  # restatement
            public_rationale="same as before",
            unresolved_items=("x",),
            is_restatement=True,
            artifact_root=artifact_root,
        )
    assert exc_info.value.error_code == "INVALID_ROUND"
    with session_factory() as session:
        reloaded = load_council_run_state(session, "run-1", artifact_root=artifact_root)
    assert reloaded.current_round == 0


def test_ten_round_cap_and_checkpoints(tmp_path):
    session_factory = _fresh_database(tmp_path)
    artifact_root = tmp_path / "artifacts"
    run = _create_and_start(session_factory, artifact_root, rounds=10)
    for expected in range(1, 11):
        run = _advance(session_factory, artifact_root, run)
        assert run.current_round == expected
        if checkpoint_due(expected):
            with session_factory() as session:
                checkpoint = load_council_checkpoint(session, "run-1", artifact_root=artifact_root)
            assert checkpoint["current_round"] == expected
    # cap reached: one more round is refused
    with session_factory() as session, pytest.raises(DomainError) as exc_info:
        advance_council_round(
            session,
            project_id="p-1",
            run=run,
            progress_kind=ProgressKind.MECHANISM,
            produced_new_artifact_or_diff=True,
            public_rationale="r",
            unresolved_items=("x",),
            is_restatement=False,
            artifact_root=artifact_root,
        )
    assert exc_info.value.error_code == "COUNCIL_COMPLETE"
    assert next_round_target(10, 10) is None


def test_maturity_gate_at_round_20(tmp_path):
    session_factory = _fresh_database(tmp_path)
    artifact_root = tmp_path / "artifacts"
    run = _create_and_start(session_factory, artifact_root, rounds=30)
    for expected in range(1, 20):
        run = _advance(session_factory, artifact_root, run)
        assert run.current_round == expected
    with session_factory() as session, pytest.raises(DomainError) as exc_info:
        advance_council_round(
            session,
            project_id="p-1",
            run=run,
            progress_kind=ProgressKind.MECHANISM,
            produced_new_artifact_or_diff=True,
            public_rationale="r",
            unresolved_items=("x",),
            is_restatement=False,
            artifact_root=artifact_root,
        )
    assert exc_info.value.error_code == "MATURITY_GATE_REQUIRED"
    # real user CONTINUE allows passing the gate
    from synaisthesis.domain.enums import ProvenanceType

    assert can_continue_after_maturity_gate(
        decision="CONTINUE_AFTER_ROUND_20", actor=ProvenanceType.USER_DECISION
    )
    assert not can_continue_after_maturity_gate(
        decision="CONTINUE_AFTER_ROUND_20", actor=ProvenanceType.ASSISTANT_PROPOSAL
    )
    run = _advance(
        session_factory,
        artifact_root,
        run,
        maturity_continue=True,
    )
    assert run.current_round == 20
    assert maturity_gate_due(20)


def test_pause_resume_round_trip(tmp_path):
    session_factory = _fresh_database(tmp_path)
    artifact_root = tmp_path / "artifacts"
    run = _create_and_start(session_factory, artifact_root)
    with session_factory() as session:
        paused = pause_council_run(session, project_id="p-1", run=run, artifact_root=artifact_root)
        session.commit()
    assert paused.status is CouncilRunStatus.PAUSED
    # advancing a paused run is refused
    with session_factory() as session, pytest.raises(DomainError) as exc_info:
        advance_council_round(
            session,
            project_id="p-1",
            run=paused,
            progress_kind=ProgressKind.MECHANISM,
            produced_new_artifact_or_diff=True,
            public_rationale="r",
            unresolved_items=("x",),
            is_restatement=False,
            artifact_root=artifact_root,
        )
    assert exc_info.value.error_code == "COUNCIL_PAUSED"
    with session_factory() as session:
        resumed = resume_council_run(
            session, project_id="p-1", run=paused, artifact_root=artifact_root
        )
        session.commit()
    assert resumed.status is CouncilRunStatus.RUNNING
    assert pause_resume_edges() == (
        ("RUNNING", "PAUSED"),
        ("PAUSED", "RUNNING"),
    )


def test_checkpoint_recovery_and_mismatch(tmp_path):
    session_factory = _fresh_database(tmp_path)
    artifact_root = tmp_path / "artifacts"
    run = _create_and_start(session_factory, artifact_root)
    for _ in range(5):
        run = _advance(session_factory, artifact_root, run)
    # checkpoint exists at round 5 and matches the replayed run state
    with session_factory() as session:
        recovered = recover_council_run_from_checkpoint(
            session, project_id="p-1", run=run, artifact_root=artifact_root
        )
    assert recovered.current_round == 5
    # a stale run object (older round) fails closed
    import dataclasses

    with session_factory() as session:
        run_at_zero = load_council_run_state(session, "run-1", artifact_root=artifact_root)
    run_at_zero = dataclasses.replace(run_at_zero, current_round=0)
    with session_factory() as session, pytest.raises(DomainError) as exc_info:
        recover_council_run_from_checkpoint(
            session, project_id="p-1", run=run_at_zero, artifact_root=artifact_root
        )
    assert exc_info.value.error_code == "CHECKPOINT_MISMATCH"


def test_round_plan_and_nodes(tmp_path):
    plan = build_round_plan(10)
    kinds = [kind for _number, kind in plan]
    assert kinds.count(PLAN_KIND_ROUND) == 10
    assert kinds.count(PLAN_KIND_CHECKPOINT) == 2  # rounds 5 and 10
    assert kinds[-1] == PLAN_KIND_COMPLETE
    long_plan = build_round_plan(30)
    assert any(kind == PLAN_KIND_MATURITY_GATE for _number, kind in long_plan)

    session_factory = _fresh_database(tmp_path)
    artifact_root = tmp_path / "artifacts"
    _create_and_start(session_factory, artifact_root)
    with session_factory() as session:
        advanced = council_round_node(
            session,
            project_id="p-1",
            run_id="run-1",
            progress_kind=ProgressKind.MECHANISM,
            produced_new_artifact_or_diff=True,
            public_rationale="r",
            unresolved_items=("x",),
            is_restatement=False,
            artifact_root=artifact_root,
        )
        session.commit()
    assert advanced.current_round == 1

    with session_factory() as session:
        paused = council_pause_node(
            session, project_id="p-1", run_id="run-1", artifact_root=artifact_root
        )
        resumed = council_resume_node(
            session, project_id="p-1", run_id="run-1", artifact_root=artifact_root
        )
        session.commit()
    assert paused.status is CouncilRunStatus.PAUSED
    assert resumed.status is CouncilRunStatus.RUNNING
    # advance to round 5 so a WIP_CHECKPOINT exists before recovery
    current = resumed
    for _ in range(4):
        current = _advance(session_factory, artifact_root, current)
    with session_factory() as session:
        recovered = council_recover_node(
            session, project_id="p-1", run_id="run-1", artifact_root=artifact_root
        )
    assert recovered.current_round == 5
