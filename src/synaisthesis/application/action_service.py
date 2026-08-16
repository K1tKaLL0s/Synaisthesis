"""Action broker service (blueprint 08 sections 2/12; M5.1).

Routes action requests deterministically (AUTO/GATE/REJECT), opens and
resolves action Human Gates through real user events only, and records
execution receipts whose request/result hashes must recompute from the
original request before they can ever become Tool Evidence.
"""

from __future__ import annotations

import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from synaisthesis.domain.action import (
    ACTION_GATE_DECISIONS,
    ActionGate,
    ActionRequest,
    ActionRouteDecision,
    ActionRouteVerdict,
    DelegationMode,
    SemanticDelta,
    action_route,
)
from synaisthesis.domain.enums import ProvenanceType
from synaisthesis.domain.errors import DomainError
from synaisthesis.domain.event import DomainEvent
from synaisthesis.domain.receipt import (
    ExecutionReceipt,
    verify_receipt_binding,
)
from synaisthesis.storage.artifact_store import ArtifactRecord
from synaisthesis.storage.hashing import verify_artifact_hash
from synaisthesis.storage.repositories.event_repository import (
    DomainEventRecord,
    append_domain_event,
)

ACTION_GATE_AGGREGATE_TYPE = "ActionGate"
RECEIPT_AGGREGATE_TYPE = "ExecutionReceipt"

EVENT_ACTION_GATE_OPENED = "ActionGateOpened"
EVENT_ACTION_GATE_RESOLVED = "ActionGateResolved"
EVENT_EXECUTION_RECEIPT_RECORDED = "ExecutionReceiptRecorded"


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


def _persist_action_event(
    session: Session,
    *,
    event_type: str,
    aggregate_type: str,
    aggregate_id: str,
    payload: dict[str, Any],
    project_id: str,
    artifact_root: Path,
) -> None:
    stream = _event_stream(session, aggregate_type, aggregate_id)
    event = DomainEvent(
        aggregate_type=aggregate_type,
        aggregate_id=aggregate_id,
        event_type=event_type,
        payload=payload,
        sequence=len(stream) + 1,
    )
    append_domain_event(session, event, project_id=project_id, artifact_root=artifact_root)


def request_and_route_action(
    *,
    request: ActionRequest,
    delegation_mode: DelegationMode,
    allowlist_paths: frozenset[str] = frozenset(),
    allowed_network_domains: frozenset[str] = frozenset(),
    budget_within_limit: bool = True,
    semantic_delta: SemanticDelta = SemanticDelta.F0_EXACT,
) -> ActionRouteDecision:
    """Pure deterministic routing; the service never overrides the domain."""
    return action_route(
        request=request,
        delegation_mode=delegation_mode,
        allowlist_paths=allowlist_paths,
        allowed_network_domains=allowed_network_domains,
        budget_within_limit=budget_within_limit,
        semantic_delta=semantic_delta,
    )


def open_action_gate(
    session: Session,
    *,
    project_id: str,
    request: ActionRequest,
    route: ActionRouteDecision,
    artifact_root: Path,
    gate_id: str | None = None,
) -> ActionGate:
    """Open an action gate for a GATE verdict (never for AUTO/REJECT)."""
    if route.verdict is not ActionRouteVerdict.GATE:
        raise DomainError(
            f"verdict {route.verdict.value} 不需要 Human Gate",
            error_code="ACTION_GATE_NOT_REQUIRED",
        )
    gate = ActionGate(
        gate_id=gate_id or f"gate-act-{uuid.uuid4().hex[:12]}",
        project_id=project_id,
        action_request=request,
        route=route,
        reason=route.reason,
    )
    _persist_action_event(
        session,
        event_type=EVENT_ACTION_GATE_OPENED,
        aggregate_type=ACTION_GATE_AGGREGATE_TYPE,
        aggregate_id=gate.gate_id,
        payload={"gate": gate.to_event_payload()},
        project_id=project_id,
        artifact_root=artifact_root,
    )
    return gate


def resolve_action_gate(
    session: Session,
    *,
    gate: ActionGate,
    decision: str,
    actor: ProvenanceType,
    user_event_id: str,
    at: datetime,
    artifact_root: Path,
) -> ActionGate:
    """Resolve an action gate; models/workflows/defaults can never approve."""
    if decision not in ACTION_GATE_DECISIONS:
        raise DomainError(
            f"decision {decision!r} is not legal for an action gate; "
            f"allowed: {', '.join(ACTION_GATE_DECISIONS)}",
            error_code="INVALID_GATE_DECISION",
        )
    resolved = gate.resolve(
        decision=decision,
        actor=actor,
        user_event_id=user_event_id,
        at=at,
    )
    _persist_action_event(
        session,
        event_type=EVENT_ACTION_GATE_RESOLVED,
        aggregate_type=ACTION_GATE_AGGREGATE_TYPE,
        aggregate_id=resolved.gate_id,
        payload={"gate": resolved.to_event_payload()},
        project_id=gate.project_id,
        artifact_root=artifact_root,
    )
    return resolved


