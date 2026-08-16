"""Execution receipt domain (blueprint 08 section 12; M5.1).

An action without a verified ExecutionReceipt can never become Tool Evidence.
Both the request hash and the result hash are mandatory: a receipt missing a
hash fails closed, and the request hash must recompute from the original
ActionRequest.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime
from typing import Any

from synaisthesis.domain.action import ActionRequest
from synaisthesis.domain.errors import DomainError
from synaisthesis.domain.event import canonicalize, sha256_hex


def _canonical_payload(value: Any) -> dict[str, Any]:
    payload = canonicalize(value)
    if not isinstance(payload, dict):
        raise TypeError("receipt payload must canonicalize to an object")
    return payload


def action_request_hash(request: ActionRequest) -> str:
    """Content-bound hash of an action request (08, section 12)."""
    return sha256_hex(request.to_event_payload())


def execution_result_hash(
    *,
    actual_parameters: dict[str, Any],
    produced_artifacts: tuple[str, ...],
    exit_status: int | None,
) -> str:
    """Content-bound hash of the executed outcome (08, section 12)."""
    return sha256_hex(
        {
            "actual_parameters": actual_parameters,
            "produced_artifacts": list(produced_artifacts),
            "exit_status": exit_status,
        }
    )


@dataclass(frozen=True, slots=True)
class ExecutionReceipt:
    """One immutable execution receipt (08, section 12)."""

    receipt_id: str
    request_hash: str
    executor: str
    actual_parameters: dict[str, Any]
    started_at: datetime
    ended_at: datetime
    exit_status: int | None
    stdout: str
    stderr: str
    produced_artifacts: tuple[str, ...]
    diff: str | None
    result_hash: str
    environment_version: str
    deviations: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        missing: list[str] = []
        if not self.request_hash:
            missing.append("request_hash")
        if not self.result_hash:
            missing.append("result_hash")
        if missing:
            raise DomainError(
                "receipt missing mandatory hash: " + ", ".join(missing),
                error_code="RECEIPT_HASH_MISSING",
            )
        if not self.executor.strip():
            raise DomainError(
                "receipt requires executor",
                error_code="RECEIPT_INVALID",
            )

    def to_event_payload(self) -> dict[str, Any]:
        return _canonical_payload(asdict(self))


def verify_receipt_binding(receipt: ExecutionReceipt, request: ActionRequest) -> tuple[str, ...]:
    """Recompute the request/result hashes; a mismatch fails closed."""
    blockers: list[str] = []
    expected_request_hash = action_request_hash(request)
    if receipt.request_hash != expected_request_hash:
        blockers.append("request_hash 与 ActionRequest 内容不符")
    expected_result_hash = execution_result_hash(
        actual_parameters=receipt.actual_parameters,
        produced_artifacts=receipt.produced_artifacts,
        exit_status=receipt.exit_status,
    )
    if receipt.result_hash != expected_result_hash:
        blockers.append("result_hash 与实际参数/产物/退出码不符")
    return tuple(blockers)


def receipt_tool_evidence(receipt: ExecutionReceipt) -> bool:
    """A receipt only forms Tool Evidence when both hashes are present.

    The caller must additionally verify the binding against the original
    request before recording evidence; this predicate is the fail-closed
    minimum (08, section 8).
    """
    return bool(receipt.request_hash and receipt.result_hash)


__all__ = [
    "ExecutionReceipt",
    "action_request_hash",
    "execution_result_hash",
    "receipt_tool_evidence",
    "verify_receipt_binding",
]
