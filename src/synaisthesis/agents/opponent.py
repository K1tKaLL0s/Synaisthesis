"""Oppose track agent skeleton (blueprint 04 §3 OpposeTrack; M6.2).

An Opponent consumes only its own visibility bundle; it never shares context
with the Support or Independent tracks. Attempting to construct it from another
track's bundle fails closed with ``ISOLATION_VIOLATION``.
"""

from __future__ import annotations

from dataclasses import dataclass

from synaisthesis.domain.errors import DomainError
from synaisthesis.domain.isolation import (
    CouncilRole,
    ModelFamilyFingerprint,
    VisibilityBundle,
    assert_visibility_scope,
)


@dataclass(frozen=True, slots=True)
class Opponent:
    """Isolated Oppose track session; reads only its own bundle."""

    session_id: str
    bundle: VisibilityBundle
    model_fingerprint: ModelFamilyFingerprint

    @classmethod
    def create(
        cls,
        *,
        session_id: str,
        bundle: VisibilityBundle,
        model_fingerprint: ModelFamilyFingerprint,
    ) -> Opponent:
        blockers = assert_visibility_scope(
            bundle=bundle,
            consumer_role=CouncilRole.OPPOSE,
            consumer_session_id=session_id,
        )
        if blockers:
            raise DomainError(
                "ISOLATION_VIOLATION: " + "; ".join(blockers),
                error_code="ISOLATION_VIOLATION",
            )
        return cls(session_id=session_id, bundle=bundle, model_fingerprint=model_fingerprint)

    def consume(self) -> str:
        """Return the agent's own bundle content; no other track is read."""
        return self.bundle.content


__all__ = ["Opponent"]
