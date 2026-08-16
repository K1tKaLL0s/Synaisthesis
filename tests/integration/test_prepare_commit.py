"""M0.5 integration tests for prepare -> commit, state version and idempotency (05A, 15-20).

These tests exercise the event-sourced Command Gateway end to end: instruction
capture, token issuance, two-phase commit, stale-state detection, idempotent
replay, user-confirmation anti-forgery, corrective supersede, and DisplayContract
build/audit.
"""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config

from synaisthesis.application.fidelity_service import (
    FidelityConfig,
    cancel_prepared_command,
    commit_command,
    current_state_version,
    issue_instruction_token,
    load_command_receipt,
    load_instruction_capsule,
    load_prepared_command,
    prepare_command,
    register_instruction_capsule,
    supersede_instruction,
)
from synaisthesis.domain.errors import ConflictError, DomainError
from synaisthesis.fidelity.command_receipt import CommandReceiptStatus
from synaisthesis.fidelity.context_manifest import ContextManifest
from synaisthesis.fidelity.display_contract import (
    DisplayContract,
    validate_displayed_message,
)
from synaisthesis.fidelity.instruction_capsule import InstructionCapsule
from synaisthesis.fidelity.instruction_delta import CommandProposal, PlatformInterpretation
from synaisthesis.fidelity.instruction_token import OperationClass
from synaisthesis.fidelity.prepare_commit import PreparedCommandStatus
from synaisthesis.storage.database import init_database

KEY = b"integration-signing-key"
NOW = datetime(2026, 8, 17, 2, 0, 0, tzinfo=UTC)
PROJECT = "p1"
REPO_ROOT = Path(__file__).resolve().parents[2]
MIGRATIONS_DIR = REPO_ROOT / "src" / "synaisthesis" / "storage" / "migrations"


def _fresh_database(tmp_path: Path):
    db_url = f"sqlite:///{tmp_path / 'fidelity.db'}"
    cfg = Config()
    cfg.set_main_option("script_location", str(MIGRATIONS_DIR))
    cfg.set_main_option("sqlalchemy.url", db_url)
    command.upgrade(cfg, "head")
    _, session_factory = init_database(db_url)
    return session_factory


def _config() -> FidelityConfig:
    return FidelityConfig(signing_key=KEY, now_fn=lambda: NOW)


def _capsule(**overrides) -> InstructionCapsule:
    params = {
        "instruction_id": "i1",
        "session_id": "s1",
        "turn_id": "t1",
        "raw_user_text": "运行 10 轮，不得修改核心语义",
        "submitted_at": NOW,
    }
    params.update(overrides)
    return InstructionCapsule(**params)


def _proposal(**overrides) -> CommandProposal:
    params = {
        "operation": "research_start_council",
        "target_project": PROJECT,
        "target_claim": "c1",
        "loop_rounds": 10,
        "read_only": False,
        "prohibitions": ("不得修改核心语义",),
    }
    params.update(overrides)
    return CommandProposal(**params)


def _interpretation(**overrides) -> PlatformInterpretation:
    params = {
        "operation": "research_start_council",
        "target_project": PROJECT,
        "target_claim": "c1",
        "loop_rounds": 10,
        "read_only": False,
        "prohibitions": ("不得修改核心语义",),
    }
    params.update(overrides)
    return PlatformInterpretation(**params)


def _register(
    session,
    artifact_root: Path,
    *,
    instruction_id: str = "i1",
    raw_user_text: str = "运行 10 轮，不得修改核心语义",
) -> InstructionCapsule:
    capsule = _capsule(instruction_id=instruction_id, raw_user_text=raw_user_text)
    register_instruction_capsule(session, capsule, project_id=PROJECT, artifact_root=artifact_root)
    session.commit()
    return capsule


def _prepare(
    session,
    artifact_root: Path,
    *,
    capsule: InstructionCapsule | None = None,
    idempotency_key: str = "k1",
    expected_state_version: int = 0,
    loop_rounds: int = 10,
):
    if capsule is None:
        capsule = _register(session, artifact_root)
    config = _config()
    token = issue_instruction_token(
        config,
        capsule,
        project_id=PROJECT,
        state_version=expected_state_version,
        operation_class=OperationClass.HIGH_RISK_MUTATION,
    )
    manifest = ContextManifest(context_manifest_id="m1")
    prepared = prepare_command(
        session,
        config,
        instruction_token=token,
        instruction_id=capsule.instruction_id,
        project_id=PROJECT,
        command_proposal=_proposal(loop_rounds=loop_rounds),
        platform_interpretation=_interpretation(loop_rounds=loop_rounds),
        context_manifest=manifest,
        expected_state_version=expected_state_version,
        idempotency_key=idempotency_key,
        operation_class=OperationClass.HIGH_RISK_MUTATION,
        artifact_root=artifact_root,
    )
    session.commit()
    return capsule, prepared


