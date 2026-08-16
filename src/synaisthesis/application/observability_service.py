"""Web observability service (19 §5 M14.WEB.OBSERVABILITY).

Reads persisted, hash-verified event-sourced state and surfaces it verbatim
under the frozen API schema (configs/api/observability_schema.json).  This
service never derives state: every route, artifact hash, score, trace, gap,
evidence tier and compliance status shown is copied from the store.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from synaisthesis.application.engineering_design_service import _verified_payload
from synaisthesis.application.gate_service import HUMAN_GATE_AGGREGATE_TYPE
from synaisthesis.domain.errors import DomainError
from synaisthesis.storage.repositories.event_repository import DomainEventRecord

OBSERVABILITY_SCHEMA_VERSION = "1.0.0"

# Qualification flow pages (19 §5 M14): each page lists the stored aggregate
# types it renders.  Only stored aggregates appear; nothing is computed.
PAGE_SPECS: tuple[tuple[str, str, tuple[str, ...]], ...] = (
    (
        "design",
        "Design (S1/S2/S4 inputs and hashes)",
        (
            "Seed",
            "NaturalLanguageSpec",
            "MechanismSketch",
            "ResearchScopeSpec",
            "ResearchSpec",
        ),
    ),
    (
        "feasibility_route_gate",
        "Feasibility / Route Gate (RQ2F + ENG0)",
        (
            "EngineeringMissionCharter",
            "OperationalConceptBundle",
            "RequirementsBaseline",
        ),
    ),
    (
        "formula_concept_review",
        "Formula / Engineering Concept Review (RQ3M/RQ3E + S5)",
        ("MinimalCaseBundle", "TheoryKernel", "FormalizationPlan"),
    ),
    (
        "novelty_score_gate",
        "Novelty Score / Gate (RQ4)",
        (),
    ),
    (
        "engineering_trace_blueprint",
        "Engineering Trace / Blueprint",
        (
            "RequirementsTraceabilityMatrix",
            "ArchitectureBaseline",
            "MechanicalEngineeringBlueprint",
            "EngineeringGate",
        ),
    ),
    (
        "publication",
        "Publication (master manuscript, audit, compliance)",
        (
            "EngineeringMasterManuscript",
            "EngineeringManuscriptAudit",
            "EngineeringVenueAdaptedManuscript",
            "TheoryMasterManuscript",
            "TheoryVenueAdaptedManuscript",
        ),
    ),
)

GATE_TYPES_BY_PAGE: dict[str, tuple[str, ...]] = {
    "design": (),
    "feasibility_route_gate": (
        "ENGINEERING_ROUTE_DECISION",
        "FORMALIZATION_FEASIBILITY_DECISION",
    ),
    "formula_concept_review": (
        "EARLY_FORMALIZATION_REVIEW",
        "EARLY_ENGINEERING_CONCEPT_REVIEW",
    ),
    "novelty_score_gate": ("LOW_NOVELTY_RESEARCH_DECISION",),
    "engineering_trace_blueprint": (),
    "publication": (),
}


@dataclass(frozen=True, slots=True)
class StoredArtifact:
    aggregate_type: str
    aggregate_id: str
    event_type: str
    artifact: dict[str, Any] | None


@dataclass(frozen=True, slots=True)
class StoredGate:
    gate_id: str
    gate_type: str
    status: str
    binding: dict[str, Any] | None


def _latest_events(session: Session, project_id: str) -> list[DomainEventRecord]:
    return list(
        session.execute(
            select(DomainEventRecord)
            .where(DomainEventRecord.project_id == project_id)
            .order_by(DomainEventRecord.id)
        )
        .scalars()
        .all()
    )


def _latest_artifact_per_aggregate(
    session: Session,
    records: list[DomainEventRecord],
    aggregate_types: tuple[str, ...],
    artifact_root: Path,
) -> list[StoredArtifact]:
    latest: dict[tuple[str, str], DomainEventRecord] = {}
    for record in records:
        if record.aggregate_type not in aggregate_types:
            continue
        key = (record.aggregate_type, record.aggregate_id)
        latest[key] = record
    artifacts: list[StoredArtifact] = []
    for (aggregate_type, aggregate_id), record in sorted(latest.items()):
        payload = _verified_payload(session, record, artifact_root)
        artifact = payload.get("artifact")
        if artifact is not None and not isinstance(artifact, dict):
            raise DomainError(
                f"aggregate {aggregate_type}/{aggregate_id} artifact payload 不是对象",
                error_code="ARTIFACT_HASH_MISMATCH",
            )
        artifacts.append(
            StoredArtifact(
                aggregate_type=aggregate_type,
                aggregate_id=aggregate_id,
                event_type=record.event_type,
                artifact=artifact,
            )
        )
    return artifacts


def _latest_gates(
    session: Session,
    records: list[DomainEventRecord],
    gate_types: tuple[str, ...],
    artifact_root: Path,
) -> list[StoredGate]:
    latest: dict[str, DomainEventRecord] = {}
    for record in records:
        if record.aggregate_type != HUMAN_GATE_AGGREGATE_TYPE:
            continue
        key = record.aggregate_id
        if key in latest and record.id <= latest[key].id:
            continue
        latest[key] = record
    gates: list[StoredGate] = []
    for gate_id, record in sorted(latest.items()):
        payload = _verified_payload(session, record, artifact_root)
        gate = payload.get("gate")
        if not isinstance(gate, dict):
            raise DomainError(
                f"gate {gate_id!r} payload 缺少 gate 对象",
                error_code="ARTIFACT_HASH_MISMATCH",
            )
        if gate_types and gate.get("gate_type") not in gate_types:
            continue
        gates.append(
            StoredGate(
                gate_id=gate_id,
                gate_type=str(gate.get("gate_type", "")),
                status=str(gate.get("status", "")),
                binding=gate.get("binding") if isinstance(gate.get("binding"), dict) else None,
            )
        )
    return gates


def _page_status(
    artifacts: list[StoredArtifact], gates: list[StoredGate], expected: tuple[str, ...]
) -> str:
    if not artifacts and not gates:
        return "NOT_STARTED"
    present = {artifact.aggregate_type for artifact in artifacts}
    if expected and not set(expected) <= present:
        return "IN_PROGRESS"
    if any(gate.status == "OPEN" for gate in gates):
        return "IN_PROGRESS"
    return "READY"


def _page_route(artifacts: list[StoredArtifact], gates: list[StoredGate]) -> str | None:
    for gate in gates:
        binding = gate.binding or {}
        route = binding.get("route")
        if isinstance(route, str) and route:
            return route
    for artifact in artifacts:
        payload = artifact.artifact or {}
        route = payload.get("route")
        if isinstance(route, str) and route:
            return route
        charter = payload.get("charter") if isinstance(payload.get("charter"), dict) else None
        if charter and isinstance(charter.get("route"), str):
            return str(charter["route"])
    return None


def _page_payload(
    *,
    page_id: str,
    title: str,
    artifacts: list[StoredArtifact],
    gates: list[StoredGate],
    expected_types: tuple[str, ...],
) -> dict[str, Any]:
    return {
        "page_id": page_id,
        "title": title,
        "status": _page_status(artifacts, gates, expected_types),
        "route": _page_route(artifacts, gates),
        "inputs": [
            {
                "aggregate_type": artifact.aggregate_type,
                "aggregate_id": artifact.aggregate_id,
                "event_type": artifact.event_type,
                "artifact": artifact.artifact,
            }
            for artifact in artifacts
        ],
        "artifacts": [
            {
                "aggregate_type": artifact.aggregate_type,
                "aggregate_id": artifact.aggregate_id,
                "event_type": artifact.event_type,
                "artifact": artifact.artifact,
            }
            for artifact in artifacts
        ],
        "gates": [
            {
                "gate_id": gate.gate_id,
                "gate_type": gate.gate_type,
                "status": gate.status,
                "binding": gate.binding,
            }
            for gate in gates
        ],
        "rendered_from_store": True,
    }


def project_observability_payload(
    session: Session,
    *,
    project_id: str,
    artifact_root: Path,
) -> dict[str, Any]:
    """Assemble the frozen-schema observability payload from stored state only."""
    if not project_id.strip():
        raise DomainError(
            "project_id 不能为空",
            error_code="PROJECT_NOT_FOUND",
        )
    records = _latest_events(session, project_id)
    pages: list[dict[str, Any]] = []
    for page_id, title, aggregate_types in PAGE_SPECS:
        artifacts = _latest_artifact_per_aggregate(session, records, aggregate_types, artifact_root)
        gates = _latest_gates(session, records, GATE_TYPES_BY_PAGE.get(page_id, ()), artifact_root)
        pages.append(
            _page_payload(
                page_id=page_id,
                title=title,
                artifacts=artifacts,
                gates=gates,
                expected_types=aggregate_types,
            )
        )
    return {
        "project_id": project_id,
        "schema_version": OBSERVABILITY_SCHEMA_VERSION,
        "rendered_from_store": True,
        "pages": pages,
    }


__all__ = [
    "GATE_TYPES_BY_PAGE",
    "OBSERVABILITY_SCHEMA_VERSION",
    "PAGE_SPECS",
    "project_observability_payload",
]