def record_execution_receipt(
    session: Session,
    *,
    project_id: str,
    request: ActionRequest,
    receipt: ExecutionReceipt,
    artifact_root: Path,
) -> ExecutionReceipt:
    """Record a receipt only when both hashes recompute (08, section 12)."""
    blockers = verify_receipt_binding(receipt, request)
    if blockers:
        raise DomainError(
            "RECEIPT_HASH_MISMATCH: " + "; ".join(blockers),
            error_code="RECEIPT_HASH_MISMATCH",
        )
    _persist_action_event(
        session,
        event_type=EVENT_EXECUTION_RECEIPT_RECORDED,
        aggregate_type=RECEIPT_AGGREGATE_TYPE,
        aggregate_id=receipt.receipt_id,
        payload={"receipt": receipt.to_event_payload()},
        project_id=project_id,
        artifact_root=artifact_root,
    )
    return receipt


def _load_payload(
    session: Session, record: DomainEventRecord, artifact_root: Path
) -> dict[str, Any]:
    if record.event_payload_artifact_id is None:
        raise DomainError(
            f"event {record.id} has no payload artifact; state unrecoverable",
            error_code="ARTIFACT_HASH_MISMATCH",
        )
    artifact = session.get(ArtifactRecord, record.event_payload_artifact_id)
    if artifact is None:
        raise DomainError(
            f"payload artifact of event {record.id} is missing; state unrecoverable",
            error_code="ARTIFACT_HASH_MISMATCH",
        )
    path = artifact_root / artifact.relative_path
    if not verify_artifact_hash(path, artifact.sha256):
        raise DomainError(
            f"payload artifact of event {record.id} is missing or tampered; state unrecoverable",
            error_code="ARTIFACT_HASH_MISMATCH",
        )
    return json.loads(path.read_text(encoding="utf-8"))


def load_action_gate(session: Session, gate_id: str, *, artifact_root: Path) -> ActionGate:
    from synaisthesis.application.engineering_design_service import rebuild_dataclass

    records = _event_stream(session, ACTION_GATE_AGGREGATE_TYPE, gate_id)
    if not records:
        raise DomainError(
            f"action gate {gate_id!r} has no events",
            error_code="PROJECT_NOT_FOUND",
        )
    gate: ActionGate | None = None
    for record in records:
        payload = _load_payload(session, record, artifact_root)
        if record.event_type in {EVENT_ACTION_GATE_OPENED, EVENT_ACTION_GATE_RESOLVED}:
            gate = rebuild_dataclass(ActionGate, payload["gate"])
    if gate is None:
        raise DomainError(
            f"state of gate {gate_id!r} is unrecoverable",
            error_code="PROJECT_STATE_UNRECOVERABLE",
        )
    return gate


def load_execution_receipt(
    session: Session, receipt_id: str, *, artifact_root: Path
) -> ExecutionReceipt:
    from synaisthesis.application.engineering_design_service import rebuild_dataclass

    records = _event_stream(session, RECEIPT_AGGREGATE_TYPE, receipt_id)
    if not records:
        raise DomainError(
            f"execution receipt {receipt_id!r} has no events",
            error_code="PROJECT_NOT_FOUND",
        )
    receipt: ExecutionReceipt | None = None
    for record in records:
        payload = _load_payload(session, record, artifact_root)
        if record.event_type == EVENT_EXECUTION_RECEIPT_RECORDED:
            receipt = rebuild_dataclass(ExecutionReceipt, payload["receipt"])
    if receipt is None:
        raise DomainError(
            f"state of receipt {receipt_id!r} is unrecoverable",
            error_code="PROJECT_STATE_UNRECOVERABLE",
        )
    return receipt


__all__ = [
    "ACTION_GATE_AGGREGATE_TYPE",
    "EVENT_ACTION_GATE_OPENED",
    "EVENT_ACTION_GATE_RESOLVED",
    "EVENT_EXECUTION_RECEIPT_RECORDED",
    "RECEIPT_AGGREGATE_TYPE",
    "load_action_gate",
    "load_execution_receipt",
    "open_action_gate",
    "record_execution_receipt",
    "request_and_route_action",
    "resolve_action_gate",
]
