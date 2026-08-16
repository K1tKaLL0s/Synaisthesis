"""DisplayContract: faithful display of platform results to the user (05A, section 20).

Codex may add explanation around the exact summary block but must not modify or
omit it, and must surface every mandatory status, warning and next action. The
Stop Hook audit compares Codex's final message against this contract; omitted
warnings or prohibited overclaims fail the audit.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

from synaisthesis.domain.errors import DomainError
from synaisthesis.domain.event import canonicalize, sha256_hex


@dataclass(frozen=True, slots=True)
class DisplayContract:
    """Immutable display obligations tied to one CommandReceipt (05A, section 20)."""

    display_contract_id: str
    receipt_id: str
    exact_summary_block: str
    mandatory_statuses: tuple[str, ...]
    mandatory_warnings: tuple[str, ...]
    mandatory_next_action: str
    prohibited_claims: tuple[str, ...]
    allowed_paraphrase_fields: tuple[str, ...]
    display_hash: str | None = None

    def __post_init__(self) -> None:
        if not self.display_contract_id.strip() or not self.receipt_id.strip():
            raise DomainError(
                "display contract requires display_contract_id and receipt_id",
                error_code="DISPLAY_CONTRACT_INVALID",
            )
        if not self.exact_summary_block:
            raise DomainError(
                "display contract requires a non-empty exact_summary_block",
                error_code="DISPLAY_CONTRACT_INVALID",
            )
        expected = self._compute_hash()
        if self.display_hash is not None and self.display_hash != expected:
            raise DomainError(
                "display_hash does not match the display contract content",
                error_code="ARTIFACT_HASH_MISMATCH",
            )
        object.__setattr__(self, "display_hash", expected)

    def _compute_hash(self) -> str:
        return sha256_hex(self.content_payload())

    def content_payload(self) -> dict[str, Any]:
        payload = asdict(self)
        payload.pop("display_hash", None)
        return _canonical_object(payload)

    def to_event_payload(self) -> dict[str, Any]:
        return _canonical_object(asdict(self))


def _canonical_object(value: Any) -> dict[str, Any]:
    payload = canonicalize(value)
    if not isinstance(payload, dict):
        raise TypeError("display contract payload must canonicalize to an object")
    return payload


def validate_displayed_message(message: str, contract: DisplayContract) -> tuple[str, ...]:
    """Audit Codex's final message against the DisplayContract (05A, Stop Hook).

    Returns structured issues; an empty tuple means the display is faithful.
    """
    issues: list[str] = []
    if contract.exact_summary_block not in message:
        issues.append("exact_summary_block 被省略或改写")
    for status in contract.mandatory_statuses:
        if status not in message:
            issues.append(f"mandatory_status 缺失: {status}")
    for warning in contract.mandatory_warnings:
        if warning not in message:
            issues.append(f"mandatory_warning 缺失: {warning}")
    if contract.mandatory_next_action and contract.mandatory_next_action not in message:
        issues.append("mandatory_next_action 缺失")
    for claim in contract.prohibited_claims:
        if claim in message:
            issues.append(f"prohibited_claim 出现: {claim}")
    return tuple(issues)
