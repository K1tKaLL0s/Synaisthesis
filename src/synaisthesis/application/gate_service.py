"""Generic Human Gate service (blueprint 08 section 15; M5.1).

Opens and resolves any gate record with a ``to_event_payload`` and a
user-only ``resolve(...)`` contract (Gate, EngineeringGate, ActionGate, ...).
Persistence is event-sourced with hash-verified payloads; the resolution path
re-checks the user actor inside the domain object, so a model, workflow or
default-timeout action can never approve.
"""

from __future__ import annotations

import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from synaisthesis.domain.enums import ProvenanceType
from synaisthesis.domain.errors import DomainError
from synaisthesis.domain.event import DomainEvent
from synaisthesis.storage.artifact_store import ArtifactRecord
from synaisthesis.storage.hashing import verify_artifact_hash
from synaisthesis.storage.repositories.event_repository import (
    DomainEventRecord,
    append_domain_event,
)

HUMAN_GATE_AGGREGATE_TYPE = "HumanGateRecord"

EVENT_HUMAN_GATE_OPENED = "HumanGateOpened"
EVENT_HUMAN_GATE_RESOLVED = "HumanGateResolved"


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


def _persist_gate_event(
    session: Session,
    *,
    event_type: str,
    gate_id: str,
    payload: dict[str, Any],
    project_id: str,
    artifact_root: Path,
) -> None:
    stream = _event_stream(session, HUMAN_GATE_AGGREGATE_TYPE, gate_id)
    event = DomainEvent(
        aggregate_type=HUMAN_GATE_AGGREGATE_TYPE,
        aggregate_id=gate_id,
        event_type=event_type,
        payload=payload,
        sequence=len(stream) + 1,
    )
    append_domain_event(session, event, project_id=project_id, artifact_root=artifact_root)


def open_human_gate(
    session: Session,
    *,
    project_id: str,
    gate: Any,
    artifact_root: Path,
    gate_id: str | None = None,
) -> Any:
    """Persist any opened gate record (requires to_event_payload())."""
    if not hasattr(gate, "to_event_payload"):
        raise DomainError(
            "gate 对象必须提供 to_event_payload()",
            error_code="GATE_BINDING_INVALID",
        )
    resolved_id = gate_id or getattr(gate, "gate_id", None) or f"gate-{uuid.uuid4().hex[:12]}"
    _persist_gate_event(
        session,
        event_type=EVENT_HUMAN_GATE_OPENED,
        gate_id=resolved_id,
        payload={"gate": gate.to_event_payload()},
        project_id=project_id,
        artifact_root=artifact_root,
    )
    return gate


def resolve_human_gate(
    session: Session,
    *,
    gate: Any,
    decision: str,
    actor: ProvenanceType,
    user_event_id: str,
    at: datetime,
    artifact_root: Path,
) -> Any:
    """Resolve a gate through its user-only resolve() and persist the outcome."""
    resolved = gate.resolve(
        decision=decision,
        actor=actor,
        user_event_id=user_event_id,
        at=at,
    )
    _persist_gate_event(
        session,
        event_type=EVENT_HUMAN_GATE_RESOLVED,
        gate_id=resolved.gate_id,
        payload={"gate": resolved.to_event_payload()},
        project_id=getattr(resolved, "project_id", ""),
        artifact_root=artifact_root,
    )
    return resolved


def load_human_gate(session: Session, gate_id: str, *, model: type, artifact_root: Path) -> Any:
    """Replay a gate record; model must be the gate dataclass type."""
    from synaisthesis.application.engineering_design_service import rebuild_dataclass

    records = _event_stream(session, HUMAN_GATE_AGGREGATE_TYPE, gate_id)
    if not records:
        raise DomainError(
            f"human gate {gate_id!r} has no events",
            error_code="PROJECT_NOT_FOUND",
        )
    gate: Any | None = None
    for record in records:
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
                f"payload artifact of event {record.id} is missing or "
                "tampered; state unrecoverable",
                error_code="ARTIFACT_HASH_MISMATCH",
            )
        payload = json.loads(path.read_text(encoding="utf-8"))
        if record.event_type in {EVENT_HUMAN_GATE_OPENED, EVENT_HUMAN_GATE_RESOLVED}:
            gate = rebuild_dataclass(model, payload["gate"])
    if gate is None:
        raise DomainError(
            f"state of gate {gate_id!r} is unrecoverable",
            error_code="PROJECT_STATE_UNRECOVERABLE",
        )
    return gate


__all__ = [
    "EVENT_HUMAN_GATE_OPENED",
    "EVENT_HUMAN_GATE_RESOLVED",
    "HUMAN_GATE_AGGREGATE_TYPE",
    "load_human_gate",
    "open_human_gate",
    "resolve_human_gate",
]
