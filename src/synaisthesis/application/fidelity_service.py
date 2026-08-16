"""Command Gateway application service for the Codex Instruction Fidelity Layer (05A, M0.5).

The gateway is the only mutation path: every mutation is registered against an
immutable InstructionCapsule, authorized by a signed InstructionToken, graded for
instruction drift, then prepared and committed with optimistic state-version
concurrency and idempotency. Persistence reuses the M1 event-sourced pattern:
ordered DomainEvents whose canonical JSON payloads live in content-addressed
artifacts, so raw instruction text and receipts are always re-verifiable.
"""

from __future__ import annotations

import json
import uuid
from collections.abc import Callable
from dataclasses import dataclass, field, replace
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from synaisthesis.domain.errors import ConflictError, DomainError
from synaisthesis.domain.event import DomainEvent
from synaisthesis.fidelity.command_gateway import (
    MutationRequest,
    evaluate_mutation_request,
)
from synaisthesis.fidelity.command_receipt import (
    CommandReceipt,
    CommandReceiptStatus,
    command_receipt_from_payload,
)
from synaisthesis.fidelity.context_manifest import ContextManifest
from synaisthesis.fidelity.instruction_capsule import (
    InstructionCapsule,
    InstructionStatus,
    instruction_capsule_from_payload,
    raw_user_text_sha256,
)
from synaisthesis.fidelity.instruction_delta import (
    CommandProposal,
    InstructionDelta,
    PlatformInterpretation,
)
from synaisthesis.fidelity.instruction_token import (
    InstructionToken,
    OperationClass,
    sign_instruction_token,
)
from synaisthesis.fidelity.prepare_commit import (
    PreparedCommand,
    PreparedCommandStatus,
    prepared_command_from_payload,
    prepared_command_requires_confirmation,
    validate_prepared_for_commit,
)
from synaisthesis.storage.artifact_store import ArtifactRecord
from synaisthesis.storage.hashing import verify_artifact_hash
from synaisthesis.storage.repositories.event_repository import (
    DomainEventRecord,
    append_domain_event,
)

INSTRUCTION_AGGREGATE_TYPE = "Instruction"
EVENT_INSTRUCTION_CAPTURED = "InstructionCaptured"
EVENT_INSTRUCTION_SUPERSEDED = "InstructionSuperseded"

PREPARED_COMMAND_AGGREGATE_TYPE = "PreparedCommand"
EVENT_COMMAND_PREPARED = "CommandPrepared"
EVENT_PREPARED_COMMAND_RESOLVED = "PreparedCommandResolved"

COMMAND_AGGREGATE_TYPE = "Command"
EVENT_COMMAND_COMMITTED = "CommandCommitted"

SIGNER_KEY_ID = "syn-fidelity-hmac-v1"


@dataclass(frozen=True, slots=True)
class FidelityConfig:
    """Runtime configuration for the Command Gateway."""

    signing_key: bytes
    token_ttl_seconds: int = 300
    prepared_command_ttl_seconds: int = 600
    require_context_manifest_for_mutation: bool = True
    now_fn: Callable[[], datetime] = field(default=lambda: datetime.now(UTC))


def _verified_payload(
    session: Session, record: DomainEventRecord, artifact_root: Path
) -> dict[str, Any]:
    """Read and verify a payload artifact; fail closed when it cannot be trusted."""
    if record.event_payload_artifact_id is None:
        raise DomainError(
            f"event {record.id} has no payload artifact; state unrecoverable",
            error_code="ARTIFACT_HASH_MISMATCH",
        )
    artifact = session.get(ArtifactRecord, record.event_payload_artifact_id)
    if artifact is None:
        raise DomainError(
            f"payload artifact {record.event_payload_artifact_id} of event "
            f"{record.id} is missing; state unrecoverable",
            error_code="ARTIFACT_HASH_MISMATCH",
        )
    path = artifact_root / artifact.relative_path
    if not verify_artifact_hash(path, artifact.sha256):
        raise DomainError(
            f"payload artifact of event {record.id} is missing or tampered; state unrecoverable",
            error_code="ARTIFACT_HASH_MISMATCH",
        )
    return json.loads(path.read_text(encoding="utf-8"))


