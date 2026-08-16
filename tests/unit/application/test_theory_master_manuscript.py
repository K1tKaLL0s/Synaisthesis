"""M9.2 unit tests for the theory master manuscript service (03C sections 5-7)."""

from __future__ import annotations

import dataclasses
from datetime import UTC, datetime
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config

from synaisthesis.application.theory_publication_service import (
    audit_theory_master_manuscript,
    create_theory_master_manuscript,
    create_theory_venue_adapted_manuscript,
    load_theory_master_manuscript,
    open_theory_formal_manuscript_decision,
    open_theory_profile_selection,
    resolve_theory_formal_manuscript_decision,
    resolve_theory_profile_selection,
)
from synaisthesis.domain.enums import (
    GateStatus,
    ProvenanceType,
    ResearchRoute,
)
from synaisthesis.domain.errors import DomainError
from synaisthesis.domain.publication import (
    TheoryEvidenceTier,
    TheoryManuscriptAuditStatus,
    VenueComplianceEntry,
    VenueComplianceMatrix,
    VenueComplianceStatus,
)
from synaisthesis.publication.compliance import theory_compliance_overall_status
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
REPO_ROOT = Path(__file__).resolve().parents[3]
MIGRATIONS_DIR = REPO_ROOT / "src" / "synaisthesis" / "storage" / "migrations"


def _fresh_database(tmp_path: Path):
    db_url = f"sqlite:///{tmp_path / 'theory-pub.db'}"
    cfg = Config()
    cfg.set_main_option("script_location", str(MIGRATIONS_DIR))
    cfg.set_main_option("sqlalchemy.url", db_url)
    command.upgrade(cfg, "head")
    _, session_factory = init_database(db_url)
    return session_factory


def _claim(claim_id: str = "thm-1") -> MathematicalManuscriptClaim:
    statement = "∀ A B ∈ M_n，tr(AB)=tr(BA)"
    return MathematicalManuscriptClaim(
        manuscript_claim_id=claim_id,
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


def _persist_and_audit(session_factory, artifact_root: Path):
    manuscript = _manuscript()
    with session_factory() as session:
        create_theory_master_manuscript(
            session, project_id="p-1", manuscript=manuscript, artifact_root=artifact_root
        )
        audited, findings = audit_theory_master_manuscript(
            session,
            project_id="p-1",
            manuscript=manuscript,
            auditor_session_id="auditor-1",
            draft_generator_session_ids=("generator-1",),
            artifact_root=artifact_root,
        )
        session.commit()
    return audited, findings


def test_manuscript_round_trip(tmp_path):
    session_factory = _fresh_database(tmp_path)
    artifact_root = tmp_path / "artifacts"
    manuscript = _manuscript()
    with session_factory() as session:
        create_theory_master_manuscript(
            session, project_id="p-1", manuscript=manuscript, artifact_root=artifact_root
        )
        session.commit()
    with session_factory() as session:
        reloaded = load_theory_master_manuscript(session, "tms-1", artifact_root=artifact_root)
    assert reloaded == manuscript
    assert reloaded.master_hash == manuscript.master_hash


def test_audit_clean_opens_formal_decision(tmp_path):
    session_factory = _fresh_database(tmp_path)
    artifact_root = tmp_path / "artifacts"
    audited, findings = _persist_and_audit(session_factory, artifact_root)
    assert audited.audit_status is TheoryManuscriptAuditStatus.AUDITED_CLEAN
    assert findings == ()
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
            decision="KEEP_MASTER_ONLY",
            actor=ProvenanceType.USER_DECISION,
            user_event_id="uev-fm",
            manuscript=audited,
            at=NOW,
            artifact_root=artifact_root,
        )
        session.commit()
    assert resolved.status is GateStatus.RESOLVED
    assert resolved.decision == "KEEP_MASTER_ONLY"


def test_unaudited_manuscript_cannot_open_decision(tmp_path):
    session_factory = _fresh_database(tmp_path)
    artifact_root = tmp_path / "artifacts"
    manuscript = _manuscript()
    with session_factory() as session:
        create_theory_master_manuscript(
            session, project_id="p-1", manuscript=manuscript, artifact_root=artifact_root
        )
        with pytest.raises(DomainError) as exc_info:
            open_theory_formal_manuscript_decision(
                session,
                project_id="p-1",
                manuscript=manuscript,
                evidence_baseline_hash="e" * 64,
                artifact_root=artifact_root,
            )
    assert exc_info.value.error_code == "THEORY_MASTER_MANUSCRIPT_AUDITING"


def _write_gate(session_factory, artifact_root: Path):
    audited, _findings = _persist_and_audit(session_factory, artifact_root)
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
            decision="WRITE_FORMAL_MANUSCRIPT",
            actor=ProvenanceType.USER_DECISION,
            user_event_id="uev-write",
            manuscript=audited,
            at=NOW,
            artifact_root=artifact_root,
        )
        session.commit()
    return audited, resolved


