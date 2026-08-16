"""M10 contract tests for the MCP server over the Fidelity Gateway (05A §18)."""

from __future__ import annotations

import io
from datetime import UTC, datetime
from pathlib import Path

from alembic import command
from alembic.config import Config

from synaisthesis.application.fidelity_service import (
    FidelityConfig,
    issue_instruction_token,
    load_instruction_capsule,
    register_instruction_capsule,
)
from synaisthesis.application.gate_service import open_human_gate
from synaisthesis.domain.enums import (
    QualificationGateType,
)
from synaisthesis.domain.gate import Gate, GateBinding
from synaisthesis.interfaces.mcp.protocol import (
    read_message,
    rpc_error,
    rpc_notification,
    rpc_response,
    write_message,
)
from synaisthesis.interfaces.mcp.server import PROTOCOL_VERSION, MCPServer
from synaisthesis.interfaces.mcp.tools import (
    MUTATION_TOOLS,
    READ_ONLY_TOOLS,
    TOOL_DEFINITIONS,
    TOOL_GET_PENDING_GATES,
)
from synaisthesis.storage.database import init_database

NOW = datetime(2026, 8, 17, 2, 0, 0, tzinfo=UTC)
REPO_ROOT = Path(__file__).resolve().parents[3]
MIGRATIONS_DIR = REPO_ROOT / "src" / "synaisthesis" / "storage" / "migrations"
FIDELITY_KEY = b"test-signing-key-0123456789abcdef"


def _fresh_database(tmp_path: Path):
    db_url = f"sqlite:///{tmp_path / 'mcp.db'}"
    cfg = Config()
    cfg.set_main_option("script_location", str(MIGRATIONS_DIR))
    cfg.set_main_option("sqlalchemy.url", db_url)
    command.upgrade(cfg, "head")
    _, session_factory = init_database(db_url)
    return session_factory


def _handle(server: MCPServer, message: dict) -> dict:
    response = server.handle(message)
    assert response is not None
    return response


def _server(session_factory, artifact_root: Path) -> MCPServer:
    return MCPServer(
        session_factory,
        fidelity=FidelityConfig(signing_key=FIDELITY_KEY, now_fn=lambda: NOW),
        artifact_root=artifact_root,
    )


def test_initialize_handshake():
    server = _server(*_setup())
    response = _handle(server, {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}})
    assert response["result"]["protocolVersion"] == PROTOCOL_VERSION
    assert "tools" in response["result"]["capabilities"]