def _commit(
    session, artifact_root: Path, *, prepared, idempotency_key: str, expected_state_version: int
):
    return commit_command(
        session,
        _config(),
        prepared_command_id=prepared.prepared_command_id,
        confirmation_nonce=prepared.confirmation_nonce,
        user_confirmation_text="确认执行 10 轮",
        expected_state_version=expected_state_version,
        idempotency_key=idempotency_key,
        artifact_root=artifact_root,
    )


# ---------------------------------------------------------------------------
# End-to-end prepare -> commit
# ---------------------------------------------------------------------------


def test_prepare_commit_end_to_end(tmp_path):
    session_factory = _fresh_database(tmp_path)
    artifact_root = tmp_path / "artifacts"
    with session_factory() as session:
        capsule, prepared = _prepare(session, artifact_root)
        assert prepared.status is PreparedCommandStatus.PREPARED
        assert prepared.confirmation_requirement is True

        receipt = _commit(
            session,
            artifact_root,
            prepared=prepared,
            idempotency_key="k1",
            expected_state_version=0,
        )
        session.commit()
        assert receipt.status is CommandReceiptStatus.COMMITTED
        assert receipt.starting_state_version == 0
        assert receipt.ending_state_version == 1
        assert current_state_version(session, PROJECT) == 1

        loaded = load_command_receipt(session, receipt.command_id, artifact_root=artifact_root)
        assert loaded.receipt_hash == receipt.receipt_hash
        assert loaded.to_event_payload() == receipt.to_event_payload()

        consumed = load_prepared_command(
            session, prepared.prepared_command_id, artifact_root=artifact_root
        )
        assert consumed.status is PreparedCommandStatus.CONSUMED


def test_idempotent_retry_returns_same_receipt(tmp_path):
    session_factory = _fresh_database(tmp_path)
    artifact_root = tmp_path / "artifacts"
    with session_factory() as session:
        capsule, prepared = _prepare(session, artifact_root, idempotency_key="k1")
        first = _commit(
            session,
            artifact_root,
            prepared=prepared,
            idempotency_key="k1",
            expected_state_version=0,
        )
        session.commit()

        # A retried identical request (same idempotency key) returns the original
        # receipt without executing again.
        retry = commit_command(
            session,
            _config(),
            prepared_command_id=prepared.prepared_command_id,
            confirmation_nonce=prepared.confirmation_nonce,
            user_confirmation_text="确认执行 10 轮",
            expected_state_version=0,
            idempotency_key="k1",
            artifact_root=artifact_root,
        )
        assert retry.command_id == first.command_id
        assert retry.receipt_hash == first.receipt_hash
        assert current_state_version(session, PROJECT) == 1
        assert capsule.instruction_id == "i1"


def test_stale_state_between_prepare_and_commit(tmp_path):
    session_factory = _fresh_database(tmp_path)
    artifact_root = tmp_path / "artifacts"
    with session_factory() as session:
        capsule, first_prepared = _prepare(session, artifact_root, idempotency_key="k1")
        _commit(
            session,
            artifact_root,
            prepared=first_prepared,
            idempotency_key="k1",
            expected_state_version=0,
        )
        session.commit()

        # A second prepared command is created against state version 1...
        token = issue_instruction_token(
            _config(),
            capsule,
            project_id=PROJECT,
            state_version=1,
            operation_class=OperationClass.HIGH_RISK_MUTATION,
        )
        second_prepared = prepare_command(
            session,
            _config(),
            instruction_token=token,
            instruction_id=capsule.instruction_id,
            project_id=PROJECT,
            command_proposal=_proposal(),
            platform_interpretation=_interpretation(),
            context_manifest=ContextManifest(context_manifest_id="m2"),
            expected_state_version=1,
            idempotency_key="k2",
            operation_class=OperationClass.HIGH_RISK_MUTATION,
            artifact_root=artifact_root,
        )
        session.commit()

        # ...but the commit carries the stale expected version 0.
        with pytest.raises(ConflictError) as exc_info:
            _commit(
                session,
                artifact_root,
                prepared=second_prepared,
                idempotency_key="k2",
                expected_state_version=0,
            )
        assert exc_info.value.error_code == "CONFLICT"