def test_profile_selection_requires_write_and_route(tmp_path):
    session_factory = _fresh_database(tmp_path)
    artifact_root = tmp_path / "artifacts"
    audited, write_gate = _write_gate(session_factory, artifact_root)
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
            decision="MATH_ARXIV_PREPRINT",
            actor=ProvenanceType.USER_DECISION,
            user_event_id="uev-profile",
            now=NOW,
            manuscript=audited,
            artifact_root=artifact_root,
        )
        session.commit()
    assert resolved.decision == "MATH_ARXIV_PREPRINT"
    assert profile.route is ResearchRoute.THEORY
    assert profile.venue_kind.value == "PREPRINT_REPOSITORY"

    # engineering profile is rejected on the theory route
    with session_factory() as session:
        selection2 = open_theory_profile_selection(
            session,
            project_id="p-1",
            formal_decision=write_gate,
            manuscript=audited,
            artifact_root=artifact_root,
            gate_id="gate-tps-2",
        )
        with pytest.raises(DomainError) as exc_info:
            resolve_theory_profile_selection(
                session,
                gate=selection2,
                decision="ENG_IEEE_TSE",
                actor=ProvenanceType.USER_DECISION,
                user_event_id="uev-bad",
                now=NOW,
                manuscript=audited,
                artifact_root=artifact_root,
            )
    assert exc_info.value.error_code == "PROFILE_ROUTE_MISMATCH"


def test_adapted_manuscript_preserves_statement_hashes(tmp_path):
    session_factory = _fresh_database(tmp_path)
    artifact_root = tmp_path / "artifacts"
    audited, write_gate = _write_gate(session_factory, artifact_root)
    profile = profile_for("MATH_ARXIV_PREPRINT")
    with session_factory() as session:
        selection = open_theory_profile_selection(
            session,
            project_id="p-1",
            formal_decision=write_gate,
            manuscript=audited,
            artifact_root=artifact_root,
            gate_id="gate-tps-1",
        )
        resolved, _profile = resolve_theory_profile_selection(
            session,
            gate=selection,
            decision="MATH_ARXIV_PREPRINT",
            actor=ProvenanceType.USER_DECISION,
            user_event_id="uev-profile",
            now=NOW,
            manuscript=audited,
            artifact_root=artifact_root,
        )
        del resolved
        adapted = create_theory_venue_adapted_manuscript(
            session,
            project_id="p-1",
            manuscript=audited,
            profile=profile,
            compliance_matrix=VenueComplianceMatrix(
                matrix_id="tcm-1",
                project_id="p-1",
                profile_id="MATH_ARXIV_PREPRINT",
                entries=(
                    VenueComplianceEntry(
                        requirement_id="preprint",
                        status=VenueComplianceStatus.NOT_APPLICABLE,
                        evidence_ref=None,
                    ),
                ),
            ),
            adapted_text="# Preprint\n",
            machine_blocking_requirements=(),
            human_blocking_requirements=(),
            artifact_root=artifact_root,
        )
        session.commit()
    assert adapted["master_hash"] == audited.master_hash
    assert adapted["master_statement_hashes"]["thm-1"] == audited.statement_hashes()["thm-1"]
    assert adapted["status"] == "ARXIV_PACKAGE_READY"


def test_arxiv_adaptation_rejects_peer_review_label(tmp_path):
    session_factory = _fresh_database(tmp_path)
    artifact_root = tmp_path / "artifacts"
    audited, write_gate = _write_gate(session_factory, artifact_root)
    profile = profile_for("MATH_ARXIV_PREPRINT")
    with session_factory() as session, pytest.raises(DomainError) as exc_info:
        create_theory_venue_adapted_manuscript(
            session,
            project_id="p-1",
            manuscript=audited,
            profile=profile,
            compliance_matrix=VenueComplianceMatrix(
                matrix_id="tcm-2",
                project_id="p-1",
                profile_id="MATH_ARXIV_PREPRINT",
                entries=(),
            ),
            adapted_text="# Peer Reviewed\n",
            machine_blocking_requirements=(),
            human_blocking_requirements=(),
            artifact_root=artifact_root,
        )
    assert exc_info.value.error_code == "ARXIV_IDENTITY_VIOLATION"


def test_compliance_overall_status():
    matrix = VenueComplianceMatrix(
        matrix_id="tcm-3",
        project_id="p-1",
        profile_id="MATH_ANNALS_OF_MATHEMATICS",
        entries=(
            VenueComplianceEntry(
                requirement_id="machine-1",
                status=VenueComplianceStatus.PASS,
                evidence_ref="sec:1",
            ),
            VenueComplianceEntry(
                requirement_id="human-1",
                status=VenueComplianceStatus.NEEDS_AUTHOR_INPUT,
                evidence_ref=None,
            ),
        ),
    )
    overall, blockers = theory_compliance_overall_status(
        matrix,
        machine_blocking_requirements=("machine-1",),
        human_blocking_requirements=("human-1",),
    )
    assert overall == "FORMAL_MANUSCRIPT_DRAFT"
    assert any("human-only" in blocker for blocker in blockers)
    ready_matrix = dataclasses.replace(
        matrix,
        entries=(
            VenueComplianceEntry(
                requirement_id="machine-1",
                status=VenueComplianceStatus.PASS,
                evidence_ref="sec:1",
            ),
            VenueComplianceEntry(
                requirement_id="human-1",
                status=VenueComplianceStatus.PASS,
                evidence_ref="sec:2",
            ),
        ),
    )
    overall, blockers = theory_compliance_overall_status(
        ready_matrix,
        machine_blocking_requirements=("machine-1",),
        human_blocking_requirements=("human-1",),
    )
    assert overall == "FORMAL_MANUSCRIPT_READY"
    assert blockers == ()
