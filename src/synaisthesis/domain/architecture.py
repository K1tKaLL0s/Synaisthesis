"""ENG4 architecture, interface, diagram and review-baseline domain (03B, section 7).

Machine-readable design objects are authoritative; diagrams are projection
views and must carry stable IDs plus hash-bound source and rendered files
(03B, section 7.3).  The ENGINEERING_ARCHITECTURE_REVIEW binds the three
hashes: requirements, trade study and architecture (03B, section 7.4).
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime
from typing import Any

from synaisthesis.domain.engineering import (
    EngineeringArtifactStatus,
    finalize_artifact_hash,
)
from synaisthesis.domain.errors import DomainError
from synaisthesis.domain.event import canonicalize


def _canonical_payload(value: Any) -> dict[str, Any]:
    payload = canonicalize(value)
    if not isinstance(payload, dict):
        raise TypeError("architecture payload must canonicalize to an object")
    return payload


@dataclass(frozen=True, slots=True)
class ArchitectureComponent:
    """One architecture component with a stable id (03B, sections 7.1/16.6)."""

    component_id: str
    name: str
    responsibilities: tuple[str, ...]

    def __post_init__(self) -> None:
        if not self.component_id.strip() or not self.name.strip():
            raise DomainError(
                "component requires stable component_id and name",
                error_code="ARCHITECTURE_INVALID",
            )

    def to_event_payload(self) -> dict[str, Any]:
        return _canonical_payload(asdict(self))


@dataclass(frozen=True, slots=True)
class ArchitectureDiagram:
    """One diagram with versioned source + rendered hash pair (03B, section 7.3)."""

    diagram_id: str
    title: str
    version: int
    input_hash: str
    legend: str
    node_edge_semantics: str
    stable_id_mapping: dict[str, str]
    node_component_ids: tuple[str, ...]
    source_path: str
    source_hash: str
    rendered_svg_path: str
    rendered_svg_hash: str
    render_receipt: str
    broken_link_refs: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not self.diagram_id.strip() or not self.title.strip():
            raise DomainError(
                "diagram requires diagram_id and title",
                error_code="DIAGRAM_INVALID",
            )
        if not self.legend.strip() or not self.node_edge_semantics.strip():
            raise DomainError(
                f"diagram {self.diagram_id!r} requires legend and node/edge semantics",
                error_code="DIAGRAM_INVALID",
            )
        for node_id in self.node_component_ids:
            if node_id not in self.stable_id_mapping:
                raise DomainError(
                    f"diagram {self.diagram_id!r} 的节点 {node_id!r} 缺少稳定 component ID",
                    error_code="DIAGRAM_INVALID",
                )
        if not self.source_hash or not self.rendered_svg_hash or not self.render_receipt:
            raise DomainError(
                f"diagram {self.diagram_id!r} 必须保存源 hash、SVG hash 与渲染回执",
                error_code="DIAGRAM_INVALID",
            )
        if self.broken_link_refs:
            raise DomainError(
                f"diagram {self.diagram_id!r} 存在断链：" + ", ".join(self.broken_link_refs),
                error_code="DIAGRAM_BROKEN_LINKS",
            )

    def to_event_payload(self) -> dict[str, Any]:
        return _canonical_payload(asdict(self))


@dataclass(frozen=True, slots=True)
class ArchitectureDecisionRecord:
    """One ADR (03B, section 7.2)."""

    adr_id: str
    title: str
    status: str  # PROPOSED | ACCEPTED | SUPERSEDED
    decision: str
    alternatives_considered: tuple[str, ...]
    rationale: str
    affected_component_ids: tuple[str, ...]
    irreversible: bool

    def __post_init__(self) -> None:
        if self.status not in {"PROPOSED", "ACCEPTED", "SUPERSEDED"}:
            raise DomainError(
                f"ADR {self.adr_id!r} 状态非法：{self.status!r}",
                error_code="ARCHITECTURE_INVALID",
            )

    def to_event_payload(self) -> dict[str, Any]:
        return _canonical_payload(asdict(self))


@dataclass(frozen=True, slots=True)
class InterfaceContractSet:
    """Public interface contracts with schema and version policy (03B, section 7.2)."""

    interface_id: str
    schema_ref: str
    version_policy: str

    def __post_init__(self) -> None:
        if not self.interface_id.strip() or not self.schema_ref.strip():
            raise DomainError(
                f"interface contract {self.interface_id!r} 必须带 Schema 引用",
                error_code="ARCHITECTURE_INVALID",
            )

    def to_event_payload(self) -> dict[str, Any]:
        return _canonical_payload(asdict(self))


@dataclass(frozen=True, slots=True)
class DataContractSet:
    """Data contracts (03B, section 7.2)."""

    contract_id: str
    schema_ref: str
    lifecycle: str

    def to_event_payload(self) -> dict[str, Any]:
        return _canonical_payload(asdict(self))


@dataclass(frozen=True, slots=True)
class StateAndFailureModel:
    """State machine, error recovery, idempotency and concurrency model (03B, 7.1)."""

    model_id: str
    states: tuple[str, ...]
    errors: tuple[str, ...]
    recovery_actions: tuple[str, ...]
    idempotency_boundary: str
    concurrency_boundary: str

    def __post_init__(self) -> None:
        if not self.states or not self.errors or not self.recovery_actions:
            raise DomainError(
                f"state/failure model {self.model_id!r} 不完整",
                error_code="ARCHITECTURE_INVALID",
            )

    def to_event_payload(self) -> dict[str, Any]:
        return _canonical_payload(asdict(self))


@dataclass(frozen=True, slots=True)
class ThreatModel:
    """Trust boundaries, threat model and security controls (03B, section 7.2)."""

    model_id: str
    trust_boundaries: tuple[str, ...]
    threats: tuple[str, ...]
    security_controls: tuple[str, ...]

    def __post_init__(self) -> None:
        if not self.trust_boundaries or not self.threats or not self.security_controls:
            raise DomainError(
                f"threat model {self.model_id!r} 不完整",
                error_code="ARCHITECTURE_INVALID",
            )

    def to_event_payload(self) -> dict[str, Any]:
        return _canonical_payload(asdict(self))


@dataclass(frozen=True, slots=True)
class DeploymentAndOperationsDesign:
    """Deployment topology, environment and operations boundary (03B, section 7.1)."""

    design_id: str
    topology: str
    environment: str
    operations_boundary: str
    observability_audit_backup_recovery: str
    retirement: str

    def __post_init__(self) -> None:
        for field_name in ("topology", "environment", "operations_boundary"):
            if not getattr(self, field_name).strip():
                raise DomainError(
                    f"deployment design {self.design_id!r} 缺 {field_name}",
                    error_code="ARCHITECTURE_INVALID",
                )

    def to_event_payload(self) -> dict[str, Any]:
        return _canonical_payload(asdict(self))


@dataclass(frozen=True, slots=True)
class ArchitectureBaseline:
    """ENG4 output (03B, sections 7.1-7.3)."""

    baseline_id: str
    version: int
    project_id: str
    requirements_baseline_id: str
    requirements_hash: str
    trade_study_id: str
    trade_study_hash: str
    components: tuple[ArchitectureComponent, ...]
    views: dict[str, str]
    interface_contracts: tuple[InterfaceContractSet, ...]
    data_contracts: tuple[DataContractSet, ...]
    state_and_failure_model: StateAndFailureModel
    threat_model: ThreatModel
    deployment_and_operations: DeploymentAndOperationsDesign
    adrs: tuple[ArchitectureDecisionRecord, ...]
    diagrams: tuple[ArchitectureDiagram, ...]
    artifact_hash: str | None = None
    status: EngineeringArtifactStatus = EngineeringArtifactStatus.ACTIVE
    created_at: datetime | None = None

    def __post_init__(self) -> None:
        seen: set[str] = set()
        for component in self.components:
            if component.component_id in seen:
                raise DomainError(
                    f"duplicate component id {component.component_id!r}",
                    error_code="ARCHITECTURE_INVALID",
                )
            seen.add(component.component_id)
        finalize_artifact_hash(self)

    def content_payload(self) -> dict[str, Any]:
        payload = asdict(self)
        payload.pop("artifact_hash", None)
        payload.pop("status", None)
        return _canonical_payload(payload)

    def to_event_payload(self) -> dict[str, Any]:
        return _canonical_payload(asdict(self))


def architecture_review_blockers(baseline: ArchitectureBaseline) -> tuple[str, ...]:
    """Return ENG4 review blockers (03B, sections 7.3/7.4/16.6)."""
    blockers: list[str] = []
    if not baseline.requirements_hash or not baseline.trade_study_hash:
        blockers.append("ArchitectureBaseline 必须绑定 requirements 与 trade study hash")
    component_ids = {component.component_id for component in baseline.components}
    for diagram in baseline.diagrams:
        for component_id in diagram.stable_id_mapping.values():
            if component_id not in component_ids:
                blockers.append(
                    f"diagram {diagram.diagram_id!r} 的节点映射到未定义组件 {component_id!r}"
                )
    if not baseline.adrs:
        blockers.append("ArchitectureBaseline 必须包含 ADR 集")
    return tuple(blockers)


@dataclass(frozen=True, slots=True)
class ArchitectureReviewBinding:
    """Three-hash binding confirmed by ENGINEERING_ARCHITECTURE_REVIEW (03B, 7.4)."""

    requirements_hash: str
    trade_study_hash: str
    architecture_hash: str

    def __post_init__(self) -> None:
        if not (self.requirements_hash and self.trade_study_hash and self.architecture_hash):
            raise DomainError(
                "architecture review binding requires all three hashes",
                error_code="ARCHITECTURE_REVIEW_BINDING_INVALID",
            )

    def to_event_payload(self) -> dict[str, Any]:
        return _canonical_payload(asdict(self))

    def matches(self, baseline: ArchitectureBaseline) -> bool:
        return (
            self.requirements_hash == baseline.requirements_hash
            and self.trade_study_hash == baseline.trade_study_hash
            and self.architecture_hash == baseline.artifact_hash
        )


__all__ = [
    "ArchitectureBaseline",
    "ArchitectureComponent",
    "ArchitectureDecisionRecord",
    "ArchitectureDiagram",
    "ArchitectureReviewBinding",
    "DataContractSet",
    "DeploymentAndOperationsDesign",
    "InterfaceContractSet",
    "StateAndFailureModel",
    "ThreatModel",
    "architecture_review_blockers",
]
