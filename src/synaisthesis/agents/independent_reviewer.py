"""Independent track agent skeleton (blueprint 04 §3 IndependentTrack; M6.2).

Phase A is a blind review: the Independent reviewer reads only its own
visibility bundle (FrozenClaim + original ResearchSpec + allowed public
literature), never the Support/Oppose outputs. Constructing it from another
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
class IndependentReviewer:
    """Isolated Independent track session; reads only its own bundle."""

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
    ) -> IndependentReviewer:
        blockers = assert_visibility_scope(
            bundle=bundle,
            consumer_role=CouncilRole.INDEPENDENT,
            consumer_session_id=session_id,
        )
        if blockers:
            raise DomainError(
                "ISOLATION_VIOLATION: " + "; ".join(blockers),
                error_code="ISOLATION_VIOLATION",
            )
        return cls(session_id=session_id, bundle=bundle, model_fingerprint=model_fingerprint)

    def consume(self) -> str:
        """Return the agent's own blind-baseline bundle content."""
        return self.bundle.content


__all__ = ["IndependentReviewer"]