def _event_stream(
    session: Session, aggregate_type: str, aggregate_id: str
) -> list[DomainEventRecord]:
    return list(
        session.execute(
            select(DomainEventRecord)
            .where(
                DomainEventRecord.aggregate_type == aggregate_type,
                DomainEventRecord.aggregate_id == aggregate_id,
            )
            .order_by(DomainEventRecord.id)
        )
        .scalars()
        .all()
    )


def _next_sequence(session: Session, aggregate_type: str, aggregate_id: str) -> int:
    return (
        session.execute(
            select(func.count(DomainEventRecord.id)).where(
                DomainEventRecord.aggregate_type == aggregate_type,
                DomainEventRecord.aggregate_id == aggregate_id,
            )
        ).scalar_one()
        + 1
    )


def _aggregate_project_id(session: Session, aggregate_type: str, aggregate_id: str) -> str:
    record = (
        session.execute(
            select(DomainEventRecord)
            .where(
                DomainEventRecord.aggregate_type == aggregate_type,
                DomainEventRecord.aggregate_id == aggregate_id,
            )
            .order_by(DomainEventRecord.id)
        )
        .scalars()
        .first()
    )
    if record is None:
        raise DomainError(
            f"aggregate {aggregate_type}:{aggregate_id!r} has no events",
            error_code="PROJECT_NOT_FOUND",
        )
    return str(record.project_id) if record.project_id is not None else ""


# ---------------------------------------------------------------------------
# InstructionCapsule
# ---------------------------------------------------------------------------


def register_instruction_capsule(
    session: Session,
    capsule: InstructionCapsule,
    *,
    project_id: str,
    artifact_root: Path,
) -> InstructionCapsule:
    """Persist an immutable InstructionCapsule; idempotent for repeated Hook events.

    The raw user text and its re-computable SHA-256 are stored in the event
    payload artifact; a capsule whose hash does not cover the text already failed
    closed in its constructor.
    """
    existing = _event_stream(session, INSTRUCTION_AGGREGATE_TYPE, capsule.instruction_id)
    if existing:
        return load_instruction_capsule(
            session, capsule.instruction_id, artifact_root=artifact_root
        )
    event = DomainEvent(
        aggregate_type=INSTRUCTION_AGGREGATE_TYPE,
        aggregate_id=capsule.instruction_id,
        event_type=EVENT_INSTRUCTION_CAPTURED,
        payload=capsule.to_event_payload(),
        sequence=1,
    )
    append_domain_event(session, event, project_id=project_id, artifact_root=artifact_root)
    return capsule


def load_instruction_capsule(
    session: Session, instruction_id: str, *, artifact_root: Path
) -> InstructionCapsule:
    """Replay an InstructionCapsule from its hash-verified event payload."""
    records = _event_stream(session, INSTRUCTION_AGGREGATE_TYPE, instruction_id)
    if not records:
        raise DomainError(
            f"instruction {instruction_id!r} has no events",
            error_code="PROJECT_NOT_FOUND",
        )
    capsule: InstructionCapsule | None = None
    for record in records:
        payload = _verified_payload(session, record, artifact_root)
        if record.event_type == EVENT_INSTRUCTION_CAPTURED:
            capsule = instruction_capsule_from_payload(payload)
        elif record.event_type == EVENT_INSTRUCTION_SUPERSEDED:
            if capsule is None:
                raise DomainError(
                    f"event stream of {instruction_id!r} starts with {record.event_type!r}; "
                    "state unrecoverable",
                    error_code="PROJECT_STATE_UNRECOVERABLE",
                )
            capsule = replace(capsule, status=InstructionStatus.SUPERSEDED)
        else:
            raise DomainError(
                f"unknown event type {record.event_type!r} for {instruction_id!r}; "
                "state unrecoverable",
                error_code="PROJECT_STATE_UNRECOVERABLE",
            )
    if capsule is None:
        raise DomainError(
            f"state of instruction {instruction_id!r} is unrecoverable",
            error_code="PROJECT_STATE_UNRECOVERABLE",
        )
    return capsule


