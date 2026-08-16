"""Codex recursion guard (blueprint 19 §5 M12, 05 Recursion Guard).

The origin chain must be verifiable at every hop: OPERATOR -> PLATFORM ->
WORKER -> PLATFORM.  A worker that tries to act as an operator, a repeated
origin, or a chain beyond the configured depth is rejected with
REENTRANCY_BLOCKED — no mutation may ever loop back into the platform.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

from synaisthesis.domain.enums import StrictStrEnum
from synaisthesis.domain.errors import DomainError
from synaisthesis.domain.event import sha256_hex

DEFAULT_MAX_DELEGATION_DEPTH = 3


class OriginActorType(StrictStrEnum):
    """Origin chain actor kinds (05 Recursion Guard; M12)."""

    OPERATOR = "OPERATOR"
    PLATFORM = "PLATFORM"
    WORKER = "WORKER"


@dataclass(frozen=True, slots=True)
class OriginHop:
    """One hop in the origin chain (M12)."""

    actor_type: OriginActorType
    session_id: str
    delegation_id: str | None = None

    def to_event_payload(self) -> dict[str, Any]:
        return dict(asdict(self))


@dataclass(frozen=True, slots=True)
class OriginChain:
    """The verifiable origin chain of one mutation (M12)."""

    hops: tuple[OriginHop, ...]

    def __post_init__(self) -> None:
        if not self.hops:
            raise DomainError(
                "origin chain 不能为空",
                error_code="ORIGIN_CHAIN_INVALID",
            )

    def chain_hash(self) -> str:
        return sha256_hex(
            {
                "hops": [
                    {
                        "actor_type": hop.actor_type.value,
                        "session_id": hop.session_id,
                        "delegation_id": hop.delegation_id,
                    }
                    for hop in self.hops
                ]
            }
        )


def delegation_depth(chain: OriginChain) -> int:
    """Number of WORKER hops in the chain (verifiable depth)."""
    return sum(1 for hop in chain.hops if hop.actor_type is OriginActorType.WORKER)


def verify_origin_chain(
    chain: OriginChain,
    *,
    max_depth: int = DEFAULT_MAX_DELEGATION_DEPTH,
) -> tuple[bool, tuple[str, ...]]:
    """Validate alternation, first-hop identity, repeats and depth."""
    blockers: list[str] = []
    if chain.hops[0].actor_type is not OriginActorType.OPERATOR:
        blockers.append("origin chain 必须以 OPERATOR 开头")
    for index, hop in enumerate(chain.hops):
        if index == 0:
            continue
        previous = chain.hops[index - 1]
        if hop.actor_type is previous.actor_type:
            blockers.append(f"第 {index + 1} 跳与前一跳同属 {hop.actor_type.value}")
        if (
            hop.actor_type is OriginActorType.WORKER
            and previous.actor_type is not OriginActorType.PLATFORM
        ):
            blockers.append("WORKER 只能由 PLATFORM 派生")
        if hop.actor_type is OriginActorType.OPERATOR:
            blockers.append("非首个跳不得出现 OPERATOR（递归回环）")
    if delegation_depth(chain) > max_depth:
        blockers.append(f"delegation depth 超过上限 {max_depth}")
    seen_workers: set[str] = set()
    for hop in chain.hops:
        if hop.actor_type is OriginActorType.WORKER:
            key = hop.delegation_id or hop.session_id
            if key in seen_workers:
                blockers.append(f"WORKER 跳重复（delegation={key}）")
            seen_workers.add(key)
    return (not blockers, tuple(blockers))


def assert_no_reentrancy(
    chain: OriginChain,
    *,
    max_depth: int = DEFAULT_MAX_DELEGATION_DEPTH,
) -> None:
    """Fail closed with REENTRANCY_BLOCKED on any invalid origin chain."""
    valid, blockers = verify_origin_chain(chain, max_depth=max_depth)
    if not valid:
        raise DomainError(
            "REENTRANCY_BLOCKED: " + "; ".join(blockers),
            error_code="REENTRANCY_BLOCKED",
        )


__all__ = [
    "DEFAULT_MAX_DELEGATION_DEPTH",
    "OriginActorType",
    "OriginChain",
    "OriginHop",
    "assert_no_reentrancy",
    "delegation_depth",
    "verify_origin_chain",
]
