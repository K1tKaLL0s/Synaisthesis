"""Project aggregate (blueprint 06, section 1, projects table).

A Project is an immutable entity: lifecycle changes produce a new Project
instance rather than mutating the original.
"""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from datetime import UTC, datetime

from synaisthesis.domain.enums import ProjectLifecycleStatus


@dataclass(frozen=True, slots=True)
class Project:
    """An immutable research project."""

    id: str
    name: str
    description: str = ""
    lifecycle_status: ProjectLifecycleStatus = ProjectLifecycleStatus.SEED
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    def change_lifecycle(
        self,
        new_status: ProjectLifecycleStatus,
        *,
        at: datetime | None = None,
    ) -> Project:
        """Return a new Project with the lifecycle status updated."""
        return replace(
            self,
            lifecycle_status=new_status,
            updated_at=at if at is not None else datetime.now(UTC),
        )