def supersede_instruction(
    session: Session,
    new_capsule: InstructionCapsule,
    *,
    project_id: str,
    artifact_root: Path,
) -> InstructionCapsule:
    """Register a corrective instruction and invalidate prior PreparedCommands (05A, section 14)."""
    if not new_capsule.supersedes_instruction_id:
        raise DomainError(
            "supersede requires supersedes_instruction_id on the new capsule",
            error_code="INSTRUCTION_CAPSULE_INVALID",
        )
    old_id = new_capsule.supersedes_instruction_id
    load_instruction_capsule(session, old_id, artifact_root=artifact_root)  # raises if missing
    register_instruction_capsule(
        session, new_capsule, project_id=project_id, artifact_root=artifact_root
    )
    supersede_event = DomainEvent(
        aggregate_type=INSTRUCTION_AGGREGATE_TYPE,
        aggregate_id=old_id,
        event_type=EVENT_INSTRUCTION_SUPERSEDED,
        payload={"superseded_by_instruction_id": new_capsule.instruction_id},
        sequence=_next_sequence(session, INSTRUCTION_AGGREGATE_TYPE, old_id),
    )
    append_domain_event(
        session, supersede_event, project_id=project_id, artifact_root=artifact_root
    )
    for prepared in _prepared_commands_for_instruction(session, old_id, artifact_root):
        if prepared.status is PreparedCommandStatus.PREPARED:
            _resolve_prepared(session, prepared, "SUPERSEDED", project_id, artifact_root)
    return new_capsule


# ---------------------------------------------------------------------------
# InstructionToken
# ---------------------------------------------------------------------------


def issue_instruction_token(
    config: FidelityConfig,
    capsule: InstructionCapsule,
    *,
    project_id: str,
    state_version: int,
    operation_class: OperationClass,
    nonce: str | None = None,
) -> InstructionToken:
    """Issue a signed short-lived token bound to one instruction and state version."""
    assert capsule.raw_user_text_hash is not None
    now = config.now_fn()
    token = InstructionToken(
        instruction_id=capsule.instruction_id,
        session_id=capsule.session_id,
        turn_id=capsule.turn_id,
        project_id=project_id,
        raw_user_text_hash=capsule.raw_user_text_hash,
        allowed_operation_class=operation_class,
        issued_at=now,
        expires_at=now + timedelta(seconds=config.token_ttl_seconds),
        nonce=nonce or uuid.uuid4().hex,
        state_version=state_version,
        signer_key_id=SIGNER_KEY_ID,
    )
    return sign_instruction_token(token, signing_key=config.signing_key)


# ---------------------------------------------------------------------------
# PreparedCommand
# ---------------------------------------------------------------------------


def _prepared_commands_for_instruction(
    session: Session, instruction_id: str, artifact_root: Path
) -> list[PreparedCommand]:
    records = (
        session.execute(
            select(DomainEventRecord)
            .where(
                DomainEventRecord.aggregate_type == PREPARED_COMMAND_AGGREGATE_TYPE,
                DomainEventRecord.event_type == EVENT_COMMAND_PREPARED,
            )
            .order_by(DomainEventRecord.id)
        )
        .scalars()
        .all()
    )
    prepared: list[PreparedCommand] = []
    for record in records:
        payload = _verified_payload(session, record, artifact_root)
        if payload.get("instruction_id") == instruction_id:
            prepared.append(
                load_prepared_command(
                    session, str(payload["prepared_command_id"]), artifact_root=artifact_root
                )
            )
    return prepared


def _prepared_by_idempotency_key(
    session: Session, project_id: str, idempotency_key: str, artifact_root: Path
) -> PreparedCommand | None:
    records = (
        session.execute(
            select(DomainEventRecord)
            .where(
                DomainEventRecord.project_id == project_id,
                DomainEventRecord.aggregate_type == PREPARED_COMMAND_AGGREGATE_TYPE,
                DomainEventRecord.event_type == EVENT_COMMAND_PREPARED,
            )
            .order_by(DomainEventRecord.id)
        )
        .scalars()
        .all()
    )
    for record in records:
        payload = _verified_payload(session, record, artifact_root)
        if payload.get("idempotency_key") == idempotency_key:
            return load_prepared_command(
                session, str(payload["prepared_command_id"]), artifact_root=artifact_root
            )
    return None


