"""Immutable domain event with stable serialization and content hashing.

The event record mirrors the domain_events table in blueprint 06, section 1.
event_hash is a deterministic SHA-256 over the content (aggregate type and id,
event type, payload, sequence and timestamp) so tampering is detectable and
replay is stable; it deliberately excludes the random event_id.
"""

from __future__ import annotations

import hashlib
import json
import uuid
from collections.abc import Mapping
from dataclasses import dataclass, field
from datetime import UTC, date, datetime
from enum import Enum
from typing import Any


def _canonicalize(value: Any) -> Any:
    """Recursively convert a value into a canonical, JSON-safe form."""
    if isinstance(value, Mapping):
        return {key: _canonicalize(item) for key, item in sorted(value.items())}
    if isinstance(value, (list, tuple, set, frozenset)):
        return [_canonicalize(item) for item in value]
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    raise TypeError(f"cannot canonicalize value of type {type(value).__name__}")


def _canonical_json(value: Any) -> str:
    return json.dumps(
        _canonicalize(value),
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    )


@dataclass(frozen=True, slots=True)
class DomainEvent:
    """An immutable domain event (blueprint 06, section 1, domain_events)."""

    aggregate_type: str
    aggregate_id: str
    event_type: str
    payload: Mapping[str, Any]
    sequence: int
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    event_id: str = field(default_factory=lambda: str(uuid.uuid4()))

    def _content_dict(self) -> dict[str, Any]:
        return {
            "aggregate_type": self.aggregate_type,
            "aggregate_id": self.aggregate_id,
            "event_type": self.event_type,
            "payload": self.payload,
            "sequence": self.sequence,
            "created_at": self.created_at.isoformat(),
        }

    @property
    def event_hash(self) -> str:
        """Deterministic SHA-256 content hash (excludes event_id)."""
        digest = hashlib.sha256(_canonical_json(self._content_dict()).encode("utf-8"))
        return digest.hexdigest()

    def to_dict(self) -> dict[str, Any]:
        """Return the full event record as a JSON-safe dict."""
        return {
            "event_id": self.event_id,
            "aggregate_type": self.aggregate_type,
            "aggregate_id": self.aggregate_id,
            "event_type": self.event_type,
            "payload": dict(self.payload),
            "sequence": self.sequence,
            "created_at": self.created_at.isoformat(),
            "event_hash": self.event_hash,
        }

    def to_json(self) -> str:
        """Return the canonical, deterministically-ordered JSON serialization."""
        return _canonical_json(self.to_dict())
