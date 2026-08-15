"""Project application service (blueprint 12, application/project_service.py)."""

from __future__ import annotations

import uuid
from pathlib import Path

from sqlalchemy.orm import Session

from synaisthesis.domain.errors import DomainError
from synaisthesis.domain.project import Project
from synaisthesis.storage.repositories.project_repository import (
    load_project,
    save_project,
)


def create_project(
    session: Session,
    *,
    name: str,
    description: str = "",
    artifact_root: Path,
    project_id: str | None = None,
) -> Project:
    """Create a new SEED project and persist it as the first event of its stream."""
    clean_name = name.strip()
    if not clean_name:
        raise DomainError(
            "project name must not be blank",
            error_code="INVALID_PROJECT_NAME",
        )
    project = Project(
        id=project_id or uuid.uuid4().hex,
        name=clean_name,
        description=description,
    )
    save_project(session, project, artifact_root=artifact_root)
    return project


def get_project(session: Session, *, project_id: str, artifact_root: Path) -> Project:
    """Re-read a project by replaying its persisted event stream."""
    return load_project(session, project_id, artifact_root=artifact_root)