def load_prepared_command(
    session: Session, prepared_command_id: str, *, artifact_root: Path
) -> PreparedCommand:
    """Replay a PreparedCommand and its resolved status from verified events."""
    records = _event_stream(session, PREPARED_COMMAND_AGGREGATE_TYPE, prepared_command_id)
    if not records:
        raise DomainError(
            f"prepared command {prepared_command_id!r} has no events",
            error_code="PROJECT_NOT_FOUND",
        )
    prepared: PreparedCommand | None = None
    for record in records:
        payload = _verified_payload(session, record, artifact_root)
        if record.event_type == EVENT_COMMAND_PREPARED:
            prepared = prepared_command_from_payload(payload)
        elif record.event_type == EVENT_PREPARED_COMMAND_RESOLVED:
            if prepared is None:
                raise DomainError(
                    f"event stream of {prepared_command_id!r} starts with "
                    f"{record.event_type!r}; state unrecoverable",
                    error_code="PROJECT_STATE_UNRECOVERABLE",
                )
            resolution = PreparedCommandStatus.parse(
                payload.get("resolution", PreparedCommandStatus.CANCELLED.value),
                field="resolution",
            )
            prepared = replace(prepared, status=resolution)
        else:
            raise DomainError(
                f"unknown event type {record.event_type!r} for {prepared_command_id!r}; "
                "state unrecoverable",
                error_code="PROJECT_STATE_UNRECOVERABLE",
            )
    if prepared is None:
        raise DomainError(
            f"state of prepared command {prepared_command_id!r} is unrecoverable",
            error_code="PROJECT_STATE_UNRECOVERABLE",
        )
    return prepared


def _resolve_prepared(
    session: Session,
    prepared: PreparedCommand,
    resolution: str,
    project_id: str,
    artifact_root: Path,
) -> PreparedCommand:
    event = DomainEvent(
        aggregate_type=PREPARED_COMMAND_AGGREGATE_TYPE,
        aggregate_id=prepared.prepared_command_id,
        event_type=EVENT_PREPARED_COMMAND_RESOLVED,
        payload={"resolution": resolution, "resolved_at": datetime.now(UTC).isoformat()},
        sequence=_next_sequence(
            session, PREPARED_COMMAND_AGGREGATE_TYPE, prepared.prepared_command_id
        ),
    )
    append_domain_event(session, event, project_id=project_id, artifact_root=artifact_root)
    return replace(prepared, status=PreparedCommandStatus.parse(resolution))


# ---------------------------------------------------------------------------
# CommandReceipt
# ---------------------------------------------------------------------------


def _committed_receipt_by_idempotency_key(
    session: Session, project_id: str, idempotency_key: str, artifact_root: Path
) -> CommandReceipt | None:
    records = (
        session.execute(
            select(DomainEventRecord)
            .where(
                DomainEventRecord.project_id == project_id,
                DomainEventRecord.aggregate_type == COMMAND_AGGREGATE_TYPE,
                DomainEventRecord.event_type == EVENT_COMMAND_COMMITTED,
            )
            .order_by(DomainEventRecord.id)
        )
        .scalars()
        .all()
    )
    for record in records:
        payload = _verified_payload(session, record, artifact_root)
        if payload.get("idempotency_key") == idempotency_key:
            return command_receipt_from_payload(payload)
    return None


def load_command_receipt(
    session: Session, command_id: str, *, artifact_root: Path
) -> CommandReceipt:
    """Replay a CommandReceipt from the CommandCommitted event."""
    records = _event_stream(session, COMMAND_AGGREGATE_TYPE, command_id)
    for record in records:
        if record.event_type == EVENT_COMMAND_COMMITTED:
            payload = _verified_payload(session, record, artifact_root)
            return command_receipt_from_payload(payload)
    raise DomainError(
        f"command {command_id!r} has no committed receipt",
        error_code="PROJECT_NOT_FOUND",
    )


# ---------------------------------------------------------------------------
# State version
# ---------------------------------------------------------------------------


def current_state_version(session: Session, project_id: str) -> int:
    """Return the project's committed-mutation count (optimistic concurrency version)."""
    return int(
        session.execute(
            select(func.count(DomainEventRecord.id)).where(
                DomainEventRecord.project_id == project_id,
                DomainEventRecord.aggregate_type == COMMAND_AGGREGATE_TYPE,
                DomainEventRecord.event_type == EVENT_COMMAND_COMMITTED,
            )
        ).scalar_one()
    )


# ---------------------------------------------------------------------------
# Prepare -> Commit
# ---------------------------------------------------------------------------


def _action_summary(command: CommandProposal) -> dict[str, Any]:
    return {
        "operation": command.operation,
        "target_project": command.target_project,
        "target_claim": command.target_claim,
        "target_revision": command.target_revision,
        "loop_rounds": command.loop_rounds,
        "read_only": command.read_only,
    }


