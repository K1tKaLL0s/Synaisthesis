"""Incubation application service for S0/S1 (blueprint 07 section 2, M2.1).

S0 raw input is persisted with its re-computable SHA-256 and never silently
rewritten. S1 specs are proposed by the assistant and can only be confirmed
by a real user event; the confirming provenance is persisted with the event.
Persistence reuses the M1.4 event-sourced pattern: ordered DomainEvents whose
canonical JSON payloads live in content-addressed artifacts.
"""

from __future__ import annotations

import json
import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from synaisthesis.agents.schemas import NaturalLanguageSpec, SeedRecord
from synaisthesis.domain.enums import ProvenanceType, StageGateStatus, StageId
from synaisthesis.domain.errors import DomainError
from synaisthesis.domain.event import DomainEvent
from synaisthesis.domain.stage import (
    validate_natural_language_spec,
    validate_seed_record,
)
from synaisthesis.storage.artifact_store import ArtifactRecord
from synaisthesis.storage.hashing import sha256_bytes, verify_artifact_hash
from synaisthesis.storage.repositories.event_repository import (
    DomainEventRecord,
    append_domain_event,
)

SEED_AGGREGATE_TYPE = "Seed"
SPEC_AGGREGATE_TYPE = "NaturalLanguageSpec"
EVENT_SEED_CAPTURED = "SeedCaptured"
EVENT_SPEC_PROPOSED = "NaturalLanguageSpecProposed"
EVENT_SPEC_CONFIRMED = "NaturalLanguageSpecConfirmed"

USER_ACTOR_PROVENANCE = frozenset({ProvenanceType.USER_INPUT, ProvenanceType.USER_DECISION})


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
# Gate evaluation
# ---------------------------------------------------------------------------


def validate_stage_output(stage_id: StageId, output: Any) -> tuple[str, ...]:
    """Run the schema-independent business validators for a stage output."""
    if stage_id is StageId.S0:
        return validate_seed_record(output)
    if stage_id is StageId.S1:
        return validate_natural_language_spec(output)
    return (f"unknown stage {stage_id.value}",)


def evaluate_stage_gate(
    stage_id: StageId, *, output: Any = None, confirmed: bool = False
) -> StageGateStatus:
    """Compute PASS/PARTIAL/BLOCKED/NOT_TESTED from Schema + validators + confirmation.

    Mapping (documented in the M2.1 WorkUnitContract): no output -> NOT_TESTED;
    wrong output type -> BLOCKED; validator issues or missing S1 user
    confirmation -> PARTIAL; clean validators and (S1: confirmed) -> PASS.
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
    return StageGateStatus.BLOCKED


__all__ = [
    "confirm_natural_language_spec",
    "capture_seed",
    "evaluate_stage_gate",
    "load_natural_language_spec",
    "load_seed",
    "propose_natural_language_spec",
    "validate_stage_output",
]
