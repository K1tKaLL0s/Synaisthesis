"""Council checkpoint persistence (03 section 2 WIP_CHECKPOINT; M7.1)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from synaisthesis.domain.errors import DomainError
from synaisthesis.orchestration.state import (
    EVENT_COUNCIL_CHECKPOINT_WRITTEN,
    build_council_state_event,
)
from synaisthesis.storage.artifact_store import ArtifactRecord
from synaisthesis.storage.hashing import verify_artifact_hash
from synaisthesis.storage.repositories.event_repository import (
    DomainEventRecord,
    append_domain_event,
)

CHECKPOINT_AGGREGATE_TYPE = "CouncilCheckpoint"


def write_council_checkpoint(
    session: Session,
    *,
    project_id: str,
    run_id: str,
    run_state: dict[str, Any],
    artifact_root: Path,
) -> dict[str, Any]:
    """Persist a WIP_CHECKPOINT snapshot bound to the run id (03, section 2)."""
    stream = list(
        session.execute(
            select(DomainEventRecord)
            .where(
                DomainEventRecord.aggregate_type == CHECKPOINT_AGGREGATE_TYPE,
                DomainEventRecord.aggregate_id == run_id,
            )
            .order_by(DomainEventRecord.id)
        )
        .scalars()
        .all()
    )
    event = build_council_state_event(
        EVENT_COUNCIL_CHECKPOINT_WRITTEN,
        aggregate_type=CHECKPOINT_AGGREGATE_TYPE,
        aggregate_id=run_id,
        payload={"checkpoint": {"run_id": run_id, "run_state": run_state}},
        sequence=len(stream) + 1,
    )
    append_domain_event(session, event, project_id=project_id, artifact_root=artifact_root)
    return run_state


def load_council_checkpoint(
    session: Session, run_id: str, *, artifact_root: Path
) -> dict[str, Any]:
    """Replay the latest verified checkpoint snapshot for a run."""
    records = list(
        session.execute(
            select(DomainEventRecord)
            .where(
                DomainEventRecord.aggregate_type == CHECKPOINT_AGGREGATE_TYPE,
                DomainEventRecord.aggregate_id == run_id,
            )
            .order_by(DomainEventRecord.id)
        )
        .scalars()
        .all()
    )
    if not records:
        raise DomainError(
            f"no checkpoint for run {run_id!r}",
            error_code="PROJECT_NOT_FOUND",
        )
    snapshot: dict[str, Any] | None = None
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
        if record.event_type == EVENT_COUNCIL_CHECKPOINT_WRITTEN:
            snapshot = payload["checkpoint"]["run_state"]
    if snapshot is None:
        raise DomainError(
            f"state of checkpoint {run_id!r} is unrecoverable",
            error_code="PROJECT_STATE_UNRECOVERABLE",
        )
    return snapshot


__all__ = [
    "CHECKPOINT_AGGREGATE_TYPE",
    "load_council_checkpoint",
    "write_council_checkpoint",
]
