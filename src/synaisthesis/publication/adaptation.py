"""Venue-adapted engineering manuscript (03B, section 12.3; M2.11).

The adapted manuscript is mechanically derived from the master plus a
PublicationProfile; the master is never overwritten.  arXiv packages are only
ever ARXIV_PACKAGE_READY and must not claim journal/peer-review status.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime
from typing import Any

from synaisthesis.domain.engineering import finalize_artifact_hash
from synaisthesis.domain.enums import StrictStrEnum
from synaisthesis.domain.errors import DomainError
from synaisthesis.domain.event import canonicalize


class VenueAdaptedManuscriptStatus(StrictStrEnum):
    """Statuses of a venue-adapted manuscript (03B, sections 12.3/13.3)."""

    VENUE_ADAPTATION_DRAFT = "VENUE_ADAPTATION_DRAFT"
    FORMAL_MANUSCRIPT_READY = "FORMAL_MANUSCRIPT_READY"
    ARXIV_PACKAGE_READY = "ARXIV_PACKAGE_READY"


def _canonical_payload(value: Any) -> dict[str, Any]:
    payload = canonicalize(value)
    if not isinstance(payload, dict):
        raise TypeError("adaptation payload must canonicalize to an object")
    return payload


@dataclass(frozen=True, slots=True)
class VenueAdaptedManuscript:
    """One derived venue adaptation; conversion never mutates the master."""

    adapted_id: str
    version: int
    project_id: str
    master_manuscript_id: str
    master_version: int
    master_hash: str
    profile_id: str
    profile_hash: str
    conversion_record: str
    compliance_matrix_id: str
    adapted_text: str
    status: VenueAdaptedManuscriptStatus
    artifact_hash: str | None = None
    created_at: datetime | None = None

    def __post_init__(self) -> None:
        if not self.adapted_text.strip():
            raise DomainError(
                f"adapted manuscript {self.adapted_id!r} 为空",
                error_code="ADAPTED_MANUSCRIPT_INVALID",
            )
        finalize_artifact_hash(self)

    def content_payload(self) -> dict[str, Any]:
        payload = asdict(self)
        payload.pop("artifact_hash", None)
        payload.pop("status", None)
        return _canonical_payload(payload)

    def to_event_payload(self) -> dict[str, Any]:
        return _canonical_payload(asdict(self))


__all__ = [
    "VenueAdaptedManuscript",
    "VenueAdaptedManuscriptStatus",
]
