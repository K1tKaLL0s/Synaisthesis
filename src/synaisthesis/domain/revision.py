"""Revision aggregate (immutable chain; blueprint 06, section 1, revisions).

Every change to evolving content creates a new Revision linked to its parent;
revisions are never modified in place, so history is preserved.
"""

from __future__ import annotations

from dataclasses import dataclass

from synaisthesis.domain.event import sha256_hex


@dataclass(frozen=True, slots=True)
class Revision:
    """An immutable revision; new content always creates a new Revision."""

    id: str
    parent_revision_id: str | None
    natural_language_statement: str
    semantic_delta_level: int
    created_by: str

    @property
    def immutable_hash(self) -> str:
        """Deterministic hash over content and ancestry."""
        return sha256_hex(
            {
                "parent_revision_id": self.parent_revision_id,
                "natural_language_statement": self.natural_language_statement,
                "semantic_delta_level": self.semantic_delta_level,
                "created_by": self.created_by,
            }
        )

    def create_child(
        self,
        *,
        id: str,
        natural_language_statement: str,
        semantic_delta_level: int,
        created_by: str,
    ) -> Revision:
        """Return a new Revision chained to this one as its parent."""
        return Revision(
            id=id,
            parent_revision_id=self.id,
            natural_language_statement=natural_language_statement,
            semantic_delta_level=semantic_delta_level,
            created_by=created_by,
        )
