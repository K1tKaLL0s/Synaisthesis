"""Frozen claim contract domain (blueprint 04 section 2, 06 claim_contracts; M4.2).

The ClaimContract is immutable: its contract_hash covers the semantic
statement hashes, the object-domain/assumption/conclusion/baseline snapshots,
the tool plan, and the network/data/budget/approval policies plus the
artifact manifest.  Any change creates a new revision; the old contract is
never modified in place (04 section 2: 冻结后任何修改都生成新版本).
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime
from typing import Any, cast

from synaisthesis.domain.errors import DomainError
from synaisthesis.domain.event import DomainEvent, canonicalize, sha256_hex

CLAIM_CONTRACT_AGGREGATE_TYPE = "ClaimContract"
EVENT_CLAIM_CONTRACT_FROZEN = "ClaimContractFrozen"
EVENT_CLAIM_CONTRACT_REVISED = "ClaimContractRevised"
CLAIM_CONTRACT_EVENT_TYPES: frozenset[str] = frozenset(
    {EVENT_CLAIM_CONTRACT_FROZEN, EVENT_CLAIM_CONTRACT_REVISED}
)


def _canonical_payload(value: Any) -> dict[str, Any]:
    payload = canonicalize(value)
    if not isinstance(payload, dict):
        raise TypeError("claim contract payload must canonicalize to an object")
    return cast(dict[str, Any], payload)


def build_claim_contract_event(
    event_type: str,
    *,
    aggregate_type: str,
    aggregate_id: str,
    payload: dict[str, Any],
    sequence: int,
) -> DomainEvent:
    """Build an immutable claim-contract DomainEvent with a stable hash."""
    if event_type not in CLAIM_CONTRACT_EVENT_TYPES:
        raise DomainError(
            f"unknown claim contract event type {event_type!r}",
            error_code="UNKNOWN_EVENT_TYPE",
        )
    return DomainEvent(
        aggregate_type=aggregate_type,
        aggregate_id=aggregate_id,
        event_type=event_type,
        payload=payload,
        sequence=sequence,
    )


@dataclass(frozen=True, slots=True)
class ClaimContract:
    """One immutable frozen claim contract (04 section 2, 06 claim_contracts).

    user_confirmed may only become True through the real-user-event freeze
    path in the claim compiler service; the domain itself never flips it.
    """

    contract_id: str
    claim_id: str
    claim_revision_id: str
    version: int
    natural_language_hash: str
    formal_statement_hash: str
    object_domain_snapshot: str
    assumption_snapshot: tuple[str, ...]
    conclusion_snapshot: str
    baseline_snapshot: str
    stop_conditions: tuple[str, ...]
    output_scope: str
    tool_plan: tuple[str, ...]
    network_policy: str
    data_policy: str
    budget_policy: str
    allowed_semantic_delta: str
    approval_policy: str
    artifact_manifest_hash: str
    model_role_assignments: tuple[str, ...]
    contract_hash: str | None = None
    user_confirmed: bool = False
    supersedes_id: str | None = None
    frozen_at: datetime | None = None
    created_at: datetime | None = None

    def __post_init__(self) -> None:
        for field_name in (
            "contract_id",
            "claim_id",
            "claim_revision_id",
            "natural_language_hash",
            "formal_statement_hash",
            "object_domain_snapshot",
            "conclusion_snapshot",
            "baseline_snapshot",
            "output_scope",
            "tool_plan",
            "network_policy",
            "data_policy",
            "budget_policy",
            "allowed_semantic_delta",
            "approval_policy",
            "artifact_manifest_hash",
        ):
            value = getattr(self, field_name)
            if isinstance(value, str) and not value.strip():
                raise DomainError(
                    f"claim contract {self.contract_id!r} 缺少 {field_name}",
                    error_code="CLAIM_CONTRACT_INVALID",
                )
            if isinstance(value, (tuple,)) and not value:
                raise DomainError(
                    f"claim contract {self.contract_id!r} 缺少 {field_name}",
                    error_code="CLAIM_CONTRACT_INVALID",
                )
        if self.version < 1:
            raise DomainError(
                f"claim contract {self.contract_id!r} version 必须 >= 1",
                error_code="CLAIM_CONTRACT_INVALID",
            )
        if self.user_confirmed and self.frozen_at is None:
            raise DomainError(
                f"claim contract {self.contract_id!r} user_confirmed 必须带 frozen_at",
                error_code="CLAIM_CONTRACT_INVALID",
            )
        expected = sha256_hex(self.content_payload())
        if self.contract_hash is not None and self.contract_hash != expected:
            raise DomainError(
                "contract_hash does not match the claim contract content",
                error_code="ARTIFACT_HASH_MISMATCH",
            )
        object.__setattr__(self, "contract_hash", expected)

    def content_payload(self) -> dict[str, Any]:
        """Return the hash-covered content (metadata excluded).

        user_confirmed/frozen_at/created_at are confirmation metadata and are
        recovered from the event stream, exactly like the S1/S4 confirmation
        markers; contract_hash covers semantics, tools, budget and policies.
        """
        payload = asdict(self)
        for key in (
            "contract_hash",
            "user_confirmed",
            "supersedes_id",
            "frozen_at",
            "created_at",
        ):
            payload.pop(key, None)
        return _canonical_payload(payload)

    def to_event_payload(self) -> dict[str, Any]:
        return _canonical_payload(asdict(self))


def claim_contract_blockers(contract: ClaimContract) -> tuple[str, ...]:
    """Re-run the freeze rules without constructing a new instance."""
    blockers: list[str] = []
    if not contract.object_domain_snapshot.strip():
        blockers.append("缺少 object_domain_snapshot")
    if not contract.tool_plan:
        blockers.append("tool_plan 为空（冻结必须覆盖工具计划）")
    if not contract.budget_policy.strip():
        blockers.append("budget_policy 为空（冻结必须覆盖预算策略）")
    if not contract.network_policy.strip():
        blockers.append("network_policy 为空（冻结必须覆盖网络策略）")
    if not contract.data_policy.strip():
        blockers.append("data_policy 为空（冻结必须覆盖数据策略）")
    if not contract.approval_policy.strip():
        blockers.append("approval_policy 为空（冻结必须覆盖审批策略）")
    return tuple(blockers)


__all__ = [
    "CLAIM_CONTRACT_AGGREGATE_TYPE",
    "CLAIM_CONTRACT_EVENT_TYPES",
    "EVENT_CLAIM_CONTRACT_FROZEN",
    "EVENT_CLAIM_CONTRACT_REVISED",
    "ClaimContract",
    "build_claim_contract_event",
    "claim_contract_blockers",
]