def _target_dict(command: CommandProposal, project_id: str) -> dict[str, Any]:
    return {
        "project_id": project_id,
        "claim_id": command.target_claim,
        "revision_id": command.target_revision,
    }


def prepare_command(
    session: Session,
    config: FidelityConfig,
    *,
    instruction_token: InstructionToken | None,
    instruction_id: str,
    project_id: str,
    command_proposal: CommandProposal,
    platform_interpretation: PlatformInterpretation,
    context_manifest: ContextManifest | None,
    expected_state_version: int,
    idempotency_key: str,
    operation_class: OperationClass,
    artifact_root: Path,
    command_id: str | None = None,
    prepared_command_id: str | None = None,
) -> PreparedCommand:
    """Prepare a mutation after every fail-closed gateway check passes.

    The prepared command binds the instruction, the expected state version and an
    idempotency key; identical re-prepares return the existing prepared command.
    """
    capsule = load_instruction_capsule(session, instruction_id, artifact_root=artifact_root)
    now = config.now_fn()
    request = MutationRequest(
        instruction_token=instruction_token,
        instruction_id=instruction_id,
        project_id=project_id,
        command_proposal=command_proposal,
        platform_interpretation=platform_interpretation,
        expected_state_version=expected_state_version,
        idempotency_key=idempotency_key,
        context_manifest=context_manifest,
        operation_class=operation_class,
    )
    verdict = evaluate_mutation_request(
        request,
        capsule=capsule,
        signing_key=config.signing_key,
        current_state_version=current_state_version(session, project_id),
        now=now,
        require_context_manifest=config.require_context_manifest_for_mutation,
    )
    if not verdict.allowed:
        if verdict.error_code == "STALE_STATE":
            raise ConflictError(verdict.reason, trace_id=instruction_id)
        raise DomainError(verdict.reason, error_code=verdict.error_code or "FIDELITY_BLOCKED")

    assert instruction_token is not None
    if expected_state_version != instruction_token.state_version:
        raise ConflictError(
            f"expected_state_version={expected_state_version!r} does not match the "
            f"token state_version={instruction_token.state_version!r}",
            trace_id=instruction_id,
        )

    existing = _prepared_by_idempotency_key(session, project_id, idempotency_key, artifact_root)
    if existing is not None and existing.status is PreparedCommandStatus.PREPARED:
        return existing

    confirmation_required = prepared_command_requires_confirmation(
        operation_class=operation_class,
        inferred_default=(
            verdict.delta is not None
            and verdict.delta.grade is InstructionDelta.F2_INFERRED_DEFAULT
        ),
    )
    prepared = PreparedCommand(
        prepared_command_id=prepared_command_id or uuid.uuid4().hex,
        instruction_id=instruction_id,
        command_id=command_id or uuid.uuid4().hex,
        idempotency_key=idempotency_key,
        expected_state_version=expected_state_version,
        canonical_action_summary=_action_summary(command_proposal),
        preserved_constraints=command_proposal.prohibitions,
        intended_state_diff={"state_version_delta": 1},
        cost_permission_impact={
            "operation_class": operation_class.value,
            "allow_network": command_proposal.allow_network,
            "allow_execute_code": command_proposal.allow_execute_code,
        },
        unresolved_ambiguity=platform_interpretation.unresolved_references,
        confirmation_requirement=confirmation_required,
        confirmation_nonce=uuid.uuid4().hex,
        created_at=now,
        expires_at=now + timedelta(seconds=config.prepared_command_ttl_seconds),
    )
    event = DomainEvent(
        aggregate_type=PREPARED_COMMAND_AGGREGATE_TYPE,
        aggregate_id=prepared.prepared_command_id,
        event_type=EVENT_COMMAND_PREPARED,
        payload=prepared.to_event_payload(),
        sequence=1,
    )
    append_domain_event(session, event, project_id=project_id, artifact_root=artifact_root)
    return prepared


