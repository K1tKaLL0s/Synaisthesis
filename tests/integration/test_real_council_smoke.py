"""M9.1 integration tests for the real council vertical slice (04, 19 §5 M9.1).

One small claim runs the whole chain: council run -> oppose counterexample ->
repair -> semantic gate -> REAL Lean verification -> user confirmation ->
bundle events.  Model roles are deterministic (paid calls are manual); only
the Lean step is a real tool invocation.
"""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config

from synaisthesis.application.council_service import (
    council_confirm_and_bundle,
    council_semantic_gate,
    create_council_run,
    start_council_run,
)
from synaisthesis.domain.action import SemanticDelta
from synaisthesis.domain.enums import ProvenanceType
from synaisthesis.domain.errors import DomainError
from synaisthesis.orchestration.nodes.council_nodes import (
    council_confirm_node,
    council_regression_node,
    council_repair_node,
    council_semantic_gate_node,
    council_verification_node,
)
from synaisthesis.storage.database import init_database
from synaisthesis.storage.repositories.event_repository import DomainEventRecord

NOW = datetime(2026, 8, 17, 2, 0, 0, tzinfo=UTC)
REPO_ROOT = Path(__file__).resolve().parents[2]
MIGRATIONS_DIR = REPO_ROOT / "src" / "synaisthesis" / "storage" / "migrations"

FIXED_CLAIM_LEAN = """theorem add_zero (n : Nat) : n + 0 = n := by
  simp
"""


def _fresh_database(tmp_path: Path):
    db_url = f"sqlite:///{tmp_path / 'real-council.db'}"
    cfg = Config()
    cfg.set_main_option("script_location", str(MIGRATIONS_DIR))
    cfg.set_main_option("sqlalchemy.url", db_url)
    command.upgrade(cfg, "head")
    _, session_factory = init_database(db_url)
    return session_factory


def _start_run(session_factory, artifact_root: Path):
    with session_factory() as session:
        run = create_council_run(
            session,
            project_id="p-1",
            claim_contract_id="cc-1",
            configured_rounds=2,
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


def _events(session_factory, run_id: str):
    from sqlalchemy import select

    with session_factory() as session:
        return (
            session.execute(
                select(DomainEventRecord).where(DomainEventRecord.aggregate_id == run_id)
            )
            .scalars()
            .all()
        )


def test_real_council_vertical_slice_chain(tmp_path):
    session_factory = _fresh_database(tmp_path)
    artifact_root = tmp_path / "artifacts"
    _start_run(session_factory, artifact_root)

    # 1. oppose track deterministically finds a counterexample -> repair
    with session_factory() as session:
        repair = council_repair_node(
            session,
            project_id="p-1",
            run_id="run-1",
            repaired_claim="∀ n : Nat, n + 0 = n",
            repair_rationale="反例 n=1 表明原假设过强，收窄对象域",
            artifact_root=artifact_root,
        )
        session.commit()
    assert repair["repaired_claim"].startswith("∀ n : Nat")

    # 2. semantic gate: F1 repair approved by the real user
    with session_factory() as session:
        gate = council_semantic_gate_node(
            session,
            project_id="p-1",
            run_id="run-1",
            delta=SemanticDelta.F1_PRESENTATIONAL_ONLY,
            actor=ProvenanceType.USER_DECISION,
            user_event_id="uev-semantic",
            at=NOW,
            artifact_root=artifact_root,
        )
        session.commit()
    assert gate["decision"] == "APPROVE"

    # 3. verification: REAL Lean proves the repaired claim
    with session_factory() as session:
        result = council_verification_node(
            session,
            project_id="p-1",
            run_id="run-1",
            lean_source=FIXED_CLAIM_LEAN,
            artifact_root=artifact_root,
        )
        session.commit()
    assert result.exit_code == 0
    assert result.receipt_hash

    # 4. user confirmation closes the slice with the evidence receipt bound
    with session_factory() as session:
        bundle = council_confirm_node(
            session,
            project_id="p-1",
            run_id="run-1",
            claim_id="cc-1",
            actor=ProvenanceType.USER_DECISION,
            user_event_id="uev-confirm",
            at=NOW,
            evidence_receipt_hash=result.receipt_hash or "",
            artifact_root=artifact_root,
        )
        session.commit()
    assert bundle["evidence_receipt_hash"] == result.receipt_hash

    event_types = [event.event_type for event in _events(session_factory, "run-1")]
    assert event_types == [
        "CouncilRunCreated",
        "CouncilRunStarted",
        "CouncilRepairRecorded",
        "CouncilSemanticGateResolved",
        "CouncilEvidenceRecorded",
        "CouncilSliceConfirmed",
    ]


def test_semantic_gate_rejects_semantic_drift(tmp_path):
    session_factory = _fresh_database(tmp_path)
    artifact_root = tmp_path / "artifacts"
    _start_run(session_factory, artifact_root)
    with session_factory() as session, pytest.raises(DomainError) as exc_info:
        council_semantic_gate(
            session,
            project_id="p-1",
            run_id="run-1",
            delta=SemanticDelta.F4_SEMANTIC_DRIFT,
            actor=ProvenanceType.USER_DECISION,
            user_event_id="uev-bad",
            at=NOW,
            artifact_root=artifact_root,
        )
    assert exc_info.value.error_code == "SEMANTIC_DELTA_REJECTED"


def test_confirm_requires_real_user_and_receipt(tmp_path):
    session_factory = _fresh_database(tmp_path)
    artifact_root = tmp_path / "artifacts"
    _start_run(session_factory, artifact_root)
    with session_factory() as session, pytest.raises(DomainError) as exc_info:
        council_confirm_and_bundle(
            session,
            project_id="p-1",
            run_id="run-1",
            claim_id="cc-1",
            actor=ProvenanceType.ASSISTANT_PROPOSAL,
            user_event_id="uev-bad",
            at=NOW,
            evidence_receipt_hash="h" * 64,
            artifact_root=artifact_root,
        )
    assert exc_info.value.error_code == "CONFIRMATION_REQUIRES_USER_EVENT"
    with session_factory() as session, pytest.raises(DomainError) as exc_info:
        council_confirm_and_bundle(
            session,
            project_id="p-1",
            run_id="run-1",
            claim_id="cc-1",
            actor=ProvenanceType.USER_DECISION,
            user_event_id="uev-bad",
            at=NOW,
            evidence_receipt_hash="",
            artifact_root=artifact_root,
        )
    assert exc_info.value.error_code == "EVIDENCE_RECEIPT_REQUIRED"


def test_regression_node_exits_on_statement_change(tmp_path):
    from synaisthesis.verifiers.lean.adapter import statement_hash_of_source

    _ = tmp_path  # no database needed for the pure guard
    expected = statement_hash_of_source(FIXED_CLAIM_LEAN)
    council_regression_node(current_source=FIXED_CLAIM_LEAN, expected_statement_hash=expected)
    changed = FIXED_CLAIM_LEAN.replace("n + 0 = n", "n + 1 = n")
    with pytest.raises(DomainError) as exc_info:
        council_regression_node(current_source=changed, expected_statement_hash=expected)
    assert exc_info.value.error_code == "PROOF_LOOP_STATEMENT_CHANGED"