def test_high_risk_commit_requires_user_confirmation_text(tmp_path):
    session_factory = _fresh_database(tmp_path)
    artifact_root = tmp_path / "artifacts"
    with session_factory() as session:
        _, prepared = _prepare(session, artifact_root)
        with pytest.raises(DomainError) as exc_info:
            commit_command(
                session,
                _config(),
                prepared_command_id=prepared.prepared_command_id,
                confirmation_nonce=prepared.confirmation_nonce,
                user_confirmation_text="",  # no real user confirmation; no boolean flag exists
                expected_state_version=0,
                idempotency_key="k1",
                artifact_root=artifact_root,
            )
        assert exc_info.value.error_code == "CONFIRMATION_REQUIRES_USER_EVENT"


def test_nonce_mismatch_rejects_commit(tmp_path):
    session_factory = _fresh_database(tmp_path)
    artifact_root = tmp_path / "artifacts"
    with session_factory() as session:
        _, prepared = _prepare(session, artifact_root)
        with pytest.raises(DomainError) as exc_info:
            commit_command(
                session,
                _config(),
                prepared_command_id=prepared.prepared_command_id,
                confirmation_nonce="wrong-nonce",
                user_confirmation_text="确认执行 10 轮",
                expected_state_version=0,
                idempotency_key="k1",
                artifact_root=artifact_root,
            )
        assert exc_info.value.error_code == "CONFIRMATION_NONCE_MISMATCH"


def test_user_correction_supersedes_prepared_command(tmp_path):
    session_factory = _fresh_database(tmp_path)
    artifact_root = tmp_path / "artifacts"
    with session_factory() as session:
        _, prepared = _prepare(session, artifact_root, idempotency_key="k1")
        correction = _capsule(
            instruction_id="i2",
            raw_user_text="上一条中的 10 轮改为 5 轮",
            supersedes_instruction_id="i1",
        )
        supersede_instruction(session, correction, project_id=PROJECT, artifact_root=artifact_root)
        session.commit()

        superseded = load_prepared_command(
            session, prepared.prepared_command_id, artifact_root=artifact_root
        )
        assert superseded.status is PreparedCommandStatus.SUPERSEDED

        with pytest.raises(DomainError) as exc_info:
            _commit(
                session,
                artifact_root,
                prepared=superseded,
                idempotency_key="k1",
                expected_state_version=0,
            )
        assert exc_info.value.error_code == "PREPARED_COMMAND_SUPERSEDED"

        old = load_instruction_capsule(session, "i1", artifact_root=artifact_root)
        assert old.status.value == "SUPERSEDED"


def test_cancel_prepared_command(tmp_path):
    session_factory = _fresh_database(tmp_path)
    artifact_root = tmp_path / "artifacts"
    with session_factory() as session:
        _, prepared = _prepare(session, artifact_root, idempotency_key="k1")
        cancelled = cancel_prepared_command(
            session, prepared_command_id=prepared.prepared_command_id, artifact_root=artifact_root
        )
        session.commit()
        assert cancelled.status is PreparedCommandStatus.CANCELLED
        with pytest.raises(ConflictError):
            cancel_prepared_command(
                session,
                prepared_command_id=prepared.prepared_command_id,
                artifact_root=artifact_root,
            )


# ---------------------------------------------------------------------------
# DisplayContract build/audit after a real commit
# ---------------------------------------------------------------------------


def test_display_contract_after_commit(tmp_path):
    session_factory = _fresh_database(tmp_path)
    artifact_root = tmp_path / "artifacts"
    with session_factory() as session:
        _, prepared = _prepare(session, artifact_root)
        receipt = _commit(
            session,
            artifact_root,
            prepared=prepared,
            idempotency_key="k1",
            expected_state_version=0,
        )
        session.commit()

        contract = DisplayContract(
            display_contract_id="dc1",
            receipt_id=receipt.command_id,
            exact_summary_block=f"已提交 {receipt.executed_operation}，状态 "
            f"{receipt.starting_state_version} -> {receipt.ending_state_version}",
            mandatory_statuses=("COUNCIL_RUNNING",),
            mandatory_warnings=("WARNING: UNDECIDED",),
            mandatory_next_action="等待用户确认下一轮",
            prohibited_claims=("已证明原创",),
            allowed_paraphrase_fields=("side_effects",),
        )
        faithful = (
            contract.exact_summary_block
            + "。COUNCIL_RUNNING。WARNING: UNDECIDED。等待用户确认下一轮。"
        )
        assert validate_displayed_message(faithful, contract) == ()
        assert validate_displayed_message("已证明原创。", contract) != ()
