"""Codex delegation service (blueprint 19 §5 M11).

Delegates one work unit to an isolated git worktree, enforces controlled
files, captures a real diff and persists an execution receipt.  The worker
never touches the main workspace; the adapter re-verifies the receipt against
the actual diff hash before anything becomes evidence.
"""

from __future__ import annotations

import uuid
from pathlib import Path
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from synaisthesis.domain.errors import DomainError
from synaisthesis.domain.event import DomainEvent, sha256_hex
from synaisthesis.integrations.codex.worker import (
    WorkerExecutionReceipt,
    WorktreeHandle,
    create_isolated_worktree,
    remove_worktree,
    run_worker_command,
    validate_controlled_files,
    verify_worker_receipt,
    worktree_diff,
)
from synaisthesis.storage.repositories.event_repository import (
    DomainEventRecord,
    append_domain_event,
)

CODEX_DELEGATION_AGGREGATE_TYPE = "CodexDelegation"

EVENT_CODEX_DELEGATION_STARTED = "CodexDelegationStarted"
EVENT_CODEX_DELEGATION_RECEIPT = "CodexDelegationReceiptRecorded"


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


def _persist_delegation_event(
    session: Session,
    *,
    event_type: str,
    delegation_id: str,
    payload: dict[str, Any],
    project_id: str,
    artifact_root: Path,
) -> None:
    stream = _event_stream(session, CODEX_DELEGATION_AGGREGATE_TYPE, delegation_id)
    event = DomainEvent(
        aggregate_type=CODEX_DELEGATION_AGGREGATE_TYPE,
        aggregate_id=delegation_id,
        event_type=event_type,
        payload=payload,
        sequence=len(stream) + 1,
    )
    append_domain_event(session, event, project_id=project_id, artifact_root=artifact_root)


def delegate_work_unit(
    session: Session,
    *,
    project_id: str,
    repo_dir: Path,
    base_ref: str,
    allowed_files: tuple[str, ...],
    forbidden_files: tuple[str, ...],
    command: tuple[str, ...],
    artifact_root: Path,
    delegation_id: str | None = None,
    timeout_seconds: int = 120,
) -> tuple[WorktreeHandle, WorkerExecutionReceipt]:
    """Delegate one work unit to an isolated worktree (M11).

    The worktree lives beside the main repo and is removed after capture; the
    main workspace is never writable by the worker.
    """
    delegation_id = delegation_id or f"cd-{uuid.uuid4().hex[:12]}"
    handle = create_isolated_worktree(repo_dir=repo_dir, base_ref=base_ref)
    _persist_delegation_event(
        session,
        event_type=EVENT_CODEX_DELEGATION_STARTED,
        delegation_id=delegation_id,
        payload={"handle": handle.to_event_payload(), "command": list(command)},
        project_id=project_id,
        artifact_root=artifact_root,
    )
    receipt = run_worker_command(handle=handle, command=command, timeout_seconds=timeout_seconds)
    diff = worktree_diff(repo_dir=repo_dir, base_ref=base_ref, branch=handle.branch)
    diff_sha256 = sha256_hex({"diff": diff})
    receipt = WorkerExecutionReceipt(
        receipt_id=receipt.receipt_id,
        delegation_id=delegation_id,
        branch=receipt.branch,
        worktree_path=receipt.worktree_path,
        command=receipt.command,
        exit_code=receipt.exit_code,
        stdout=receipt.stdout,
        stderr=receipt.stderr,
        elapsed_ms=receipt.elapsed_ms,
        diff_sha256=diff_sha256,
        environment=receipt.environment,
    )
    blockers = validate_controlled_files(
        repo_dir=repo_dir,
        branch=handle.branch,
        base_ref=base_ref,
        worktree_path=Path(handle.worktree_path),
        allowed_files=allowed_files,
        forbidden_files=forbidden_files,
    )
    _persist_delegation_event(
        session,
        event_type=EVENT_CODEX_DELEGATION_RECEIPT,
        delegation_id=delegation_id,
        payload={
            "receipt": {
                "receipt_id": receipt.receipt_id,
                "exit_code": receipt.exit_code,
                "diff_sha256": diff_sha256,
                "receipt_hash": receipt.receipt_hash,
                "controlled_file_blockers": list(blockers),
            }
        },
        project_id=project_id,
        artifact_root=artifact_root,
    )
    remove_worktree(repo_dir=repo_dir, handle=handle)
    if blockers:
        raise DomainError(
            "CODEX_WORKER_VIOLATION: " + "; ".join(blockers),
            error_code="CODEX_WORKER_VIOLATION",
        )
    return handle, receipt


def verify_delegation_receipt(
    receipt: WorkerExecutionReceipt,
    *,
    expected_diff_sha256: str,
) -> tuple[str, ...]:
    """Adapter re-verification: the receipt must bind the real diff (M11)."""
    return verify_worker_receipt(receipt=receipt, expected_diff_sha256=expected_diff_sha256)


__all__ = [
    "CODEX_DELEGATION_AGGREGATE_TYPE",
    "EVENT_CODEX_DELEGATION_RECEIPT",
    "EVENT_CODEX_DELEGATION_STARTED",
    "delegate_work_unit",
    "verify_delegation_receipt",
]
