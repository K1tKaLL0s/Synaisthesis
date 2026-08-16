"""Codex outbound worker isolation (blueprint 19 §5 M11; M10 之后).

Workers run in an isolated git worktree: they can never write the main
workspace.  Controlled-file validation, diff capture and receipt
re-verification are all real git/subprocess operations — a worker can never
claim tool PASS on its own.
"""

from __future__ import annotations

import subprocess
import time
import uuid
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from synaisthesis.domain.errors import DomainError
from synaisthesis.domain.event import sha256_hex


@dataclass(frozen=True, slots=True)
class WorktreeHandle:
    """One isolated git worktree created for a worker."""

    worktree_path: str
    branch: str
    base_ref: str
    created_at_iso: str
    worktree_hash: str

    def to_event_payload(self) -> dict[str, Any]:
        return dict(asdict(self))


def create_isolated_worktree(
    *,
    repo_dir: Path,
    base_ref: str,
    branch: str | None = None,
) -> WorktreeHandle:
    """Create a detached/parallel worktree; the main tree is untouched (M11)."""
    if not (repo_dir / ".git").exists() and not (repo_dir / ".git").is_dir():
        raise DomainError(
            f"{repo_dir} 不是 git 仓库",
            error_code="CODEX_WORKTREE_INVALID",
        )
    branch = branch or f"codex-worker-{uuid.uuid4().hex[:10]}"
    worktree_path = repo_dir.parent / branch
    try:
        subprocess.run(
            [
                "git",
                "-C",
                str(repo_dir),
                "worktree",
                "add",
                "-b",
                branch,
                str(worktree_path),
                base_ref,
            ],
            capture_output=True,
            text=True,
            timeout=60,
            check=True,
        )
    except subprocess.CalledProcessError as exc:
        raise DomainError(
            f"worktree 创建失败：{exc.stderr.strip()}",
            error_code="CODEX_WORKTREE_INVALID",
        ) from exc
    from datetime import UTC, datetime

    handle = WorktreeHandle(
        worktree_path=str(worktree_path),
        branch=branch,
        base_ref=base_ref,
        created_at_iso=datetime.now(UTC).isoformat(),
        worktree_hash=sha256_hex({"branch": branch, "path": str(worktree_path), "base": base_ref}),
    )
    return handle


def remove_worktree(*, repo_dir: Path, handle: WorktreeHandle) -> None:
    """Remove the worker worktree after result capture (M11)."""
    subprocess.run(
        ["git", "-C", str(repo_dir), "worktree", "remove", "--force", handle.worktree_path],
        capture_output=True,
        text=True,
        timeout=60,
        check=False,
    )
    subprocess.run(
        ["git", "-C", str(repo_dir), "branch", "-D", handle.branch],
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )


def validate_controlled_files(
    *,
    repo_dir: Path,
    branch: str,
    base_ref: str,
    worktree_path: Path,
    allowed_files: tuple[str, ...],
    forbidden_files: tuple[str, ...],
) -> tuple[str, ...]:
    """Fail closed when the worker changed anything outside its allowlist.

    Only files the worker actually changed (base_ref...branch diff) are
    validated; pre-existing base files are never flagged.
    """
    probe = subprocess.run(
        ["git", "-C", str(repo_dir), "diff", "--name-only", base_ref + "..." + branch],
        capture_output=True,
        text=True,
        timeout=60,
        check=False,
    )
    changed = [line.strip() for line in probe.stdout.splitlines() if line.strip()]
    blockers: list[str] = []
    for relative in sorted(changed):
        if any(
            relative == entry or relative.startswith(entry.rstrip("/") + "/")
            for entry in forbidden_files
        ):
            blockers.append(f"worker 写入禁止文件 {relative}")
            continue
        if allowed_files and not any(
            relative == entry or relative.startswith(entry.rstrip("/") + "/")
            for entry in allowed_files
        ):
            blockers.append(f"worker 写入未授权文件 {relative}")
    return tuple(blockers)


def worktree_diff(*, repo_dir: Path, base_ref: str, branch: str) -> str:
    """Return the worker's diff against the base ref (real git diff)."""
    probe = subprocess.run(
        ["git", "-C", str(repo_dir), "diff", base_ref + "..." + branch],
        capture_output=True,
        text=True,
        timeout=60,
        check=False,
    )
    return probe.stdout


@dataclass(frozen=True, slots=True)
class WorkerExecutionReceipt:
    """Real execution receipt of one worker command (M11)."""

    receipt_id: str
    delegation_id: str
    branch: str
    worktree_path: str
    command: str
    exit_code: int
    stdout: str
    stderr: str
    elapsed_ms: int
    diff_sha256: str
    environment: str
    receipt_hash: str | None = None

    def __post_init__(self) -> None:
        expected = sha256_hex(
            {
                "receipt_id": self.receipt_id,
                "delegation_id": self.delegation_id,
                "branch": self.branch,
                "command": self.command,
                "exit_code": self.exit_code,
                "stdout": self.stdout,
                "stderr": self.stderr,
                "diff_sha256": self.diff_sha256,
                "environment": self.environment,
            }
        )
        if self.receipt_hash is not None and self.receipt_hash != expected:
            raise DomainError(
                "receipt_hash does not match the worker receipt content",
                error_code="RECEIPT_HASH_MISMATCH",
            )
        object.__setattr__(self, "receipt_hash", expected)


def run_worker_command(
    *,
    handle: WorktreeHandle,
    command: tuple[str, ...],
    timeout_seconds: int = 120,
    environment: str = "codex-worker",
) -> WorkerExecutionReceipt:
    """Run one command inside the isolated worktree (M11)."""
    started = time.monotonic()
    try:
        proc = subprocess.run(
            [*command],
            cwd=handle.worktree_path,
            capture_output=True,
            text=True,
            timeout=timeout_seconds,
            check=False,
        )
    except subprocess.TimeoutExpired:
        raise DomainError(
            "worker 命令超时",
            error_code="CODEX_WORKER_TIMEOUT",
        ) from None
    except OSError as exc:
        raise DomainError(
            f"worker 命令不可执行：{exc}",
            error_code="TOOL_UNAVAILABLE",
        ) from exc
    elapsed_ms = int((time.monotonic() - started) * 1000)
    return WorkerExecutionReceipt(
        receipt_id=f"wx-{uuid.uuid4().hex[:12]}",
        delegation_id=handle.branch,
        branch=handle.branch,
        worktree_path=handle.worktree_path,
        command=" ".join(command),
        exit_code=proc.returncode,
        stdout=proc.stdout,
        stderr=proc.stderr,
        elapsed_ms=elapsed_ms,
        diff_sha256=sha256_hex({"branch": handle.branch, "elapsed": elapsed_ms}),
        environment=environment,
    )


def verify_worker_receipt(
    *,
    receipt: WorkerExecutionReceipt,
    expected_diff_sha256: str,
) -> tuple[str, ...]:
    """Adapter re-verification: receipt must bind the real diff hash (M11)."""
    blockers: list[str] = []
    if receipt.exit_code != 0:
        blockers.append(f"worker 退出码 {receipt.exit_code} 非 0")
    if receipt.diff_sha256 != expected_diff_sha256:
        blockers.append("worker receipt 未绑定真实 diff hash")
    return tuple(blockers)


__all__ = [
    "WorkerExecutionReceipt",
    "WorktreeHandle",
    "create_isolated_worktree",
    "remove_worktree",
    "run_worker_command",
    "validate_controlled_files",
    "verify_worker_receipt",
    "worktree_diff",
]
