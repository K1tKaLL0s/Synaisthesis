"""Engineering publication service (03B sections 11-12, 03C; M2.11).

Order is enforced: master manuscript first, independent audit, user delivery,
then FORMAL_MANUSCRIPT_DECISION; only WRITE_FORMAL_MANUSCRIPT opens profile
selection; adaptation never overwrites the master; arXiv is always a
preprint repository; JOSS requires real software with license and tests.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from pathlib import Path
from typing import Any

from sqlalchemy.orm import Session

from synaisthesis.application.engineering_design_service import (
    GATE_AGGREGATE_TYPE,
    _load_artifact,
    _persist_engineering_event,
    _persist_stage_and_artifact,
)
from synaisthesis.domain.engineering import (
    EVENT_ENGINEERING_ARTIFACT_CREATED,
    EVENT_ENGINEERING_GATE_OPENED,
    EVENT_ENGINEERING_GATE_RESOLVED,
    EngineeringGateType,
    EngineeringStageId,
    FormalManuscriptDecision,
)
from synaisthesis.domain.enums import ProvenanceType
from synaisthesis.domain.errors import DomainError
from synaisthesis.domain.gate import EngineeringGate, EngineeringGateBinding
from synaisthesis.domain.publication import (
    ClaimEvidenceMatrix,
    EngineeringEvidenceTier,
    EngineeringManuscriptAuditStatus,
    EngineeringMasterManuscript,
    VenueComplianceMatrix,
    compliance_blockers,
    manuscript_claim_blockers,
    paper_type_allowed_by_evidence,
)
from synaisthesis.publication.adaptation import (
    VenueAdaptedManuscript,
    VenueAdaptedManuscriptStatus,
)
from synaisthesis.publication.profiles import (
    FreshnessStatus,
    PublicationProfile,
    ScopeFitStatus,
    profile_for,
)

MASTER_MANUSCRIPT_AGGREGATE_TYPE = "EngineeringMasterManuscript"
MANUSCRIPT_AUDIT_AGGREGATE_TYPE = "EngineeringManuscriptAudit"
ADAPTED_MANUSCRIPT_AGGREGATE_TYPE = "EngineeringVenueAdaptedManuscript"

MANUSCRIPT_SEVERITY_MAJOR = "MAJOR"
MANUSCRIPT_SEVERITY_CRITICAL = "CRITICAL"


def _audit_findings_blockers(
    findings: tuple[tuple[str, str], ...],
) -> tuple[str, ...]:
    return tuple(
        f"{severity}: {description}"
        for severity, description in findings
        if severity in {MANUSCRIPT_SEVERITY_MAJOR, MANUSCRIPT_SEVERITY_CRITICAL}
    )


# ---------------------------------------------------------------------------
# ENG8 — master manuscript (03B, section 11)
# ---------------------------------------------------------------------------


def create_engineering_master_manuscript(
    session: Session,
    *,
    project_id: str,
    manuscript: EngineeringMasterManuscript,
    claim_matrix: ClaimEvidenceMatrix,
    artifact_root: Path,
) -> EngineeringMasterManuscript:
    """Persist ENG8 only when evidence, claims and author fields all hold."""
    if not paper_type_allowed_by_evidence(manuscript.paper_type, manuscript.evidence_tier):
        raise DomainError(
            f"paper_type {manuscript.paper_type.value} 不允许于 evidence tier "
            f"{manuscript.evidence_tier.value}",
            error_code="MANUSCRIPT_PAPER_TYPE_INVALID",
        )
    if manuscript.evidence_tier is EngineeringEvidenceTier.BLUEPRINT_ONLY:
        for entry in claim_matrix.entries:
            if entry.evidence_receipt_id is not None:
                raise DomainError(
                    f"BLUEPRINT_ONLY 不得产生完成态结果；claim {entry.claim_id!r} 携带执行回执",
                    error_code="MANUSCRIPT_CLAIM_UNSUPPORTED",
                )
    claim_blockers = manuscript_claim_blockers(claim_matrix, manuscript.claim_ids)
    if claim_blockers:
        raise DomainError(
            "MANUSCRIPT_CLAIM_UNSUPPORTED: " + "; ".join(claim_blockers),
            error_code="MANUSCRIPT_CLAIM_UNSUPPORTED",
        )
    _persist_stage_and_artifact(
        session,
        project_id=project_id,
        stage=EngineeringStageId.ENG8,
        aggregate_type=MASTER_MANUSCRIPT_AGGREGATE_TYPE,
        aggregate_id=manuscript.manuscript_id,
        artifact_payload=manuscript.to_event_payload(),
        artifact_root=artifact_root,
    )
    _persist_engineering_event(
        session,
        event_type=EVENT_ENGINEERING_ARTIFACT_CREATED,
        aggregate_type=MANUSCRIPT_AUDIT_AGGREGATE_TYPE,
        aggregate_id=manuscript.manuscript_id,
        payload={"claim_matrix": claim_matrix.to_event_payload()},
        project_id=project_id,
        artifact_root=artifact_root,
    )
    return manuscript


def load_engineering_master_manuscript(
    session: Session, manuscript_id: str, *, artifact_root: Path
) -> EngineeringMasterManuscript:
    return _load_artifact(
        session,
        aggregate_type=MASTER_MANUSCRIPT_AGGREGATE_TYPE,
        aggregate_id=manuscript_id,
        model=EngineeringMasterManuscript,
        artifact_root=artifact_root,
        not_found_code="MANUSCRIPT_REQUIRED",
    )


def audit_engineering_master_manuscript(
    session: Session,
    *,
    project_id: str,
    manuscript: EngineeringMasterManuscript,
    auditor_session_id: str,
    draft_generator_session_ids: tuple[str, ...],
    findings: tuple[tuple[str, str], ...],
    artifact_root: Path,
) -> EngineeringMasterManuscript:
    """Audit by an auditor who never generated the draft (03B, 11.3)."""
    if auditor_session_id in draft_generator_session_ids:
        raise DomainError(
            "母稿审计人不得参与母稿生成",
            error_code="AUDITOR_NOT_INDEPENDENT",
        )
    findings_blockers = _audit_findings_blockers(findings)
    audit_status = (
        EngineeringManuscriptAuditStatus.AUDITED_WITH_FINDINGS
        if findings_blockers
        else EngineeringManuscriptAuditStatus.AUDITED_CLEAN
    )
    import dataclasses

    audited = dataclasses.replace(manuscript, audit_status=audit_status)
    if audited.master_hash != manuscript.master_hash:
        raise DomainError(
            "audit status 不得改变母稿内容 hash",
            error_code="ARTIFACT_HASH_MISMATCH",
        )
    _persist_engineering_event(
        session,
        event_type=EVENT_ENGINEERING_ARTIFACT_CREATED,
        aggregate_type=MANUSCRIPT_AUDIT_AGGREGATE_TYPE,
        aggregate_id=manuscript.manuscript_id,
        payload={
            "audit": {
                "manuscript_id": manuscript.manuscript_id,
                "auditor_session_id": auditor_session_id,
                "audit_status": audit_status.value,
                "findings": [list(finding) for finding in findings],
            }
        },
        project_id=project_id,
        artifact_root=artifact_root,
    )
    return audited


def _master_manuscript_delivered(manuscript: EngineeringMasterManuscript) -> bool:
    return manuscript.audit_status is EngineeringManuscriptAuditStatus.AUDITED_CLEAN


def open_formal_manuscript_decision(
    session: Session,
    *,
    project_id: str,
    manuscript: EngineeringMasterManuscript,
    artifact_root: Path,
    delivery_hash: str,
    gate_id: str | None = None,
) -> EngineeringGate:
    """Open FORMAL_MANUSCRIPT_DECISION only after the audited master delivery."""
    if not _master_manuscript_delivered(manuscript):
        raise DomainError(
            "母稿必须先独立审计并交付用户，才能打开 FORMAL_MANUSCRIPT_DECISION",
            error_code="ENGINEERING_MASTER_MANUSCRIPT_AUDITING",
        )
    if manuscript.master_hash is None:
        raise DomainError(
            "母稿缺少 master_hash",
            error_code="ARTIFACT_HASH_MISMATCH",
        )
    gate = EngineeringGate(
        gate_id=gate_id or f"gate-fm-{uuid.uuid4().hex[:12]}",
        project_id=project_id,
        gate_type=EngineeringGateType.FORMAL_MANUSCRIPT_DECISION,
        binding=EngineeringGateBinding(
            gate_type=EngineeringGateType.FORMAL_MANUSCRIPT_DECISION,
            artifact_id=manuscript.manuscript_id,
            version=manuscript.version,
            artifact_hash=manuscript.master_hash,
            bound_hashes={
                "master_manuscript": manuscript.master_hash,
                "delivery": delivery_hash,
            },
        ),
        reason="EngineeringMasterManuscript 已审计并交付，等待正式稿决策",
    )
    _persist_engineering_event(
        session,
        event_type=EVENT_ENGINEERING_GATE_OPENED,
        aggregate_type=GATE_AGGREGATE_TYPE,
        aggregate_id=gate.gate_id,
        payload={"gate": gate.to_event_payload()},
        project_id=project_id,
        artifact_root=artifact_root,
    )
    return gate


def resolve_formal_manuscript_decision(
    session: Session,
    *,
    gate: EngineeringGate,
    decision: str,
    actor: ProvenanceType,
    user_event_id: str,
    manuscript: EngineeringMasterManuscript,
    at: datetime,
    artifact_root: Path,
) -> EngineeringGate:
    """Resolve FORMAL_MANUSCRIPT_DECISION; binding must match the master."""
    if gate.gate_type is not EngineeringGateType.FORMAL_MANUSCRIPT_DECISION:
        raise DomainError(
            f"gate type {gate.gate_type.value} is not FORMAL_MANUSCRIPT_DECISION",
            error_code="GATE_TYPE_MISMATCH",
        )
    if manuscript.master_hash is None or gate.binding.artifact_hash != manuscript.master_hash:
        raise DomainError(
            "formal manuscript decision 绑定与当前母稿 hash 不一致",
            error_code="STALE_MANUSCRIPT_BINDING",
        )
    resolved = gate.resolve(
        decision=decision,
        actor=actor,
        user_event_id=user_event_id,
        at=at,
    )
    _persist_engineering_event(
        session,
        event_type=EVENT_ENGINEERING_GATE_RESOLVED,
        aggregate_type=GATE_AGGREGATE_TYPE,
        aggregate_id=resolved.gate_id,
        payload={"gate": resolved.to_event_payload()},
        project_id=gate.project_id,
        artifact_root=artifact_root,
    )
    return resolved


# ---------------------------------------------------------------------------
# ENG9 — profile selection and venue adaptation (03B, section 12)
# ---------------------------------------------------------------------------


def open_publication_profile_selection(
    session: Session,
    *,
    project_id: str,
    formal_decision: EngineeringGate,
    manuscript: EngineeringMasterManuscript,
    artifact_root: Path,
    gate_id: str | None = None,
) -> EngineeringGate:
    """Only a user WRITE_FORMAL_MANUSCRIPT decision may open profile selection."""
    if formal_decision.status.value != "RESOLVED" or (
        formal_decision.decision != FormalManuscriptDecision.WRITE_FORMAL_MANUSCRIPT.value
    ):
        raise DomainError(
            "只有用户选择 WRITE_FORMAL_MANUSCRIPT 后才允许 Profile Selection",
            error_code="FORMAL_MANUSCRIPT_DECISION_REQUIRED",
        )
    if (
        manuscript.master_hash is None
        or formal_decision.binding.artifact_hash != manuscript.master_hash
    ):
        raise DomainError(
            "formal decision 未绑定当前母稿",
            error_code="STALE_MANUSCRIPT_BINDING",
        )
    gate = EngineeringGate(
        gate_id=gate_id or f"gate-ps-{uuid.uuid4().hex[:12]}",
        project_id=project_id,
        gate_type=EngineeringGateType.PUBLICATION_PROFILE_SELECTION,
        binding=EngineeringGateBinding(
            gate_type=EngineeringGateType.PUBLICATION_PROFILE_SELECTION,
            artifact_id=manuscript.manuscript_id,
            version=manuscript.version,
            artifact_hash=manuscript.master_hash or "",
            bound_hashes={"master_manuscript": manuscript.master_hash or ""},
        ),
        reason="用户已选择 WRITE_FORMAL_MANUSCRIPT，等待 Profile 选择",
    )
    _persist_engineering_event(
        session,
        event_type=EVENT_ENGINEERING_GATE_OPENED,
        aggregate_type=GATE_AGGREGATE_TYPE,
        aggregate_id=gate.gate_id,
        payload={"gate": gate.to_event_payload()},
        project_id=project_id,
        artifact_root=artifact_root,
    )
    return gate


def resolve_publication_profile_selection(
    session: Session,
    *,
    gate: EngineeringGate,
    decision: str,
    actor: ProvenanceType,
    user_event_id: str,
    project_kind: str,
    now: datetime,
    manuscript: EngineeringMasterManuscript,
    software_evidence: dict[str, Any] | None,
    artifact_root: Path,
    profile_override: PublicationProfile | None = None,
) -> tuple[EngineeringGate, PublicationProfile]:
    """Resolve profile selection with scope/freshness/JOSS gates (03C, 2.2/2.3)."""
    if gate.gate_type is not EngineeringGateType.PUBLICATION_PROFILE_SELECTION:
        raise DomainError(
            f"gate type {gate.gate_type.value} is not PUBLICATION_PROFILE_SELECTION",
            error_code="GATE_TYPE_MISMATCH",
        )
    if manuscript.master_hash is None or gate.binding.artifact_hash != manuscript.master_hash:
        raise DomainError(
            "profile selection 绑定与当前母稿不一致",
            error_code="STALE_MANUSCRIPT_BINDING",
        )
    if profile_override is not None:
        if profile_override.profile_id != decision:
            raise DomainError(
                "profile_override 与 decision 不一致",
                error_code="PROFILE_UNKNOWN",
            )
        profile = profile_override
    else:
        profile = profile_for(decision)
    scope = profile.scope_fit(project_kind=project_kind)
    if scope is ScopeFitStatus.SCOPE_MISMATCH:
        raise DomainError(
            f"profile {profile.profile_id} 与项目类型 {project_kind!r} 不匹配；"
            "非软件项目可选择 CUSTOM_VENUE",
            error_code="PROFILE_SCOPE_MISMATCH",
        )
    if profile.freshness_status(now) is FreshnessStatus.STALE_GUIDANCE:
        raise DomainError(
            f"profile {profile.profile_id} 官方指南超过 freshness window，"
            "禁止生成 FORMAL_MANUSCRIPT_READY",
            error_code="STALE_GUIDANCE",
        )
    if profile.profile_id == "JOSS_RESEARCH_SOFTWARE":
        software_ok = (
            software_evidence is not None
            and bool(software_evidence.get("software_exists"))
            and bool(software_evidence.get("open_source_license"))
            and bool(software_evidence.get("automated_tests_pass"))
        )
        if not software_ok:
            raise DomainError(
                "JOSS 要求真实软件、可浏览源码、开源许可证与自动化测试",
                error_code="SOFTWARE_ARTICLE_INELIGIBLE",
            )
    resolved = gate.resolve(
        decision=decision,
        actor=actor,
        user_event_id=user_event_id,
        at=now,
    )
    _persist_engineering_event(
        session,
        event_type=EVENT_ENGINEERING_GATE_RESOLVED,
        aggregate_type=GATE_AGGREGATE_TYPE,
        aggregate_id=resolved.gate_id,
        payload={"gate": resolved.to_event_payload()},
        project_id=gate.project_id,
        artifact_root=artifact_root,
    )
    return resolved, profile


def create_venue_adapted_manuscript(
    session: Session,
    *,
    project_id: str,
    manuscript: EngineeringMasterManuscript,
    profile: PublicationProfile,
    compliance_matrix: VenueComplianceMatrix,
    adapted_text: str,
    artifact_root: Path,
    adapted_id: str | None = None,
) -> VenueAdaptedManuscript:
    """Derive a venue-adapted manuscript; the master is never overwritten."""
    compliance_blockers_ = compliance_blockers(compliance_matrix)
    if compliance_blockers_:
        raise DomainError(
            "VENUE_COMPLIANCE_BLOCKED: " + "; ".join(compliance_blockers_),
            error_code="COMPLIANCE_MATRIX_INVALID",
        )
    if manuscript.master_hash is None:
        raise DomainError(
            "母稿缺少 master_hash",
            error_code="ARTIFACT_HASH_MISMATCH",
        )
    if profile.venue_kind.value == "PREPRINT_REPOSITORY":
        upper = adapted_text.upper()
        for marker in ("PEER_REVIEWED", "JOURNAL_ACCEPTED", "PUBLISHED_IN_JOURNAL"):
            if marker in upper or marker.replace("_", " ") in upper:
                raise DomainError(
                    "arXiv 适配稿不得标注期刊/同行评审状态",
                    error_code="ARXIV_IDENTITY_VIOLATION",
                )
        status = VenueAdaptedManuscriptStatus.ARXIV_PACKAGE_READY
    else:
        status = VenueAdaptedManuscriptStatus.FORMAL_MANUSCRIPT_READY
    adapted = VenueAdaptedManuscript(
        adapted_id=adapted_id or f"adapted-{uuid.uuid4().hex[:12]}",
        version=1,
        project_id=project_id,
        master_manuscript_id=manuscript.manuscript_id,
        master_version=manuscript.version,
        master_hash=manuscript.master_hash,
        profile_id=profile.profile_id,
        profile_hash=profile.profile_hash or "",
        conversion_record=(
            "由 EngineeringMasterManuscript + PublicationProfile 机械派生；"
            "不修改 Requirement/Architecture/V&V/Evidence"
        ),
        compliance_matrix_id=compliance_matrix.matrix_id,
        adapted_text=adapted_text,
        status=status,
    )
    _persist_stage_and_artifact(
        session,
        project_id=project_id,
        stage=EngineeringStageId.ENG9,
        aggregate_type=ADAPTED_MANUSCRIPT_AGGREGATE_TYPE,
        aggregate_id=adapted.adapted_id,
        artifact_payload=adapted.to_event_payload(),
        artifact_root=artifact_root,
    )
    return adapted


def load_venue_adapted_manuscript(
    session: Session, adapted_id: str, *, artifact_root: Path
) -> VenueAdaptedManuscript:
    return _load_artifact(
        session,
        aggregate_type=ADAPTED_MANUSCRIPT_AGGREGATE_TYPE,
        aggregate_id=adapted_id,
        model=VenueAdaptedManuscript,
        artifact_root=artifact_root,
        not_found_code="MANUSCRIPT_REQUIRED",
    )


__all__ = [
    "ADAPTED_MANUSCRIPT_AGGREGATE_TYPE",
    "MANUSCRIPT_AUDIT_AGGREGATE_TYPE",
    "MASTER_MANUSCRIPT_AGGREGATE_TYPE",
    "audit_engineering_master_manuscript",
    "create_engineering_master_manuscript",
    "create_venue_adapted_manuscript",
    "load_engineering_master_manuscript",
    "load_venue_adapted_manuscript",
    "open_formal_manuscript_decision",
    "open_publication_profile_selection",
    "resolve_formal_manuscript_decision",
    "resolve_publication_profile_selection",
]
