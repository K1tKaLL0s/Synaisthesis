"""ENG0-ENG4 engineering design application service (blueprint 03B; M2.9).

The service enforces the M2.8 domain preconditions at every stage, persists
each stage artifact as hash-verified DomainEvents (content-addressed
payloads), and reloads them into identical domain objects.  Diagram sources
and rendered SVGs are stored as artifacts so images are never the sole source
of truth (03B, section 7.3).
"""

from __future__ import annotations

import dataclasses
import datetime
import json
import types
import typing
import uuid
from collections.abc import Mapping, Sequence
from enum import Enum
from pathlib import Path
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from synaisthesis.domain.architecture import (
    ArchitectureBaseline,
    ArchitectureComponent,
    ArchitectureDecisionRecord,
    ArchitectureDiagram,
    DataContractSet,
    DeploymentAndOperationsDesign,
    InterfaceContractSet,
    StateAndFailureModel,
    ThreatModel,
    architecture_review_blockers,
)
from synaisthesis.domain.engineering import (
    EVENT_ENGINEERING_ARTIFACT_CREATED,
    EVENT_ENGINEERING_GATE_OPENED,
    EVENT_ENGINEERING_GATE_RESOLVED,
    EVENT_ENGINEERING_STAGE_OPENED,
    EngineeringGateType,
    EngineeringMissionCharter,
    EngineeringReference,
    EngineeringReferenceSet,
    EngineeringStageId,
    MechanicalEngineeringBlueprint,
    OperationalConceptBundle,
    OptionTradeStudy,
    TechnologySelectionRecord,
    build_engineering_event,
    conops_blockers,
    delivery_status_for_stage,
    eng0_entry_blockers,
    trade_study_blockers,
    validate_technology_selection,
)
from synaisthesis.domain.enums import NoveltyStatus, ProvenanceType
from synaisthesis.domain.errors import DomainError
from synaisthesis.domain.gate import EngineeringGate, EngineeringGateBinding
from synaisthesis.domain.novelty import LowNoveltyOverride
from synaisthesis.domain.qualification import (
    EngineeringRouteSelection,
    UserEngineeringConceptApproval,
)
from synaisthesis.domain.requirements import (
    EngineeringRequirement,
    RequirementsBaseline,
    requirements_baseline_blockers,
)
from synaisthesis.domain.traceability import RequirementsTraceabilityMatrix
from synaisthesis.providers.prior_art.base import (
    EngineeringReferenceProvider,
    EngineeringReferenceQuery,
)
from synaisthesis.renderers.diagram_renderers import (
    DiagramRenderResult,
    DiagramSource,
    render_diagram_source,
    verify_diagram_render,
)
from synaisthesis.storage.artifact_store import ArtifactRecord, save_artifact
from synaisthesis.storage.hashing import verify_artifact_hash
from synaisthesis.storage.repositories.event_repository import (
    DomainEventRecord,
    append_domain_event,
)

CHARTER_AGGREGATE_TYPE = "EngineeringMissionCharter"
CONOPS_AGGREGATE_TYPE = "OperationalConceptBundle"
REQUIREMENTS_AGGREGATE_TYPE = "RequirementsBaseline"
REFERENCE_SET_AGGREGATE_TYPE = "EngineeringReferenceSet"
TRADE_STUDY_AGGREGATE_TYPE = "OptionTradeStudy"
TECHNOLOGY_SELECTION_AGGREGATE_TYPE = "TechnologySelectionRecord"
ARCHITECTURE_AGGREGATE_TYPE = "ArchitectureBaseline"
GATE_AGGREGATE_TYPE = "EngineeringGate"


# ---------------------------------------------------------------------------
# Event-sourced persistence helpers
# ---------------------------------------------------------------------------


def _verified_payload(
    session: Session, record: DomainEventRecord, artifact_root: Path
) -> dict[str, Any]:
    """Read and verify a payload artifact; fail closed when untrusted."""
    if record.event_payload_artifact_id is None:
        raise DomainError(
            f"event {record.id} has no payload artifact; state unrecoverable",
            error_code="ARTIFACT_HASH_MISMATCH",
        )
    artifact = session.get(ArtifactRecord, record.event_payload_artifact_id)
    if artifact is None:
        raise DomainError(
            f"payload artifact of event {record.id} is missing; state unrecoverable",
            error_code="ARTIFACT_HASH_MISMATCH",
        )
    path = artifact_root / artifact.relative_path
    if not verify_artifact_hash(path, artifact.sha256):
        raise DomainError(
            f"payload artifact of event {record.id} is missing or tampered; state unrecoverable",
            error_code="ARTIFACT_HASH_MISMATCH",
        )
    return json.loads(path.read_text(encoding="utf-8"))


