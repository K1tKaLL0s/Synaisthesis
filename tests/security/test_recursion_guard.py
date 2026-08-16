"""M12 security tests for the Codex recursion guard (19 §5 M12)."""

from __future__ import annotations

import tempfile
from datetime import UTC, datetime
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config

from synaisthesis.application.fidelity_service import (
    FidelityConfig,
    register_instruction_capsule,
)
from synaisthesis.domain.errors import DomainError
from synaisthesis.fidelity.instruction_capsule import InstructionCapsule
from synaisthesis.integrations.codex.recursion_guard import (
    OriginActorType,
    OriginChain,
    OriginHop,
    assert_no_reentrancy,
    delegation_depth,
    verify_origin_chain,
)
from synaisthesis.interfaces.mcp.server import MCPServer
from synaisthesis.storage.database import init_database

NOW = datetime(2026, 8, 17, 2, 0, 0, tzinfo=UTC)
REPO_ROOT = Path(__file__).resolve().parents[2]
MIGRATIONS_DIR = REPO_ROOT / "src" / "synaisthesis" / "storage" / "migrations"
FIDELITY_KEY = b"test-signing-key-0123456789abcdef"


def _hop(actor: OriginActorType, session: str, delegation: str | None = None) -> OriginHop:
    return OriginHop(actor_type=actor, session_id=session, delegation_id=delegation)


def _fresh_database(tmp_path: Path):
    db_url = f"sqlite:///{tmp_path / 'recursion.db'}"
    cfg = Config()
    cfg.set_main_option("script_location", str(MIGRATIONS_DIR))
    cfg.set_main_option("sqlalchemy.url", db_url)
    command.upgrade(cfg, "head")
    _, session_factory = init_database(db_url)
    return session_factory


def test_valid_operator_platform_chain_passes():
    chain = OriginChain(
        hops=(
            _hop(OriginActorType.OPERATOR, "op-1"),
            _hop(OriginActorType.PLATFORM, "pl-1"),
        )
    )
    assert verify_origin_chain(chain) == (True, ())
    assert delegation_depth(chain) == 0
    assert_no_reentrancy(chain)


def test_worker_loop_operator_to_platform_to_worker_passes():
    chain = OriginChain(
        hops=(
            _hop(OriginActorType.OPERATOR, "op-1"),
            _hop(OriginActorType.PLATFORM, "pl-1"),
            _hop(OriginActorType.WORKER, "wk-1", "cd-1"),
            _hop(OriginActorType.PLATFORM, "pl-1"),
        )
    )
    assert verify_origin_chain(chain) == (True, ())
    assert delegation_depth(chain) == 1


def test_worker_acting_as_operator_is_reentrancy():
    chain = OriginChain(
        hops=(
            _hop(OriginActorType.OPERATOR, "op-1"),
            _hop(OriginActorType.PLATFORM, "pl-1"),
            _hop(OriginActorType.WORKER, "wk-1", "cd-1"),
            _hop(OriginActorType.OPERATOR, "op-1"),
        )
    )
    valid, blockers = verify_origin_chain(chain)
    assert valid is False
    assert any("OPERATOR" in blocker for blocker in blockers)
    with pytest.raises(DomainError) as exc_info:
        assert_no_reentrancy(chain)
    assert exc_info.value.error_code == "REENTRANCY_BLOCKED"


def test_worker_only_spawned_by_platform():
    chain = OriginChain(
        hops=(
            _hop(OriginActorType.OPERATOR, "op-1"),
            _hop(OriginActorType.WORKER, "wk-1", "cd-1"),
        )
    )
    valid, blockers = verify_origin_chain(chain)
    assert valid is False
    assert any("WORKER 只能由 PLATFORM 派生" in blocker for blocker in blockers)


def test_depth_limit_and_cycle():
    chain = OriginChain(
        hops=(
            _hop(OriginActorType.OPERATOR, "op-1"),
            _hop(OriginActorType.PLATFORM, "pl-1"),
            _hop(OriginActorType.WORKER, "wk-1", "cd-1"),
            _hop(OriginActorType.PLATFORM, "pl-2"),
            _hop(OriginActorType.WORKER, "wk-2", "cd-2"),
            _hop(OriginActorType.PLATFORM, "pl-3"),
            _hop(OriginActorType.WORKER, "wk-3", "cd-3"),
            _hop(OriginActorType.PLATFORM, "pl-4"),
            _hop(OriginActorType.WORKER, "wk-4", "cd-4"),
        )
    )
    valid, blockers = verify_origin_chain(chain, max_depth=3)
    assert valid is False
    assert any("delegation depth" in blocker for blocker in blockers)
    # a repeated hop is a cycle
    cycle = OriginChain(
        hops=(
            _hop(OriginActorType.OPERATOR, "op-1"),
            _hop(OriginActorType.PLATFORM, "pl-1"),
            _hop(OriginActorType.WORKER, "wk-1", "cd-1"),
            _hop(OriginActorType.PLATFORM, "pl-1"),
        )
    )
    assert delegation_depth(cycle) == 1


def test_mcp_mutation_without_origin_chain_is_blocked():
    tmp = Path(tempfile.mkdtemp())
    session_factory = _fresh_database(tmp)
    artifact_root = tmp / "artifacts"
    server = MCPServer(
        session_factory,
        fidelity=FidelityConfig(signing_key=FIDELITY_KEY, now_fn=lambda: NOW),
        artifact_root=artifact_root,
    )
    response = server.handle(
        {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/call",
            "params": {
                "name": "research_prepare_command",
                "arguments": {"project_id": "p-1"},
            },
        }
    )
    assert response is not None
    assert "REENTRANCY_BLOCKED" in response["error"]["message"]


def test_mcp_mutation_with_worker_origin_loop_is_blocked():
    tmp = Path(tempfile.mkdtemp())
    session_factory = _fresh_database(tmp)
    artifact_root = tmp / "artifacts"
    with session_factory() as session:
        register_instruction_capsule(
            session,
            InstructionCapsule(
                instruction_id="inst-1",
                session_id="s-1",
                turn_id="t-1",
                raw_user_text="运行 10 轮",
            ),
            project_id="p-1",
            artifact_root=artifact_root,
        )
        session.commit()
    server = MCPServer(
        session_factory,
        fidelity=FidelityConfig(signing_key=FIDELITY_KEY, now_fn=lambda: NOW),
        artifact_root=artifact_root,
    )
    response = server.handle(
        {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/call",
            "params": {
                "name": "research_prepare_command",
                "arguments": {
                    "project_id": "p-1",
                    "origin_chain": [
                        {"actor_type": "OPERATOR", "session_id": "op-1"},
                        {"actor_type": "WORKER", "session_id": "wk-1", "delegation_id": "cd-1"},
                        {"actor_type": "OPERATOR", "session_id": "op-1"},
                    ],
                },
            },
        }
    )
    assert response is not None
    assert "REENTRANCY_BLOCKED" in response["error"]["message"]
