"""Prepare -> Commit two-phase command (05A, sections 15-17).

High-risk mutations must be prepared first; the PreparedCommand carries a
confirmation nonce and an expiry. Commit never accepts a boolean ``confirmed``
flag: a real user confirmation text is required, and its nonce must match the
prepared command.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime
from typing import Any, cast

from synaisthesis.domain.enums import StrictStrEnum
from synaisthesis.domain.errors import DomainError
from synaisthesis.domain.event import canonicalize


class PreparedCommandStatus(StrictStrEnum):
    """Lifecycle of a PreparedCommand."""

    PREPARED = "PREPARED"
    CONSUMED = "CONSUMED"
    CANCELLED = "CANCELLED"
    SUPERSEDED = "SUPERSEDED"
    EXPIRED = "EXPIRED"


@dataclass(frozen=True, slots=True)
class PreparedCommand:
    """Immutable prepared command awaiting a matching user confirmation (05A, section 16.2)."""

    prepared_command_id: str
    instruction_id: str
    command_id: str
    idempotency_key: str
    expected_state_version: int
    canonical_action_summary: dict[str, Any]
    preserved_constraints: tuple[str, ...]
    intended_state_diff: dict[str, Any]
    cost_permission_impact: dict[str, Any]
    unresolved_ambiguity: tuple[str, ...]
    confirmation_requirement: bool
    confirmation_nonce: str
    created_at: datetime
    expires_at: datetime
    status: PreparedCommandStatus = PreparedCommandStatus.PREPARED

    def __post_init__(self) -> None:
        if not self.prepared_command_id.strip() or not self.command_id.strip():
            raise DomainError(
                "prepared command requires prepared_command_id and command_id",
                error_code="PREPARED_COMMAND_INVALID",
            )
        if not self.instruction_id.strip() or not self.idempotency_key.strip():
            raise DomainError(
                "prepared command requires instruction_id and idempotency_key",
                error_code="PREPARED_COMMAND_INVALID",
            )
        if self.confirmation_requirement and not self.confirmation_nonce.strip():
            raise DomainError(
                "a prepared command that requires confirmation needs a nonce",
                error_code="PREPARED_COMMAND_INVALID",
            )

    def to_event_payload(self) -> dict[str, Any]:
        payload = canonicalize(asdict(self))
        if not isinstance(payload, dict):
            raise TypeError("prepared command payload must canonicalize to an object")
        return payload

    def is_expired(self, now: datetime) -> bool:
        return now >= self.expires_at


def prepared_command_requires_confirmation(
    *,
    operation_class: Any,
    inferred_default: bool = False,
) -> bool:
    """Return whether the operation needs an independent user confirmation.

    R3+ (high-risk) mutations always require confirmation; an inferred-default
    mutation also requires a preview confirmation (05A, sections 11/16.2).
    """
    from synaisthesis.fidelity.instruction_token import OperationClass

    if operation_class is OperationClass.HIGH_RISK_MUTATION:
        return True
    return bool(inferred_default) and operation_class is not OperationClass.READ_ONLY


def prepared_command_from_payload(payload: dict[str, Any]) -> PreparedCommand:
    """Reconstruct a PreparedCommand from a verified event payload."""
    data = dict(payload)
    status = cast(
        PreparedCommandStatus,
        PreparedCommandStatus.parse(
            data.get("status", PreparedCommandStatus.PREPARED.value), field="status"
        ),
    )
    return PreparedCommand(
        prepared_command_id=str(data["prepared_command_id"]),
        instruction_id=str(data["instruction_id"]),
        command_id=str(data["command_id"]),
        idempotency_key=str(data["idempotency_key"]),
        expected_state_version=int(data["expected_state_version"]),
        canonical_action_summary=dict(data.get("canonical_action_summary", {})),
        preserved_constraints=tuple(data.get("preserved_constraints", ())),
        intended_state_diff=dict(data.get("intended_state_diff", {})),
        cost_permission_impact=dict(data.get("cost_permission_impact", {})),
        unresolved_ambiguity=tuple(data.get("unresolved_ambiguity", ())),
        confirmation_requirement=bool(data.get("confirmation_requirement", False)),
        confirmation_nonce=str(data.get("confirmation_nonce", "")),
        created_at=datetime.fromisoformat(str(data["created_at"])),
        expires_at=datetime.fromisoformat(str(data["expires_at"])),
        status=status,
    )


def validate_prepared_for_commit(
    prepared: PreparedCommand,
    *,
    confirmation_nonce: str,
    user_confirmation_text: str | None,
    now: datetime,
) -> tuple[str, ...]:
    """Return structured failure codes; empty tuple means the commit may proceed.

    Confirmation is anti-forged (05A, section 17): a boolean ``confirmed`` flag is
    never accepted; the caller must supply the user's confirmation text, and the
    nonce must match the prepared command exactly.
    """
    if prepared.status is not PreparedCommandStatus.PREPARED:
        return ("PREPARED_COMMAND_" + prepared.status.value,)
    if prepared.is_expired(now):
        return ("PREPARED_COMMAND_EXPIRED",)
    if prepared.confirmation_nonce != confirmation_nonce:
        return ("CONFIRMATION_NONCE_MISMATCH",)
    if prepared.confirmation_requirement and not (user_confirmation_text or "").strip():
        return ("CONFIRMATION_REQUIRES_USER_EVENT",)
    return ()
