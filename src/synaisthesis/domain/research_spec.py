"""ResearchSpec aggregate (blueprint 06, section 1, research_specs table).

A confirmed spec is immutable: its content cannot be overwritten in place. Any
content change must create a new version (version + 1) and reset confirmation.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, replace
from datetime import UTC, datetime
from typing import Any

from synaisthesis.domain.errors import ConflictError
from synaisthesis.domain.event import sha256_hex


@dataclass(frozen=True, slots=True)
class ResearchSpec:
    """A versioned, optionally user-confirmed research specification."""

    project_id: str
    version: int
    s1_natural_language_spec: Mapping[str, Any]
    s4_scope_spec: Mapping[str, Any] | None = None
    user_confirmed: bool = False
    confirmed_at: datetime | None = None

    @property
    def is_confirmed(self) -> bool:
        return self.user_confirmed

    @property
    def content_hash(self) -> str:
        """Deterministic content hash over S1 and S4 (excludes version)."""
        return sha256_hex(
            {
                "s1": dict(self.s1_natural_language_spec),
                "s4": dict(self.s4_scope_spec) if self.s4_scope_spec is not None else None,
            }
        )

    def confirm(self, *, at: datetime | None = None) -> ResearchSpec:
        """Return a confirmed copy of this spec."""
        if self.user_confirmed:
            raise ConflictError(f"spec version {self.version} is already confirmed")
        return replace(
            self,
            user_confirmed=True,
            confirmed_at=at if at is not None else datetime.now(UTC),
        )

    def new_version(
        self,
        *,
        s1_natural_language_spec: Mapping[str, Any],
        s4_scope_spec: Mapping[str, Any] | None = None,
    ) -> ResearchSpec:
        """Return a new version; never overwrites the current version."""
        return replace(
            self,
            version=self.version + 1,
            s1_natural_language_spec=s1_natural_language_spec,
            s4_scope_spec=s4_scope_spec,
            user_confirmed=False,
            confirmed_at=None,
        )
