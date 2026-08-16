"""Engineering delivery audit and acceptance (03B, section 13; M2.11).

At least one auditor who did not generate any ENG3-ENG9 draft must audit the
delivery; Critical/Major findings block readiness.  ENGINEERING_DELIVERY_ACCEPTANCE
binds the current manifest hash, and any authoritative file change invalidates
an earlier acceptance (03B, section 16.23).
"""

from __future__ import annotations

import uuid
from datetime import datetime
from pathlib import Path

from sqlalchemy.orm import Session

from synaisthesis.application.engineering_design_service import (
    GATE_AGGREGATE_TYPE,
    _persist_engineering_event,
)
from synaisthesis.domain.engineering import (
    EVENT_ENGINEERING_ARTIFACT_CREATED,
    EVENT_ENGINEERING_GATE_OPENED,
    EVENT_ENGINEERING_GATE_RESOLVED,
    EngineeringDeliveryStatus,
    EngineeringGateType,
)
from synaisthesis.domain.enums import ProvenanceType
from synaisthesis.domain.errors import DomainError
from synaisthesis.domain.gate import EngineeringGate, EngineeringGateBinding

DELIVERY_AUDIT_AGGREGATE_TYPE = "EngineeringDeliveryAudit"

AUDIT_SEVERITY_MAJOR = "MAJOR"
AUDIT_SEVERITY_CRITICAL = "CRITICAL"


def _blocking_findings(findings: tuple[tuple[str, str], ...]) -> tuple[str, ...]:
    return tuple(
        f"{severity}: {description}"
        for severity, description in findings
        if severity in {AUDIT_SEVERITY_MAJOR, AUDIT_SEVERITY_CRITICAL}
    )


def run_engineering_delivery_audit(
    session: Session,
    *,
    project_id: str,
    auditor_session_id: str,
    draft_generator_session_ids: tuple[str, ...],
    findings: tuple[tuple[str, str], ...],
    artifact_root: Path,
    audit_id: str | None = None,
) -> tuple[EngineeringDeliveryStatus, tuple[str, ...]]:
    """Audit the delivery; the auditor must be independent (03B, 13.1)."""
    if auditor_session_id in draft_generator_session_ids:
        raise DomainError(
            "交付审计人不得参与 ENG3-ENG9 初稿生成",
            error_code="AUDITOR_NOT_INDEPENDENT",
        )
    blockers = _blocking_findings(findings)
    status = (
        EngineeringDeliveryStatus.BLOCKED_ENGINEERING_DELIVERY
        if blockers
        else EngineeringDeliveryStatus.ENGINEERING_DELIVERY_CANDIDATE
    )
    _persist_engineering_event(
        session,
        event_type=EVENT_ENGINEERING_ARTIFACT_CREATED,
        aggregate_type=DELIVERY_AUDIT_AGGREGATE_TYPE,
        aggregate_id=audit_id or f"audit-{uuid.uuid4().hex[:12]}",
        payload={
            "audit": {
                "project_id": project_id,
                "auditor_session_id": auditor_session_id,
                "status": status.value,
                "findings": [list(finding) for finding in findings],
            }
        },
        project_id=project_id,
        artifact_root=artifact_root,
    )
    return status, blockers


def open_engineering_delivery_acceptance(
    session: Session,
    *,
    project_id: str,
    manifest_hash: str,
    artifact_root: Path,
    gate_id: str | None = None,
) -> EngineeringGate:
    """Open ENGINEERING_DELIVERY_ACCEPTANCE bound to the current manifest hash."""
    gate = EngineeringGate(
        gate_id=gate_id or f"gate-da-{uuid.uuid4().hex[:12]}",
        project_id=project_id,
        gate_type=EngineeringGateType.ENGINEERING_DELIVERY_ACCEPTANCE,
        binding=EngineeringGateBinding(
            gate_type=EngineeringGateType.ENGINEERING_DELIVERY_ACCEPTANCE,
            artifact_id="engineering_delivery",
            version=1,
            artifact_hash=manifest_hash,
            bound_hashes={"manifest": manifest_hash},
        ),
        reason="工程交付包已生成，等待用户验收",
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


def resolve_engineering_delivery_acceptance(
    session: Session,
    *,
    gate: EngineeringGate,
    decision: str,
    actor: ProvenanceType,
    user_event_id: str,
    current_manifest_hash: str,
    at: datetime,
    artifact_root: Path,
) -> EngineeringGate:
    """Resolve acceptance; any manifest change invalidates the old acceptance."""
    if gate.gate_type is not EngineeringGateType.ENGINEERING_DELIVERY_ACCEPTANCE:
        raise DomainError(
            f"gate type {gate.gate_type.value} is not ENGINEERING_DELIVERY_ACCEPTANCE",
            error_code="GATE_TYPE_MISMATCH",
        )
    if gate.binding.bound_hashes.get("manifest") != current_manifest_hash:
        raise DomainError(
            "交付 manifest hash 已变化，旧验收自动失效",
            error_code="STALE_DELIVERY_ACCEPTANCE",
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


def engineering_delivery_readiness_blockers(
    *,
    stages_not_blocked: bool,
    blueprint_gate_ok: bool,
    diagrams_rerenderable: bool,
    vv_plans_complete: bool,
    master_complete: bool,
    master_audited_and_delivered: bool,
    keep_master_only: bool | None,
    formal_requested: bool,
    profile_fresh: bool,
    compliance_ok: bool,
    no_fabricated_results: bool,
    audit_clean: bool,
    acceptance_bound: bool,
) -> tuple[str, ...]:
    """All 03B 13.3 final pass conditions; empty means ENGINEERING_DELIVERY_READY."""
    blockers: list[str] = []
    if not stages_not_blocked:
        blockers.append("ENG0-ENG9 存在 BLOCKED/SUPERSEDED 版本")
    if not blueprint_gate_ok:
        blockers.append("Blueprint Completeness Gate 未全通过")
    if not diagrams_rerenderable:
        blockers.append("图示无法从源文件重渲染或存在断链")
    if not vv_plans_complete:
        blockers.append("Critical requirement 的 Verification 计划不完整")
    if not master_complete:
        blockers.append("EngineeringMasterManuscript 不完整")
    if not master_audited_and_delivered:
        blockers.append("母稿未独立审计或未先交付用户")
    if keep_master_only is False and not formal_requested:
        blockers.append("WRITE 路径缺少正式稿请求")
    if keep_master_only is None and formal_requested is None:
        blockers.append("缺少 FORMAL_MANUSCRIPT_DECISION")
    if formal_requested and not profile_fresh:
        blockers.append("所选 Profile 过期或不可用")
    if formal_requested and not compliance_ok:
        blockers.append("Compliance Matrix 存在 FAIL/STALE_GUIDANCE")
    if not no_fabricated_results:
        blockers.append("存在虚构结果、伪造引用或未披露 AI 辅助")
    if not audit_clean:
        blockers.append("独立审计存在 Critical/Major finding")
    if not acceptance_bound:
        blockers.append("用户未接受当前 manifest hash")
    return tuple(blockers)


__all__ = [
    "DELIVERY_AUDIT_AGGREGATE_TYPE",
    "engineering_delivery_readiness_blockers",
    "open_engineering_delivery_acceptance",
    "resolve_engineering_delivery_acceptance",
    "run_engineering_delivery_audit",
]