def commit_command(
    session: Session,
    config: FidelityConfig,
    *,
    prepared_command_id: str,
    confirmation_nonce: str,
    user_confirmation_text: str | None,
    expected_state_version: int,
    idempotency_key: str,
    artifact_root: Path,
) -> CommandReceipt:
    """Commit a prepared command exactly once.

    Confirmation is anti-forged (05A, section 17): there is no boolean ``confirmed``
    parameter; a real user confirmation text is required for high-risk commands and
    its nonce must match the prepared command. A stale state version returns
    STALE_STATE; a reused idempotency key returns the original receipt.
    """
    prepared = load_prepared_command(session, prepared_command_id, artifact_root=artifact_root)
    project_id = _aggregate_project_id(
        session, PREPARED_COMMAND_AGGREGATE_TYPE, prepared_command_id
    )

    # Idempotent replay: a retried mutation returns the original receipt without
    # re-executing (05A, section 15; acceptance scenario 5).
    existing = _committed_receipt_by_idempotency_key(
        session, project_id, idempotency_key, artifact_root
    )
    if existing is not None:
        return existing

    now = config.now_fn()
    issues = validate_prepared_for_commit(
        prepared,
        confirmation_nonce=confirmation_nonce,
        user_confirmation_text=user_confirmation_text,
        now=now,
    )
    if issues:
        raise DomainError("commit blocked: " + "; ".join(issues), error_code=issues[0])

    current = current_state_version(session, project_id)
    if (
        expected_state_version != current
        or expected_state_version != prepared.expected_state_version
    ):
        raise ConflictError(
            f"state changed between prepare and commit: expected {expected_state_version}, "
            f"current {current}",
            trace_id=prepared.command_id,
        )

    ending = current + 1
    summary = prepared.canonical_action_summary
    receipt = CommandReceipt(
        command_id=prepared.command_id,
        instruction_id=prepared.instruction_id,
        executed_operation=str(summary.get("operation", "")),
        target=_target_dict(
            CommandProposal(
                operation=str(summary.get("operation", "")),
                target_project=summary.get("target_project"),
                target_claim=summary.get("target_claim"),
                target_revision=summary.get("target_revision"),
                loop_rounds=summary.get("loop_rounds"),
                read_only=bool(summary.get("read_only", False)),
            ),
            project_id,
        ),
        starting_state_version=current,
        ending_state_version=ending,
        accepted_parameters={
            "idempotency_key": idempotency_key,
            "user_confirmation_hash": (
                raw_user_text_sha256(user_confirmation_text) if user_confirmation_text else None
            ),
        },
        rejected_parameters={},
        preserved_constraints=prepared.preserved_constraints,
        side_effects=(),
        evidence_ids=(),
        pending_gate_ids=(),
        cost_used={},
        status=CommandReceiptStatus.COMMITTED,
    )
    event = DomainEvent(
        aggregate_type=COMMAND_AGGREGATE_TYPE,
        aggregate_id=prepared.command_id,
        event_type=EVENT_COMMAND_COMMITTED,
        payload={**receipt.to_event_payload(), "idempotency_key": idempotency_key},
        sequence=ending,
    )
    append_domain_event(session, event, project_id=project_id, artifact_root=artifact_root)
    _resolve_prepared(session, prepared, "CONSUMED", project_id, artifact_root)
    return receipt


def cancel_prepared_command(
    session: Session, *, prepared_command_id: str, artifact_root: Path
) -> PreparedCommand:
    """Cancel a prepared command before commit (05A, section 18.2)."""
    prepared = load_prepared_command(session, prepared_command_id, artifact_root=artifact_root)
    if prepared.status is not PreparedCommandStatus.PREPARED:
        raise ConflictError(
            f"prepared command {prepared_command_id!r} is already {prepared.status.value}",
            trace_id=prepared.command_id,
        )
    project_id = _aggregate_project_id(
        session, PREPARED_COMMAND_AGGREGATE_TYPE, prepared_command_id
    )
    return _resolve_prepared(session, prepared, "CANCELLED", project_id, artifact_root)


__all__ = [
    "COMMAND_AGGREGATE_TYPE",
    "EVENT_COMMAND_COMMITTED",
    "EVENT_COMMAND_PREPARED",
    "EVENT_INSTRUCTION_CAPTURED",
    "EVENT_INSTRUCTION_SUPERSEDED",
    "EVENT_PREPARED_COMMAND_RESOLVED",
    "FidelityConfig",
    "INSTRUCTION_AGGREGATE_TYPE",
    "PREPARED_COMMAND_AGGREGATE_TYPE",
    "cancel_prepared_command",
    "commit_command",
    "current_state_version",
    "issue_instruction_token",
    "load_command_receipt",
    "load_instruction_capsule",
    "load_prepared_command",
    "prepare_command",
    "register_instruction_capsule",
    "supersede_instruction",
]
