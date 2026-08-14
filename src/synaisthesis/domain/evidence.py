"""Evidence aggregate (blueprint 06, section 1, evidence table).

Revocation preserves history: revoke() returns a new Evidence with revoked_at
set; the original record is never mutated or deleted.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import datetime

from synaisthesis.domain.enums import EvidenceStrength, EvidenceType, ProvenanceType
from synaisthesis.domain.errors import ConflictError


@dataclass(frozen=True, slots=True)
class Evidence:
    """An immutable piece of evidence."""

    id: str
    evidence_type: EvidenceType
    provenance_type: ProvenanceType
    strength: EvidenceStrength
    scope: str
    artifact_id: str
    created_at: datetime
    revoked_at: datetime | None = None
    claim_id: str | None = None
    revision_id: str | None = None

    @property
    def is_revoked(self) -> bool:
        return self.revoked_at is not None

    def revoke(self, *, at: datetime) -> Evidence:
        """Return a revoked copy; the original evidence is preserved."""
        if self.revoked_at is not None:
            raise ConflictError(f"evidence {self.id} is already revoked")
        return replace(self, revoked_at=at)
