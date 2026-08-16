"""CommandReceipt: faithful platform result returned to Codex (05A, section 20).

The receipt records exactly what was executed, the state version before/after,
accepted/rejected parameters, preserved constraints, side effects and gates. Its
receipt_hash is a deterministic SHA-256 over that content, so a tampered receipt
fails closed.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, cast

from synaisthesis.domain.enums import StrictStrEnum
from synaisthesis.domain.errors import DomainError
from synaisthesis.domain.event import canonicalize, sha256_hex


class CommandReceiptStatus(StrictStrEnum):
    """Outcome recorded on a CommandReceipt."""

    COMMITTED = "COMMITTED"
    REJECTED = "REJECTED"
    FAILED_CLOSED = "FAILED_CLOSED"


@dataclass(frozen=True, slots=True)
class CommandReceipt:
    """Immutable receipt of one executed (or failed-closed) command (05A, section 20)."""

    command_id: str
    instruction_id: str
    executed_operation: str
    target: dict[str, Any]
    starting_state_version: int
    ending_state_version: int
    accepted_parameters: dict[str, Any]
    rejected_parameters: dict[str, Any]
    preserved_constraints: tuple[str, ...]
    side_effects: tuple[str, ...]
    evidence_ids: tuple[str, ...]
    pending_gate_ids: tuple[str, ...]
    cost_used: dict[str, Any]
    status: CommandReceiptStatus
    receipt_hash: str | None = None

    def __post_init__(self) -> None:
        if not self.command_id.strip() or not self.instruction_id.strip():
            raise DomainError(
                "command receipt requires command_id and instruction_id",
                error_code="COMMAND_RECEIPT_INVALID",
            )
        if self.ending_state_version < self.starting_state_version:
            raise DomainError(
                "ending_state_version must be >= starting_state_version",
                error_code="COMMAND_RECEIPT_INVALID",
            )
        expected = self._compute_hash()
        if self.receipt_hash is not None and self.receipt_hash != expected:
            raise DomainError(
                "receipt_hash does not match the receipt content",
                error_code="ARTIFACT_HASH_MISMATCH",
            )
        object.__setattr__(self, "receipt_hash", expected)

    def _compute_hash(self) -> str:
        return sha256_hex(self.content_payload())

    def content_payload(self) -> dict[str, Any]:
        payload = asdict(self)
        payload.pop("receipt_hash", None)
        return _canonical_object(payload)

    def to_event_payload(self) -> dict[str, Any]:
        return _canonical_object(asdict(self))


def _canonical_object(value: Any) -> dict[str, Any]:
    payload = canonicalize(value)
    if not isinstance(payload, dict):
        raise TypeError("command receipt payload must canonicalize to an object")
    return payload


def command_receipt_from_payload(payload: dict[str, Any]) -> CommandReceipt:
    """Reconstruct a CommandReceipt from a verified event payload."""
    data = dict(payload)
    status = cast(
        CommandReceiptStatus,
        CommandReceiptStatus.parse(
            data.get("status", CommandReceiptStatus.COMMITTED.value), field="status"
        ),
    )
    return CommandReceipt(
        command_id=str(data["command_id"]),
        instruction_id=str(data["instruction_id"]),
        executed_operation=str(data["executed_operation"]),
        target=dict(data.get("target", {})),
        starting_state_version=int(data["starting_state_version"]),
        ending_state_version=int(data["ending_state_version"]),
        accepted_parameters=dict(data.get("accepted_parameters", {})),
        rejected_parameters=dict(data.get("rejected_parameters", {})),
        preserved_constraints=tuple(data.get("preserved_constraints", ())),
        side_effects=tuple(data.get("side_effects", ())),
        evidence_ids=tuple(data.get("evidence_ids", ())),
        pending_gate_ids=tuple(data.get("pending_gate_ids", ())),
        cost_used=dict(data.get("cost_used", {})),
        status=status,
        receipt_hash=data.get("receipt_hash"),
    )
