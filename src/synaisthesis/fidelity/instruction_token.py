"""InstructionToken: short-lived signed token for one mutation (05A, section 8).

Codex cannot fabricate a user instruction by freely generating parameters: every
mutation token must carry a valid HMAC-SHA256 signature over the bound
instruction identity, session/turn, project, raw-text hash and state version.
"""

from __future__ import annotations

import hashlib
import hmac
from dataclasses import asdict, dataclass, replace
from datetime import datetime
from typing import Any

from synaisthesis.domain.enums import StrictStrEnum
from synaisthesis.domain.errors import DomainError
from synaisthesis.domain.event import canonical_json


class OperationClass(StrictStrEnum):
    """Operation class authorized by an InstructionToken (05A, section 8)."""

    READ_ONLY = "READ_ONLY"
    LOW_RISK_MUTATION = "LOW_RISK_MUTATION"
    HIGH_RISK_MUTATION = "HIGH_RISK_MUTATION"


_OPERATION_CLASS_RANK: dict[OperationClass, int] = {
    OperationClass.READ_ONLY: 0,
    OperationClass.LOW_RISK_MUTATION: 1,
    OperationClass.HIGH_RISK_MUTATION: 2,
}


def token_authorizes(token: InstructionToken, operation_class: OperationClass) -> bool:
    """Return True when the token authorizes at least the requested operation class."""
    return (
        _OPERATION_CLASS_RANK[token.allowed_operation_class]
        >= _OPERATION_CLASS_RANK[operation_class]
    )


@dataclass(frozen=True, slots=True)
class InstructionToken:
    """Signed short-term token for a single mutation path (05A, section 8)."""

    instruction_id: str
    session_id: str
    turn_id: str
    project_id: str
    raw_user_text_hash: str
    allowed_operation_class: OperationClass
    issued_at: datetime
    expires_at: datetime
    nonce: str
    state_version: int
    signer_key_id: str
    signature: str = ""

    def __post_init__(self) -> None:
        if not self.instruction_id.strip() or not self.project_id.strip():
            raise DomainError(
                "instruction token requires instruction_id and project_id",
                error_code="INSTRUCTION_TOKEN_INVALID",
            )
        if not self.nonce.strip() or not self.signer_key_id.strip():
            raise DomainError(
                "instruction token requires nonce and signer_key_id",
                error_code="INSTRUCTION_TOKEN_INVALID",
            )

    def signing_payload(self) -> dict[str, Any]:
        """Return the canonical payload the signature covers (everything but the signature)."""
        payload = asdict(self)
        payload.pop("signature", None)
        return payload


def sign_instruction_token(token: InstructionToken, *, signing_key: bytes) -> InstructionToken:
    """Return a copy of the token carrying a valid HMAC-SHA256 signature."""
    signature = _hmac_signature(token.signing_payload(), signing_key)
    return replace(token, signature=signature)


def _hmac_signature(payload: dict[str, Any], signing_key: bytes) -> str:
    message = canonical_json(payload).encode("utf-8")
    return hmac.new(signing_key, message, hashlib.sha256).hexdigest()


def verify_instruction_token(
    token: InstructionToken,
    *,
    signing_key: bytes,
    expected_session_id: str,
    expected_turn_id: str,
    expected_project_id: str,
    expected_raw_text_hash: str,
    now: datetime,
) -> tuple[str, ...]:
    """Return structured failure codes; an empty tuple means the token is trusted.

    A token is trusted only when its signature is valid, it has not expired, and
    every bound identity field matches the expected values. Any mismatch fails
    closed instead of guessing.
    """
    if token.signature and not hmac.compare_digest(
        token.signature, _hmac_signature(token.signing_payload(), signing_key)
    ):
        return ("INVALID_INSTRUCTION_TOKEN",)
    if not token.signature:
        return ("INVALID_INSTRUCTION_TOKEN",)
    if now >= token.expires_at:
        return ("TOKEN_EXPIRED",)
    mismatches: list[str] = []
    if token.session_id != expected_session_id:
        mismatches.append("session_id")
    if token.turn_id != expected_turn_id:
        mismatches.append("turn_id")
    if token.project_id != expected_project_id:
        mismatches.append("project_id")
    if token.raw_user_text_hash != expected_raw_text_hash:
        mismatches.append("raw_user_text_hash")
    if mismatches:
        return ("TOKEN_MISMATCH",)
    return ()