def _event_stream(
    session: Session, aggregate_type: str, aggregate_id: str
) -> list[DomainEventRecord]:
    return list(
        session.execute(
            select(DomainEventRecord)
            .where(
                DomainEventRecord.aggregate_type == aggregate_type,
                DomainEventRecord.aggregate_id == aggregate_id,
            )
            .order_by(DomainEventRecord.id)
        )
        .scalars()
        .all()
    )


def _persist_engineering_event(
    session: Session,
    *,
    event_type: str,
    aggregate_type: str,
    aggregate_id: str,
    payload: dict[str, Any],
    project_id: str,
    artifact_root: Path,
) -> None:
    stream = _event_stream(session, aggregate_type, aggregate_id)
    event = build_engineering_event(
        event_type,
        aggregate_type=aggregate_type,
        aggregate_id=aggregate_id,
        payload=payload,
        sequence=len(stream) + 1,
    )
    append_domain_event(session, event, project_id=project_id, artifact_root=artifact_root)


def _persist_stage_and_artifact(
    session: Session,
    *,
    project_id: str,
    stage: EngineeringStageId,
    aggregate_type: str,
    aggregate_id: str,
    artifact_payload: dict[str, Any],
    artifact_root: Path,
) -> None:
    _persist_engineering_event(
        session,
        event_type=EVENT_ENGINEERING_STAGE_OPENED,
        aggregate_type=aggregate_type,
        aggregate_id=aggregate_id,
        payload={"stage": stage.value, "delivery_status": delivery_status_for_stage(stage).value},
        project_id=project_id,
        artifact_root=artifact_root,
    )
    _persist_engineering_event(
        session,
        event_type=EVENT_ENGINEERING_ARTIFACT_CREATED,
        aggregate_type=aggregate_type,
        aggregate_id=aggregate_id,
        payload={"artifact": artifact_payload},
        project_id=project_id,
        artifact_root=artifact_root,
    )


def _load_artifact(
    session: Session,
    *,
    aggregate_type: str,
    aggregate_id: str,
    model: type,
    artifact_root: Path,
    not_found_code: str = "PROJECT_NOT_FOUND",
) -> Any:
    records = _event_stream(session, aggregate_type, aggregate_id)
    if not records:
        raise DomainError(
            f"{aggregate_type} {aggregate_id!r} has no events",
            error_code=not_found_code,
        )
    artifact: Any | None = None
    for record in records:
        payload = _verified_payload(session, record, artifact_root)
        if record.event_type == EVENT_ENGINEERING_ARTIFACT_CREATED:
            artifact = rebuild_dataclass(model, payload["artifact"])
    if artifact is None:
        raise DomainError(
            f"state of {aggregate_id!r} is unrecoverable",
            error_code="PROJECT_STATE_UNRECOVERABLE",
        )
    return artifact


# ---------------------------------------------------------------------------
# Generic canonical-payload -> dataclass rebuild
# ---------------------------------------------------------------------------


def _convert(value: Any, annotation: Any) -> Any:
    if annotation is None:
        return value
    origin = typing.get_origin(annotation)
    if origin in (typing.Union, types.UnionType):
        if value is None:
            return None
        for argument in typing.get_args(annotation):
            if argument is type(None):
                continue
            try:
                return _convert(value, argument)
            except (TypeError, ValueError, DomainError):
                continue
        return value
    if origin is tuple:
        arguments = typing.get_args(annotation)
        if len(arguments) == 2 and arguments[1] is Ellipsis:
            return tuple(_convert(item, arguments[0]) for item in value)
        return tuple(
            _convert(item, argument) for item, argument in zip(value, arguments, strict=False)
        )
    if origin in (dict, typing.Mapping):
        (_key_type, value_type) = typing.get_args(annotation)
        return {key: _convert(item, value_type) for key, item in value.items()}
    if isinstance(annotation, type):
        if issubclass(annotation, Enum):
            return annotation(value)
        if dataclasses.is_dataclass(annotation):
            return rebuild_dataclass(annotation, value)
        if issubclass(annotation, datetime.datetime):
            return datetime.datetime.fromisoformat(value)
    return value


