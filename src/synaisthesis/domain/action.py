"""Action authorization domain (blueprint 08 sections 1-2/12, 05A section 11; M5.1).

Delegation modes A0-A3 and risk classes R0-R6 combine into a deterministic
AUTO / GATE / REJECT route: R0 reads are automatic, R1 writes are automatic
only under A2/A3 with an explicit path allowlist, R2 needs a network-domain
allowlist, R3 is budget-bound, and R4-R6 always require a Human Gate.  Models
can never approve; only a real user event resolves an ActionGate.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime
from typing import Any

from synaisthesis.domain.enums import ProvenanceType, StrictStrEnum
from synaisthesis.domain.errors import DomainError
from synaisthesis.domain.event import canonicalize
from synaisthesis.domain.qualification import is_user_actor


class DelegationMode(StrictStrEnum):
    """A0-A3 delegation modes (08, section 1)."""

    A0_USER_LED = "A0_USER_LED"
    A1_AI_ASSISTED = "A1_AI_ASSISTED"
    A2_AI_DELEGATED = "A2_AI_DELEGATED"
    A3_AI_AUTONOMOUS_BOUNDED = "A3_AI_AUTONOMOUS_BOUNDED"


class ActionRiskClass(StrictStrEnum):
    """R0-R6 action risk classes (08, section 2)."""

    R0_READ = "R0"
    R1_ISOLATED_WRITE = "R1"
    R2_NETWORK_READ = "R2"
    R3_COSTLY_COMPUTE = "R3"
    R4_EXTERNAL_WRITE = "R4"
    R5_SECRET_OR_SENSITIVE = "R5"
    R6_DESTRUCTIVE = "R6"


class ActionRouteVerdict(StrictStrEnum):
    """Deterministic action route outcomes (08, section 2)."""

    AUTO = "AUTO"
    GATE = "GATE"
    REJECT = "REJECT"


class SemanticDelta(StrictStrEnum):
    """Instruction delta grades (05A, section 11)."""

    F0_EXACT = "F0"
    F1_PRESENTATIONAL_ONLY = "F1"
    F2_INFERRED_DEFAULT = "F2"
    F3_PARAMETER_DRIFT = "F3"
    F4_SEMANTIC_DRIFT = "F4"
    F5_UNAUTHORIZED_ACTION = "F5"


ACTION_GATE_DECISIONS: tuple[str, ...] = ("APPROVE", "REJECT", "PAUSE")


def _canonical_payload(value: Any) -> dict[str, Any]:
    payload = canonicalize(value)
    if not isinstance(payload, dict):
        raise TypeError("action payload must canonicalize to an object")
    return payload


@dataclass(frozen=True, slots=True)
class ActionRequest:
    """One action request (08, section 12)."""

    action_type: str
    risk_class: ActionRiskClass
    requester: str
    exact_parameters: dict[str, Any]
    allowed_paths: tuple[str, ...]
    network_intent: str | None = None
    cost_estimate: str | None = None
    expected_outputs: tuple[str, ...] = ()
    expiry: datetime | None = None
    required_approval: str = ""

    def __post_init__(self) -> None:
        if not self.action_type.strip() or not self.requester.strip():
            raise DomainError(
                "action request requires action_type and requester",
                error_code="ACTION_REQUEST_INVALID",
            )

    def to_event_payload(self) -> dict[str, Any]:
        return _canonical_payload(asdict(self))


@dataclass(frozen=True, slots=True)
class ActionRouteDecision:
    """Deterministic routing result (08, section 2)."""

    verdict: ActionRouteVerdict
    reason: str
    semantic_delta: SemanticDelta = SemanticDelta.F0_EXACT


def action_route(
    *,
    request: ActionRequest,
    delegation_mode: DelegationMode,
    allowlist_paths: frozenset[str] = frozenset(),
    allowed_network_domains: frozenset[str] = frozenset(),
    budget_within_limit: bool = True,
    semantic_delta: SemanticDelta = SemanticDelta.F0_EXACT,
) -> ActionRouteDecision:
    """Route one action deterministically; R4-R6 always need a Human Gate.

    The route never depends on the requester's self-declared authority: risk
    class and delegation mode are the only inputs, plus explicit allowlists.
    """
    if semantic_delta is SemanticDelta.F5_UNAUTHORIZED_ACTION:
        return ActionRouteDecision(
            verdict=ActionRouteVerdict.REJECT,
            reason="F5 UNAUTHORIZED_ACTION：指令未经授权，直接拒绝",
            semantic_delta=semantic_delta,
        )
    if semantic_delta is SemanticDelta.F4_SEMANTIC_DRIFT:
        return ActionRouteDecision(
            verdict=ActionRouteVerdict.GATE,
            reason="F4 SEMANTIC_DRIFT：语义漂移必须用户 Gate，不得自动执行",
            semantic_delta=semantic_delta,
        )

    risk = request.risk_class
    if risk in {
        ActionRiskClass.R4_EXTERNAL_WRITE,
        ActionRiskClass.R5_SECRET_OR_SENSITIVE,
        ActionRiskClass.R6_DESTRUCTIVE,
    }:
        return ActionRouteDecision(
            verdict=ActionRouteVerdict.GATE,
            reason=f"{risk.value} 必须 Human Gate",
            semantic_delta=semantic_delta,
        )

    if risk is ActionRiskClass.R0_READ:
        return ActionRouteDecision(
            verdict=ActionRouteVerdict.AUTO,
            reason="R0 只读自动",
            semantic_delta=semantic_delta,
        )

    if risk is ActionRiskClass.R1_ISOLATED_WRITE:
        if delegation_mode in {
            DelegationMode.A2_AI_DELEGATED,
            DelegationMode.A3_AI_AUTONOMOUS_BOUNDED,
        } and _paths_allowed(request.allowed_paths, allowlist_paths):
            return ActionRouteDecision(
                verdict=ActionRouteVerdict.AUTO,
                reason="R1 在 A2/A3 且路径在 allowlist 内自动",
                semantic_delta=semantic_delta,
            )
        return ActionRouteDecision(
            verdict=ActionRouteVerdict.GATE,
            reason="R1 需要 A2/A3 + 路径 allowlist，否则 Human Gate",
            semantic_delta=semantic_delta,
        )

    if risk is ActionRiskClass.R2_NETWORK_READ:
        if request.network_intent and _domains_allowed(
            request.network_intent, allowed_network_domains
        ):
            return ActionRouteDecision(
                verdict=ActionRouteVerdict.AUTO,
                reason="R2 域名在 allowlist 内自动",
                semantic_delta=semantic_delta,
            )
        return ActionRouteDecision(
            verdict=ActionRouteVerdict.GATE,
            reason="R2 需要网络域名 allowlist，否则 Human Gate",
            semantic_delta=semantic_delta,
        )

    if risk is ActionRiskClass.R3_COSTLY_COMPUTE:
        if delegation_mode is DelegationMode.A3_AI_AUTONOMOUS_BOUNDED and budget_within_limit:
            return ActionRouteDecision(
                verdict=ActionRouteVerdict.AUTO,
                reason="R3 在 A3 且预算内自动",
                semantic_delta=semantic_delta,
            )
        return ActionRouteDecision(
            verdict=ActionRouteVerdict.GATE,
            reason="R3 受预算约束，超预算或非 A3 必须 Human Gate",
            semantic_delta=semantic_delta,
        )

    raise DomainError(
        f"risk class {risk.value} 无法确定路由",
        error_code="RISK_CLASS_UNDETERMINED",
    )


def _paths_allowed(paths: tuple[str, ...], allowlist: frozenset[str]) -> bool:
    if not paths:
        return False
    return all(
        any(path == allowed or path.startswith(allowed.rstrip("/") + "/") for allowed in allowlist)
        for path in paths
    )


def _domains_allowed(network_intent: str, allowlist: frozenset[str]) -> bool:
    if not allowlist:
        return False
    return any(domain in network_intent for domain in allowlist)


@dataclass(frozen=True, slots=True)
class ActionGate:
    """An immutable action Human Gate; only a real user event resolves it."""

    gate_id: str
    project_id: str
    action_request: ActionRequest
    route: ActionRouteDecision
    reason: str
    status: str = "OPEN"
    decision: str | None = None
    resolved_at: datetime | None = None

    def __post_init__(self) -> None:
        if self.status == "RESOLVED" and self.decision is None:
            raise DomainError(
                f"gate {self.gate_id!r} RESOLVED 必须带 decision",
                error_code="GATE_BINDING_INVALID",
            )

    def resolve(
        self,
        *,
        decision: str,
        actor: ProvenanceType,
        user_event_id: str,
        at: datetime,
    ) -> ActionGate:
        """Return a RESOLVED copy; only a real user event may decide."""
        if self.status != "OPEN":
            raise DomainError(
                f"gate {self.gate_id!r} is already {self.status}",
                error_code="CONFLICT",
            )
        if not is_user_actor(actor):
            raise DomainError(
                f"gate resolution requires a real user event; got actor={actor.value}",
                error_code="CONFIRMATION_REQUIRES_USER_EVENT",
            )
        if decision not in ACTION_GATE_DECISIONS:
            raise DomainError(
                f"decision {decision!r} is not legal for an action gate; "
                f"allowed: {', '.join(ACTION_GATE_DECISIONS)}",
                error_code="INVALID_GATE_DECISION",
            )
        from dataclasses import replace

        return replace(
            self,
            status="RESOLVED",
            decision=decision,
            resolved_at=at,
        )

    def to_event_payload(self) -> dict[str, Any]:
        return _canonical_payload(asdict(self))


__all__ = [
    "ACTION_GATE_DECISIONS",
    "ActionGate",
    "ActionRequest",
    "ActionRiskClass",
    "ActionRouteDecision",
    "ActionRouteVerdict",
    "DelegationMode",
    "SemanticDelta",
    "action_route",
]
