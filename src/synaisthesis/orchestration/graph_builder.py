"""Council graph builder (M7.1).

Builds the deterministic round plan for a council run: rounds up to the
configured cap (ten for the Fake council), WIP_CHECKPOINT markers every five
valid rounds and the Mandatory Maturity Gate at round 20.  Pause/resume edges
are explicit so the graph can never silently skip a checkpoint or gate.
"""

from __future__ import annotations

from synaisthesis.domain.isolation import CouncilRunStatus
from synaisthesis.orchestration.state import (
    CHECKPOINT_EVERY,
    MATURITY_GATE_ROUND,
)

PLAN_KIND_ROUND = "ROUND"
PLAN_KIND_CHECKPOINT = "CHECKPOINT"
PLAN_KIND_MATURITY_GATE = "MATURITY_GATE"
PLAN_KIND_COMPLETE = "COMPLETE"


def build_round_plan(configured_rounds: int) -> tuple[tuple[int, str], ...]:
    """Return (step_number, kind) pairs for the full run (deterministic)."""
    if configured_rounds < 1:
        raise ValueError("configured_rounds must be >= 1")
    plan: list[tuple[int, str]] = []
    for round_number in range(1, configured_rounds + 1):
        plan.append((round_number, PLAN_KIND_ROUND))
        if round_number % CHECKPOINT_EVERY == 0:
            plan.append((round_number, PLAN_KIND_CHECKPOINT))
        if round_number == MATURITY_GATE_ROUND:
            plan.append((round_number, PLAN_KIND_MATURITY_GATE))
    plan.append((configured_rounds + 1, PLAN_KIND_COMPLETE))
    return tuple(plan)


def pause_resume_edges() -> tuple[tuple[str, str], ...]:
    """Legal status transitions for pause/resume (state graph edges)."""
    return (
        (CouncilRunStatus.RUNNING.value, CouncilRunStatus.PAUSED.value),
        (CouncilRunStatus.PAUSED.value, CouncilRunStatus.RUNNING.value),
    )


__all__ = [
    "PLAN_KIND_CHECKPOINT",
    "PLAN_KIND_COMPLETE",
    "PLAN_KIND_MATURITY_GATE",
    "PLAN_KIND_ROUND",
    "build_round_plan",
    "pause_resume_edges",
]
