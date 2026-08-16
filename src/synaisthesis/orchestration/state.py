"""Council orchestration state machine (blueprint 03 section 2, 04; M7.1).

Owns the effective-round rules (03 section 2), the ten-round cap, the
WIP_CHECKPOINT cadence (every 5 valid rounds), the Mandatory Maturity Gate at
the 20th valid round (08 section 15 CONTINUE_AFTER_ROUND_20) and the council
state-event catalog.  The run/round records themselves live in
domain/isolation.py (M6.2); this module drives their transitions.

Blueprint note (GAP-1): the council state-event catalog lives here instead of
domain/isolation.py because M6.2 froze that module; orchestration/state.py is
the M7.1 home of CouncilRoundCompleted/CouncilPaused/CouncilResumed/
CouncilCheckpointWritten/CouncilMaturityGateRequired.
"""

from __future__ import annotations

from typing import Any

from synaisthesis.domain.enums import ProgressKind, ProvenanceType
from synaisthesis.domain.errors import DomainError
from synaisthesis.domain.event import DomainEvent
from synaisthesis.domain.qualification import is_user_actor

EVENT_COUNCIL_RUN_STARTED = "CouncilRunStarted"
EVENT_COUNCIL_ROUND_COMPLETED = "CouncilRoundCompleted"
EVENT_COUNCIL_ROUND_INVALID = "CouncilRoundInvalid"
EVENT_COUNCIL_PAUSED = "CouncilPaused"
EVENT_COUNCIL_RESUMED = "CouncilResumed"
EVENT_COUNCIL_CHECKPOINT_WRITTEN = "CouncilCheckpointWritten"
EVENT_COUNCIL_MATURITY_GATE_REQUIRED = "CouncilMaturityGateRequired"

COUNCIL_STATE_EVENT_TYPES: frozenset[str] = frozenset(
    {
        EVENT_COUNCIL_RUN_STARTED,
        EVENT_COUNCIL_ROUND_COMPLETED,
        EVENT_COUNCIL_ROUND_INVALID,
        EVENT_COUNCIL_PAUSED,
        EVENT_COUNCIL_RESUMED,
        EVENT_COUNCIL_CHECKPOINT_WRITTEN,
        EVENT_COUNCIL_MATURITY_GATE_REQUIRED,
    }
)

MATURITY_GATE_ROUND = 20
CHECKPOINT_EVERY = 5


def build_council_state_event(
    event_type: str,
    *,
    aggregate_type: str,
    aggregate_id: str,
    payload: dict[str, Any],
    sequence: int,
) -> DomainEvent:
    """Build an immutable council state event with a stable event hash."""
    if event_type not in COUNCIL_STATE_EVENT_TYPES:
        raise DomainError(
            f"unknown council state event type {event_type!r}",
            error_code="UNKNOWN_EVENT_TYPE",
        )
    return DomainEvent(
        aggregate_type=aggregate_type,
        aggregate_id=aggregate_id,
        event_type=event_type,
        payload=payload,
        sequence=sequence,
    )


def is_valid_round(
    *,
    progress_kind: ProgressKind | None,
    produced_new_artifact_or_diff: bool,
    public_rationale: str,
    unresolved_items: tuple[str, ...],
    is_restatement: bool,
) -> tuple[bool, tuple[str, ...]]:
    """03 section 2: an effective round must satisfy all five conditions."""
    blockers: list[str] = []
    if progress_kind is None:
        blockers.append("必须选择一个 ProgressKind")
    if not produced_new_artifact_or_diff:
        blockers.append("必须产生新 Artifact 或明确差异")
    if not public_rationale.strip():
        blockers.append("必须保存公开理由")
    if not unresolved_items:
        blockers.append("必须记录未解决项")
    if is_restatement:
        blockers.append("不得是上一轮的简单重述")
    return (not blockers, tuple(blockers))


def next_round_target(current_round: int, configured_rounds: int) -> int | None:
    """Return the next round number or None when the cap is reached (10-round)."""
    if current_round >= configured_rounds:
        return None
    return current_round + 1


def checkpoint_due(valid_round_number: int) -> bool:
    """Every 5 valid rounds writes a WIP_CHECKPOINT (03, section 2)."""
    return valid_round_number > 0 and valid_round_number % CHECKPOINT_EVERY == 0


def maturity_gate_due(valid_round_number: int) -> bool:
    """The 20th valid round triggers the Mandatory Maturity Gate (03, section 2)."""
    return valid_round_number == MATURITY_GATE_ROUND


def can_continue_after_maturity_gate(
    *,
    decision: str,
    actor: ProvenanceType,
) -> bool:
    """CONTINUE_AFTER_ROUND_20 requires a real user event (08, section 15)."""
    return is_user_actor(actor) and decision == "CONTINUE_AFTER_ROUND_20"


__all__ = [
    "CHECKPOINT_EVERY",
    "COUNCIL_STATE_EVENT_TYPES",
    "EVENT_COUNCIL_CHECKPOINT_WRITTEN",
    "EVENT_COUNCIL_MATURITY_GATE_REQUIRED",
    "EVENT_COUNCIL_PAUSED",
    "EVENT_COUNCIL_RESUMED",
    "EVENT_COUNCIL_RUN_STARTED",
    "EVENT_COUNCIL_ROUND_COMPLETED",
    "EVENT_COUNCIL_ROUND_INVALID",
    "MATURITY_GATE_ROUND",
    "build_council_state_event",
    "can_continue_after_maturity_gate",
    "checkpoint_due",
    "is_valid_round",
    "maturity_gate_due",
    "next_round_target",
]