def rebuild_dataclass(model: type, payload: Mapping[str, Any]) -> Any:
    """Rebuild a frozen domain dataclass from its canonical event payload."""
    hints = typing.get_type_hints(model)
    kwargs: dict[str, Any] = {}
    for field in dataclasses.fields(model):
        if field.name not in payload:
            continue
        kwargs[field.name] = _convert(payload[field.name], hints.get(field.name))
    return model(**kwargs)


def _artifact_key(
    session: Session, artifact_root: Path, content: str, media_type: str, project_id: str
) -> ArtifactRecord:
    return save_artifact(
        session,
        project_id=project_id,
        relative_path=f"engineering/{uuid.uuid4().hex[:16]}.{media_type.split('/')[-1]}",
        media_type=media_type,
        content=content.encode("utf-8"),
        artifact_root=artifact_root,
    )


# ---------------------------------------------------------------------------
# ENG0 — mission charter (03B, sections 1.1/3)
# ---------------------------------------------------------------------------


def _eng0_error_code(blockers: tuple[str, ...]) -> str:
    joined = " ".join(blockers)
    if "工程路线未由用户选择" in joined or "TRY_ENGINEERING_PROJECT" in joined:
        return "ENGINEERING_ROUTE_DECISION_REQUIRED"
    if "ENGINEERING_NOVELTY_QUALIFIED" in joined or "RQ4E" in joined:
        return "ENGINEERING_NOVELTY_REQUIRED"
    return "EARLY_QUALIFICATION_REQUIRED"


def create_engineering_mission_charter(
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
    charter_id: str | None = None,
) -> EngineeringMissionCharter:
    """Create ENG0 only after every 03B 1.1 precondition holds."""
    blockers = eng0_entry_blockers(
        bound_input_spec_hash=bound_input_spec_hash,
        current_input_spec_hash=current_input_spec_hash,
        route_selection=route_selection,
        concept_approval=concept_approval,
        concept_hash=concept_hash,
        novelty_status=novelty_status,
        novelty_review_hash=novelty_review_hash,
        override=override,
        open_gate_types=open_gate_types,
    )
    if blockers:
        raise DomainError(
            "ENG0 entry blocked: " + "; ".join(blockers),
            error_code=_eng0_error_code(blockers),
        )
    aggregate_id = charter_id or charter.charter_id
    _persist_stage_and_artifact(
        session,
        project_id=project_id,
        stage=EngineeringStageId.ENG0,
        aggregate_type=CHARTER_AGGREGATE_TYPE,
        aggregate_id=aggregate_id,
        artifact_payload=charter.to_event_payload(),
        artifact_root=artifact_root,
    )
    return charter


def load_engineering_charter(
    session: Session, charter_id: str, *, artifact_root: Path
) -> EngineeringMissionCharter:
    return _load_artifact(
        session,
        aggregate_type=CHARTER_AGGREGATE_TYPE,
        aggregate_id=charter_id,
        model=EngineeringMissionCharter,
        artifact_root=artifact_root,
    )


# ---------------------------------------------------------------------------
# ENG1 — ConOps (03B, section 4)
# ---------------------------------------------------------------------------


def create_operational_concept_bundle(
    session: Session,
    *,
    project_id: str,
    charter: EngineeringMissionCharter,
    conops: OperationalConceptBundle,
    artifact_root: Path,
    conops_id: str | None = None,
) -> OperationalConceptBundle:
    if conops.charter_hash != charter.artifact_hash:
        raise DomainError(
            "ConOps 未绑定当前 charter hash",
            error_code="CONOPS_CHARTER_MISMATCH",
        )
    blockers = conops_blockers(conops)
    if blockers:
        raise DomainError(
            "ConOps blocked: " + "; ".join(blockers),
            error_code="CONOPS_INVALID",
        )
    aggregate_id = conops_id or conops.conops_id
    _persist_stage_and_artifact(
        session,
        project_id=project_id,
        stage=EngineeringStageId.ENG1,
        aggregate_type=CONOPS_AGGREGATE_TYPE,
        aggregate_id=aggregate_id,
        artifact_payload=conops.to_event_payload(),
        artifact_root=artifact_root,
    )
    return conops


