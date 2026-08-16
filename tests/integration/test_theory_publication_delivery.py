"""M9.2 integration tests for the theory publication delivery chain (03C)."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config

from synaisthesis.application.theory_publication_service import (
    audit_theory_master_manuscript,
    create_theory_master_manuscript,
    create_theory_venue_adapted_manuscript,
    open_theory_formal_manuscript_decision,
    open_theory_profile_selection,
    resolve_theory_formal_manuscript_decision,
    resolve_theory_profile_selection,
    theory_delivery_readiness_blockers,
)
from synaisthesis.domain.enums import ProvenanceType
from synaisthesis.domain.publication import (
    TheoryEvidenceTier,
    TheoryManuscriptAuditStatus,
    VenueComplianceEntry,
    VenueComplianceMatrix,
    VenueComplianceStatus,
)
from synaisthesis.publication.profiles import profile_for
from synaisthesis.publication.theory_master_manuscript import (
    MathematicalManuscriptClaim,
    ProofDependencyGraph,
    ProofStatus,
    TheoryClaimKind,
    TheoryMasterManuscript,
    claim_statement_hash,
)
from synaisthesis.storage.database import init_database

NOW = datetime(2026, 8, 17, 2, 0, 0, tzinfo=UTC)
REPO_ROOT = Path(__file__).resolve().parents[2]
MIGRATIONS_DIR = REPO_ROOT / "src" / "synaisthesis" / "storage" / "migrations"


def _fresh_database(tmp_path: Path):
    db_url = f"sqlite:///{tmp_path / 'theory-delivery.db'}"
    cfg = Config()
    cfg.set_main_option("script_location", str(MIGRATIONS_DIR))
    cfg.set_main_option("sqlalchemy.url", db_url)
    command.upgrade(cfg, "head")
    _, session_factory = init_database(db_url)
    return session_factory


def _claim() -> MathematicalManuscriptClaim:
    statement = "∀ A B ∈ M_n，tr(AB)=tr(BA)"
    return MathematicalManuscriptClaim(
        manuscript_claim_id="thm-1",
        kind=TheoryClaimKind.THEOREM,
        display_statement=statement,
        normalized_statement_hash=claim_statement_hash(
            display_statement=statement,
            object_domain="有限矩阵 M_n",
            quantifiers=("forall A", "forall B"),
            assumptions=("A,B 为方阵",),
            conclusion="tr(AB)=tr(BA)",
        ),
        source_claim_contract_id="cc-1",
        object_domain="有限矩阵 M_n",
        quantifiers=("forall A", "forall B"),
        assumptions=("A,B 为方阵",),
        conclusion="tr(AB)=tr(BA)",
        proof_status=ProofStatus.COMPLETE,
        proof_artifact_ids=("proof-1",),
        tool_receipt_ids=("lean-1",),
        semantic_status="ALIGNED",
        citation_refs=("ref-cyclic",),
        limitations=("浮点实现未覆盖",),
        manuscript_locations=("sec:main",),
    )


def _manuscript() -> TheoryMasterManuscript:
    return TheoryMasterManuscript(
        manuscript_id="tms-1",
        version=1,
        project_id="p-1",
        evidence_tier=TheoryEvidenceTier.PROVED_AND_SEMANTICALLY_ACCEPTED,
        title="Cyclic trace invariance",
        abstract="abstract",
        msc="15A15",
        keywords=("trace",),
        introduction="intro",
        related_work="related",
        notation_and_preliminaries="notation",
        definitions_and_assumptions="defs",
        main_results="tr(AB)=tr(BA)",
        proof_architecture="direct",
        proofs_status="complete",
        examples_counterexamples="non-square",
        verification_methods_scope="Lean 4",
        limitations_unresolved_obligations="floating point not covered",
        implications_applications="numerical libraries",
        availability="lean sources",
        structured_author_fields={
            "author_contributions": "NEEDS_AUTHOR_INPUT",
            "funding": "NEEDS_AUTHOR_INPUT",
        },
        references=("ref-cyclic",),
        claims=(_claim(),),
        dependency_graph=ProofDependencyGraph(nodes=("thm-1",), edges=()),
        created_at=NOW,
    )


def _run_to_audited(session_factory, artifact_root: Path):
    with session_factory() as session:
        create_theory_master_manuscript(
            session,
            project_id="p-1",
            manuscript=_manuscript(),
            artifact_root=artifact_root,
        )
        audited, findings = audit_theory_master_manuscript(
            session,
            project_id="p-1",
            manuscript=_manuscript(),
            auditor_session_id="auditor-1",
            draft_generator_session_ids=("generator-1",),
            artifact_root=artifact_root,
        )
        session.commit()
    assert audited.audit_status is TheoryManuscriptAuditStatus.AUDITED_CLEAN
    assert findings == ()
    return audited


def _formal_decision(session_factory, artifact_root: Path, decision: str):
    audited = _run_to_audited(session_factory, artifact_root)
    with session_factory() as session:
        gate = open_theory_formal_manuscript_decision(
            session,
            project_id="p-1",
            manuscript=audited,
            evidence_baseline_hash="e" * 64,
            artifact_root=artifact_root,
            gate_id="gate-tfm-1",
        )
        resolved = resolve_theory_formal_manuscript_decision(
            session,
            gate=gate,
            decision=decision,
            actor=ProvenanceType.USER_DECISION,
            user_event_id="uev-fm",
            manuscript=audited,
            at=NOW,
            artifact_root=artifact_root,
        )
        session.commit()
    return audited, resolved


def test_keep_master_only_delivery_is_complete(tmp_path):
    session_factory = _fresh_database(tmp_path)
    artifact_root = tmp_path / "artifacts"
    audited, resolved = _formal_decision(session_factory, artifact_root, "KEEP_MASTER_ONLY")
    assert resolved.decision == "KEEP_MASTER_ONLY"
    blockers = theory_delivery_readiness_blockers(
        master_ready=True,
        master_delivered=True,
        keep_master_only=True,
        formal_requested=False,
        profile_fresh=True,
        compliance_ok=True,
        audit_clean=True,
    )
    assert blockers == ()
    # formal path not requested: nothing else needed (03C section 9)
    assert audited.master_hash


def test_write_path_selects_profile_and_adapts(tmp_path):
    session_factory = _fresh_database(tmp_path)
    artifact_root = tmp_path / "artifacts"
    audited, write_gate = _formal_decision(
        session_factory, artifact_root, "WRITE_FORMAL_MANUSCRIPT"
    )
    with session_factory() as session:
        selection = open_theory_profile_selection(
            session,
            project_id="p-1",
            formal_decision=write_gate,
            manuscript=audited,
            artifact_root=artifact_root,
            gate_id="gate-tps-1",
        )
        resolved, profile = resolve_theory_profile_selection(
            session,
            gate=selection,
            decision="MATH_ANNALS_OF_MATHEMATICS",
            actor=ProvenanceType.USER_DECISION,
            user_event_id="uev-profile",
            now=NOW,
            manuscript=audited,
            artifact_root=artifact_root,
        )
        adapted = create_theory_venue_adapted_manuscript(
            session,
            project_id="p-1",
            manuscript=audited,
            profile=profile,
            compliance_matrix=VenueComplianceMatrix(
                matrix_id="tcm-1",
                project_id="p-1",
                profile_id="MATH_ANNALS_OF_MATHEMATICS",
                entries=(
                    VenueComplianceEntry(
                        requirement_id="machine-1",
                        status=VenueComplianceStatus.PASS,
                        evidence_ref="sec:1",
                    ),
                ),
            ),
            adapted_text="# Adapted for Annals\n",
            machine_blocking_requirements=("machine-1",),
            human_blocking_requirements=(),
            artifact_root=artifact_root,
        )
        session.commit()
    assert resolved.decision == "MATH_ANNALS_OF_MATHEMATICS"
    assert adapted["status"] == "FORMAL_MANUSCRIPT_READY"
    assert adapted["master_statement_hashes"]["thm-1"] == audited.statement_hashes()["thm-1"]
    blockers = theory_delivery_readiness_blockers(
        master_ready=True,
        master_delivered=True,
        keep_master_only=False,
        formal_requested=True,
        profile_fresh=True,
        compliance_ok=True,
        audit_clean=True,
    )
    assert blockers == ()


def test_write_path_without_profile_is_not_ready(tmp_path):
    session_factory = _fresh_database(tmp_path)
    artifact_root = tmp_path / "artifacts"
    _formal_decision(session_factory, artifact_root, "WRITE_FORMAL_MANUSCRIPT")
    blockers = theory_delivery_readiness_blockers(
        master_ready=True,
        master_delivered=True,
        keep_master_only=False,
        formal_requested=True,
        profile_fresh=False,
        compliance_ok=False,
        audit_clean=True,
    )
    assert blockers
    assert any("Profile" in blocker for blocker in blockers)
    assert any("Compliance" in blocker for blocker in blockers)


def test_stale_guidance_blocks_formal_manuscript(tmp_path):
    import dataclasses
    from datetime import timedelta

    from synaisthesis.domain.errors import DomainError
    from synaisthesis.publication.profiles import FreshnessStatus

    session_factory = _fresh_database(tmp_path)
    artifact_root = tmp_path / "artifacts"
    audited, write_gate = _formal_decision(
        session_factory, artifact_root, "WRITE_FORMAL_MANUSCRIPT"
    )
    stale_profile = dataclasses.replace(
        profile_for("MATH_ANNALS_OF_MATHEMATICS"),
        accessed_at=NOW - timedelta(days=90),
        last_modified_if_available=NOW - timedelta(days=90),
        profile_hash=None,
    )
    assert stale_profile.freshness_status(NOW) is FreshnessStatus.STALE_GUIDANCE
    with session_factory() as session:
        selection = open_theory_profile_selection(
            session,
            project_id="p-1",
            formal_decision=write_gate,
            manuscript=audited,
            artifact_root=artifact_root,
            gate_id="gate-tps-1",
        )
        with pytest.raises(DomainError) as exc_info:
            resolve_theory_profile_selection(
                session,
                gate=selection,
                decision="MATH_ANNALS_OF_MATHEMATICS",
                actor=ProvenanceType.USER_DECISION,
                user_event_id="uev-profile",
                now=NOW,
                manuscript=audited,
                artifact_root=artifact_root,
                profile_override=stale_profile,
            )
    assert exc_info.value.error_code == "STALE_GUIDANCE"