def test_tools_list_has_readonly_and_mutation():
    server = _server(*_setup())
    response = _handle(server, {"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}})
    names = {tool["name"] for tool in response["result"]["tools"]}
    assert set(READ_ONLY_TOOLS).issubset(names)
    assert set(MUTATION_TOOLS).issubset(names)
    assert len(TOOL_DEFINITIONS) == len(names)


def test_unknown_method_and_tool_fail_closed():
    server = _server(*_setup())
    response = _handle(server, {"jsonrpc": "2.0", "id": 3, "method": "nope", "params": {}})
    assert response["error"]["code"] == -32601
    response = _handle(
        server,
        {
            "jsonrpc": "2.0",
            "id": 4,
            "method": "tools/call",
            "params": {"name": "research_freeze_claim", "arguments": {}},
        },
    )
    assert response["error"]["code"] == -32601


def test_mutation_without_token_fails_closed():
    session_factory, artifact_root = _setup()
    server = _server(session_factory, artifact_root)
    response = _handle(
        server,
        {
            "jsonrpc": "2.0",
            "id": 5,
            "method": "tools/call",
            "params": {
                "name": "research_prepare_command",
                "arguments": {"project_id": "p-1"},
            },
        },
    )
    assert (
        response["error"]["code"] == -32602
        or "FIDELITY_CHANNEL_REQUIRED" in response["error"]["message"]
    )


def test_prepare_commit_round_trip_through_gateway():
    session_factory, artifact_root = _setup()
    from synaisthesis.fidelity.instruction_capsule import InstructionCapsule
    from synaisthesis.fidelity.instruction_token import OperationClass

    with session_factory() as session:
        register_instruction_capsule(
            session,
            InstructionCapsule(
                instruction_id="inst-1",
                session_id="s-1",
                turn_id="t-1",
                raw_user_text="运行 10 轮",
                cwd="/tmp",
                permission_mode="STRICT_BOUND_SESSION",
            ),
            project_id="p-1",
            artifact_root=artifact_root,
        )
        capsule = load_instruction_capsule(session, "inst-1", artifact_root=artifact_root)
        token = issue_instruction_token(
            FidelityConfig(signing_key=FIDELITY_KEY, now_fn=lambda: NOW),
            capsule,
            project_id="p-1",
            state_version=0,
            operation_class=OperationClass.HIGH_RISK_MUTATION,
        )
        session.commit()
    server = _server(session_factory, artifact_root)
    prepare = _handle(
        server,
        {
            "jsonrpc": "2.0",
            "id": 6,
            "method": "tools/call",
            "params": {
                "name": "research_prepare_command",
                "arguments": {
                    "instruction_token": {
                        **token.signing_payload(),
                        "signature": token.signature,
                    },
                    "instruction_id": "inst-1",
                    "project_id": "p-1",
                    "command_proposal": {
                        "operation": "run_council",
                        "loop_rounds": 10,
                        "read_only": False,
                    },
                    "platform_interpretation": {
                        "operation": "run_council",
                        "loop_rounds": 10,
                        "read_only": False,
                    },
                    "context_manifest": {
                        "context_manifest_id": "cm-1",
                        "workspace_root": "/tmp",
                        "selected_file_refs": [],
                    },
                    "expected_state_version": 0,
                    "idempotency_key": "k-1",
                    "operation_class": "HIGH_RISK_MUTATION",
                },
            },
        },
    )
    assert prepare["result"]["content"][0]["type"] == "text"
    # mutation was served (no FIDELITY_CHANNEL_REQUIRED error)
    assert "error" not in prepare


def _setup():
    import tempfile

    tmp = Path(tempfile.mkdtemp())
    session_factory = _fresh_database(tmp)
    artifact_root = tmp / "artifacts"
    # persist one open qualification gate for the pending-gates query
    with session_factory() as session:
        gate = Gate(
            gate_id="gate-q-1",
            project_id="p-1",
            gate_type=QualificationGateType.ENGINEERING_ROUTE_DECISION,
            binding=GateBinding(
                gate_type=QualificationGateType.ENGINEERING_ROUTE_DECISION,
                artifact_id="fa-1",
                version=1,
                artifact_hash="a" * 64,
                input_spec_hash="s" * 64,
            ),
            reason="route decision",
        )
        open_human_gate(session, project_id="p-1", gate=gate, artifact_root=artifact_root)
        session.commit()
    return session_factory, artifact_root


def test_pending_gates_read_only():
    session_factory, artifact_root = _setup()
    server = _server(session_factory, artifact_root)
    response = _handle(
        server,
        {
            "jsonrpc": "2.0",
            "id": 7,
            "method": "tools/call",
            "params": {
                "name": TOOL_GET_PENDING_GATES,
                "arguments": {"project_id": "p-1"},
            },
        },
    )
    text = response["result"]["content"][0]["text"]
    assert "gate-q-1" in text


def test_protocol_framing_round_trip():
    message = rpc_response(1, {"ok": True})
    stream = io.StringIO()
    write_message(stream, message)
    stream.seek(0)
    parsed = read_message(stream)
    assert parsed == message
    notification = rpc_notification("notify", {"x": 1})
    error = rpc_error(2, -32601, "nope")
    assert notification["method"] == "notify"
    assert error["error"]["code"] == -32601
