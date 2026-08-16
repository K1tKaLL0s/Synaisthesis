"""M5.1 security tests for action routing, gates and execution receipts (08)."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config

from synaisthesis.application.action_service import (
    load_action_gate,
    load_execution_receipt,
    open_action_gate,
    record_execution_receipt,
    request_and_route_action,
    resolve_action_gate,
)
from synaisthesis.application.gate_service import (
    load_human_gate,
    open_human_gate,
    resolve_human_gate,
)
from synaisthesis.domain.action import (
    ActionGate,
    ActionRequest,
    ActionRiskClass,
    ActionRouteVerdict,
    DelegationMode,
    SemanticDelta,
)
from synaisthesis.domain.enums import ProvenanceType
from synaisthesis.domain.errors import DomainError
from synaisthesis.domain.receipt import (
    ExecutionReceipt,
    action_request_hash,
    execution_result_hash,
    receipt_tool_evidence,
    verify_receipt_binding,
)
from synaisthesis.storage.database import init_database

NOW = datetime(2026, 8, 17, 2, 0, 0, tzinfo=UTC)
REPO_ROOT = Path(__file__).resolve().parents[2]
MIGRATIONS_DIR = REPO_ROOT / "src" / "synaisthesis" / "storage" / "migrations"


def _fresh_database(tmp_path: Path):
    db_url = f"sqlite:///{tmp_path / 'action.db'}"
    cfg = Config()
    cfg.set_main_option("script_location", str(MIGRATIONS_DIR))
    cfg.set_main_option("sqlalchemy.url", db_url)
    command.upgrade(cfg, "head")
    _, session_factory = init_database(db_url)
    return session_factory


def _request(risk: ActionRiskClass, **overrides) -> ActionRequest:
    params = {
        "action_type": "write_artifact",
        "risk_class": risk,
        "requester": "model-x",
        "exact_parameters": {"path": "workspace/out.json"},
        "allowed_paths": ("workspace/out.json",),
        "network_intent": (
            "https://example.org/search" if risk is ActionRiskClass.R2_NETWORK_READ else None
        ),
        "cost_estimate": "10k tokens",
        "expected_outputs": ("artifact",),
    }
    params.update(overrides)
    return ActionRequest(**params)


# ---------------------------------------------------------------------------
# Deterministic routing (08, section 2)
# ---------------------------------------------------------------------------


def test_r0_read_is_always_auto():
    for mode in DelegationMode:
        route = request_and_route_action(
            request=_request(ActionRiskClass.R0_READ), delegation_mode=mode
        )
        assert route.verdict is ActionRouteVerdict.AUTO


def test_r4_r6_always_require_human_gate():
    for risk in (
        ActionRiskClass.R4_EXTERNAL_WRITE,
        ActionRiskClass.R5_SECRET_OR_SENSITIVE,
        ActionRiskClass.R6_DESTRUCTIVE,
    ):
        route = request_and_route_action(
            request=_request(risk),
            delegation_mode=DelegationMode.A3_AI_AUTONOMOUS_BOUNDED,
        )
        assert route.verdict is ActionRouteVerdict.GATE


def test_r1_write_routing_depends_on_mode_and_allowlist():
    request = _request(ActionRiskClass.R1_ISOLATED_WRITE)
    assert (
        request_and_route_action(
            request=request, delegation_mode=DelegationMode.A1_AI_ASSISTED
        ).verdict
        is ActionRouteVerdict.GATE
    )
    assert (
        request_and_route_action(
            request=request,
            delegation_mode=DelegationMode.A3_AI_AUTONOMOUS_BOUNDED,
            allowlist_paths=frozenset(),
        ).verdict
        is ActionRouteVerdict.GATE
    )
    assert (
        request_and_route_action(
            request=request,
            delegation_mode=DelegationMode.A3_AI_AUTONOMOUS_BOUNDED,
            allowlist_paths=frozenset({"workspace/out.json"}),
        ).verdict
        is ActionRouteVerdict.AUTO
    )
    assert (
        request_and_route_action(
            request=request,
            delegation_mode=DelegationMode.A2_AI_DELEGATED,
            allowlist_paths=frozenset({"workspace/"}),
        ).verdict
        is ActionRouteVerdict.AUTO
    )


def test_r2_network_requires_domain_allowlist():
    request = _request(ActionRiskClass.R2_NETWORK_READ)
    assert (
        request_and_route_action(
            request=request, delegation_mode=DelegationMode.A3_AI_AUTONOMOUS_BOUNDED
        ).verdict
        is ActionRouteVerdict.GATE
    )
    assert (
        request_and_route_action(
            request=request,
            delegation_mode=DelegationMode.A3_AI_AUTONOMOUS_BOUNDED,
            allowed_network_domains=frozenset({"example.org"}),
        ).verdict
        is ActionRouteVerdict.AUTO
    )


def test_r3_compute_is_budget_bound():
    request = _request(ActionRiskClass.R3_COSTLY_COMPUTE)
    assert (
        request_and_route_action(
            request=request,
            delegation_mode=DelegationMode.A3_AI_AUTONOMOUS_BOUNDED,
            budget_within_limit=True,
        ).verdict
        is ActionRouteVerdict.AUTO
    )
    assert (
        request_and_route_action(
            request=request,
            delegation_mode=DelegationMode.A3_AI_AUTONOMOUS_BOUNDED,
            budget_within_limit=False,
        ).verdict
        is ActionRouteVerdict.GATE
    )
    assert (
        request_and_route_action(
            request=request, delegation_mode=DelegationMode.A1_AI_ASSISTED
        ).verdict
        is ActionRouteVerdict.GATE
    )


def test_semantic_delta_f4_f5_never_auto():
    request = _request(ActionRiskClass.R0_READ)
    assert (
        request_and_route_action(
            request=request,
            delegation_mode=DelegationMode.A3_AI_AUTONOMOUS_BOUNDED,
            semantic_delta=SemanticDelta.F4_SEMANTIC_DRIFT,
        ).verdict
        is ActionRouteVerdict.GATE
    )
    assert (
        request_and_route_action(
            request=request,
            delegation_mode=DelegationMode.A3_AI_AUTONOMOUS_BOUNDED,
            semantic_delta=SemanticDelta.F5_UNAUTHORIZED_ACTION,
        ).verdict
        is ActionRouteVerdict.REJECT
    )


# ---------------------------------------------------------------------------
# Action gates (08, section 15; M5.1)
# ---------------------------------------------------------------------------


def _open_gate(session_factory, artifact_root: Path) -> ActionGate:
    request = _request(ActionRiskClass.R6_DESTRUCTIVE)
    route = request_and_route_action(
        request=request, delegation_mode=DelegationMode.A3_AI_AUTONOMOUS_BOUNDED
    )
    with session_factory() as session:
        gate = open_action_gate(
            session,
            project_id="p-1",
            request=request,
            route=route,
            artifact_root=artifact_root,
            gate_id="gate-act-1",
        )
        session.commit()
    return gate


def test_gate_open_requires_gate_verdict(tmp_path):
    session_factory = _fresh_database(tmp_path)
    artifact_root = tmp_path / "artifacts"
    request = _request(ActionRiskClass.R0_READ)
    route = request_and_route_action(
        request=request, delegation_mode=DelegationMode.A3_AI_AUTONOMOUS_BOUNDED
    )
    with session_factory() as session, pytest.raises(DomainError) as exc_info:
        open_action_gate(
            session,
            project_id="p-1",
            request=request,
            route=route,
            artifact_root=artifact_root,
        )
    assert exc_info.value.error_code == "ACTION_GATE_NOT_REQUIRED"


def test_model_cannot_resolve_action_gate(tmp_path):
    session_factory = _fresh_database(tmp_path)
    artifact_root = tmp_path / "artifacts"
    gate = _open_gate(session_factory, artifact_root)
    with session_factory() as session, pytest.raises(DomainError) as exc_info:
        resolve_action_gate(
            session,
            gate=gate,
            decision="APPROVE",
            actor=ProvenanceType.ASSISTANT_PROPOSAL,
            user_event_id="ev-1",
            at=NOW,
            artifact_root=artifact_root,
        )
    assert exc_info.value.error_code == "CONFIRMATION_REQUIRES_USER_EVENT"


def test_action_gate_user_approve_round_trip(tmp_path):
    session_factory = _fresh_database(tmp_path)
    artifact_root = tmp_path / "artifacts"
    gate = _open_gate(session_factory, artifact_root)
    with session_factory() as session:
        resolved = resolve_action_gate(
            session,
            gate=gate,
            decision="APPROVE",
            actor=ProvenanceType.USER_DECISION,
            user_event_id="uev-approve",
            at=NOW,
            artifact_root=artifact_root,
        )
        session.commit()
    assert resolved.decision == "APPROVE"
    assert resolved.status == "RESOLVED"
    with session_factory() as session:
        reloaded = load_action_gate(session, "gate-act-1", artifact_root=artifact_root)
    assert reloaded == resolved


def test_action_gate_rejects_illegal_decision(tmp_path):
    session_factory = _fresh_database(tmp_path)
    artifact_root = tmp_path / "artifacts"
    gate = _open_gate(session_factory, artifact_root)
    with session_factory() as session, pytest.raises(DomainError) as exc_info:
        resolve_action_gate(
            session,
            gate=gate,
            decision="MAYBE",
            actor=ProvenanceType.USER_DECISION,
            user_event_id="ev-2",
            at=NOW,
            artifact_root=artifact_root,
        )
    assert exc_info.value.error_code == "INVALID_GATE_DECISION"


def test_generic_gate_service_persists_any_gate(tmp_path):
    from synaisthesis.domain.enums import QualificationGateType
    from synaisthesis.domain.gate import Gate, GateBinding

    session_factory = _fresh_database(tmp_path)
    artifact_root = tmp_path / "artifacts"
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
    with session_factory() as session:
        open_human_gate(session, project_id="p-1", gate=gate, artifact_root=artifact_root)
        resolved = resolve_human_gate(
            session,
            gate=gate,
            decision="TRY_ENGINEERING_PROJECT",
            actor=ProvenanceType.USER_DECISION,
            user_event_id="uev-generic",
            at=NOW,
            artifact_root=artifact_root,
        )
        session.commit()
    assert resolved.decision == "TRY_ENGINEERING_PROJECT"
    with session_factory() as session:
        reloaded = load_human_gate(session, "gate-q-1", model=Gate, artifact_root=artifact_root)
    assert reloaded == resolved


# ---------------------------------------------------------------------------
# Execution receipts (08, section 12; M5.1)
# ---------------------------------------------------------------------------


def _receipt(request: ActionRequest, **overrides) -> ExecutionReceipt:
    params = {
        "receipt_id": "rec-1",
        "request_hash": action_request_hash(request),
        "executor": "sandbox-1",
        "actual_parameters": dict(request.exact_parameters),
        "started_at": NOW,
        "ended_at": NOW,
        "exit_status": 0,
        "stdout": "ok",
        "stderr": "",
        "produced_artifacts": ("workspace/out.json",),
        "diff": "1 insertion",
        "result_hash": execution_result_hash(
            actual_parameters=dict(request.exact_parameters),
            produced_artifacts=("workspace/out.json",),
            exit_status=0,
        ),
        "environment_version": "py3.14@wsl",
    }
    params.update(overrides)
    return ExecutionReceipt(**params)


def test_receipt_without_hash_fails_closed():
    request = _request(ActionRiskClass.R1_ISOLATED_WRITE)
    with pytest.raises(DomainError) as exc_info:
        _receipt(request, request_hash="", result_hash="x")
    assert exc_info.value.error_code == "RECEIPT_HASH_MISSING"
    with pytest.raises(DomainError) as exc_info:
        _receipt(request, request_hash="x", result_hash="")
    assert exc_info.value.error_code == "RECEIPT_HASH_MISSING"


def test_receipt_binding_mismatch_rejected():
    request = _request(ActionRiskClass.R1_ISOLATED_WRITE)
    other = _request(ActionRiskClass.R1_ISOLATED_WRITE, action_type="delete_artifact")
    receipt = _receipt(request)
    assert verify_receipt_binding(receipt, request) == ()
    assert verify_receipt_binding(receipt, other)


def test_receipt_recording_and_tool_evidence(tmp_path):
    session_factory = _fresh_database(tmp_path)
    artifact_root = tmp_path / "artifacts"
    request = _request(ActionRiskClass.R1_ISOLATED_WRITE)
    receipt = _receipt(request)
    assert receipt_tool_evidence(receipt) is True
    with session_factory() as session:
        record_execution_receipt(
            session,
            project_id="p-1",
            request=request,
            receipt=receipt,
            artifact_root=artifact_root,
        )
        session.commit()
    with session_factory() as session:
        reloaded = load_execution_receipt(session, "rec-1", artifact_root=artifact_root)
    assert reloaded == receipt


def test_receipt_recording_rejects_tampered_request(tmp_path):
    session_factory = _fresh_database(tmp_path)
    artifact_root = tmp_path / "artifacts"
    request = _request(ActionRiskClass.R1_ISOLATED_WRITE)
    tampered = _request(ActionRiskClass.R1_ISOLATED_WRITE, exact_parameters={"path": "elsewhere"})
    receipt = _receipt(request)
    with session_factory() as session, pytest.raises(DomainError) as exc_info:
        record_execution_receipt(
            session,
            project_id="p-1",
            request=tampered,
            receipt=receipt,
            artifact_root=artifact_root,
        )
    assert exc_info.value.error_code == "RECEIPT_HASH_MISMATCH"