def load_operational_concept_bundle(
    session: Session, conops_id: str, *, artifact_root: Path
) -> OperationalConceptBundle:
    return _load_artifact(
        session,
        aggregate_type=CONOPS_AGGREGATE_TYPE,
        aggregate_id=conops_id,
        model=OperationalConceptBundle,
        artifact_root=artifact_root,
        not_found_code="CONOPS_REQUIRED",
    )


# ---------------------------------------------------------------------------
# ENG2 — requirements baseline (03B, section 5)
# ---------------------------------------------------------------------------


def create_engineering_requirements_baseline(
    session: Session,
    *,
    project_id: str,
    conops: OperationalConceptBundle,
    requirements: tuple[EngineeringRequirement, ...],
    artifact_root: Path,
    baseline_id: str | None = None,
    version: int = 1,
) -> RequirementsBaseline:
    """Persist ENG2 only when the 03B 5.4 pass criteria hold."""
    if conops.artifact_hash is None:
        raise DomainError("ConOps 缺少 artifact_hash", error_code="CONOPS_INVALID")
    baseline = RequirementsBaseline(
        baseline_id=baseline_id or f"rb-{uuid.uuid4().hex[:12]}",
        version=version,
        project_id=project_id,
        conops_id=conops.conops_id,
        input_spec_hash=conops.input_spec_hash,
        conops_hash=conops.artifact_hash,
        source_refs_required=conops.intent_refs,
        requirements=requirements,
    )
    blockers = requirements_baseline_blockers(baseline)
    if blockers:
        raise DomainError(
            "REQUIREMENTS_BASELINE_BLOCKED: " + "; ".join(blockers),
            error_code="REQUIREMENTS_BASELINE_BLOCKED",
        )
    _persist_stage_and_artifact(
        session,
        project_id=project_id,
        stage=EngineeringStageId.ENG2,
        aggregate_type=REQUIREMENTS_AGGREGATE_TYPE,
        aggregate_id=baseline.baseline_id,
        artifact_payload=baseline.to_event_payload(),
        artifact_root=artifact_root,
    )
    return baseline


def load_requirements_baseline(
    session: Session, baseline_id: str, *, artifact_root: Path
) -> RequirementsBaseline:
    return _load_artifact(
        session,
        aggregate_type=REQUIREMENTS_AGGREGATE_TYPE,
        aggregate_id=baseline_id,
        model=RequirementsBaseline,
        artifact_root=artifact_root,
        not_found_code="BASELINE_REQUIRED",
    )


# ---------------------------------------------------------------------------
# ENG3 — reference deep search and trade study (03B, section 6)
# ---------------------------------------------------------------------------


def run_engineering_reference_search(
    *,
    providers: Sequence[EngineeringReferenceProvider],
    query: EngineeringReferenceQuery,
    project_id: str,
    requirements_baseline_id: str,
    reference_set_id: str | None = None,
    version: int = 1,
) -> EngineeringReferenceSet:
    """Collect, quarantine and deduplicate deep-search hits (03B, 6.1/6.3)."""
    hits: list[Any] = []
    for provider in providers:
        hits.extend(provider.search_references(query))
    seen: set[tuple[str, str]] = set()
    references: list[EngineeringReference] = []
    for hit in sorted(hits, key=lambda item: (item.stable_identifier, item.canonical_url)):
        key = (hit.stable_identifier, hit.canonical_url)
        if key in seen:
            continue
        seen.add(key)
        references.append(
            EngineeringReference(
                stable_identifier=hit.stable_identifier,
                reference_type=hit.category,
                canonical_url=hit.canonical_url,
                evidence_refs=hit.evidence_refs,
                maturity_claims=hit.maturity_evidence_refs,
            )
        )
    return EngineeringReferenceSet(
        reference_set_id=reference_set_id or f"refs-{uuid.uuid4().hex[:12]}",
        version=version,
        project_id=project_id,
        requirements_baseline_id=requirements_baseline_id,
        references=tuple(references),
    )


