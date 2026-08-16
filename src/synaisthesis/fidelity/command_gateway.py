"""Command Gateway fail-closed policy (05A, sections 18/24).

This module is the framework-free decision core of the mutation gateway. It never
persists anything; the application service feeds it the current state and the
verified InstructionCapsule. Every check that cannot be satisfied rejects the
mutation instead of guessing.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from synaisthesis.fidelity.context_manifest import ContextManifest
from synaisthesis.fidelity.instruction_capsule import InstructionCapsule
from synaisthesis.fidelity.instruction_delta import (
    CommandProposal,
    DeltaAssessment,
    InstructionDelta,
    PlatformInterpretation,
    grade_instruction_delta,
)
from synaisthesis.fidelity.instruction_token import (
    InstructionToken,
    OperationClass,
    token_authorizes,
    verify_instruction_token,
)


@dataclass(frozen=True, slots=True)
class MutationRequest:
    """Transport fields every mutation must carry (05A, section 18.3)."""

    instruction_token: InstructionToken | None
    instruction_id: str
    project_id: str
    command_proposal: CommandProposal
    platform_interpretation: PlatformInterpretation
    expected_state_version: int
    idempotency_key: str
    context_manifest: ContextManifest | None
    operation_class: OperationClass

    @property
    def is_mutation(self) -> bool:
        return self.operation_class is not OperationClass.READ_ONLY


@dataclass(frozen=True, slots=True)
class GatewayVerdict:
    """Decision of the fail-closed gateway policy."""

    allowed: bool
    error_code: str | None
    reason: str
    delta: DeltaAssessment | None = None


def evaluate_mutation_request(
    request: MutationRequest,
    *,
    capsule: InstructionCapsule,
    signing_key: bytes,
    current_state_version: int,
    now: datetime,
    require_context_manifest: bool = True,
) -> GatewayVerdict:
    """Return the gateway decision for one mutation request.

    Fail-closed order (05A, section 8/18/24): no token -> FIDELITY_CHANNEL_REQUIRED;
    invalid/expired/mismatched token -> rejected; stale state -> rejected; delta
    drift -> blocked; missing context -> MISSING_CONTEXT. Only a request passing
    every check is allowed.
    """
    token = request.instruction_token
    if token is None:
        return GatewayVerdict(
            allowed=False,
            error_code="FIDELITY_CHANNEL_REQUIRED",
            reason="mutation requires a trusted InstructionToken; no trusted hook/token present",
        )

    raw_text_hash = capsule.raw_user_text_hash
    assert raw_text_hash is not None
    token_errors = verify_instruction_token(
        token,
        signing_key=signing_key,
        expected_session_id=capsule.session_id,
        expected_turn_id=capsule.turn_id,
        expected_project_id=request.project_id,
        expected_raw_text_hash=raw_text_hash,
        now=now,
    )
    if token_errors:
        return GatewayVerdict(
            allowed=False,
            error_code=token_errors[0],
            reason="instruction token failed trust verification: " + ", ".join(token_errors),
        )

    if token.state_version != current_state_version:
        return GatewayVerdict(
            allowed=False,
            error_code="STALE_STATE",
            reason=(
                f"token bound state_version={token.state_version} but current is "
                f"{current_state_version}; re-prepare with the latest state"
            ),
        )

    if request.is_mutation and not token_authorizes(token, request.operation_class):
        return GatewayVerdict(
            allowed=False,
            error_code="TOKEN_OPERATION_CLASS_INSUFFICIENT",
            reason=(
                f"token authorizes {token.allowed_operation_class.value} but the request "
                f"needs {request.operation_class.value}"
            ),
        )

    delta = grade_instruction_delta(request.command_proposal, request.platform_interpretation)
    if delta.grade is InstructionDelta.F5_UNAUTHORIZED_ACTION:
        return GatewayVerdict(
            allowed=False,
            error_code="UNAUTHORIZED_ACTION",
            reason="Codex proposed an unauthorized action: " + "; ".join(delta.differences),
            delta=delta,
        )
    if delta.grade is InstructionDelta.F4_SEMANTIC_DRIFT:
        return GatewayVerdict(
            allowed=False,
            error_code="INSTRUCTION_MISMATCH",
            reason="semantic drift from the verbatim instruction: " + "; ".join(delta.differences),
            delta=delta,
        )
    if delta.grade is InstructionDelta.F3_PARAMETER_DRIFT:
        return GatewayVerdict(
            allowed=False,
            error_code="INSTRUCTION_MISMATCH",
            reason="parameter drift from the verbatim instruction: " + "; ".join(delta.differences),
            delta=delta,
        )

    if request.is_mutation and require_context_manifest:
        if request.context_manifest is None:
            return GatewayVerdict(
                allowed=False,
                error_code="MISSING_CONTEXT",
                reason="mutation requires a ContextManifest resolving context references",
            )
        if request.context_manifest.has_unresolved_references():
            return GatewayVerdict(
                allowed=False,
                error_code="MISSING_CONTEXT",
                reason="ContextManifest still has unresolved deictic references",
            )

    return GatewayVerdict(allowed=True, error_code=None, reason="ok", delta=delta)
