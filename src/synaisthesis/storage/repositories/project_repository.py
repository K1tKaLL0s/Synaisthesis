"""Event-sourced project repository (blueprint 12, storage/repositories/project_repository.py).

M1.4 scope: a Project is persisted as an ordered stream of DomainEvents whose
canonical JSON payloads live in content-addressed artifacts, so the state can
always be re-built from the event store without a dedicated projects table
(see workspace/workunit-contracts/M1.4.PROJECT.VERTICAL_SLICE.md, GAP-2).
"""

from __future__ import annotations

import json
from collections.abc import Mapping
from datetime import datetime
from pathlib import Path
from typing import Any, cast

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from synaisthesis.domain.enums import ProjectLifecycleStatus
from synaisthesis.domain.errors import DomainError
from synaisthesis.domain.event import DomainEvent
from synaisthesis.domain.project import Project
from synaisthesis.storage.artifact_store import ArtifactRecord
from synaisthesis.storage.hashing import verify_artifact_hash
from synaisthesis.storage.repositories.event_repository import (
    DomainEventRecord,
    append_domain_event,
)

PROJECT_AGGREGATE_TYPE = "Project"
EVENT_PROJECT_CREATED = "ProjectCreated"
EVENT_PROJECT_LIFECYCLE_CHANGED = "ProjectLifecycleChanged"


def project_state_dict(project: Project) -> dict[str, Any]:
    """Return the project state as a dict for canonical JSON serialization."""
    return {
        "id": project.id,
        "name": project.name,
        "description": project.description,
        "lifecycle_status": project.lifecycle_status,
        "created_at": project.created_at,
        "updated_at": project.updated_at,
    }


def project_from_state(state: Mapping[str, Any]) -> Project:
    """Rebuild a Project aggregate from a persisted state mapping."""
    return Project(
        id=str(state["id"]),
        name=str(state["name"]),
        description=str(state["description"]),
        lifecycle_status=cast(
            ProjectLifecycleStatus,
            ProjectLifecycleStatus.parse(state["lifecycle_status"]),
        ),
        created_at=datetime.fromisoformat(str(state["created_at"])),
        updated_at=datetime.fromisoformat(str(state["updated_at"])),
    )


def save_project(session: Session, project: Project, *, artifact_root: Path) -> DomainEventRecord:
    """Append the project's current state as the next event of its stream.

    The first event is ProjectCreated carrying the full state; later events are
    ProjectLifecycleChanged carrying only the lifecycle delta. Sequences are
    strictly increasing per aggregate and derived from the persisted count.
    """
    sequence = (
        session.execute(
            select(func.count(DomainEventRecord.id)).where(
                DomainEventRecord.aggregate_type == PROJECT_AGGREGATE_TYPE,
                DomainEventRecord.aggregate_id == project.id,
            )
        ).scalar_one()
        + 1
    )
    if sequence == 1:
        event_type = EVENT_PROJECT_CREATED
        payload: dict[str, Any] = project_state_dict(project)
    else:
        event_type = EVENT_PROJECT_LIFECYCLE_CHANGED
        payload = {
            "lifecycle_status": project.lifecycle_status,
            "updated_at": project.updated_at,
        }
    event = DomainEvent(
        aggregate_type=PROJECT_AGGREGATE_TYPE,
        aggregate_id=project.id,
        event_type=event_type,
        payload=payload,
        sequence=sequence,
    )
    return append_domain_event(session, event, project_id=project.id, artifact_root=artifact_root)


def _verified_payload(
    session: Session, record: DomainEventRecord, artifact_root: Path
) -> dict[str, Any]:
    """Read and verify a payload artifact; fail closed when it cannot be trusted."""
    if record.event_payload_artifact_id is None:
        raise DomainError(
            f"event {record.id} has no payload artifact; state unrecoverable",
            error_code="ARTIFACT_HASH_MISMATCH",
        )
    artifact = session.get(ArtifactRecord, record.event_payload_artifact_id)
    if artifact is None:
        raise DomainError(
            f"payload artifact {record.event_payload_artifact_id} of event "
            f"{record.id} is missing; state unrecoverable",
            error_code="ARTIFACT_HASH_MISMATCH",
        )
    path = artifact_root / artifact.relative_path
    if not verify_artifact_hash(path, artifact.sha256):
        raise DomainError(
            f"payload artifact of event {record.id} is missing or tampered; state unrecoverable",
            error_code="ARTIFACT_HASH_MISMATCH",
        )
    return json.loads(path.read_text(encoding="utf-8"))


def load_project(session: Session, project_id: str, *, artifact_root: Path) -> Project:
    """Replay the project's ordered event stream and return the rebuilt state.

    Every payload artifact is hash-verified before it is applied, so a missing
    or tampered record never yields a partial or guessed project state.
    """
    records = (
        session.execute(
            select(DomainEventRecord)
            .where(
                DomainEventRecord.aggregate_type == PROJECT_AGGREGATE_TYPE,
                DomainEventRecord.aggregate_id == project_id,
            )
            .order_by(DomainEventRecord.id)
        )
        .scalars()
        .all()
    )
    if not records:
        raise DomainError(
            f"project {project_id!r} has no events",
            error_code="PROJECT_NOT_FOUND",
        )
    project: Project | None = None
    for record in records:
        payload = _verified_payload(session, record, artifact_root)
        if record.event_type == EVENT_PROJECT_CREATED:
            project = project_from_state(payload)
        elif record.event_type == EVENT_PROJECT_LIFECYCLE_CHANGED:
            if project is None:
                raise DomainError(
                    f"event stream of {project_id!r} starts with "
                    f"{record.event_type!r}; state unrecoverable",
                    error_code="PROJECT_STATE_UNRECOVERABLE",
                )
            project = project.change_lifecycle(
                cast(
                    ProjectLifecycleStatus,
                    ProjectLifecycleStatus.parse(payload["lifecycle_status"]),
                ),
                at=datetime.fromisoformat(str(payload["updated_at"])),
            )
        else:
            raise DomainError(
                f"unknown event type {record.event_type!r} for {project_id!r}; state unrecoverable",
                error_code="PROJECT_STATE_UNRECOVERABLE",
            )
    if project is None:
        raise DomainError(
            f"state of {project_id!r} is unrecoverable",
            error_code="PROJECT_STATE_UNRECOVERABLE",
        )
    return project
