"""M2.11 unit tests for the engineering publication evidence policy (03B/03C)."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config

from synaisthesis.application.publication_service import (
    audit_engineering_master_manuscript,
    create_engineering_master_manuscript,
    create_venue_adapted_manuscript,
    load_engineering_master_manuscript,
    open_formal_manuscript_decision,
    open_publication_profile_selection,
    resolve_formal_manuscript_decision,
    resolve_publication_profile_selection,
)
from synaisthesis.domain.enums import (
    GateStatus,
    ProvenanceType,
    ResearchRoute,
)
from synaisthesis.domain.errors import DomainError
from synaisthesis.domain.publication import (
    AUTHOR_INPUT_NEEDS,
    AUTHOR_INPUT_PROVIDED,
    ClaimEvidenceEntry,
    ClaimEvidenceMatrix,
    ClaimStatus,
    EngineeringEvidenceTier,
    EngineeringManuscriptAuditStatus,
    EngineeringMasterManuscript,
    EngineeringPaperType,
    VenueComplianceEntry,
    VenueComplianceMatrix,
    VenueComplianceStatus,
)
from synaisthesis.publication.profiles import (
    ENGINEERING_PROFILES,
    FreshnessStatus,
    PublicationProfile,
    VenueKind,
    profile_for,
)
from synaisthesis.storage.database import init_database

NOW = datetime(2026, 8, 17, 2, 0, 0, tzinfo=UTC)
REPO_ROOT = Path(__file__).resolve().parents[3]
MIGRATIONS_DIR = REPO_ROOT / "src" / "synaisthesis" / "storage" / "migrations"

AUTHOR_FIELDS = (
    "author_contributions",
    "ai_use_disclosure",
    "funding",
    "conflicts",
    "acknowledgements",
)


def _fresh_database(tmp_path: Path):
    db_url = f"sqlite:///{tmp_path / 'pub.db'}"
    cfg = Config()
    cfg.set_main_option("script_location", str(MIGRATIONS_DIR))
    cfg.set_main_option("sqlalchemy.url", db_url)
    command.upgrade(cfg, "head")
    _, session_factory = init_database(db_url)
    return session_factory


def _claim_matrix(*entries: ClaimEvidenceEntry) -> ClaimEvidenceMatrix:
    return ClaimEvidenceMatrix(matrix_id="cem-1", project_id="p-1", entries=entries)


def _planned_claim(claim_id: str, statement: str) -> ClaimEvidenceEntry:
    return ClaimEvidenceEntry(
        claim_id=claim_id,
        statement=statement,
        source_requirement_id="R1",
        design_element_id="d-1",
        evidence_receipt_id=None,
        figure_table_ref=None,
        citation_ref=None,
        status=ClaimStatus.PLANNED,
    )


def _manuscript(**overrides) -> EngineeringMasterManuscript:
    params = {
        "manuscript_id": "ms-1",
        "version": 1,
        "project_id": "p-1",
        "paper_type": EngineeringPaperType.DESIGN_ARTICLE,
        "evidence_tier": EngineeringEvidenceTier.BLUEPRINT_ONLY,
        "title": "A design",
        "abstract": "abstract",
        "keywords": ("design",),
        "statement_of_need": "need",
        "related_work_neighbors": ("n1",),
        "requirements_conops_design": "section",
        "method_architecture": "section",
        "vv_methods": "section",
        "results": "no results",
        "comparison_with_baseline": "none",
        "threats_limitations": "limits",
        "application_extension": "none",
        "security_privacy_ethics": "none",
        "data_availability": "none",
        "reproducibility_instructions": "steps",
        "conclusion": "conclusion",
        "references": ("r1",),
        "author_contributions": AUTHOR_INPUT_NEEDS,
        "ai_use_disclosure": AUTHOR_INPUT_NEEDS,
        "funding": AUTHOR_INPUT_NEEDS,
        "conflicts": AUTHOR_INPUT_NEEDS,
        "acknowledgements": AUTHOR_INPUT_NEEDS,
        "author_input_status": {field: AUTHOR_INPUT_NEEDS for field in AUTHOR_FIELDS},
        "claim_ids": ("claim-1",),
    }
    params.update(overrides)
    return EngineeringMasterManuscript(**params)


def _provided_manuscript(**overrides) -> EngineeringMasterManuscript:
    return _manuscript(
        author_contributions="设计并实现",
        author_input_status={
            "author_contributions": AUTHOR_INPUT_PROVIDED,
            "ai_use_disclosure": AUTHOR_INPUT_NEEDS,
            "funding": AUTHOR_INPUT_NEEDS,
            "conflicts": AUTHOR_INPUT_NEEDS,
            "acknowledgements": AUTHOR_INPUT_NEEDS,
        },
        **overrides,
    )


# ---------------------------------------------------------------------------
# ENG8 evidence policy (03B, section 11)
# ---------------------------------------------------------------------------


def test_blueprint_only_rejects_execution_receipt_claims(tmp_path):
    session_factory = _fresh_database(tmp_path)
    artifact_root = tmp_path / "artifacts"
    matrix = _claim_matrix(
        ClaimEvidenceEntry(
            claim_id="claim-1",
            statement="蓝图覆盖所有关键需求",
            source_requirement_id="R1",
            design_element_id="d-1",
            evidence_receipt_id="receipt-1",
            figure_table_ref="fig-1",
            citation_ref="ref-1",
        )
    )
    with session_factory() as session, pytest.raises(DomainError) as exc_info:
        create_engineering_master_manuscript(
            session,
            project_id="p-1",
            manuscript=_manuscript(),
            claim_matrix=matrix,
            artifact_root=artifact_root,
        )
    assert exc_info.value.error_code == "MANUSCRIPT_CLAIM_UNSUPPORTED"


def test_completion_claim_without_receipt_is_blocked(tmp_path):
    session_factory = _fresh_database(tmp_path)
    artifact_root = tmp_path / "artifacts"
    matrix = _claim_matrix(_planned_claim("claim-1", "结果表明系统延迟优于基线"))
    with session_factory() as session, pytest.raises(DomainError) as exc_info:
        create_engineering_master_manuscript(
            session,
            project_id="p-1",
            manuscript=_manuscript(),
            claim_matrix=matrix,
            artifact_root=artifact_root,
        )
    assert exc_info.value.error_code == "MANUSCRIPT_CLAIM_UNSUPPORTED"


def test_blueprint_only_master_round_trip(tmp_path):
    session_factory = _fresh_database(tmp_path)
    artifact_root = tmp_path / "artifacts"
    manuscript = _provided_manuscript()
    matrix = _claim_matrix(_planned_claim("claim-1", "蓝图覆盖所有关键需求（计划）"))
    with session_factory() as session:
        saved = create_engineering_master_manuscript(
            session,
            project_id="p-1",
            manuscript=manuscript,
            claim_matrix=matrix,
            artifact_root=artifact_root,
        )
        session.commit()
    with session_factory() as session:
        reloaded = load_engineering_master_manuscript(session, "ms-1", artifact_root=artifact_root)
    assert reloaded == saved
    assert reloaded.paper_type is EngineeringPaperType.DESIGN_ARTICLE


def test_audit_requires_independent_auditor(tmp_path):
    session_factory = _fresh_database(tmp_path)
    artifact_root = tmp_path / "artifacts"
    manuscript = _provided_manuscript()
    with session_factory() as session, pytest.raises(DomainError) as exc_info:
        audit_engineering_master_manuscript(
            session,
            project_id="p-1",
            manuscript=manuscript,
            auditor_session_id="session-a",
            draft_generator_session_ids=("session-a", "session-b"),
            findings=(("INFO", "style"),),
            artifact_root=artifact_root,
        )
    assert exc_info.value.error_code == "AUDITOR_NOT_INDEPENDENT"


def test_audit_major_finding_blocks_clean_status(tmp_path):
    session_factory = _fresh_database(tmp_path)
    artifact_root = tmp_path / "artifacts"
    manuscript = _provided_manuscript()
    with session_factory() as session:
        audited = audit_engineering_master_manuscript(
            session,
            project_id="p-1",
            manuscript=manuscript,
            auditor_session_id="auditor-1",
            draft_generator_session_ids=("generator-1",),
            findings=(("MAJOR", "结果时态无证据"),),
            artifact_root=artifact_root,
        )
    assert audited.audit_status is EngineeringManuscriptAuditStatus.AUDITED_WITH_FINDINGS
    assert audited.master_hash == manuscript.master_hash


def test_audit_clean_preserves_master_hash(tmp_path):
    session_factory = _fresh_database(tmp_path)
    artifact_root = tmp_path / "artifacts"
    manuscript = _provided_manuscript()
    with session_factory() as session:
        audited = audit_engineering_master_manuscript(
            session,
            project_id="p-1",
            manuscript=manuscript,
            auditor_session_id="auditor-1",
            draft_generator_session_ids=("generator-1",),
            findings=(("MINOR", "措辞建议"),),
            artifact_root=artifact_root,
        )
    assert audited.audit_status is EngineeringManuscriptAuditStatus.AUDITED_CLEAN
    assert audited.master_hash == manuscript.master_hash


def test_formal_decision_requires_audited_delivery(tmp_path):
    session_factory = _fresh_database(tmp_path)
    artifact_root = tmp_path / "artifacts"
    manuscript = _provided_manuscript()
    with session_factory() as session, pytest.raises(DomainError) as exc_info:
        open_formal_manuscript_decision(
            session,
            project_id="p-1",
            manuscript=manuscript,
            delivery_hash="d" * 64,
            artifact_root=artifact_root,
        )
    assert exc_info.value.error_code == "ENGINEERING_MASTER_MANUSCRIPT_AUDITING"


def _audited_manuscript(tmp_path) -> EngineeringMasterManuscript:
    session_factory = _fresh_database(tmp_path)
    artifact_root = tmp_path / "artifacts"
    manuscript = _provided_manuscript()
    with session_factory() as session:
        audited = audit_engineering_master_manuscript(
            session,
            project_id="p-1",
            manuscript=manuscript,
            auditor_session_id="auditor-1",
            draft_generator_session_ids=("generator-1",),
            findings=(),
            artifact_root=artifact_root,
        )
        session.commit()
    return audited


def test_formal_decision_open_and_resolve_keep_master(tmp_path):
    session_factory = _fresh_database(tmp_path)
    artifact_root = tmp_path / "artifacts"
    manuscript = _audited_manuscript(tmp_path)
    with session_factory() as session:
        gate = open_formal_manuscript_decision(
            session,
            project_id="p-1",
            manuscript=manuscript,
            delivery_hash="d" * 64,
            artifact_root=artifact_root,
            gate_id="gate-fm-1",
        )
        resolved = resolve_formal_manuscript_decision(
            session,
            gate=gate,
            decision="KEEP_MASTER_ONLY",
            actor=ProvenanceType.USER_DECISION,
            user_event_id="uev-fm",
            manuscript=manuscript,
            at=NOW,
            artifact_root=artifact_root,
        )
        session.commit()
    assert resolved.status is GateStatus.RESOLVED
    assert resolved.decision == "KEEP_MASTER_ONLY"


def test_profile_selection_requires_write_decision(tmp_path):
    session_factory = _fresh_database(tmp_path)
    artifact_root = tmp_path / "artifacts"
    manuscript = _audited_manuscript(tmp_path)
    with session_factory() as session:
        gate = open_formal_manuscript_decision(
            session,
            project_id="p-1",
            manuscript=manuscript,
            delivery_hash="d" * 64,
            artifact_root=artifact_root,
            gate_id="gate-fm-1",
        )
        # user chooses KEEP_MASTER_ONLY -> profile selection must be blocked
        resolved = resolve_formal_manuscript_decision(
            session,
            gate=gate,
            decision="KEEP_MASTER_ONLY",
            actor=ProvenanceType.USER_DECISION,
            user_event_id="uev-fm",
            manuscript=manuscript,
            at=NOW,
            artifact_root=artifact_root,
        )
        with pytest.raises(DomainError) as exc_info:
            open_publication_profile_selection(
                session,
                project_id="p-1",
                formal_decision=resolved,
                manuscript=manuscript,
                artifact_root=artifact_root,
            )
    assert exc_info.value.error_code == "FORMAL_MANUSCRIPT_DECISION_REQUIRED"


def test_scope_mismatch_blocks_software_journal(tmp_path):
    session_factory = _fresh_database(tmp_path)
    artifact_root = tmp_path / "artifacts"
    manuscript = _audited_manuscript(tmp_path)
    with session_factory() as session:
        gate = open_formal_manuscript_decision(
            session,
            project_id="p-1",
            manuscript=manuscript,
            delivery_hash="d" * 64,
            artifact_root=artifact_root,
            gate_id="gate-fm-1",
        )
        write_gate = resolve_formal_manuscript_decision(
            session,
            gate=gate,
            decision="WRITE_FORMAL_MANUSCRIPT",
            actor=ProvenanceType.USER_DECISION,
            user_event_id="uev-fm",
            manuscript=manuscript,
            at=NOW,
            artifact_root=artifact_root,
        )
        selection = open_publication_profile_selection(
            session,
            project_id="p-1",
            formal_decision=write_gate,
            manuscript=manuscript,
            artifact_root=artifact_root,
            gate_id="gate-ps-1",
        )
        with pytest.raises(DomainError) as exc_info:
            resolve_publication_profile_selection(
                session,
                gate=selection,
                decision="ENG_IEEE_TSE",
                actor=ProvenanceType.USER_DECISION,
                user_event_id="uev-ps",
                project_kind="hardware",
                now=NOW,
                manuscript=manuscript,
                software_evidence=None,
                artifact_root=artifact_root,
            )
    assert exc_info.value.error_code == "PROFILE_SCOPE_MISMATCH"


def test_joss_requires_real_software(tmp_path):
    session_factory = _fresh_database(tmp_path)
    artifact_root = tmp_path / "artifacts"
    manuscript = _audited_manuscript(tmp_path)
    with session_factory() as session:
        gate = open_formal_manuscript_decision(
            session,
            project_id="p-1",
            manuscript=manuscript,
            delivery_hash="d" * 64,
            artifact_root=artifact_root,
            gate_id="gate-fm-1",
        )
        write_gate = resolve_formal_manuscript_decision(
            session,
            gate=gate,
            decision="WRITE_FORMAL_MANUSCRIPT",
            actor=ProvenanceType.USER_DECISION,
            user_event_id="uev-fm",
            manuscript=manuscript,
            at=NOW,
            artifact_root=artifact_root,
        )
        selection = open_publication_profile_selection(
            session,
            project_id="p-1",
            formal_decision=write_gate,
            manuscript=manuscript,
            artifact_root=artifact_root,
            gate_id="gate-ps-1",
        )
        with pytest.raises(DomainError) as exc_info:
            resolve_publication_profile_selection(
                session,
                gate=selection,
                decision="JOSS_RESEARCH_SOFTWARE",
                actor=ProvenanceType.USER_DECISION,
                user_event_id="uev-ps",
                project_kind="software",
                now=NOW,
                manuscript=manuscript,
                software_evidence={
                    "software_exists": False,
                    "open_source_license": None,
                    "automated_tests_pass": None,
                },
                artifact_root=artifact_root,
            )
    assert exc_info.value.error_code == "SOFTWARE_ARTICLE_INELIGIBLE"


def test_stale_guidance_blocks_formal_manuscript(tmp_path):
    stale_profile = _stale_profile()
    assert stale_profile.freshness_status(NOW) is FreshnessStatus.STALE_GUIDANCE
    session_factory = _fresh_database(tmp_path)
    artifact_root = tmp_path / "artifacts"
    manuscript = _audited_manuscript(tmp_path)
    with session_factory() as session:
        gate = open_formal_manuscript_decision(
            session,
            project_id="p-1",
            manuscript=manuscript,
            delivery_hash="d" * 64,
            artifact_root=artifact_root,
            gate_id="gate-fm-1",
        )
        write_gate = resolve_formal_manuscript_decision(
            session,
            gate=gate,
            decision="WRITE_FORMAL_MANUSCRIPT",
            actor=ProvenanceType.USER_DECISION,
            user_event_id="uev-fm",
            manuscript=manuscript,
            at=NOW,
            artifact_root=artifact_root,
        )
        selection = open_publication_profile_selection(
            session,
            project_id="p-1",
            formal_decision=write_gate,
            manuscript=manuscript,
            artifact_root=artifact_root,
            gate_id="gate-ps-1",
        )
        with pytest.raises(DomainError) as exc_info:
            resolve_publication_profile_selection(
                session,
                gate=selection,
                decision="CUSTOM_VENUE",
                actor=ProvenanceType.USER_DECISION,
                user_event_id="uev-ps",
                project_kind="hardware",
                now=NOW,
                manuscript=manuscript,
                software_evidence=None,
                artifact_root=artifact_root,
                profile_override=stale_profile,
            )
    assert exc_info.value.error_code == "STALE_GUIDANCE"


def _stale_profile() -> PublicationProfile:
    base = profile_for("CUSTOM_VENUE")
    import dataclasses

    return dataclasses.replace(
        base,
        accessed_at=NOW - timedelta(days=60),
        last_modified_if_available=NOW - timedelta(days=60),
        profile_hash=None,
    )


# ---------------------------------------------------------------------------
# Venue adaptation (03B, section 12.3)
# ---------------------------------------------------------------------------


def _compliance(entries: tuple[VenueComplianceEntry, ...]) -> VenueComplianceMatrix:
    return VenueComplianceMatrix(
        matrix_id="cm-1", project_id="p-1", profile_id="ENG_IEEE_TSE", entries=entries
    )


def test_adapted_manuscript_requires_clean_compliance(tmp_path):
    session_factory = _fresh_database(tmp_path)
    artifact_root = tmp_path / "artifacts"
    manuscript = _audited_manuscript(tmp_path)
    matrix = _compliance(
        (
            VenueComplianceEntry(
                requirement_id="template",
                status=VenueComplianceStatus.FAIL,
                evidence_ref=None,
            ),
        )
    )
    with session_factory() as session, pytest.raises(DomainError) as exc_info:
        create_venue_adapted_manuscript(
            session,
            project_id="p-1",
            manuscript=manuscript,
            profile=profile_for("ENG_IEEE_TSE"),
            compliance_matrix=matrix,
            adapted_text="# Adapted\n",
            artifact_root=artifact_root,
        )
    assert exc_info.value.error_code == "COMPLIANCE_MATRIX_INVALID"


def test_arxiv_adaptation_is_preprint_only(tmp_path):
    session_factory = _fresh_database(tmp_path)
    artifact_root = tmp_path / "artifacts"
    manuscript = _audited_manuscript(tmp_path)
    arxiv_profile = profile_for("ENG_ARXIV_PREPRINT")
    assert arxiv_profile.venue_kind is VenueKind.PREPRINT_REPOSITORY
    with session_factory() as session, pytest.raises(DomainError) as exc_info:
        create_venue_adapted_manuscript(
            session,
            project_id="p-1",
            manuscript=manuscript,
            profile=arxiv_profile,
            compliance_matrix=_compliance(
                (
                    VenueComplianceEntry(
                        requirement_id="preprint",
                        status=VenueComplianceStatus.NOT_APPLICABLE,
                        evidence_ref=None,
                    ),
                )
            ),
            adapted_text="# Peer Reviewed Article\n",
            artifact_root=artifact_root,
        )
    assert exc_info.value.error_code == "ARXIV_IDENTITY_VIOLATION"


def test_arxiv_adaptation_package_ready(tmp_path):
    from synaisthesis.publication.adaptation import VenueAdaptedManuscriptStatus

    session_factory = _fresh_database(tmp_path)
    artifact_root = tmp_path / "artifacts"
    manuscript = _audited_manuscript(tmp_path)
    with session_factory() as session:
        adapted = create_venue_adapted_manuscript(
            session,
            project_id="p-1",
            manuscript=manuscript,
            profile=profile_for("ENG_ARXIV_PREPRINT"),
            compliance_matrix=_compliance(
                (
                    VenueComplianceEntry(
                        requirement_id="preprint",
                        status=VenueComplianceStatus.NOT_APPLICABLE,
                        evidence_ref=None,
                    ),
                )
            ),
            adapted_text="# Preprint\n",
            artifact_root=artifact_root,
        )
    assert adapted.status is VenueAdaptedManuscriptStatus.ARXIV_PACKAGE_READY
    assert adapted.master_hash == manuscript.master_hash
    assert adapted.profile_id == "ENG_ARXIV_PREPRINT"


# ---------------------------------------------------------------------------
# Profile registry (03C, sections 2-3)
# ---------------------------------------------------------------------------


def test_profile_registry_integrity():
    assert len(ENGINEERING_PROFILES) == 8
    for profile in ENGINEERING_PROFILES:
        assert profile.route is ResearchRoute.ENGINEERING
        assert profile.profile_hash is not None and len(profile.profile_hash) == 64
    arxiv = profile_for("ENG_ARXIV_PREPRINT")
    assert arxiv.venue_kind is VenueKind.PREPRINT_REPOSITORY
    assert any("PEER_REVIEWED" in check for check in arxiv.blocking_checks)
    with pytest.raises(DomainError) as exc_info:
        profile_for("MISSING_PROFILE")
    assert exc_info.value.error_code == "PROFILE_UNKNOWN"


def test_scope_fit_rules():
    software = profile_for("ENG_IEEE_TSE")
    assert software.scope_fit(project_kind="software").value == "SCOPE_FIT_CANDIDATE"
    assert software.scope_fit(project_kind="hardware").value == "SCOPE_MISMATCH"
    arxiv = profile_for("ENG_ARXIV_PREPRINT")
    assert arxiv.scope_fit(project_kind="hardware").value == "SCOPE_FIT_CANDIDATE"
    custom = profile_for("CUSTOM_VENUE")
    assert custom.scope_fit(project_kind="hardware").value == "SCOPE_FIT_CANDIDATE"