def create_option_trade_study(
    session: Session,
    *,
    project_id: str,
    baseline: RequirementsBaseline,
    study: OptionTradeStudy,
    artifact_root: Path,
) -> OptionTradeStudy:
    """Persist ENG3 only when hard elimination and weights are valid (03B, 6.2)."""
    if study.requirements_baseline_id != baseline.baseline_id:
        raise DomainError(
            "trade study 未绑定当前 Requirements Baseline",
            error_code="TRADE_STUDY_BLOCKED",
        )
    blockers = trade_study_blockers(study, baseline.baseline_id)
    if blockers:
        raise DomainError(
            "TRADE_STUDY_BLOCKED: " + "; ".join(blockers),
            error_code="TRADE_STUDY_BLOCKED",
        )
    _persist_stage_and_artifact(
        session,
        project_id=project_id,
        stage=EngineeringStageId.ENG3,
        aggregate_type=TRADE_STUDY_AGGREGATE_TYPE,
        aggregate_id=study.study_id,
        artifact_payload=study.to_event_payload(),
        artifact_root=artifact_root,
    )
    return study


def load_option_trade_study(
    session: Session, study_id: str, *, artifact_root: Path
) -> OptionTradeStudy:
    return _load_artifact(
        session,
        aggregate_type=TRADE_STUDY_AGGREGATE_TYPE,
        aggregate_id=study_id,
        model=OptionTradeStudy,
        artifact_root=artifact_root,
        not_found_code="TRADE_STUDY_REQUIRED",
    )


def select_engineering_technology(
    session: Session,
    *,
    project_id: str,
    record: TechnologySelectionRecord,
    study: OptionTradeStudy,
    artifact_root: Path,
) -> TechnologySelectionRecord:
    """Persist a technology selection only while the study hash still binds."""
    blockers = validate_technology_selection(record, study)
    if blockers:
        raise DomainError(
            "TRADE_STUDY_BLOCKED: " + "; ".join(blockers),
            error_code="TRADE_STUDY_BLOCKED",
        )
    _persist_engineering_event(
        session,
        event_type=EVENT_ENGINEERING_ARTIFACT_CREATED,
        aggregate_type=TECHNOLOGY_SELECTION_AGGREGATE_TYPE,
        aggregate_id=record.selection_id,
        payload={"artifact": record.to_event_payload()},
        project_id=project_id,
        artifact_root=artifact_root,
    )
    return record


# ---------------------------------------------------------------------------
# ENG4 — architecture baseline and review gate (03B, section 7)
# ---------------------------------------------------------------------------


def _render_diagram(
    session: Session,
    *,
    project_id: str,
    source: DiagramSource,
    node_component_mapping: dict[str, str],
    artifact_root: Path,
) -> ArchitectureDiagram:
    result: DiagramRenderResult = render_diagram_source(
        source, node_component_mapping=node_component_mapping
    )
    blockers = verify_diagram_render(result)
    if blockers:
        raise DomainError(
            "diagram render failed: " + "; ".join(blockers),
            error_code="DIAGRAM_BROKEN_LINKS",
        )
    source_artifact = _artifact_key(
        session,
        artifact_root,
        result.source_text,
        "text/x-diagram-source",
        project_id,
    )
    svg_artifact = _artifact_key(
        session,
        artifact_root,
        result.svg_text,
        "image/svg+xml",
        project_id,
    )
    return ArchitectureDiagram(
        diagram_id=source.diagram_id,
        title=source.title,
        version=source.version,
        input_hash=source.input_hash,
        legend=source.legend,
        node_edge_semantics=source.node_edge_semantics,
        stable_id_mapping=dict(node_component_mapping),
        node_component_ids=result.rendered_node_ids,
        source_path=source_artifact.relative_path,
        source_hash=result.source_hash,
        rendered_svg_path=svg_artifact.relative_path,
        rendered_svg_hash=result.svg_hash,
        render_receipt=result.render_receipt,
        broken_link_refs=result.broken_link_refs,
    )


