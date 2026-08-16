"""Codex session binding (05A, section 6).

A Codex thread is bound to one Synaisthesis project by a real user instruction;
Codex can never silently bind another project. The binding is the durable
anchor that ties every later InstructionToken and mutation to the same project
and mode.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime
from typing import Any

from synaisthesis.domain.enums import StrictStrEnum
from synaisthesis.domain.errors import DomainError
from synaisthesis.domain.event import canonicalize


class FidelityMode(StrictStrEnum):
    """Codex operation modes (05A, section 5)."""

    STRICT_BOUND_SESSION = "STRICT_BOUND_SESSION"
    EXPLICIT_RESEARCHLOOP_COMMAND = "EXPLICIT_RESEARCHLOOP_COMMAND"
    RELAXED_READ_ONLY = "RELAXED_READ_ONLY"


class FidelitySurfaceStatus(StrictStrEnum):
    """Explicit per-session capability declaration (05A, section 22)."""

    FIDELITY_VERIFIED = "FIDELITY_VERIFIED"
    FIDELITY_DEGRADED_READ_ONLY = "FIDELITY_DEGRADED_READ_ONLY"
    FIDELITY_UNAVAILABLE = "FIDELITY_UNAVAILABLE"


class SessionBindingStatus(StrictStrEnum):
    """Lifecycle of a CodexSessionBinding."""

    ACTIVE = "ACTIVE"
    EXPIRED = "EXPIRED"
    REVOKED = "REVOKED"


@dataclass(frozen=True, slots=True)
class CodexSessionBinding:
    """Durable binding between a Codex session and a Synaisthesis project (05A, section 6)."""

    binding_id: str
    codex_session_id: str
    project_id: str
    mode: FidelityMode
    bound_at: datetime
    bound_by_user_instruction_id: str
    active_state_version: int
    sequence_number: int
    expires_at: datetime
    status: SessionBindingStatus = SessionBindingStatus.ACTIVE
    optional_claim_id: str | None = None

    def __post_init__(self) -> None:
        if not self.binding_id.strip() or not self.codex_session_id.strip():
            raise DomainError(
                "session binding requires binding_id and codex_session_id",
                error_code="SESSION_BINDING_INVALID",
            )
        if not self.project_id.strip() or not self.bound_by_user_instruction_id.strip():
            raise DomainError(
                "session binding requires project_id and a binding user instruction",
                error_code="SESSION_BINDING_INVALID",
            )

    def to_event_payload(self) -> dict[str, Any]:
        payload = canonicalize(asdict(self))
        if not isinstance(payload, dict):
            raise TypeError("session binding payload must canonicalize to an object")
        return payload
