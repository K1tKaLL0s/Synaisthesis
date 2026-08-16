"""Incubation application service for S0–S4 (blueprint 07 section 2, M2).

S0 raw input is persisted with its re-computable SHA-256 and never silently
rewritten. S1 and S4 are assistant-proposed and can only be confirmed by real
user events; the confirming provenance is persisted with the event. S4
confirmation binds the current S1/S4 hashes via ResearchSpecBound, and the
NATURAL_LANGUAGE_DESIGN_READY completion gate is derived from persisted
S0–S4 events plus that hash binding. Persistence reuses the M1.4
event-sourced pattern: ordered DomainEvents whose canonical JSON payloads
live in content-addressed artifacts.
"""

from __future__ import annotations

import json
import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from synaisthesis.agents.schemas import (
    MechanismSketch,
    MinimalCaseBundle,
    NaturalLanguageSpec,
    PriorWorkMap,
    ResearchScopeSpec,
    SeedRecord,
)
from synaisthesis.domain.enums import (
    NoveltyStatus,
    ProjectLifecycleStatus,
    ProvenanceType,
    QualifiedNextTarget,
    ResearchRoute,
    StageGateStatus,
    StageId,
)
from synaisthesis.domain.errors import DomainError
from synaisthesis.domain.event import DomainEvent, sha256_hex
from synaisthesis.domain.gate import qualification_next_target
from synaisthesis.domain.novelty import LowNoveltyOverride
from synaisthesis.domain.research_spec import ResearchSpec
from synaisthesis.domain.stage import (
    validate_mechanism_sketch,
    validate_natural_language_spec,
    validate_prior_work_map,
    validate_research_scope_spec,
    validate_seed_record,
)
from synaisthesis.storage.artifact_store import ArtifactRecord
from synaisthesis.storage.hashing import sha256_bytes, verify_artifact_hash
from synaisthesis.storage.repositories.event_repository import (
    DomainEventRecord,
    append_domain_event,
)
from synaisthesis.storage.repositories.project_repository import load_project, save_project

SEED_AGGREGATE_TYPE = "Seed"
SPEC_AGGREGATE_TYPE = "NaturalLanguageSpec"
MECHANISM_AGGREGATE_TYPE = "MechanismSketch"
PRIOR_WORK_AGGREGATE_TYPE = "PriorWorkMap"
SCOPE_AGGREGATE_TYPE = "ResearchScopeSpec"
RESEARCH_SPEC_AGGREGATE_TYPE = "ResearchSpec"
S5_AGGREGATE_TYPE = "MinimalCaseBundle"

EVENT_SEED_CAPTURED = "SeedCaptured"
EVENT_SPEC_PROPOSED = "NaturalLanguageSpecProposed"
EVENT_SPEC_CONFIRMED = "NaturalLanguageSpecConfirmed"
EVENT_MECHANISM_SKETCH_PROPOSED = "MechanismSketchProposed"
EVENT_PRIOR_WORK_PROPOSED = "PriorWorkMapProposed"
EVENT_SCOPE_PROPOSED = "ResearchScopeSpecProposed"
EVENT_SCOPE_CONFIRMED = "ResearchScopeSpecConfirmed"
EVENT_RESEARCH_SPEC_BOUND = "ResearchSpecBound"
EVENT_MINIMAL_CASE_PROPOSED = "MinimalCaseProposed"

USER_ACTOR_PROVENANCE = frozenset({ProvenanceType.USER_INPUT, ProvenanceType.USER_DECISION})

S1_HASH_EXCLUDED_FIELDS: set[str] = {"assistant_proposed", "user_confirmed"}
S4_HASH_EXCLUDED_FIELDS: set[str] = {"user_confirmed_scope"}


def _s1_content_hash(spec: NaturalLanguageSpec) -> str:
    """Hash the semantic content of an S1 spec, excluding proposal/confirmation flags."""
    return sha256_hex(spec.model_dump(exclude=S1_HASH_EXCLUDED_FIELDS))


def _s4_content_hash(scope: ResearchScopeSpec) -> str:
    """Hash the semantic content of an S4 scope, excluding the confirmation flag."""
    return sha256_hex(scope.model_dump(exclude=S4_HASH_EXCLUDED_FIELDS))