def create_architecture_baseline(
    session: Session,
    *,
    project_id: str,
    requirements_baseline: RequirementsBaseline,
    trade_study: OptionTradeStudy,
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
    baseline_id: str | None = None,
) -> ArchitectureBaseline:
    """Persist ENG4 with hash-bound diagrams; images are never the sole source."""
    diagrams = tuple(
        _render_diagram(
            session,
            project_id=project_id,
            source=source,
            node_component_mapping=node_component_mappings.get(source.diagram_id, {}),
            artifact_root=artifact_root,
        )
        for source in diagram_sources
    )
    if requirements_baseline.artifact_hash is None or trade_study.artifact_hash is None:
        raise DomainError(
            "requirements baseline / trade study 缺少 artifact_hash",
            error_code="BASELINE_REQUIRED",
        )
    baseline = ArchitectureBaseline(
        baseline_id=baseline_id or f"ab-{uuid.uuid4().hex[:12]}",
        version=1,
        project_id=project_id,
        requirements_baseline_id=requirements_baseline.baseline_id,
        requirements_hash=requirements_baseline.artifact_hash,
        trade_study_id=trade_study.study_id,
        trade_study_hash=trade_study.artifact_hash,
        components=components,
        views=views,
        interface_contracts=interface_contracts,
        data_contracts=data_contracts,
        state_and_failure_model=state_and_failure_model,
        threat_model=threat_model,
        deployment_and_operations=deployment_and_operations,
        adrs=adrs,
        diagrams=diagrams,
    )
    blockers = architecture_review_blockers(baseline)
    if blockers:
        raise DomainError(
            "architecture baseline invalid: " + "; ".join(blockers),
            error_code="ARCHITECTURE_INVALID",
        )
    _persist_stage_and_artifact(
        session,
        project_id=project_id,
        stage=EngineeringStageId.ENG4,
        aggregate_type=ARCHITECTURE_AGGREGATE_TYPE,
        aggregate_id=baseline.baseline_id,
        artifact_payload=baseline.to_event_payload(),
        artifact_root=artifact_root,
    )
    return baseline


def load_architecture_baseline(
    session: Session, baseline_id: str, *, artifact_root: Path
) -> ArchitectureBaseline:
    return _load_artifact(
        session,
        aggregate_type=ARCHITECTURE_AGGREGATE_TYPE,
        aggregate_id=baseline_id,
        model=ArchitectureBaseline,
        artifact_root=artifact_root,
        not_found_code="ARCHITECTURE_REQUIRED",
    )


