"""InstructionCapsule: the authoritative carrier of the raw user instruction (05A, section 7).

The platform's final semantic source of truth is the immutable InstructionCapsule,
never a Codex paraphrase. The raw user text is preserved verbatim and its SHA-256
is re-computable; a capsule whose stored hash does not cover the text fails closed.
"""

from __future__ import annotations

import hashlib
from dataclasses import asdict, dataclass
from datetime import datetime
from typing import Any, cast

from synaisthesis.domain.enums import StrictStrEnum
from synaisthesis.domain.errors import DomainError
from synaisthesis.domain.event import canonicalize, sha256_hex


class InstructionActor(StrictStrEnum):
    """Author of a captured instruction (05A, section 7)."""

    HUMAN_USER = "HUMAN_USER"


class InstructionStatus(StrictStrEnum):
    """Lifecycle of an InstructionCapsule."""

    CAPTURED = "CAPTURED"
    SUPERSEDED = "SUPERSEDED"
    REVOKED = "REVOKED"


def raw_user_text_sha256(raw_user_text: str) -> str:
    """Return the SHA-256 of the raw user text bytes (verbatim, not JSON-wrapped)."""
    return hashlib.sha256(raw_user_text.encode("utf-8")).hexdigest()


@dataclass(frozen=True, slots=True)
class InstructionCapsule:
    """Immutable verbatim instruction captured by the UserPromptSubmit Hook (05A, section 7)."""

    instruction_id: str
    session_id: str
    turn_id: str
    raw_user_text: str
    project_binding_id: str | None = None
    actor_type: InstructionActor = InstructionActor.HUMAN_USER
    raw_user_text_hash: str | None = None
    submitted_at: datetime | None = None
    cwd: str = ""
    active_model: str | None = None
    permission_mode: str | None = None
    sequence_number: int = 1
    supersedes_instruction_id: str | None = None
    context_manifest_id: str | None = None
    capture_source: str = "codex-user-prompt-submit"
    hook_version: str | None = None
    plugin_version: str | None = None
    bridge_version: str | None = None
    privacy_class: str = "PRIVATE"
    retention_policy: str = "DEFAULT"
    status: InstructionStatus = InstructionStatus.CAPTURED

    def __post_init__(self) -> None:
        if not self.instruction_id.strip() or not self.session_id.strip():
            raise DomainError(
                "instruction capsule requires instruction_id and session_id",
                error_code="INSTRUCTION_CAPSULE_INVALID",
            )
        if not self.turn_id.strip():
            raise DomainError(
                "instruction capsule requires turn_id",
                error_code="INSTRUCTION_CAPSULE_INVALID",
            )
        expected = raw_user_text_sha256(self.raw_user_text)
        if self.raw_user_text_hash is not None and self.raw_user_text_hash != expected:
            raise DomainError(
                "raw_user_text_hash does not match the raw user text",
                error_code="RAW_HASH_MISMATCH",
            )
        object.__setattr__(self, "raw_user_text_hash", expected)

    def content_payload(self) -> dict[str, Any]:
        """Return the canonical semantic content (excludes derived hash/status)."""
        payload = asdict(self)
        payload.pop("raw_user_text_hash", None)
        payload.pop("status", None)
        return _canonical_object(payload)

    def content_hash(self) -> str:
        """Deterministic hash over the semantic content of the capsule."""
        return sha256_hex(self.content_payload())

    def to_event_payload(self) -> dict[str, Any]:
        """Return the full canonical payload for the InstructionCaptured event."""
        return _canonical_object(asdict(self))


def _canonical_object(value: Any) -> dict[str, Any]:
    payload = canonicalize(value)
    if not isinstance(payload, dict):
        raise TypeError("instruction payload must canonicalize to an object")
    return payload


def instruction_capsule_from_payload(payload: dict[str, Any]) -> InstructionCapsule:
    """Reconstruct a capsule from a verified event payload; fail closed on hash drift."""
    data = dict(payload)
    actor_type = cast(
        InstructionActor,
        InstructionActor.parse(data.get("actor_type", InstructionActor.HUMAN_USER.value)),
    )
    status = cast(
        InstructionStatus,
        InstructionStatus.parse(data.get("status", InstructionStatus.CAPTURED.value)),
    )
    submitted_at = data.get("submitted_at")
    if submitted_at is not None:
        submitted_at = datetime.fromisoformat(str(submitted_at))
    return InstructionCapsule(
        instruction_id=str(data["instruction_id"]),
        session_id=str(data["session_id"]),
        turn_id=str(data["turn_id"]),
        project_binding_id=data.get("project_binding_id"),
        actor_type=actor_type,
        raw_user_text=str(data.get("raw_user_text", "")),
        raw_user_text_hash=data.get("raw_user_text_hash"),
        submitted_at=submitted_at,
        cwd=str(data.get("cwd", "")),
        active_model=data.get("active_model"),
        permission_mode=data.get("permission_mode"),
        sequence_number=int(data.get("sequence_number", 1)),
        supersedes_instruction_id=data.get("supersedes_instruction_id"),
        context_manifest_id=data.get("context_manifest_id"),
        capture_source=str(data.get("capture_source", "codex-user-prompt-submit")),
        hook_version=data.get("hook_version"),
        plugin_version=data.get("plugin_version"),
        bridge_version=data.get("bridge_version"),
        privacy_class=str(data.get("privacy_class", "PRIVATE")),
        retention_policy=str(data.get("retention_policy", "DEFAULT")),
        status=status,
    )
