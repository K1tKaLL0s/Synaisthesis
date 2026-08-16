"""Theory venue compliance (03C section 8; M9.2).

Reuses the domain VenueComplianceMatrix statuses and adds the theory-specific
blocking rules: machine blocking checks must all PASS, human-only blocking
items must be user-confirmed or the overall status drops to
FORMAL_MANUSCRIPT_DRAFT.
"""

from __future__ import annotations

from synaisthesis.domain.publication import (
    VenueComplianceMatrix,
    VenueComplianceStatus,
)


def theory_compliance_blockers(
    matrix: VenueComplianceMatrix,
    *,
    machine_blocking_requirements: tuple[str, ...],
) -> tuple[str, ...]:
    """Return blockers for the theory formal-manuscript readiness (03C, §8)."""
    blockers: list[str] = []
    by_id = {entry.requirement_id: entry for entry in matrix.entries}
    for requirement_id in machine_blocking_requirements:
        entry = by_id.get(requirement_id)
        if entry is None:
            blockers.append(f"machine blocking 项 {requirement_id} 缺失")
            continue
        if entry.status is not VenueComplianceStatus.PASS:
            blockers.append(f"machine blocking 项 {requirement_id} 状态 {entry.status.value}")
    for entry in matrix.entries:
        if entry.status is VenueComplianceStatus.STALE_GUIDANCE:
            blockers.append(f"compliance {entry.requirement_id} STALE_GUIDANCE，指南过期")
    return tuple(blockers)


def theory_compliance_overall_status(
    matrix: VenueComplianceMatrix,
    *,
    machine_blocking_requirements: tuple[str, ...],
    human_blocking_requirements: tuple[str, ...],
) -> tuple[str, tuple[str, ...]]:
    """Return (FORMAL_MANUSCRIPT_READY|FORMAL_MANUSCRIPT_DRAFT, blockers)."""
    blockers = list(
        theory_compliance_blockers(
            matrix, machine_blocking_requirements=machine_blocking_requirements
        )
    )
    by_id = {entry.requirement_id: entry for entry in matrix.entries}
    pending_human = [
        requirement_id
        for requirement_id in human_blocking_requirements
        if by_id.get(requirement_id) is None
        or by_id[requirement_id].status is VenueComplianceStatus.NEEDS_AUTHOR_INPUT
    ]
    if blockers:
        return "FORMAL_MANUSCRIPT_DRAFT", tuple(blockers)
    if pending_human:
        return "FORMAL_MANUSCRIPT_DRAFT", (
            "human-only blocking 项待用户确认：" + ", ".join(pending_human),
        )
    return "FORMAL_MANUSCRIPT_READY", ()


__all__ = [
    "theory_compliance_blockers",
    "theory_compliance_overall_status",
]