def open_engineering_architecture_review(
    session: Session,
    *,
    project_id: str,
    baseline: ArchitectureBaseline,
    artifact_root: Path,
    gate_id: str | None = None,
) -> EngineeringGate:
    """Open ENGINEERING_ARCHITECTURE_REVIEW bound to the three hashes (03B, 7.4)."""
    if baseline.artifact_hash is None:
        raise DomainError(
            "architecture baseline 缺少 artifact_hash",
            error_code="ARCHITECTURE_INVALID",
        )
    gate = EngineeringGate(
        gate_id=gate_id or f"gate-ar-{uuid.uuid4().hex[:12]}",
        project_id=project_id,
        gate_type=EngineeringGateType.ENGINEERING_ARCHITECTURE_REVIEW,
        binding=EngineeringGateBinding(
            gate_type=EngineeringGateType.ENGINEERING_ARCHITECTURE_REVIEW,
            artifact_id=baseline.baseline_id,
            version=baseline.version,
            artifact_hash=baseline.artifact_hash,
            bound_hashes={
                "requirements": baseline.requirements_hash,
                "trade_study": baseline.trade_study_hash,
                "architecture": baseline.artifact_hash,
            },
        ),
        reason="ENG4 ArchitectureBaseline 已生成，等待用户评审",
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


def resolve_engineering_architecture_review(
    session: Session,
    *,
    gate: EngineeringGate,
    decision: str,
    actor: ProvenanceType,
    user_event_id: str,
    current_baseline: ArchitectureBaseline,
    at: datetime.datetime,
    artifact_root: Path,
) -> EngineeringGate:
    """Resolve the review; any hash change invalidates the old binding (03B, 7.4)."""
    if gate.gate_type is not EngineeringGateType.ENGINEERING_ARCHITECTURE_REVIEW:
        raise DomainError(
            f"gate type {gate.gate_type.value} is not an architecture review",
            error_code="GATE_TYPE_MISMATCH",
        )
    expected = {
        "requirements": current_baseline.requirements_hash,
        "trade_study": current_baseline.trade_study_hash,
        "architecture": current_baseline.artifact_hash,
    }
    if (
        gate.binding.artifact_id != current_baseline.baseline_id
        or gate.binding.bound_hashes != expected
    ):
        raise DomainError(
            "architecture review binding 与当前 baseline 不一致"
            "（requirements/trade_study/architecture 任一 hash 变化）",
            error_code="STALE_ARCHITECTURE_BINDING",
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


def load_engineering_gate(
    session: Session, gate_id: str, *, artifact_root: Path
) -> EngineeringGate:
    records = _event_stream(session, GATE_AGGREGATE_TYPE, gate_id)
    if not records:
        raise DomainError(
            f"engineering gate {gate_id!r} has no events",
            error_code="PROJECT_NOT_FOUND",
        )
    gate: EngineeringGate | None = None
    for record in records:
        payload = _verified_payload(session, record, artifact_root)
        if record.event_type in {EVENT_ENGINEERING_GATE_OPENED, EVENT_ENGINEERING_GATE_RESOLVED}:
            gate = rebuild_dataclass(EngineeringGate, payload["gate"])
    if gate is None:
        raise DomainError(
            f"state of gate {gate_id!r} is unrecoverable",
            error_code="PROJECT_STATE_UNRECOVERABLE",
        )
    return gate


# ---------------------------------------------------------------------------
# ENG5 — mechanical engineering blueprint (03B, section 8)
# ---------------------------------------------------------------------------

BLUEPRINT_AGGREGATE_TYPE = "MechanicalEngineeringBlueprint"


def _approved_architecture_binding_blockers(
    architecture: ArchitectureBaseline, approval: EngineeringGate
) -> tuple[str, ...]:
    """A blueprint may only freeze an architecture the user approved (03B, 8.3)."""
    blockers: list[str] = []
    if approval.status.value != "RESOLVED" or approval.decision != "APPROVE_BASELINE":
        blockers.append("重大架构未由用户批准（Gate 未以 APPROVE_BASELINE 决议）")
    expected = {
        "requirements": architecture.requirements_hash,
        "trade_study": architecture.trade_study_hash,
        "architecture": architecture.artifact_hash,
    }
    if (
        approval.binding.artifact_id != architecture.baseline_id
        or approval.binding.bound_hashes != expected
    ):
        blockers.append("架构批准 Gate 未绑定当前 baseline 三 hash")
    return tuple(blockers)


def create_mechanical_engineering_blueprint(
    session: Session,
    *,
    project_id: str,
    architecture: ArchitectureBaseline,
    architecture_approval: EngineeringGate,
    matrix: RequirementsTraceabilityMatrix,
    blueprint: MechanicalEngineeringBlueprint,
    ordinary_decision_ids: tuple[str, ...] = (),
    artifact_root: Path,
    blueprint_id: str | None = None,
) -> MechanicalEngineeringBlueprint:
    """Persist ENG5 only when the Blueprint Completeness Gate passes (03B, 8.3)."""
    approval_blockers = _approved_architecture_binding_blockers(architecture, architecture_approval)
    if approval_blockers:
        raise DomainError(
            "ENGINEERING_ARCHITECTURE_REVIEW_REQUIRED: " + "; ".join(approval_blockers),
            error_code="ENGINEERING_ARCHITECTURE_REVIEW_REQUIRED",
        )
    if blueprint.architecture_baseline_id != architecture.baseline_id:
        raise DomainError(
            "blueprint 未绑定当前 ArchitectureBaseline",
            error_code="BLUEPRINT_GAP",
        )
    if blueprint.architecture_hash != architecture.artifact_hash:
        raise DomainError(
            "blueprint 绑定 architecture hash 与当前 baseline 不一致",
            error_code="BLUEPRINT_GAP",
        )
    baseline = load_requirements_baseline(
        session, architecture.requirements_baseline_id, artifact_root=artifact_root
    )
    requirements = tuple(requirement.requirement_id for requirement in baseline.requirements)
    critical_requirements = baseline.critical_requirement_ids
    from synaisthesis.domain.traceability import (
        TraceableElementType,
        uncovered_requirements,
    )

    missing_design = uncovered_requirements(
        matrix,
        requirements=requirements,
        target_type=TraceableElementType.DESIGN,
    )
    missing_task = uncovered_requirements(
        matrix,
        requirements=requirements,
        target_type=TraceableElementType.TASK,
    )
    missing_test = uncovered_requirements(
        matrix,
        requirements=critical_requirements,
        target_type=TraceableElementType.TEST,
    )
    trace_gaps = (
        ([f"requirement→design 缺失: {', '.join(missing_design)}"] if missing_design else [])
        + ([f"requirement→task 缺失: {', '.join(missing_task)}"] if missing_task else [])
        + ([f"critical→test 缺失: {', '.join(missing_test)}"] if missing_test else [])
    )
    if trace_gaps:
        raise DomainError(
            "BLUEPRINT_GAP: " + "; ".join(trace_gaps),
            error_code="BLUEPRINT_GAP",
        )
    interfaces_total = len(architecture.interface_contracts)
    interfaces_with_schema = sum(
        1 for contract in architecture.interface_contracts if contract.schema_ref.strip()
    )
    broken_diagram_references = sum(
        len(diagram.broken_link_refs) for diagram in architecture.diagrams
    )
    from synaisthesis.domain.engineering import (
        blueprint_completeness_blockers,
        validate_decision_escalation,
    )

    completeness_blockers = blueprint_completeness_blockers(
        blueprint,
        requirements_total=len(requirements),
        requirements_to_design=len(requirements) - len(missing_design),
        requirements_to_task=len(requirements) - len(missing_task),
        critical_requirements_total=len(critical_requirements),
        critical_requirements_to_test=len(critical_requirements) - len(missing_test),
        public_interfaces_total=interfaces_total,
        public_interfaces_with_schema=interfaces_with_schema,
        unresolved_product_decisions=len(blueprint.escalated_decision_ids),
        unresolved_architecture_decisions=0,
        broken_diagram_references=broken_diagram_references,
    )
    escalation_blockers = validate_decision_escalation(
        escalated_decision_ids=blueprint.escalated_decision_ids,
        ordinary_decision_ids=ordinary_decision_ids,
    )
    all_blockers = list(completeness_blockers) + list(escalation_blockers)
    if all_blockers:
        raise DomainError(
            "BLUEPRINT_GAP: " + "; ".join(all_blockers),
            error_code="BLUEPRINT_GAP",
        )
    aggregate_id = blueprint_id or blueprint.blueprint_id
    _persist_stage_and_artifact(
        session,
        project_id=project_id,
        stage=EngineeringStageId.ENG5,
        aggregate_type=BLUEPRINT_AGGREGATE_TYPE,
        aggregate_id=aggregate_id,
        artifact_payload=blueprint.to_event_payload(),
        artifact_root=artifact_root,
    )
    return blueprint


def load_mechanical_engineering_blueprint(
    session: Session, blueprint_id: str, *, artifact_root: Path
) -> MechanicalEngineeringBlueprint:
    return _load_artifact(
        session,
        aggregate_type=BLUEPRINT_AGGREGATE_TYPE,
        aggregate_id=blueprint_id,
        model=MechanicalEngineeringBlueprint,
        artifact_root=artifact_root,
        not_found_code="BLUEPRINT_REQUIRED",
    )


__all__ = [
    "ARCHITECTURE_AGGREGATE_TYPE",
    "BLUEPRINT_AGGREGATE_TYPE",
    "CHARTER_AGGREGATE_TYPE",
    "CONOPS_AGGREGATE_TYPE",
    "GATE_AGGREGATE_TYPE",
    "REFERENCE_SET_AGGREGATE_TYPE",
    "REQUIREMENTS_AGGREGATE_TYPE",
    "TECHNOLOGY_SELECTION_AGGREGATE_TYPE",
    "TRADE_STUDY_AGGREGATE_TYPE",
    "create_architecture_baseline",
    "create_engineering_mission_charter",
    "create_engineering_requirements_baseline",
    "create_mechanical_engineering_blueprint",
    "create_operational_concept_bundle",
    "create_option_trade_study",
    "load_architecture_baseline",
    "load_engineering_charter",
    "load_engineering_gate",
    "load_mechanical_engineering_blueprint",
    "load_operational_concept_bundle",
    "load_option_trade_study",
    "load_requirements_baseline",
    "open_engineering_architecture_review",
    "rebuild_dataclass",
    "resolve_engineering_architecture_review",
    "run_engineering_reference_search",
    "select_engineering_technology",
]
