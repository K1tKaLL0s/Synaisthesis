"""Council orchestration nodes (blueprint 03 section 2, 04; M7.1).

Nodes load the authoritative run state and delegate to the enforced service
paths, so there is no second, weaker route through the council graph.
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

from sqlalchemy.orm import Session

from synaisthesis.application.council_service import (
    advance_council_round,
    council_confirm_and_bundle,
    council_repair,
    council_semantic_gate,
    council_verify_with_lean,
    load_council_run_state,
    pause_council_run,
    recover_council_run_from_checkpoint,
    resume_council_run,
)
from synaisthesis.domain.action import SemanticDelta
from synaisthesis.domain.enums import ProgressKind, ProvenanceType
from synaisthesis.domain.isolation import CouncilRun
from synaisthesis.verifiers.lean.adapter import (
    LeanResult,
    assert_proof_loop_statement_unchanged,
)


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


# ---------------------------------------------------------------------------
# M9.1 — real council vertical slice nodes
# ---------------------------------------------------------------------------


def council_repair_node(
    session: Session,
    *,
    project_id: str,
    run_id: str,
    repaired_claim: str,
    repair_rationale: str,
    artifact_root: Path,
) -> dict[str, str]:
    """Repair node: record a claim revision under review."""
    return council_repair(
        session,
        project_id=project_id,
        run_id=run_id,
        repaired_claim=repaired_claim,
        repair_rationale=repair_rationale,
        artifact_root=artifact_root,
    )


def council_semantic_gate_node(
    session: Session,
    *,
    project_id: str,
    run_id: str,
    delta: SemanticDelta,
    actor: ProvenanceType,
    user_event_id: str,
    at: datetime,
    artifact_root: Path,
) -> dict[str, str]:
    """Semantic gate node: F4/F5 rejected, only real users approve."""
    return council_semantic_gate(
        session,
        project_id=project_id,
        run_id=run_id,
        delta=delta,
        actor=actor,
        user_event_id=user_event_id,
        at=at,
        artifact_root=artifact_root,
    )


def council_verification_node(
    session: Session,
    *,
    project_id: str,
    run_id: str,
    lean_source: str,
    artifact_root: Path,
    expected_statement_hash: str | None = None,
) -> LeanResult:
    """Verification node: REAL Lean run recorded as evidence."""
    return council_verify_with_lean(
        session,
        project_id=project_id,
        run_id=run_id,
        lean_source=lean_source,
        artifact_root=artifact_root,
        expected_statement_hash=expected_statement_hash,
    )


def council_regression_node(
    *,
    current_source: str,
    expected_statement_hash: str,
) -> None:
    """Regression node: statement hash change exits the proof loop."""
    assert_proof_loop_statement_unchanged(
        current_source=current_source,
        expected_statement_hash=expected_statement_hash,
    )


def council_confirm_node(
    session: Session,
    *,
    project_id: str,
    run_id: str,
    claim_id: str,
    actor: ProvenanceType,
    user_event_id: str,
    at: datetime,
    evidence_receipt_hash: str,
    artifact_root: Path,
) -> dict[str, str]:
    """User confirmation node closing the slice bundle chain."""
    return council_confirm_and_bundle(
        session,
        project_id=project_id,
        run_id=run_id,
        claim_id=claim_id,
        actor=actor,
        user_event_id=user_event_id,
        at=at,
        evidence_receipt_hash=evidence_receipt_hash,
        artifact_root=artifact_root,
    )


__all__ = [
    "council_confirm_node",
    "council_pause_node",
    "council_recover_node",
    "council_regression_node",
    "council_repair_node",
    "council_resume_node",
    "council_round_node",
    "council_semantic_gate_node",
    "council_verification_node",
]
