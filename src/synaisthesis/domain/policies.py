"""Version and idempotency invariants for mutations (blueprint 07, section 18).

Every mutation accepts an idempotency key, a trace id and an expected version.
When the expected version does not match the current state the operation must
return CONFLICT and must not overwrite.
"""

from __future__ import annotations

from dataclasses import dataclass

from synaisthesis.domain.errors import ConflictError


@dataclass(frozen=True, slots=True)
class IdempotencyContext:
    """Identity fields attached to every mutation."""

    idempotency_key: str
    trace_id: str
    expected_version: int | None = None


def check_expected_version(
    expected: int | None,
    actual: int,
    *,
    trace_id: str | None = None,
) -> None:
    """Raise ConflictError when expected differs from actual.

    expected=None means no optimistic-concurrency check is requested and the
    check is skipped.
    """
    if expected is not None and expected != actual:
        raise ConflictError(
            f"expected_version={expected!r} does not match actual={actual!r}",
            trace_id=trace_id,
        )
