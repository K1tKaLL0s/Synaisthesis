"""M0.5 security tests for the Codex Instruction Fidelity Layer (05A, sections 8-25).

These tests cover the framework-free fail-closed policy: no trusted token, forged
signature, expiry, identity mismatch, instruction drift (F0-F5), raw-text hash
fail-closed, missing context, receipt/display hash integrity.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest

from synaisthesis.domain.errors import DomainError
from synaisthesis.fidelity.command_gateway import (
    MutationRequest,
    evaluate_mutation_request,
)
from synaisthesis.fidelity.command_receipt import CommandReceipt, CommandReceiptStatus
from synaisthesis.fidelity.context_manifest import ContextManifest
from synaisthesis.fidelity.display_contract import (
    DisplayContract,
    validate_displayed_message,
)
from synaisthesis.fidelity.instruction_capsule import (
    InstructionCapsule,
    raw_user_text_sha256,
)
from synaisthesis.fidelity.instruction_delta import (
    CommandProposal,
    InstructionDelta,
    PlatformInterpretation,
    grade_instruction_delta,
)
from synaisthesis.fidelity.instruction_token import (
    InstructionToken,
    OperationClass,
    sign_instruction_token,
    verify_instruction_token,
)

KEY = b"security-test-signing-key"
NOW = datetime(2026, 8, 17, 2, 0, 0, tzinfo=UTC)
PROJECT = "p1"


def _capsule(**overrides) -> InstructionCapsule:
    params = {
        "instruction_id": "i1",
        "session_id": "s1",
        "turn_id": "t1",
        "raw_user_text": "运行 10 轮，不得修改核心语义",
        "submitted_at": NOW,
    }
    params.update(overrides)
    return InstructionCapsule(**params)


def _unsigned_token(capsule: InstructionCapsule, **overrides) -> InstructionToken:
    params = {
        "instruction_id": capsule.instruction_id,
        "session_id": capsule.session_id,
        "turn_id": capsule.turn_id,
        "project_id": PROJECT,
        "raw_user_text_hash": raw_user_text_sha256(capsule.raw_user_text),
        "allowed_operation_class": OperationClass.HIGH_RISK_MUTATION,
        "issued_at": NOW,
        "expires_at": NOW + timedelta(minutes=5),
        "nonce": "n1",
        "state_version": 0,
        "signer_key_id": "k1",
    }
    params.update(overrides)
    return InstructionToken(**params)


def _token(capsule: InstructionCapsule, **overrides) -> InstructionToken:
    return sign_instruction_token(_unsigned_token(capsule, **overrides), signing_key=KEY)


def _proposal(**overrides) -> CommandProposal:
    params = {
        "operation": "research_start_council",
        "target_project": PROJECT,
        "target_claim": "c1",
        "loop_rounds": 10,
        "read_only": False,
        "prohibitions": ("不得修改核心语义",),
    }
    params.update(overrides)
    return CommandProposal(**params)


def _interpretation(**overrides) -> PlatformInterpretation:
    params = {
        "operation": "research_start_council",
        "target_project": PROJECT,
        "target_claim": "c1",
        "loop_rounds": 10,
        "read_only": False,
        "prohibitions": ("不得修改核心语义",),
    }
    params.update(overrides)
    return PlatformInterpretation(**params)


def _request(
    capsule: InstructionCapsule, token: InstructionToken | None, **overrides
) -> MutationRequest:
    params = {
        "instruction_token": token,
        "instruction_id": capsule.instruction_id,
        "project_id": PROJECT,
        "command_proposal": _proposal(),
        "platform_interpretation": _interpretation(),
        "expected_state_version": 0,
        "idempotency_key": "k1",
        "context_manifest": ContextManifest(context_manifest_id="m1"),
        "operation_class": OperationClass.HIGH_RISK_MUTATION,
    }
    params.update(overrides)
    return MutationRequest(**params)


# ---------------------------------------------------------------------------
# Fail closed: token trust
# ---------------------------------------------------------------------------


def test_mutation_without_token_fails_closed():
    capsule = _capsule()
    verdict = evaluate_mutation_request(
        _request(capsule, None),
        capsule=capsule,
        signing_key=KEY,
        current_state_version=0,
        now=NOW,
    )
    assert verdict.allowed is False
    assert verdict.error_code == "FIDELITY_CHANNEL_REQUIRED"


def test_unsigned_token_is_rejected():
    capsule = _capsule()
    token = _unsigned_token(capsule)
    assert verify_instruction_token(
        token,
        signing_key=KEY,
        expected_session_id=capsule.session_id,
        expected_turn_id=capsule.turn_id,
        expected_project_id=PROJECT,
        expected_raw_text_hash=raw_user_text_sha256(capsule.raw_user_text),
        now=NOW,
    ) == ("INVALID_INSTRUCTION_TOKEN",)


def test_forged_signature_is_rejected():
    capsule = _capsule()
    token = _token(capsule)
    forged = InstructionToken(
        instruction_id=token.instruction_id,
        session_id=token.session_id,
        turn_id=token.turn_id,
        project_id=token.project_id,
        raw_user_text_hash=token.raw_user_text_hash,
        allowed_operation_class=token.allowed_operation_class,
        issued_at=token.issued_at,
        expires_at=token.expires_at,
        nonce=token.nonce,
        state_version=token.state_version,
        signer_key_id=token.signer_key_id,
        signature="0" * 64,
    )
    assert verify_instruction_token(
        forged,
        signing_key=KEY,
        expected_session_id=capsule.session_id,
        expected_turn_id=capsule.turn_id,
        expected_project_id=PROJECT,
        expected_raw_text_hash=raw_user_text_sha256(capsule.raw_user_text),
        now=NOW,
    ) == ("INVALID_INSTRUCTION_TOKEN",)


def test_expired_token_is_rejected():
    capsule = _capsule()
    token = _token(capsule, expires_at=NOW - timedelta(seconds=1))
    assert verify_instruction_token(
        token,
        signing_key=KEY,
        expected_session_id=capsule.session_id,
        expected_turn_id=capsule.turn_id,
        expected_project_id=PROJECT,
        expected_raw_text_hash=raw_user_text_sha256(capsule.raw_user_text),
        now=NOW,
    ) == ("TOKEN_EXPIRED",)


def test_token_bound_to_other_session_is_rejected():
    capsule = _capsule()
    token = _token(capsule, session_id="other-session")
    assert verify_instruction_token(
        token,
        signing_key=KEY,
        expected_session_id=capsule.session_id,
        expected_turn_id=capsule.turn_id,
        expected_project_id=PROJECT,
        expected_raw_text_hash=raw_user_text_sha256(capsule.raw_user_text),
        now=NOW,
    ) == ("TOKEN_MISMATCH",)


def test_token_bound_to_old_state_version_blocks_gateway():
    capsule = _capsule()
    token = _token(capsule, state_version=0)
    verdict = evaluate_mutation_request(
        _request(capsule, token),
        capsule=capsule,
        signing_key=KEY,
        current_state_version=1,
        now=NOW,
    )
    assert verdict.allowed is False
    assert verdict.error_code == "STALE_STATE"


# ---------------------------------------------------------------------------
# Instruction delta grading
# ---------------------------------------------------------------------------


def test_rounds_drift_is_blocking_parameter_drift():
    assessment = grade_instruction_delta(_proposal(), _interpretation(loop_rounds=20))
    assert assessment.grade is InstructionDelta.F3_PARAMETER_DRIFT
    assert assessment.blocking is True


def test_missing_prohibition_is_semantic_drift():
    assessment = grade_instruction_delta(_proposal(), _interpretation(prohibitions=()))
    assert assessment.grade is InstructionDelta.F4_SEMANTIC_DRIFT
    assert assessment.blocking is True


def test_read_only_turned_into_mutation_is_semantic_drift():
    proposal = _proposal(operation="research_get_project_state", read_only=True)
    interpretation = _interpretation(operation="research_start_council", read_only=False)
    assessment = grade_instruction_delta(proposal, interpretation)
    assert assessment.grade is InstructionDelta.F4_SEMANTIC_DRIFT


def test_target_claim_drift_is_blocking():
    assessment = grade_instruction_delta(_proposal(), _interpretation(target_claim="c2"))
    assert assessment.grade is InstructionDelta.F3_PARAMETER_DRIFT


def test_exact_match_is_f0():
    assessment = grade_instruction_delta(_proposal(), _interpretation())
    assert assessment.grade is InstructionDelta.F0_EXACT
    assert assessment.blocking is False


def test_permission_escalation_is_unauthorized_action():
    assessment = grade_instruction_delta(_proposal(), _interpretation(allow_network=True))
    assert assessment.grade is InstructionDelta.F5_UNAUTHORIZED_ACTION


# ---------------------------------------------------------------------------
# Gateway blocks instruction drift
# ---------------------------------------------------------------------------


def test_gateway_blocks_rounds_drift():
    capsule = _capsule()
    token = _token(capsule)
    request = _request(capsule, token, platform_interpretation=_interpretation(loop_rounds=20))
    verdict = evaluate_mutation_request(
        request, capsule=capsule, signing_key=KEY, current_state_version=0, now=NOW
    )
    assert verdict.allowed is False
    assert verdict.error_code == "INSTRUCTION_MISMATCH"


def test_gateway_requires_context_manifest_for_mutation():
    capsule = _capsule()
    token = _token(capsule)
    request = _request(capsule, token, context_manifest=None)
    verdict = evaluate_mutation_request(
        request, capsule=capsule, signing_key=KEY, current_state_version=0, now=NOW
    )
    assert verdict.allowed is False
    assert verdict.error_code == "MISSING_CONTEXT"


def test_gateway_blocks_unresolved_context_reference():
    capsule = _capsule()
    token = _token(capsule)
    manifest = ContextManifest(
        context_manifest_id="m1", unresolved_deictic_references=("这个文件",)
    )
    request = _request(capsule, token, context_manifest=manifest)
    verdict = evaluate_mutation_request(
        request, capsule=capsule, signing_key=KEY, current_state_version=0, now=NOW
    )
    assert verdict.allowed is False
    assert verdict.error_code == "MISSING_CONTEXT"


# ---------------------------------------------------------------------------
# Hash integrity (fail closed)
# ---------------------------------------------------------------------------


def test_capsule_with_wrong_raw_hash_fails_closed():
    with pytest.raises(DomainError) as exc_info:
        InstructionCapsule(
            instruction_id="i1",
            session_id="s1",
            turn_id="t1",
            raw_user_text="运行 10 轮",
            raw_user_text_hash="0" * 64,
        )
    assert exc_info.value.error_code == "RAW_HASH_MISMATCH"


def test_capsule_recomputes_raw_hash():
    capsule = _capsule()
    assert capsule.raw_user_text_hash == raw_user_text_sha256("运行 10 轮，不得修改核心语义")


def test_receipt_with_wrong_hash_fails_closed():
    with pytest.raises(DomainError) as exc_info:
        CommandReceipt(
            command_id="cmd1",
            instruction_id="i1",
            executed_operation="research_start_council",
            target={"project_id": PROJECT},
            starting_state_version=0,
            ending_state_version=1,
            accepted_parameters={},
            rejected_parameters={},
            preserved_constraints=(),
            side_effects=(),
            evidence_ids=(),
            pending_gate_ids=(),
            cost_used={},
            status=CommandReceiptStatus.COMMITTED,
            receipt_hash="0" * 64,
        )
    assert exc_info.value.error_code == "ARTIFACT_HASH_MISMATCH"


# ---------------------------------------------------------------------------
# DisplayContract / Stop Hook audit
# ---------------------------------------------------------------------------


def _contract(**overrides) -> DisplayContract:
    params = {
        "display_contract_id": "dc1",
        "receipt_id": "cmd1",
        "exact_summary_block": "已提交 research_start_council，状态 0 -> 1",
        "mandatory_statuses": ("COUNCIL_RUNNING",),
        "mandatory_warnings": ("WARNING: UNDECIDED",),
        "mandatory_next_action": "等待用户确认下一轮",
        "prohibited_claims": ("已证明原创", "NO_COUNTEREXAMPLE_WITHIN_SCOPE 表示已证明"),
        "allowed_paraphrase_fields": ("side_effects",),
    }
    params.update(overrides)
    return DisplayContract(**params)


def test_display_contract_rejects_missing_warning_and_prohibited_claim():
    contract = _contract()
    bad_message = "已提交 research_start_council，状态 0 -> 1。结论：已证明原创。"
    issues = validate_displayed_message(bad_message, contract)
    assert "mandatory_warning 缺失: WARNING: UNDECIDED" in issues
    assert "prohibited_claim 出现: 已证明原创" in issues


def test_display_contract_accepts_faithful_message():
    contract = _contract()
    good_message = (
        "已提交 research_start_council，状态 0 -> 1。"
        "COUNCIL_RUNNING。WARNING: UNDECIDED。等待用户确认下一轮。"
    )
    assert validate_displayed_message(good_message, contract) == ()


def test_display_contract_rejects_modified_summary_block():
    contract = _contract()
    issues = validate_displayed_message(
        "已提交其他操作，状态 0 -> 1。COUNCIL_RUNNING。WARNING: UNDECIDED。等待用户确认下一轮。",
        contract,
    )
    assert "exact_summary_block 被省略或改写" in issues
