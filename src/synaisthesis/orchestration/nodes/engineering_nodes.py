"""Engineering workflow orchestration nodes (03B; M2.9).

Nodes load the required upstream artifacts from the event store and delegate
to the same enforced service paths as direct service calls, so there is no
second, weaker route through the workflow.
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

from sqlalchemy.orm import Session

from synaisthesis.application.engineering_design_service import (
    create_architecture_baseline,
    create_engineering_mission_charter,
    create_engineering_requirements_baseline,
    create_operational_concept_bundle,
    create_option_trade_study,
    load_architecture_baseline,
    load_operational_concept_bundle,
    load_option_trade_study,
    load_requirements_baseline,
    open_engineering_architecture_review,
    resolve_engineering_architecture_review,
)
from synaisthesis.domain.architecture import (
    ArchitectureBaseline,
    ArchitectureComponent,
    ArchitectureDecisionRecord,
    DataContractSet,
    DeploymentAndOperationsDesign,
    InterfaceContractSet,
    StateAndFailureModel,
    ThreatModel,
)
from synaisthesis.domain.engineering import (
    EngineeringMissionCharter,
    OperationalConceptBundle,
    OptionTradeStudy,
)
from synaisthesis.domain.enums import NoveltyStatus, ProvenanceType
from synaisthesis.domain.gate import EngineeringGate
from synaisthesis.domain.novelty import LowNoveltyOverride
from synaisthesis.domain.qualification import (
    EngineeringRouteSelection,
    UserEngineeringConceptApproval,
)
from synaisthesis.domain.requirements import EngineeringRequirement, RequirementsBaseline
from synaisthesis.renderers.diagram_renderers import DiagramSource


def eng0_charter_node(
    session: Session,
    *,
    project_id: str,
    bound_input_spec_hash: str,
    current_input_spec_hash: str,
    route_selection: EngineeringRouteSelection | None,
    concept_approval: UserEngineeringConceptApproval | None,
    concept_hash: str | None,
    novelty_status: NoveltyStatus,
    novelty_review_hash: str | None,
    override: LowNoveltyOverride | None,
    open_gate_types: tuple[str, ...],
    charter: EngineeringMissionCharter,
    artifact_root: Path,
) -> EngineeringMissionCharter:
    """ENG0 node: same enforced entry precondition as the service."""
    return create_engineering_mission_charter(
        session,
        project_id=project_id,
        bound_input_spec_hash=bound_input_spec_hash,
        current_input_spec_hash=current_input_spec_hash,
        route_selection=route_selection,
        concept_approval=concept_approval,
        concept_hash=concept_hash,
        novelty_status=novelty_status,
        novelty_review_hash=novelty_review_hash,
        override=override,
        open_gate_types=open_gate_types,
        charter=charter,
        artifact_root=artifact_root,
    )


def eng1_conops_node(
    session: Session,
    *,
    project_id: str,
    charter: EngineeringMissionCharter,
    conops: OperationalConceptBundle,
    artifact_root: Path,
) -> OperationalConceptBundle:
    """ENG1 node: binds the persisted charter hash and enforces ConOps gates."""
    return create_operational_concept_bundle(
        session,
        project_id=project_id,
        charter=charter,
        conops=conops,
        artifact_root=artifact_root,
    )


def eng2_requirements_node(
    session: Session,
    *,
    project_id: str,
    conops_id: str,
    requirements: tuple[EngineeringRequirement, ...],
    artifact_root: Path,
) -> RequirementsBaseline:
    """ENG2 node: loads the persisted ConOps, then delegates to the service."""
    conops = load_operational_concept_bundle(session, conops_id, artifact_root=artifact_root)
    return create_engineering_requirements_baseline(
        session,
        project_id=project_id,
        conops=conops,
        requirements=requirements,
        artifact_root=artifact_root,
    )


def eng3_trade_study_node(
    session: Session,
    *,
    project_id: str,
    baseline_id: str,
    study: OptionTradeStudy,
    artifact_root: Path,
) -> OptionTradeStudy:
    """ENG3 node: loads the persisted baseline, then delegates to the service."""
    baseline = load_requirements_baseline(session, baseline_id, artifact_root=artifact_root)
    return create_option_trade_study(
        session,
        project_id=project_id,
        baseline=baseline,
        study=study,
        artifact_root=artifact_root,
    )


def eng4_architecture_node(
    session: Session,
    *,
    project_id: str,
    baseline_id: str,
    trade_study_id: str,
    components: tuple[ArchitectureComponent, ...],
    views: dict[str, str],
    interface_contracts: tuple[InterfaceContractSet, ...],
    data_contracts: tuple[DataContractSet, ...],
    state_and_failure_model: StateAndFailureModel,
    threat_model: ThreatModel,
    deployment_and_operations: DeploymentAndOperationsDesign,
    adrs: tuple[ArchitectureDecisionRecord, ...],
    diagram_sources: tuple[DiagramSource, ...],
    node_component_mappings: dict[str, dict[str, str]],
    artifact_root: Path,
) -> ArchitectureBaseline:
    """ENG4 node: loads persisted baseline + study, renders and persists."""
    baseline = load_requirements_baseline(session, baseline_id, artifact_root=artifact_root)
    study = load_option_trade_study(session, trade_study_id, artifact_root=artifact_root)
    return create_architecture_baseline(
        session,
        project_id=project_id,
        requirements_baseline=baseline,
        trade_study=study,
        components=components,
        views=views,
        interface_contracts=interface_contracts,
        data_contracts=data_contracts,
        state_and_failure_model=state_and_failure_model,
        threat_model=threat_model,
        deployment_and_operations=deployment_and_operations,
        adrs=adrs,
        diagram_sources=diagram_sources,
        node_component_mappings=node_component_mappings,
        artifact_root=artifact_root,
    )


def architecture_review_node(
    session: Session,
    *,
    project_id: str,
    architecture_baseline_id: str,
    artifact_root: Path,
) -> EngineeringGate:
    """Open ENGINEERING_ARCHITECTURE_REVIEW bound to the three hashes."""
    architecture = load_architecture_baseline(
        session, architecture_baseline_id, artifact_root=artifact_root
    )
    return open_engineering_architecture_review(
        session,
        project_id=project_id,
        baseline=architecture,
        artifact_root=artifact_root,
    )


def architecture_review_resolve_node(
    session: Session,
    *,
    gate: EngineeringGate,
    decision: str,
    actor: ProvenanceType,
    user_event_id: str,
    current_baseline: ArchitectureBaseline,
    at: datetime,
    artifact_root: Path,
) -> EngineeringGate:
    """Resolve the architecture review through the enforced service path."""
    return resolve_engineering_architecture_review(
        session,
        gate=gate,
        decision=decision,
        actor=actor,
        user_event_id=user_event_id,
        current_baseline=current_baseline,
        at=at,
        artifact_root=artifact_root,
    )


__all__ = [
    "architecture_review_node",
    "architecture_review_resolve_node",
    "eng0_charter_node",
    "eng1_conops_node",
    "eng2_requirements_node",
    "eng3_trade_study_node",
    "eng4_architecture_node",
]
