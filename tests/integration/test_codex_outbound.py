"""M11 integration tests for Codex outbound delegation (19 §5 M11).

Uses a throwaway git repo in tmp_path so the real workspace is never touched.
The worker runs in an isolated worktree; controlled-file violations and
self-claimed PASS are blocked by the adapter.
"""

from __future__ import annotations

import subprocess
from datetime import UTC, datetime
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config

from synaisthesis.application.codex_delegation_service import (
    delegate_work_unit,
    verify_delegation_receipt,
)
from synaisthesis.domain.errors import DomainError
from synaisthesis.integrations.codex.worker import (
    create_isolated_worktree,
    remove_worktree,
    run_worker_command,
    validate_controlled_files,
    worktree_diff,
)
from synaisthesis.orchestration.nodes.codex_nodes import codex_receive_node
from synaisthesis.storage.database import init_database

NOW = datetime(2026, 8, 17, 2, 0, 0, tzinfo=UTC)
REPO_ROOT = Path(__file__).resolve().parents[2]
MIGRATIONS_DIR = REPO_ROOT / "src" / "synaisthesis" / "storage" / "migrations"


def _fresh_database(tmp_path: Path):
    db_url = f"sqlite:///{tmp_path / 'codex.db'}"
    cfg = Config()
    cfg.set_main_option("script_location", str(MIGRATIONS_DIR))
    cfg.set_main_option("sqlalchemy.url", db_url)
    command.upgrade(cfg, "head")
    _, session_factory = init_database(db_url)
    return session_factory


def _make_repo(tmp_path: Path) -> Path:
    repo = tmp_path / "repo"
    repo.mkdir()
    subprocess.run(["git", "-C", str(repo), "init", "-q", "-b", "main"], check=True)
    (repo / "seed.txt").write_text("seed", encoding="utf-8")
    subprocess.run(["git", "-C", str(repo), "add", "seed.txt"], check=True, capture_output=True)
    subprocess.run(
        ["git", "-C", str(repo), "commit", "-q", "-m", "seed"],
        check=True,
        capture_output=True,
    )
    subprocess.run(["git", "-C", str(repo), "config", "user.email", "t@t"], check=True)
    subprocess.run(["git", "-C", str(repo), "config", "user.name", "t"], check=True)
    return repo


def test_worktree_is_isolated_from_main_tree(tmp_path):
    repo = _make_repo(tmp_path)
    main_before = sorted(path.name for path in repo.iterdir())
    handle = create_isolated_worktree(repo_dir=repo, base_ref="main")
    worktree = Path(handle.worktree_path)
    (worktree / "worker.txt").write_text("w", encoding="utf-8")
    subprocess.run(
        ["git", "-C", str(worktree), "add", "worker.txt"], check=True, capture_output=True
    )
    subprocess.run(
        ["git", "-C", str(worktree), "commit", "-q", "-m", "w"],
        check=True,
        capture_output=True,
    )
    # main tree has no worker.txt
    assert not (repo / "worker.txt").exists()
    diff = worktree_diff(repo_dir=repo, base_ref="main", branch=handle.branch)
    assert "worker.txt" in diff
    remove_worktree(repo_dir=repo, handle=handle)
    assert sorted(path.name for path in repo.iterdir()) == main_before


def test_controlled_files_block_forbidden_write(tmp_path):
    repo = _make_repo(tmp_path)
    handle = create_isolated_worktree(repo_dir=repo, base_ref="main")
    worktree = Path(handle.worktree_path)
    (worktree / "secret.txt").write_text("s", encoding="utf-8")
    subprocess.run(
        ["git", "-C", str(worktree), "add", "secret.txt"], check=True, capture_output=True
    )
    subprocess.run(
        ["git", "-C", str(worktree), "commit", "-q", "-m", "secret"],
        check=True,
        capture_output=True,
    )
    blockers = validate_controlled_files(
        repo_dir=repo,
        branch=handle.branch,
        base_ref="main",
        worktree_path=worktree,
        allowed_files=("worker/",),
        forbidden_files=("secret.txt",),
    )
    assert any("secret.txt" in blocker for blocker in blockers)
    remove_worktree(repo_dir=repo, handle=handle)


def test_delegate_work_unit_full_flow(tmp_path):
    session_factory = _fresh_database(tmp_path)
    artifact_root = tmp_path / "artifacts"
    repo = _make_repo(tmp_path)
    with session_factory() as session:
        handle, receipt = delegate_work_unit(
            session,
            project_id="p-1",
            repo_dir=repo,
            base_ref="main",
            allowed_files=("worker_out.txt",),
            forbidden_files=(),
            command=(
                "python3",
                "-c",
                "from pathlib import Path; Path('worker_out.txt').write_text('done')",
            ),
            artifact_root=artifact_root,
        )
        session.commit()
    assert receipt.exit_code == 0
    assert receipt.receipt_hash
    # worktree was removed after capture
    assert not Path(handle.worktree_path).exists()
    # adapter re-verification passes with the real diff hash
    assert verify_delegation_receipt(receipt, expected_diff_sha256=receipt.diff_sha256) == ()
    assert codex_receive_node(receipt, expected_diff_sha256=receipt.diff_sha256) == ()


def test_receive_node_rejects_self_claimed_pass(tmp_path):
    repo = _make_repo(tmp_path)
    handle = create_isolated_worktree(repo_dir=repo, base_ref="main")
    receipt = run_worker_command(handle=handle, command=("true",))
    # a worker-claimed PASS with the WRONG diff hash is rejected
    blockers = codex_receive_node(receipt, expected_diff_sha256="0" * 64)
    assert any("diff hash" in blocker for blocker in blockers)
    remove_worktree(repo_dir=repo, handle=handle)


def test_worker_violation_is_blocked(tmp_path):
    session_factory = _fresh_database(tmp_path)
    artifact_root = tmp_path / "artifacts"
    repo = _make_repo(tmp_path)
    with session_factory() as session, pytest.raises(DomainError) as exc_info:
        delegate_work_unit(
            session,
            project_id="p-1",
            repo_dir=repo,
            base_ref="main",
            allowed_files=("ok.txt",),
            forbidden_files=(),
            command=(
                "python3",
                "-c",
                "from pathlib import Path; import subprocess; "
                "Path('not_allowed.txt').write_text('x'); "
                "subprocess.run(['git','add','not_allowed.txt'],check=True); "
                "subprocess.run(['git','commit','-q','-m','x'],check=True)",
            ),
            artifact_root=artifact_root,
        )
    assert exc_info.value.error_code == "CODEX_WORKER_VIOLATION"
