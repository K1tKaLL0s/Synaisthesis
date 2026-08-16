"""Council orchestration nodes (blueprint 03 section 2, 04; M7.1).

Nodes load the authoritative run state and delegate to the enforced service
paths, so there is no second, weaker route through the council graph.
"""

from __future__ import annotations

from pathlib import Path

from sqlalchemy.orm import Session

from synaisthesis.application.council_service import (
    advance_council_round,
    load_council_run_state,
    pause_council_run,
    recover_council_run_from_checkpoint,
    resume_council_run,
)
from synaisthesis.domain.enums import ProgressKind
from synaisthesis.domain.isolation import CouncilRun


def council_round_node(
    session: Session,
    *,
    project_id: str,
    run_id: str,
    progress_kind: ProgressKind | None,
    produced_new_artifact_or_diff: bool,
    public_rationale: str,
    unresolved_items: tuple[str, ...],
    is_restatement: bool,
    artifact_root: Path,
    maturity_continue: bool = False,
) -> CouncilRun:
    """One effective council round through the enforced service path."""
    run = load_council_run_state(session, run_id, artifact_root=artifact_root)
    return advance_council_round(
        session,
        project_id=project_id,
        run=run,
        progress_kind=progress_kind,
        produced_new_artifact_or_diff=produced_new_artifact_or_diff,
        public_rationale=public_rationale,
        unresolved_items=unresolved_items,
        is_restatement=is_restatement,
        artifact_root=artifact_root,
        maturity_continue=maturity_continue,
    )


def council_pause_node(
    session: Session,
    *,
    project_id: str,
    run_id: str,
    artifact_root: Path,
) -> CouncilRun:
    run = load_council_run_state(session, run_id, artifact_root=artifact_root)
    return pause_council_run(session, project_id=project_id, run=run, artifact_root=artifact_root)


def council_resume_node(
    session: Session,
    *,
    project_id: str,
    run_id: str,
    artifact_root: Path,
) -> CouncilRun:
    run = load_council_run_state(session, run_id, artifact_root=artifact_root)
    return resume_council_run(session, project_id=project_id, run=run, artifact_root=artifact_root)


def council_recover_node(
    session: Session,
    *,
    project_id: str,
    run_id: str,
    artifact_root: Path,
) -> CouncilRun:
    run = load_council_run_state(session, run_id, artifact_root=artifact_root)
    return recover_council_run_from_checkpoint(
        session, project_id=project_id, run=run, artifact_root=artifact_root
    )


__all__ = [
    "council_pause_node",
    "council_recover_node",
    "council_resume_node",
    "council_round_node",
]
