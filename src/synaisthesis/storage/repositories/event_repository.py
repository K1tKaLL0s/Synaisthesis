"""Domain event repository (blueprint 12, storage/repositories/event_repository.py)."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, Session, mapped_column

from synaisthesis.domain.event import DomainEvent, canonical_json
from synaisthesis.storage.artifact_store import save_artifact
from synaisthesis.storage.database import Base


class DomainEventRecord(Base):
    """The domain_events table (blueprint 06, section 1)."""

    __tablename__ = "domain_events"

    id: Mapped[int] = mapped_column(primary_key=True)
    project_id: Mapped[str | None] = mapped_column(default=None)
    aggregate_type: Mapped[str]
    aggregate_id: Mapped[str]
    event_type: Mapped[str]
    event_payload_artifact_id: Mapped[int | None] = mapped_column(
        ForeignKey("artifacts.id"), default=None
    )
    event_hash: Mapped[str]
    created_at: Mapped[datetime]


def append_domain_event(
    session: Session,
    event: DomainEvent,
    *,
    project_id: str | None,
    artifact_root: Path,
) -> DomainEventRecord:
    """Persist a domain event with its payload as a content-addressed artifact.

    Events are appended in call order; the autoincrement primary key provides a
    stable monotonic ordering across reads.
    """
    payload_bytes = canonical_json(dict(event.payload)).encode("utf-8")
    artifact = save_artifact(
        session,
        project_id=project_id,
        relative_path=f"events/{event.aggregate_id}/{event.event_id}.json",
        media_type="application/json",
        content=payload_bytes,
        artifact_root=artifact_root,
    )
    session.flush()  # assign the artifact's autoincrement id
    record = DomainEventRecord(
        project_id=project_id,
        aggregate_type=event.aggregate_type,
        aggregate_id=event.aggregate_id,
        event_type=event.event_type,
        event_payload_artifact_id=artifact.id,
        event_hash=event.event_hash,
        created_at=event.created_at,
    )
    session.add(record)
    return record
