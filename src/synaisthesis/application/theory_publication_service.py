"""Theory publication service (03C sections 5-9; M9.2).

Order is enforced: master manuscript first, independent audit, user
delivery, then FORMAL_MANUSCRIPT_DECISION; only WRITE_FORMAL_MANUSCRIPT opens
theory profile selection; venue adaptation never changes statement hashes,
quantifiers, assumptions, conclusions or the evidence scope.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from pathlib import Path
from typing import Any

from sqlalchemy.orm import Session

from synaisthesis.agents.theory_manuscript_auditor import (
    TheoryAuditFinding,
    audit_theory_manuscript,
)
from synaisthesis.application.engineering_design_service import (
    GATE_AGGREGATE_TYPE,
    _load_artifact,
    _persist_engineering_event,
)
from synaisthesis.domain.engineering import (
    EVENT_ENGINEERING_ARTIFACT_CREATED,
    EVENT_ENGINEERING_GATE_OPENED,
    EVENT_ENGINEERING_GATE_RESOLVED,
    EngineeringGateType,
    FormalManuscriptDecision,
)
from synaisthesis.domain.enums import ProvenanceType
from synaisthesis.domain.errors import DomainError
from synaisthesis.domain.gate import EngineeringGate, EngineeringGateBinding
from synaisthesis.domain.publication import (
    TheoryManuscriptAuditStatus,
    VenueComplianceMatrix,
)
from synaisthesis.publication.compliance import (
    theory_compliance_overall_status,
)
from synaisthesis.publication.profiles import (
    FreshnessStatus,
    PublicationProfile,
    ScopeFitStatus,
    profile_for,
)
from synaisthesis.publication.theory_master_manuscript import (
    TheoryMasterManuscript,
)

THEORY_MASTER_AGGREGATE_TYPE = "TheoryMasterManuscript"
THEORY_ADAPTED_AGGREGATE_TYPE = "TheoryVenueAdaptedManuscript"


def create_theory_master_manuscript(
    session: Session,
    *,
    project_id: str,
    manuscript: TheoryMasterManuscript,
    artifact_root: Path,
) -> TheoryMasterManuscript:
    """Persist a TP1 master manuscript (03C, section 5)."""
    _persist_engineering_event(
        session,
        event_type=EVENT_ENGINEERING_ARTIFACT_CREATED,
        aggregate_type=THEORY_MASTER_AGGREGATE_TYPE,
        aggregate_id=manuscript.manuscript_id,
        payload={"artifact": manuscript.to_event_payload()},
        project_id=project_id,
        artifact_root=artifact_root,
    )
    return manuscript


def load_theory_master_manuscript(
    session: Session, manuscript_id: str, *, artifact_root: Path
) -> TheoryMasterManuscript:
    return _load_artifact(
        session,
        aggregate_type=THEORY_MASTER_AGGREGATE_TYPE,
        aggregate_id=manuscript_id,
        model=TheoryMasterManuscript,
        artifact_root=artifact_root,
        not_found_code="MANUSCRIPT_REQUIRED",
    )


def audit_theory_master_manuscript(
    session: Session,
    *,
    project_id: str,
    manuscript: TheoryMasterManuscript,
    auditor_session_id: str,
    draft_generator_session_ids: tuple[str, ...],
    artifact_root: Path,
) -> tuple[TheoryMasterManuscript, tuple[TheoryAuditFinding, ...]]:
    """Run the independent audit and persist the result (03C, section 6.1)."""
    import dataclasses

    findings, status = audit_theory_manuscript(
        manuscript,
        auditor_session_id=auditor_session_id,
        draft_generator_session_ids=draft_generator_session_ids,
    )
    audited = dataclasses.replace(manuscript, audit_status=status)
    _persist_engineering_event(
        session,
        event_type=EVENT_ENGINEERING_ARTIFACT_CREATED,
        aggregate_type=THEORY_MASTER_AGGREGATE_TYPE,
        aggregate_id=manuscript.manuscript_id,
        payload={
            "theory_audit": {
                "manuscript_id": manuscript.manuscript_id,
                "audit_status": status.value,
                "findings": [finding.to_event_payload() for finding in findings],
            }
        },
        project_id=project_id,
        artifact_root=artifact_root,
    )
    return audited, tuple(findings)


def open_theory_formal_manuscript_decision(
    session: Session,
    *,
    project_id: str,
    manuscript: TheoryMasterManuscript,
    evidence_baseline_hash: str,
    artifact_root: Path,
    gate_id: str | None = None,
) -> EngineeringGate:
    """Open FORMAL_MANUSCRIPT_DECISION only after audited delivery (03C, 6.3)."""
    if manuscript.audit_status is not TheoryManuscriptAuditStatus.AUDITED_CLEAN:
        raise DomainError(
            "理论母稿必须先独立审计并交付用户，才能打开 FORMAL_MANUSCRIPT_DECISION",
            error_code="THEORY_MASTER_MANUSCRIPT_AUDITING",
        )
    if manuscript.master_hash is None:
        raise DomainError(
            "母稿缺少 master_hash",
            error_code="ARTIFACT_HASH_MISMATCH",
        )
    gate = EngineeringGate(
        gate_id=gate_id or f"gate-tfm-{uuid.uuid4().hex[:12]}",
        project_id=project_id,
        gate_type=EngineeringGateType.FORMAL_MANUSCRIPT_DECISION,
        binding=EngineeringGateBinding(
            gate_type=EngineeringGateType.FORMAL_MANUSCRIPT_DECISION,
            artifact_id=manuscript.manuscript_id,
            version=manuscript.version,
            artifact_hash=manuscript.master_hash,
            bound_hashes={
                "master_manuscript": manuscript.master_hash,
                "evidence_baseline": evidence_baseline_hash,
            },
        ),
        reason="TheoryMasterManuscript 已审计并交付，等待正式稿决策",
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


def resolve_theory_formal_manuscript_decision(
    session: Session,
    *,
    gate: EngineeringGate,
    decision: str,
    actor: ProvenanceType,
    user_event_id: str,
    manuscript: TheoryMasterManuscript,
    at: datetime,
    artifact_root: Path,
) -> EngineeringGate:
    """Resolve the theory formal decision; binding must match the master."""
    if gate.gate_type is not EngineeringGateType.FORMAL_MANUSCRIPT_DECISION:
        raise DomainError(
            f"gate type {gate.gate_type.value} is not FORMAL_MANUSCRIPT_DECISION",
            error_code="GATE_TYPE_MISMATCH",
        )
    if manuscript.master_hash is None or gate.binding.artifact_hash != manuscript.master_hash:
        raise DomainError(
            "formal decision 绑定与当前理论母稿 hash 不一致",
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


def open_theory_profile_selection(
    session: Session,
    *,
    project_id: str,
    formal_decision: EngineeringGate,
    manuscript: TheoryMasterManuscript,
    artifact_root: Path,
    gate_id: str | None = None,
) -> EngineeringGate:
    """Only a user WRITE decision opens theory profile selection (03C, 7.1)."""
    if formal_decision.status.value != "RESOLVED" or (
        formal_decision.decision != FormalManuscriptDecision.WRITE_FORMAL_MANUSCRIPT.value
    ):
        raise DomainError(
            "只有用户选择 WRITE_FORMAL_MANUSCRIPT 后才允许理论 Profile Selection",
            error_code="FORMAL_MANUSCRIPT_DECISION_REQUIRED",
        )
    if (
        manuscript.master_hash is None
        or formal_decision.binding.artifact_hash != manuscript.master_hash
    ):
        raise DomainError(
            "formal decision 未绑定当前理论母稿",
            error_code="STALE_MANUSCRIPT_BINDING",
        )
    gate = EngineeringGate(
        gate_id=gate_id or f"gate-tps-{uuid.uuid4().hex[:12]}",
        project_id=project_id,
        gate_type=EngineeringGateType.PUBLICATION_PROFILE_SELECTION,
        binding=EngineeringGateBinding(
            gate_type=EngineeringGateType.PUBLICATION_PROFILE_SELECTION,
            artifact_id=manuscript.manuscript_id,
            version=manuscript.version,
            artifact_hash=manuscript.master_hash,
            bound_hashes={"master_manuscript": manuscript.master_hash},
        ),
        reason="用户已选择 WRITE_FORMAL_MANUSCRIPT，等待理论 Profile 选择",
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


def resolve_theory_profile_selection(
    session: Session,
    *,
    gate: EngineeringGate,
    decision: str,
    actor: ProvenanceType,
    user_event_id: str,
    now: datetime,
    manuscript: TheoryMasterManuscript,
    artifact_root: Path,
    profile_override: PublicationProfile | None = None,
) -> tuple[EngineeringGate, PublicationProfile]:
    """Resolve theory profile selection with freshness and scope gates."""
    if gate.gate_type is not EngineeringGateType.PUBLICATION_PROFILE_SELECTION:
        raise DomainError(
            f"gate type {gate.gate_type.value} is not PUBLICATION_PROFILE_SELECTION",
            error_code="GATE_TYPE_MISMATCH",
        )
    if manuscript.master_hash is None or gate.binding.artifact_hash != manuscript.master_hash:
        raise DomainError(
            "theory profile selection 绑定与当前母稿不一致",
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
    if profile.route.value != "THEORY":
        raise DomainError(
            f"profile {decision} 不是理论路线 Profile",
            error_code="PROFILE_ROUTE_MISMATCH",
        )
    if profile.freshness_status(now) is FreshnessStatus.STALE_GUIDANCE:
        raise DomainError(
            f"profile {decision} 官方指南过期，禁止生成 FORMAL_MANUSCRIPT_READY",
            error_code="STALE_GUIDANCE",
        )
    scope = profile.scope_fit(project_kind="theory")
    if scope is ScopeFitStatus.SCOPE_MISMATCH:
        raise DomainError(
            f"profile {decision} 与理论路线不匹配",
            error_code="PROFILE_SCOPE_MISMATCH",
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


def create_theory_venue_adapted_manuscript(
    session: Session,
    *,
    project_id: str,
    manuscript: TheoryMasterManuscript,
    profile: PublicationProfile,
    compliance_matrix: VenueComplianceMatrix,
    adapted_text: str,
    machine_blocking_requirements: tuple[str, ...],
    human_blocking_requirements: tuple[str, ...],
    artifact_root: Path,
    adapted_id: str | None = None,
) -> dict[str, Any]:
    """Derive a venue adaptation; math semantics never change (03C, 7.2/8)."""
    from synaisthesis.publication.adaptation import VenueAdaptedManuscriptStatus

    if manuscript.master_hash is None:
        raise DomainError(
            "理论母稿缺少 master_hash",
            error_code="ARTIFACT_HASH_MISMATCH",
        )
    overall, blockers = theory_compliance_overall_status(
        compliance_matrix,
        machine_blocking_requirements=machine_blocking_requirements,
        human_blocking_requirements=human_blocking_requirements,
    )
    if blockers:
        raise DomainError(
            "THEORY_COMPLIANCE_BLOCKED: " + "; ".join(blockers),
            error_code="COMPLIANCE_MATRIX_INVALID",
        )
    if profile.venue_kind.value == "PREPRINT_REPOSITORY":
        for marker in ("PEER_REVIEWED", "JOURNAL_ACCEPTED", "PUBLISHED_IN_JOURNAL"):
            if marker in adapted_text.upper() or marker.replace("_", " ") in adapted_text.upper():
                raise DomainError(
                    "arXiv 理论适配稿不得标注期刊/同行评审状态",
                    error_code="ARXIV_IDENTITY_VIOLATION",
                )
        status = VenueAdaptedManuscriptStatus.ARXIV_PACKAGE_READY
    else:
        status = VenueAdaptedManuscriptStatus.FORMAL_MANUSCRIPT_READY
    record = {
        "adapted_id": adapted_id or f"tadapted-{uuid.uuid4().hex[:12]}",
        "master_manuscript_id": manuscript.manuscript_id,
        "master_hash": manuscript.master_hash,
        "master_statement_hashes": manuscript.statement_hashes(),
        "profile_id": profile.profile_id,
        "status": status.value,
        "overall": overall,
        "adapted_text": adapted_text,
    }
    _persist_engineering_event(
        session,
        event_type=EVENT_ENGINEERING_ARTIFACT_CREATED,
        aggregate_type=THEORY_ADAPTED_AGGREGATE_TYPE,
        aggregate_id=record["adapted_id"],
        payload={"theory_adapted": record},
        project_id=project_id,
        artifact_root=artifact_root,
    )
    return record


def theory_delivery_readiness_blockers(
    *,
    master_ready: bool,
    master_delivered: bool,
    keep_master_only: bool | None,
    formal_requested: bool,
    profile_fresh: bool,
    compliance_ok: bool,
    audit_clean: bool,
) -> tuple[str, ...]:
    """All 03C sections 6-9 final conditions; empty means delivered."""
    blockers: list[str] = []
    if not master_ready:
        blockers.append("TheoryMasterManuscript 不完整")
    if not master_delivered:
        blockers.append("母稿未先交付用户")
    if not audit_clean:
        blockers.append("独立审计存在 Critical/Major finding")
    if keep_master_only is None and formal_requested is None:
        blockers.append("缺少 FORMAL_MANUSCRIPT_DECISION")
    if formal_requested and not profile_fresh:
        blockers.append("所选理论 Profile 过期")
    if formal_requested and not compliance_ok:
        blockers.append("理论 Compliance Matrix 未通过")
    return tuple(blockers)


__all__ = [
    "THEORY_ADAPTED_AGGREGATE_TYPE",
    "THEORY_MASTER_AGGREGATE_TYPE",
    "audit_theory_master_manuscript",
    "create_theory_master_manuscript",
    "create_theory_venue_adapted_manuscript",
    "load_theory_master_manuscript",
    "open_theory_formal_manuscript_decision",
    "open_theory_profile_selection",
    "resolve_theory_formal_manuscript_decision",
    "resolve_theory_profile_selection",
    "theory_delivery_readiness_blockers",
]