def _verified_payload(
    session: Session, record: DomainEventRecord, artifact_root: Path
) -> dict[str, Any]:
    """Read and verify a payload artifact; fail closed when it cannot be trusted."""
    if record.event_payload_artifact_id is None:
        raise DomainError(
            f"event {record.id} has no payload artifact; state unrecoverable",
            error_code="ARTIFACT_HASH_MISMATCH",
        )
    artifact = session.get(ArtifactRecord, record.event_payload_artifact_id)
    if artifact is None:
        raise DomainError(
            f"payload artifact {record.event_payload_artifact_id} of event "
            f"{record.id} is missing; state unrecoverable",
            error_code="ARTIFACT_HASH_MISMATCH",
        )
    path = artifact_root / artifact.relative_path
    if not verify_artifact_hash(path, artifact.sha256):
        raise DomainError(
            f"payload artifact of event {record.id} is missing or tampered; state unrecoverable",
            error_code="ARTIFACT_HASH_MISMATCH",
        )
    return json.loads(path.read_text(encoding="utf-8"))


def _event_stream(session: Session, aggregate_type: str, aggregate_id: str):
    return (
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


def _next_sequence(session: Session, aggregate_type: str, aggregate_id: str) -> int:
    return (
        session.execute(
            select(func.count(DomainEventRecord.id)).where(
                DomainEventRecord.aggregate_type == aggregate_type,
                DomainEventRecord.aggregate_id == aggregate_id,
            )
        ).scalar_one()
        + 1
    )


# ---------------------------------------------------------------------------
# S0 — SeedRecord
# ---------------------------------------------------------------------------


def capture_seed(
    session: Session,
    *,
    project_id: str,
    record: SeedRecord,
    artifact_root: Path,
    seed_id: str | None = None,
) -> tuple[SeedRecord, str]:
    """Persist an S0 SeedRecord with its raw-input hash.

    The raw input is always preserved: capture never rejects the record on
    validator issues (the gate reflects them, the raw text is kept verbatim).
    """
    raw_hash = sha256_bytes(record.raw_input.encode("utf-8"))
    event = DomainEvent(
        aggregate_type=SEED_AGGREGATE_TYPE,
        aggregate_id=seed_id or uuid.uuid4().hex,
        event_type=EVENT_SEED_CAPTURED,
        payload={"seed": record.model_dump(), "raw_hash": raw_hash},
        sequence=1,
    )
    append_domain_event(session, event, project_id=project_id, artifact_root=artifact_root)
    return record, raw_hash


def load_seed(session: Session, seed_id: str, *, artifact_root: Path) -> SeedRecord:
    """Replay a SeedRecord and verify that the raw input still hashes to raw_hash."""
    records = _event_stream(session, SEED_AGGREGATE_TYPE, seed_id)
    if not records:
        raise DomainError(f"seed {seed_id!r} has no events", error_code="PROJECT_NOT_FOUND")
    seed: SeedRecord | None = None
    for record in records:
        if record.event_type != EVENT_SEED_CAPTURED:
            raise DomainError(
                f"unknown event type {record.event_type!r} for seed {seed_id!r}; "
                "state unrecoverable",
                error_code="PROJECT_STATE_UNRECOVERABLE",
            )
        payload = _verified_payload(session, record, artifact_root)
        seed = SeedRecord.model_validate(payload["seed"])
        raw_hash = str(payload["raw_hash"])
        if sha256_bytes(seed.raw_input.encode("utf-8")) != raw_hash:
            raise DomainError(
                f"raw_input of seed {seed_id!r} does not match its stored raw_hash",
                error_code="RAW_HASH_MISMATCH",
            )
    if seed is None:
        raise DomainError(
            f"state of seed {seed_id!r} is unrecoverable",
            error_code="PROJECT_STATE_UNRECOVERABLE",
        )
    return seed


# ---------------------------------------------------------------------------
# S1 — NaturalLanguageSpec
# ---------------------------------------------------------------------------


def propose_natural_language_spec(
    session: Session,
    *,
    project_id: str,
    spec: NaturalLanguageSpec,
    artifact_root: Path,
    spec_id: str | None = None,
) -> NaturalLanguageSpec:
    """Persist an assistant-proposed S1 spec (never pre-confirmed)."""
    if spec.user_confirmed:
        raise DomainError(
            "a proposed spec cannot arrive pre-confirmed; confirmation requires a real user event",
            error_code="CONFIRMATION_REQUIRES_USER_EVENT",
        )
    issues = validate_natural_language_spec(spec)
    if issues:
        raise DomainError(
            "S1 output invalid: " + "; ".join(issues),
            error_code="STAGE_OUTPUT_INVALID",
        )
    stored = spec.model_copy(update={"assistant_proposed": True, "user_confirmed": False})
    event = DomainEvent(
        aggregate_type=SPEC_AGGREGATE_TYPE,
        aggregate_id=spec_id or uuid.uuid4().hex,
        event_type=EVENT_SPEC_PROPOSED,
        payload={"spec": stored.model_dump()},
        sequence=1,
    )
    append_domain_event(session, event, project_id=project_id, artifact_root=artifact_root)
    return stored


def confirm_natural_language_spec(
    session: Session,
    *,
    spec_id: str,
    actor: ProvenanceType,
    user_event_id: str,
    artifact_root: Path,
) -> NaturalLanguageSpec:
    """Confirm an S1 spec; only a real user event may confirm (03 S1, 07 §2)."""
    if actor not in USER_ACTOR_PROVENANCE:
        raise DomainError(
            f"confirmation requires a real user event; got actor={actor.value}",
            error_code="CONFIRMATION_REQUIRES_USER_EVENT",
        )
    spec = load_natural_language_spec(session, spec_id, artifact_root=artifact_root)
    if spec.user_confirmed:
        raise DomainError(
            f"spec {spec_id!r} is already confirmed",
            error_code="CONFLICT",
        )
    event = DomainEvent(
        aggregate_type=SPEC_AGGREGATE_TYPE,
        aggregate_id=spec_id,
        event_type=EVENT_SPEC_CONFIRMED,
        payload={
            "spec_id": spec_id,
            "actor": actor.value,
            "user_event_id": user_event_id,
            "confirmed_at": datetime.now(UTC).isoformat(),
        },
        sequence=_next_sequence(session, SPEC_AGGREGATE_TYPE, spec_id),
    )
    records = _event_stream(session, SPEC_AGGREGATE_TYPE, spec_id)
    project_id = records[0].project_id if records else None
    append_domain_event(session, event, project_id=project_id, artifact_root=artifact_root)
    return spec.model_copy(update={"user_confirmed": True})


def load_natural_language_spec(
    session: Session, spec_id: str, *, artifact_root: Path
) -> NaturalLanguageSpec:
    """Replay an S1 spec; user_confirmed is True only via a valid user event."""
    records = _event_stream(session, SPEC_AGGREGATE_TYPE, spec_id)
    if not records:
        raise DomainError(f"spec {spec_id!r} has no events", error_code="PROJECT_NOT_FOUND")
    spec: NaturalLanguageSpec | None = None
    for record in records:
        payload = _verified_payload(session, record, artifact_root)
        if record.event_type == EVENT_SPEC_PROPOSED:
            spec = NaturalLanguageSpec.model_validate(payload["spec"])
        elif record.event_type == EVENT_SPEC_CONFIRMED:
            if spec is None:
                raise DomainError(
                    f"event stream of {spec_id!r} starts with {record.event_type!r}; "
                    "state unrecoverable",
                    error_code="PROJECT_STATE_UNRECOVERABLE",
                )
            actor = ProvenanceType.parse(payload["actor"], field="actor")
            if actor not in USER_ACTOR_PROVENANCE:
                raise DomainError(
                    f"confirmation provenance of {spec_id!r} is not a user event",
                    error_code="INVALID_CONFIRMATION_PROVENANCE",
                )
            spec = spec.model_copy(update={"user_confirmed": True})
        else:
            raise DomainError(
                f"unknown event type {record.event_type!r} for {spec_id!r}; state unrecoverable",
                error_code="PROJECT_STATE_UNRECOVERABLE",
            )
    if spec is None:
        raise DomainError(
            f"state of {spec_id!r} is unrecoverable",
            error_code="PROJECT_STATE_UNRECOVERABLE",
        )
    return spec


# ---------------------------------------------------------------------------
# S2 — MechanismSketch
# ---------------------------------------------------------------------------


def propose_mechanism_sketch(
    session: Session,
    *,
    project_id: str,
    sketch: MechanismSketch,
    artifact_root: Path,
    sketch_id: str | None = None,
) -> MechanismSketch:
    """Persist an S2 MechanismSketch; invalid output never reaches the store."""
    issues = validate_mechanism_sketch(sketch)
    if issues:
        raise DomainError(
            "S2 output invalid: " + "; ".join(issues),
            error_code="STAGE_OUTPUT_INVALID",
        )
    event = DomainEvent(
        aggregate_type=MECHANISM_AGGREGATE_TYPE,
        aggregate_id=sketch_id or uuid.uuid4().hex,
        event_type=EVENT_MECHANISM_SKETCH_PROPOSED,
        payload={"mechanism_sketch": sketch.model_dump()},
        sequence=1,
    )
    append_domain_event(session, event, project_id=project_id, artifact_root=artifact_root)
    return sketch


def load_mechanism_sketch(
    session: Session, sketch_id: str, *, artifact_root: Path
) -> MechanismSketch:
    """Replay an S2 MechanismSketch from its hash-verified event payloads."""
    records = _event_stream(session, MECHANISM_AGGREGATE_TYPE, sketch_id)
    if not records:
        raise DomainError(
            f"mechanism sketch {sketch_id!r} has no events",
            error_code="PROJECT_NOT_FOUND",
        )
    sketch: MechanismSketch | None = None
    for record in records:
        payload = _verified_payload(session, record, artifact_root)
        if record.event_type != EVENT_MECHANISM_SKETCH_PROPOSED:
            raise DomainError(
                f"unknown event type {record.event_type!r} for mechanism sketch "
                f"{sketch_id!r}; state unrecoverable",
                error_code="PROJECT_STATE_UNRECOVERABLE",
            )
        sketch = MechanismSketch.model_validate(payload["mechanism_sketch"])
    if sketch is None:
        raise DomainError(
            f"state of mechanism sketch {sketch_id!r} is unrecoverable",
            error_code="PROJECT_STATE_UNRECOVERABLE",
        )
    return sketch


# ---------------------------------------------------------------------------
# S3 — PriorWorkMap
# ---------------------------------------------------------------------------


def propose_prior_work_map(
    session: Session,
    *,
    project_id: str,
    prior_work: PriorWorkMap,
    artifact_root: Path,
    prior_work_id: str | None = None,
) -> PriorWorkMap:
    """Persist an S3 PriorWorkMap; both academic and engineering seeds are required."""
    issues = validate_prior_work_map(prior_work)
    if issues:
        raise DomainError(
            "S3 output invalid: " + "; ".join(issues),
            error_code="STAGE_OUTPUT_INVALID",
        )
    event = DomainEvent(
        aggregate_type=PRIOR_WORK_AGGREGATE_TYPE,
        aggregate_id=prior_work_id or uuid.uuid4().hex,
        event_type=EVENT_PRIOR_WORK_PROPOSED,
        payload={"prior_work_map": prior_work.model_dump()},
        sequence=1,
    )
    append_domain_event(session, event, project_id=project_id, artifact_root=artifact_root)
    return prior_work


def load_prior_work_map(
    session: Session, prior_work_id: str, *, artifact_root: Path
) -> PriorWorkMap:
    """Replay an S3 PriorWorkMap from its hash-verified event payloads."""
    records = _event_stream(session, PRIOR_WORK_AGGREGATE_TYPE, prior_work_id)
    if not records:
        raise DomainError(
            f"prior work map {prior_work_id!r} has no events",
            error_code="PROJECT_NOT_FOUND",
        )
    prior_work: PriorWorkMap | None = None
    for record in records:
        payload = _verified_payload(session, record, artifact_root)
        if record.event_type != EVENT_PRIOR_WORK_PROPOSED:
            raise DomainError(
                f"unknown event type {record.event_type!r} for prior work map "
                f"{prior_work_id!r}; state unrecoverable",
                error_code="PROJECT_STATE_UNRECOVERABLE",
            )
        prior_work = PriorWorkMap.model_validate(payload["prior_work_map"])
    if prior_work is None:
        raise DomainError(
            f"state of prior work map {prior_work_id!r} is unrecoverable",
            error_code="PROJECT_STATE_UNRECOVERABLE",
        )
    return prior_work


# ---------------------------------------------------------------------------
# S4 — ResearchScopeSpec
# ---------------------------------------------------------------------------


def propose_research_scope_spec(
    session: Session,
    *,
    project_id: str,
    scope: ResearchScopeSpec,
    artifact_root: Path,
    scope_id: str | None = None,
) -> ResearchScopeSpec:
    """Persist an assistant-proposed S4 scope (never pre-confirmed)."""
    if scope.user_confirmed_scope:
        raise DomainError(
            "a proposed scope cannot arrive pre-confirmed; confirmation requires a real user event",
            error_code="CONFIRMATION_REQUIRES_USER_EVENT",
        )
    issues = validate_research_scope_spec(scope)
    if issues:
        raise DomainError(
            "S4 output invalid: " + "; ".join(issues),
            error_code="STAGE_OUTPUT_INVALID",
        )
    stored = scope.model_copy(update={"user_confirmed_scope": False})
    event = DomainEvent(
        aggregate_type=SCOPE_AGGREGATE_TYPE,
        aggregate_id=scope_id or uuid.uuid4().hex,
        event_type=EVENT_SCOPE_PROPOSED,
        payload={"scope": stored.model_dump()},
        sequence=1,
    )
    append_domain_event(session, event, project_id=project_id, artifact_root=artifact_root)
    return stored


def load_research_scope_spec(
    session: Session, scope_id: str, *, artifact_root: Path
) -> ResearchScopeSpec:
    """Replay an S4 scope; user_confirmed_scope only via a valid user event."""
    records = _event_stream(session, SCOPE_AGGREGATE_TYPE, scope_id)
    if not records:
        raise DomainError(
            f"research scope spec {scope_id!r} has no events",
            error_code="PROJECT_NOT_FOUND",
        )
    scope: ResearchScopeSpec | None = None
    for record in records:
        payload = _verified_payload(session, record, artifact_root)
        if record.event_type == EVENT_SCOPE_PROPOSED:
            scope = ResearchScopeSpec.model_validate(payload["scope"])
        elif record.event_type == EVENT_SCOPE_CONFIRMED:
            if scope is None:
                raise DomainError(
                    f"event stream of {scope_id!r} starts with {record.event_type!r}; "
                    "state unrecoverable",
                    error_code="PROJECT_STATE_UNRECOVERABLE",
                )
            actor = ProvenanceType.parse(payload["actor"], field="actor")
            if actor not in USER_ACTOR_PROVENANCE:
                raise DomainError(
                    f"confirmation provenance of {scope_id!r} is not a user event",
                    error_code="INVALID_CONFIRMATION_PROVENANCE",
                )
            scope_hash = payload.get("scope_hash")
            if not isinstance(scope_hash, str) or not scope_hash:
                raise DomainError(
                    f"confirmation event of {scope_id!r} does not bind scope_hash",
                    error_code="PROJECT_STATE_UNRECOVERABLE",
                )
            if _s4_content_hash(scope) != scope_hash:
                raise DomainError(
                    f"scope_hash of {scope_id!r} does not match the current artifact",
                    error_code="CONTENT_HASH_MISMATCH",
                )
            scope = scope.model_copy(update={"user_confirmed_scope": True})
        else:
            raise DomainError(
                f"unknown event type {record.event_type!r} for {scope_id!r}; state unrecoverable",
                error_code="PROJECT_STATE_UNRECOVERABLE",
            )
    if scope is None:
        raise DomainError(
            f"state of {scope_id!r} is unrecoverable",
            error_code="PROJECT_STATE_UNRECOVERABLE",
        )
    return scope


def confirm_research_scope_spec(
    session: Session,
    *,
    scope_id: str,
    s1_spec_id: str,
    actor: ProvenanceType,
    user_event_id: str,
    artifact_root: Path,
    research_spec_id: str | None = None,
) -> ResearchScopeSpec:
    """Confirm an S4 scope; bind the current S1/S4 hashes and content_hash.

    The S1 spec must already be user-confirmed. The confirmation provenance is
    persisted on the scope event, and a ResearchSpecBound event makes the
    S1/S4 hash binding durable without adding a new table (event-sourced).
    """
    if actor not in USER_ACTOR_PROVENANCE:
        raise DomainError(
            f"confirmation requires a real user event; got actor={actor.value}",
            error_code="CONFIRMATION_REQUIRES_USER_EVENT",
        )
    scope = load_research_scope_spec(session, scope_id, artifact_root=artifact_root)
    if scope.user_confirmed_scope:
        raise DomainError(
            f"research scope spec {scope_id!r} is already confirmed",
            error_code="CONFLICT",
        )
    spec = load_natural_language_spec(session, s1_spec_id, artifact_root=artifact_root)
    if not spec.user_confirmed:
        raise DomainError(
            f"S1 spec {s1_spec_id!r} must be user-confirmed before S4 confirmation",
            error_code="CONFIRMATION_REQUIRES_USER_EVENT",
        )

    s1_hash = _s1_content_hash(spec)
    scope_hash = _s4_content_hash(scope)
    confirmed_at = datetime.now(UTC)
    confirmed_event = DomainEvent(
        aggregate_type=SCOPE_AGGREGATE_TYPE,
        aggregate_id=scope_id,
        event_type=EVENT_SCOPE_CONFIRMED,
        payload={
            "scope_id": scope_id,
            "actor": actor.value,
            "user_event_id": user_event_id,
            "confirmed_at": confirmed_at.isoformat(),
            "scope_hash": scope_hash,
            "s1_spec_id": s1_spec_id,
            "s1_hash": s1_hash,
        },
        sequence=_next_sequence(session, SCOPE_AGGREGATE_TYPE, scope_id),
    )
    scope_records = _event_stream(session, SCOPE_AGGREGATE_TYPE, scope_id)
    project_id = scope_records[0].project_id if scope_records else None
    append_domain_event(
        session,
        confirmed_event,
        project_id=project_id,
        artifact_root=artifact_root,
    )

    binding_id = research_spec_id or uuid.uuid4().hex
    binding_sequence = _next_sequence(session, RESEARCH_SPEC_AGGREGATE_TYPE, binding_id)
    research_spec = ResearchSpec(
        project_id=project_id or "",
        version=binding_sequence,
        s1_natural_language_spec=spec.model_dump(exclude=S1_HASH_EXCLUDED_FIELDS),
        s4_scope_spec=scope.model_dump(exclude=S4_HASH_EXCLUDED_FIELDS),
        user_confirmed=True,
        confirmed_at=confirmed_at,
    )
    binding_event = DomainEvent(
        aggregate_type=RESEARCH_SPEC_AGGREGATE_TYPE,
        aggregate_id=binding_id,
        event_type=EVENT_RESEARCH_SPEC_BOUND,
        payload={
            "version": binding_sequence,
            "s1_spec_id": s1_spec_id,
            "scope_id": scope_id,
            "s1_hash": s1_hash,
            "scope_hash": scope_hash,
            "content_hash": research_spec.content_hash,
            "user_confirmed": True,
            "bound_at": confirmed_at.isoformat(),
        },
        sequence=binding_sequence,
    )
    append_domain_event(
        session,
        binding_event,
        project_id=project_id,
        artifact_root=artifact_root,
    )
    return scope.model_copy(update={"user_confirmed_scope": True})


def _latest_research_spec_binding(
    session: Session,
    *,
    s1_spec_id: str,
    scope_id: str,
    artifact_root: Path,
) -> dict[str, Any] | None:
    """Return the latest ResearchSpecBound payload binding the S1/S4 pair."""
    records = (
        session.execute(
            select(DomainEventRecord)
            .where(
                DomainEventRecord.aggregate_type == RESEARCH_SPEC_AGGREGATE_TYPE,
                DomainEventRecord.event_type == EVENT_RESEARCH_SPEC_BOUND,
            )
            .order_by(DomainEventRecord.id.desc())
        )
        .scalars()
        .all()
    )
    for record in records:
        payload = _verified_payload(session, record, artifact_root)
        if payload.get("s1_spec_id") == s1_spec_id and payload.get("scope_id") == scope_id:
            return payload
    return None


# ---------------------------------------------------------------------------
# Gate evaluation
# ---------------------------------------------------------------------------


def validate_stage_output(stage_id: StageId, output: Any) -> tuple[str, ...]:
    """Run the schema-independent business validators for a stage output."""
    if stage_id is StageId.S0:
        return validate_seed_record(output)
    if stage_id is StageId.S1:
        return validate_natural_language_spec(output)
    if stage_id is StageId.S2:
        return validate_mechanism_sketch(output)
    if stage_id is StageId.S3:
        return validate_prior_work_map(output)
    if stage_id is StageId.S4:
        return validate_research_scope_spec(output)
    return (f"unknown stage {stage_id.value}",)


def evaluate_stage_gate(
    stage_id: StageId, *, output: Any = None, confirmed: bool = False
) -> StageGateStatus:
    """Compute PASS/PARTIAL/BLOCKED/NOT_TESTED from Schema + validators + confirmation.

    Mapping (documented in the M2.1/M2.2 WorkUnitContracts): no output ->
    NOT_TESTED; wrong output type -> BLOCKED; validator issues or missing S1
    user confirmation -> PARTIAL; clean validators and (S1: confirmed) -> PASS.
    S4 stage PASS does not require scope confirmation; the completion gate
    NATURAL_LANGUAGE_DESIGN_READY does.
    """
    if output is None:
        return StageGateStatus.NOT_TESTED
    if stage_id is StageId.S0:
        if not isinstance(output, SeedRecord):
            return StageGateStatus.BLOCKED
        return StageGateStatus.PASS if not validate_seed_record(output) else StageGateStatus.PARTIAL
    if stage_id is StageId.S1:
        if not isinstance(output, NaturalLanguageSpec):
            return StageGateStatus.BLOCKED
        if validate_natural_language_spec(output):
            return StageGateStatus.PARTIAL
        return StageGateStatus.PASS if confirmed else StageGateStatus.PARTIAL
    if stage_id is StageId.S2:
        if not isinstance(output, MechanismSketch):
            return StageGateStatus.BLOCKED
        return (
            StageGateStatus.PASS
            if not validate_mechanism_sketch(output)
            else StageGateStatus.PARTIAL
        )
    if stage_id is StageId.S3:
        if not isinstance(output, PriorWorkMap):
            return StageGateStatus.BLOCKED
        return (
            StageGateStatus.PASS if not validate_prior_work_map(output) else StageGateStatus.PARTIAL
        )
    if stage_id is StageId.S4:
        if not isinstance(output, ResearchScopeSpec):
            return StageGateStatus.BLOCKED
        return (
            StageGateStatus.PASS
            if not validate_research_scope_spec(output)
            else StageGateStatus.PARTIAL
        )
    return StageGateStatus.BLOCKED


# ---------------------------------------------------------------------------
# NATURAL_LANGUAGE_DESIGN_READY
# ---------------------------------------------------------------------------


def evaluate_natural_language_design_ready(
    *,
    seed: SeedRecord | None,
    spec: NaturalLanguageSpec | None,
    mechanism: MechanismSketch | None,
    prior_work: PriorWorkMap | None,
    scope: ResearchScopeSpec | None,
    s1_hash: str | None,
    s4_hash: str | None,
) -> tuple[StageGateStatus, tuple[str, ...]]:
    """Compute the natural-language design completion gate (03/03A).

    PASS requires S0–S4 stage gates all PASS, S1 and S4 user-confirmed, the
    five critical application fields present, no unresolved ambiguous terms,
    and S1/S4 hashes bound to the exact current artifacts.
    """
    outputs = (
        ("S0", StageId.S0, seed),
        ("S1", StageId.S1, spec),
        ("S2", StageId.S2, mechanism),
        ("S3", StageId.S3, prior_work),
        ("S4", StageId.S4, scope),
    )
    missing = [label for label, _, output in outputs if output is None]
    if missing:
        return StageGateStatus.NOT_TESTED, tuple(f"{label} Artifact 缺失" for label in missing)
    assert spec is not None
    assert scope is not None

    stage_gates: dict[str, StageGateStatus] = {}
    issues: list[str] = []
    for label, stage_id, output in outputs:
        if stage_id is StageId.S1:
            gate = evaluate_stage_gate(stage_id, output=output, confirmed=bool(spec.user_confirmed))
        else:
            gate = evaluate_stage_gate(stage_id, output=output)
        stage_gates[label] = gate
        if gate is StageGateStatus.BLOCKED:
            issues.append(f"{label} Gate 为 BLOCKED")
        elif gate is StageGateStatus.PARTIAL:
            issues.append(f"{label} Gate 为 PARTIAL")
        elif gate is StageGateStatus.NOT_TESTED:
            issues.append(f"{label} Gate 为 NOT_TESTED")

    if s1_hash is None or s4_hash is None:
        return StageGateStatus.BLOCKED, ("S1/S4 hash 未绑定",)
    if _s1_content_hash(spec) != s1_hash:
        return StageGateStatus.BLOCKED, ("S1 hash 与当前 Artifact 不一致",)
    if _s4_content_hash(scope) != s4_hash:
        return StageGateStatus.BLOCKED, ("S4 hash 与当前 Artifact 不一致",)

    if not spec.user_confirmed:
        issues.append("S1 尚未由真实用户事件确认")
    if not scope.user_confirmed_scope:
        issues.append("S4 尚未由真实用户事件确认")
    for field, label in (
        ("expected_functions", "expected_functions"),
        ("target_applications", "target_applications"),
        ("intended_users", "intended_users"),
        ("operational_constraints", "operational_constraints"),
        ("success_metrics", "success_metrics"),
    ):
        values = getattr(spec, field, None)
        if not isinstance(values, (list, tuple)) or len(values) < 1:
            issues.append(f"{label} 不能为空")
    if spec.ambiguous_terms:
        issues.append("存在未解决的 Critical 歧义（ambiguous_terms 非空）")

    if issues:
        if any(gate is StageGateStatus.BLOCKED for gate in stage_gates.values()):
            return StageGateStatus.BLOCKED, tuple(issues)
        if any(gate is StageGateStatus.NOT_TESTED for gate in stage_gates.values()):
            return StageGateStatus.NOT_TESTED, tuple(issues)
        return StageGateStatus.PARTIAL, tuple(issues)
    return StageGateStatus.PASS, ()


def evaluate_natural_language_design_ready_from_events(
    session: Session,
    *,
    seed_id: str,
    spec_id: str,
    mechanism_id: str,
    prior_work_id: str,
    scope_id: str,
    artifact_root: Path,
) -> tuple[StageGateStatus, tuple[str, ...]]:
    """Replay S0–S4 and the S1/S4 hash binding, then compute the design gate."""
    seed = load_seed(session, seed_id, artifact_root=artifact_root)
    spec = load_natural_language_spec(session, spec_id, artifact_root=artifact_root)
    mechanism = load_mechanism_sketch(session, mechanism_id, artifact_root=artifact_root)
    prior_work = load_prior_work_map(session, prior_work_id, artifact_root=artifact_root)
    scope = load_research_scope_spec(session, scope_id, artifact_root=artifact_root)
    binding = _latest_research_spec_binding(
        session,
        s1_spec_id=spec_id,
        scope_id=scope_id,
        artifact_root=artifact_root,
    )
    return evaluate_natural_language_design_ready(
        seed=seed,
        spec=spec,
        mechanism=mechanism,
        prior_work=prior_work,
        scope=scope,
        s1_hash=str(binding["s1_hash"]) if binding else None,
        s4_hash=str(binding["scope_hash"]) if binding else None,
    )


def derive_natural_language_design_ready(
    session: Session,
    *,
    project_id: str,
    seed_id: str,
    spec_id: str,
    mechanism_id: str,
    prior_work_id: str,
    scope_id: str,
    artifact_root: Path,
) -> tuple[StageGateStatus, tuple[str, ...]]:
    """Compute the design gate and persist a PASS as a Project lifecycle event.

    A non-PASS result never mutates project state. PASS appends one
    ProjectLifecycleChanged event (existing M1.4 event type) unless the
    project is already NATURAL_LANGUAGE_DESIGN_READY.
    """
    status, issues = evaluate_natural_language_design_ready_from_events(
        session,
        seed_id=seed_id,
        spec_id=spec_id,
        mechanism_id=mechanism_id,
        prior_work_id=prior_work_id,
        scope_id=scope_id,
        artifact_root=artifact_root,
    )
    if status is not StageGateStatus.PASS:
        return status, issues

    project = load_project(session, project_id, artifact_root=artifact_root)
    if project.lifecycle_status is not ProjectLifecycleStatus.NATURAL_LANGUAGE_DESIGN_READY:
        project = project.change_lifecycle(ProjectLifecycleStatus.NATURAL_LANGUAGE_DESIGN_READY)
        save_project(session, project, artifact_root=artifact_root)
    return status, issues


def propose_minimal_case_bundle(
    session: Session,
    *,
    project_id: str,
    bundle: MinimalCaseBundle,
    qualification_route: ResearchRoute,
    novelty_status: NoveltyStatus,
    qualification_review_hash: str,
    override: LowNoveltyOverride | None = None,
    artifact_root: Path,
    bundle_id: str | None = None,
) -> MinimalCaseBundle:
    """Persist S5 only after RQ4M qualification; no path may bypass RQ3/RQ4."""
    target = qualification_next_target(
        route=qualification_route,
        novelty_status=novelty_status,
        override=override,
        review_artifact_hash=qualification_review_hash,
    )
    if target is not QualifiedNextTarget.S5:
        raise DomainError(
            f"qualified target {target.value} is not S5",
            error_code="EARLY_QUALIFICATION_REQUIRED",
        )
    if bundle.actually_executed and not bundle.execution_receipt_id:
        raise DomainError(
            "actually_executed=true requires execution_receipt_id",
            error_code="EXECUTION_RECEIPT_REQUIRED",
        )
    event = DomainEvent(
        aggregate_type=S5_AGGREGATE_TYPE,
        aggregate_id=bundle_id or uuid.uuid4().hex,
        event_type=EVENT_MINIMAL_CASE_PROPOSED,
        payload={"minimal_case": bundle.model_dump()},
        sequence=1,
    )
    append_domain_event(session, event, project_id=project_id, artifact_root=artifact_root)
    return bundle


def load_minimal_case_bundle(
    session: Session, bundle_id: str, *, artifact_root: Path
) -> MinimalCaseBundle:
    """Replay an S5 MinimalCaseBundle from its hash-verified event payload."""
    records = _event_stream(session, S5_AGGREGATE_TYPE, bundle_id)
    if not records:
        raise DomainError(
            f"minimal case bundle {bundle_id!r} has no events",
            error_code="PROJECT_NOT_FOUND",
        )
    bundle: MinimalCaseBundle | None = None
    for record in records:
        payload = _verified_payload(session, record, artifact_root)
        if record.event_type != EVENT_MINIMAL_CASE_PROPOSED:
            raise DomainError(
                f"unknown event type {record.event_type!r} for {bundle_id!r}; state unrecoverable",
                error_code="PROJECT_STATE_UNRECOVERABLE",
            )
        bundle = MinimalCaseBundle.model_validate(payload["minimal_case"])
    if bundle is None:
        raise DomainError(
            f"state of {bundle_id!r} is unrecoverable",
            error_code="PROJECT_STATE_UNRECOVERABLE",
        )
    return bundle


__all__ = [
    "capture_seed",
    "confirm_natural_language_spec",
    "confirm_research_scope_spec",
    "derive_natural_language_design_ready",
    "evaluate_natural_language_design_ready",
    "evaluate_natural_language_design_ready_from_events",
    "evaluate_stage_gate",
    "load_mechanism_sketch",
    "load_natural_language_spec",
    "load_prior_work_map",
    "load_research_scope_spec",
    "load_minimal_case_bundle",
    "load_seed",
    "propose_minimal_case_bundle",
    "propose_mechanism_sketch",
    "propose_natural_language_spec",
    "propose_prior_work_map",
    "propose_research_scope_spec",
    "validate_stage_output",
]
