"""Engineering traceability application service (03B, sections 5.3/8.3; M2.9)."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from synaisthesis.domain.engineering import (
    EVENT_ENGINEERING_ARTIFACT_CREATED,
    EVENT_ENGINEERING_STAGE_OPENED,
    EngineeringStageId,
    build_engineering_event,
    delivery_status_for_stage,
)
from synaisthesis.domain.errors import DomainError
from synaisthesis.domain.traceability import (
    RequirementsTraceabilityMatrix,
    traceability_coverage,
)
from synaisthesis.storage.artifact_store import ArtifactRecord
from synaisthesis.storage.hashing import verify_artifact_hash
from synaisthesis.storage.repositories.event_repository import (
    DomainEventRecord,
    append_domain_event,
)

TRACEABILITY_AGGREGATE_TYPE = "RequirementsTraceabilityMatrix"


def _verified_payload(
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
    import json

    return json.loads(path.read_text(encoding="utf-8"))


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


def record_engineering_trace_edges(
    session: Session,
    *,
    project_id: str,
    matrix: RequirementsTraceabilityMatrix,
    artifact_root: Path,
) -> RequirementsTraceabilityMatrix:
    """Persist a traceability matrix as hash-verified events (03B, section 5.3)."""
    matrix_id = matrix.matrix_id
    stream = _event_stream(session, TRACEABILITY_AGGREGATE_TYPE, matrix_id)
    append_domain_event(
        session,
        build_engineering_event(
            EVENT_ENGINEERING_STAGE_OPENED,
            aggregate_type=TRACEABILITY_AGGREGATE_TYPE,
            aggregate_id=matrix_id,
            payload={
                "stage": "ENG2",
                "delivery_status": delivery_status_for_stage(EngineeringStageId.ENG2).value,
            },
            sequence=len(stream) + 1,
        ),
        project_id=project_id,
        artifact_root=artifact_root,
    )
    append_domain_event(
        session,
        build_engineering_event(
            EVENT_ENGINEERING_ARTIFACT_CREATED,
            aggregate_type=TRACEABILITY_AGGREGATE_TYPE,
            aggregate_id=matrix_id,
            payload={"artifact": matrix.to_event_payload()},
            sequence=len(stream) + 2,
        ),
        project_id=project_id,
        artifact_root=artifact_root,
    )
    return matrix


def load_traceability_matrix(
    session: Session, matrix_id: str, *, artifact_root: Path
) -> RequirementsTraceabilityMatrix:
    from synaisthesis.application.engineering_design_service import rebuild_dataclass

    records = _event_stream(session, TRACEABILITY_AGGREGATE_TYPE, matrix_id)
    if not records:
        raise DomainError(
            f"traceability matrix {matrix_id!r} has no events",
            error_code="PROJECT_NOT_FOUND",
        )
    matrix: RequirementsTraceabilityMatrix | None = None
    for record in records:
        payload = _verified_payload(session, record, artifact_root)
        if record.event_type == EVENT_ENGINEERING_ARTIFACT_CREATED:
            matrix = rebuild_dataclass(RequirementsTraceabilityMatrix, payload["artifact"])
    if matrix is None:
        raise DomainError(
            f"state of {matrix_id!r} is unrecoverable",
            error_code="PROJECT_STATE_UNRECOVERABLE",
        )
    return matrix


def engineering_traceability_report(
    matrix: RequirementsTraceabilityMatrix,
    *,
    requirements: tuple[str, ...],
    design_elements: tuple[str, ...],
    tasks: tuple[str, ...],
    tests: tuple[str, ...],
) -> dict[str, float]:
    """Return the ENG2/ENG5 coverage fractions (03B, sections 5.4/8.3)."""
    return traceability_coverage(
        matrix,
        requirements=requirements,
        design_elements=design_elements,
        tasks=tasks,
        tests=tests,
    )


__all__ = [
    "TRACEABILITY_AGGREGATE_TYPE",
    "engineering_traceability_report",
    "load_traceability_matrix",
    "record_engineering_trace_edges",
]
