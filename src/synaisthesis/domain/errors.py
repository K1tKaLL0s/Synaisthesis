"""Structured domain errors (blueprint 07, section 19).

Every domain error carries a machine-readable error code plus the optional
fields the blueprint requires for a unified error object. The domain layer must
never surface bare natural-language exceptions.
"""

from __future__ import annotations

from typing import Any


class DomainError(Exception):
    """Base class for all domain errors.

    Follows the unified error object contract in blueprint 07 section 19:
    error_code, message, recoverable, retry_after, blocker_type,
    required_user_action, artifact_refs and trace_id.
    """

    def __init__(
        self,
        message: str,
        *,
        error_code: str = "DOMAIN_ERROR",
        recoverable: bool = False,
        retry_after: float | None = None,
        blocker_type: str | None = None,
        required_user_action: str | None = None,
        artifact_refs: tuple[str, ...] = (),
        trace_id: str | None = None,
    ) -> None:
        super().__init__(message)
        self.error_code = error_code
        self.message = message
        self.recoverable = recoverable
        self.retry_after = retry_after
        self.blocker_type = blocker_type
        self.required_user_action = required_user_action
        self.artifact_refs = artifact_refs
        self.trace_id = trace_id

    def to_dict(self) -> dict[str, Any]:
        """Return the structured error object as a JSON-safe dict."""
        return {
            "error_code": self.error_code,
            "message": self.message,
            "recoverable": self.recoverable,
            "retry_after": self.retry_after,
            "blocker_type": self.blocker_type,
            "required_user_action": self.required_user_action,
            "artifact_refs": list(self.artifact_refs),
            "trace_id": self.trace_id,
        }


class ConflictError(DomainError):
    """Raised when an optimistic-concurrency expected-version check fails.

    See blueprint 07 section 18: a mutation whose expected_version does not
    match the current state must return CONFLICT and must not overwrite.
    """

    def __init__(self, message: str, **kwargs: Any) -> None:
        super().__init__(message, error_code="CONFLICT", **kwargs)


class InvalidEnumValueError(DomainError):
    """Raised when a value is not a member of a strict domain enum."""

    def __init__(self, *, field: str, value: object, allowed: list[str]) -> None:
        message = f"unknown value {value!r} for {field}; allowed: {', '.join(allowed)}"
        super().__init__(message, error_code="INVALID_ENUM_VALUE")
        self.field = field
        self.value = value
        self.allowed = allowed
