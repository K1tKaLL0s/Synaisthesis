"""Content-addressed artifact store (blueprint 06 section 7, 12 storage/artifact_store.py)."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

from sqlalchemy.orm import Mapped, Session, mapped_column

from synaisthesis.storage.database import Base
from synaisthesis.storage.hashing import sha256_bytes


class ArtifactRecord(Base):
    """The artifacts table (blueprint 06, section 1)."""

    __tablename__ = "artifacts"

    id: Mapped[int] = mapped_column(primary_key=True)
    project_id: Mapped[str | None] = mapped_column(default=None)
    relative_path: Mapped[str]
    media_type: Mapped[str]
    sha256: Mapped[str]
    immutable: Mapped[bool] = mapped_column(default=True)
    created_at: Mapped[datetime] = mapped_column(default=lambda: datetime.now(UTC))


def save_artifact(
    session: Session,
    *,
    project_id: str | None,
    relative_path: str,
    media_type: str,
    content: bytes,
    artifact_root: Path,
) -> ArtifactRecord:
    """Write content to disk and record it, addressed by its SHA-256.

    The SHA-256 of the content is the immutable identity of the artifact, so
    identical content always maps to the same hash.
    """
    sha = sha256_bytes(content)
    target = artifact_root / relative_path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(content)
    record = ArtifactRecord(
        project_id=project_id,
        relative_path=relative_path,
        media_type=media_type,
        sha256=sha,
        immutable=True,
        created_at=datetime.now(UTC),
    )
    session.add(record)
    return record
