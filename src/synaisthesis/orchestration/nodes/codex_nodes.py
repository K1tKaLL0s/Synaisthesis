"""Codex outbound orchestration nodes (blueprint 19 §5 M11)."""

from __future__ import annotations

from pathlib import Path

from sqlalchemy.orm import Session

from synaisthesis.application.codex_delegation_service import (
    delegate_work_unit,
    verify_delegation_receipt,
)
from synaisthesis.integrations.codex.worker import WorkerExecutionReceipt


def codex_delegate_node(
    session: Session,
    *,
    project_id: str,
    repo_dir: Path,
    base_ref: str,
    allowed_files: tuple[str, ...],
    forbidden_files: tuple[str, ...],
    command: tuple[str, ...],
    artifact_root: Path,
) -> tuple[object, WorkerExecutionReceipt]:
    """Delegate a work unit through the enforced service path (M11)."""
    return delegate_work_unit(
        session,
        project_id=project_id,
        repo_dir=repo_dir,
        base_ref=base_ref,
        allowed_files=allowed_files,
        forbidden_files=forbidden_files,
        command=command,
        artifact_root=artifact_root,
    )


def codex_receive_node(
    receipt: WorkerExecutionReceipt,
    *,
    expected_diff_sha256: str,
) -> tuple[str, ...]:
    """Adapter re-verification node: no self-claimed tool PASS (M11)."""
    return verify_delegation_receipt(receipt=receipt, expected_diff_sha256=expected_diff_sha256)


__all__ = ["codex_delegate_node", "codex_receive_node"]
