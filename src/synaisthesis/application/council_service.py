"""Council role isolation service (blueprint 04 §3, 08 §3/§4/§7; M6.2).

Event-sourced run/round base, role-session registration and visibility-bundle
issuance/verification. Persistence reuses the M1.4 pattern: ordered
DomainEvents whose canonical JSON payloads live in content-addressed
artifacts, reloaded into identical domain objects via ``rebuild_dataclass``.

The round state machine (effective-round counting, stability, checkpointing)
is M7.1 and is intentionally out of scope here: ``create_council_round`` only
registers the round base with ``valid=False``.
"""

from __future__ import annotations

import json
import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from synaisthesis.application.engineering_design_service import rebuild_dataclass
from synaisthesis.domain.errors import DomainError
from synaisthesis.domain.event import sha256_hex
from synaisthesis.domain.isolation import (
    EVENT_COUNCIL_ROUND_STARTED,
    EVENT_COUNCIL_RUN_CREATED,
    EVENT_ROLE_SESSION_REGISTERED,
    EVENT_VISIBILITY_BUNDLE_ISSUED,
    CouncilRole,
    CouncilRound,
    CouncilRun,
    IsolationLevel,
    ModelFamilyFingerprint,
    RoleSession,
    UntrustedExternalText,
    VisibilityBundle,
    assert_visibility_scope,
    build_council_event,
)
from synaisthesis.storage.artifact_store import ArtifactRecord
from synaisthesis.storage.hashing import verify_artifact_hash
from synaisthesis.storage.repositories.event_repository import (
    DomainEventRecord,
    append_domain_event,
)

COUNCIL_RUN_AGGREGATE_TYPE = "CouncilRun"
COUNCIL_ROUND_AGGREGATE_TYPE = "CouncilRound"
ROLE_SESSION_AGGREGATE_TYPE = "RoleSession"
VISIBILITY_BUNDLE_AGGREGATE_TYPE = "VisibilityBundle"


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


def _persist_council_event(
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
    event = build_council_event(
        event_type,
        aggregate_type=aggregate_type,
        aggregate_id=aggregate_id,
        payload=payload,
        sequence=len(stream) + 1,
    )
    append_domain_event(session, event, project_id=project_id, artifact_root=artifact_root)


# ---------------------------------------------------------------------------
# Run / round base
# ---------------------------------------------------------------------------


def create_council_run(
    session: Session,
    *,
    project_id: str,
    claim_contract_id: str,
    configured_rounds: int,
    primary_model_profile_id: str,
    auditor_model_profile_id: str,
    delegation_policy_id: str,
    budget_policy_id: str,
    artifact_root: Path,
    run_id: str | None = None,
) -> CouncilRun:
    """Open a council run base; round transitions belong to M7.1."""
    run = CouncilRun(
        run_id=run_id or f"run-{uuid.uuid4().hex[:12]}",
        claim_contract_id=claim_contract_id,
        configured_rounds=configured_rounds,
        primary_model_profile_id=primary_model_profile_id,
        auditor_model_profile_id=auditor_model_profile_id,
        delegation_policy_id=delegation_policy_id,
        budget_policy_id=budget_policy_id,
        started_at=datetime.now(UTC),
    )
    _persist_council_event(
        session,
        event_type=EVENT_COUNCIL_RUN_CREATED,
        aggregate_type=COUNCIL_RUN_AGGREGATE_TYPE,
        aggregate_id=run.run_id,
        payload={"run": run.to_event_payload()},
        project_id=project_id,
        artifact_root=artifact_root,
    )
    return run


def create_council_round(
    session: Session,
    *,
    project_id: str,
    run_id: str,
    round_number: int,
    artifact_root: Path,
    round_id: str | None = None,
) -> CouncilRound:
    """Register a round base; ``valid`` is left for M7.1's effective-round rules."""
    round_record = CouncilRound(
        round_id=round_id or f"round-{uuid.uuid4().hex[:12]}",
        run_id=run_id,
        round_number=round_number,
    )
    _persist_council_event(
        session,
        event_type=EVENT_COUNCIL_ROUND_STARTED,
        aggregate_type=COUNCIL_ROUND_AGGREGATE_TYPE,
        aggregate_id=round_record.round_id,
        payload={"round": round_record.to_event_payload()},
        project_id=project_id,
        artifact_root=artifact_root,
    )
    return round_record


# ---------------------------------------------------------------------------
# Role session registration
# ---------------------------------------------------------------------------


def register_role_session(
    session: Session,
    *,
    project_id: str,
    run_id: str,
    role: CouncilRole,
    model_profile_id: str,
    visibility_policy_id: str,
    isolation_level: IsolationLevel,
    model_fingerprint: ModelFamilyFingerprint,
    artifact_root: Path,
    round_id: str | None = None,
    role_session_id: str | None = None,
) -> RoleSession:
    """Register one isolated role session; below-SESSION tracks fail closed."""
    role_session = RoleSession(
        role_session_id=role_session_id or f"rs-{uuid.uuid4().hex[:12]}",
        run_id=run_id,
        role=role,
        model_profile_id=model_profile_id,
        visibility_policy_id=visibility_policy_id,
        isolation_level=isolation_level,
        model_fingerprint=model_fingerprint,
        round_id=round_id,
    )
    _persist_council_event(
        session,
        event_type=EVENT_ROLE_SESSION_REGISTERED,
        aggregate_type=ROLE_SESSION_AGGREGATE_TYPE,
        aggregate_id=role_session.role_session_id,
        payload={"role_session": role_session.to_event_payload()},
        project_id=project_id,
        artifact_root=artifact_root,
    )
    return role_session


# ---------------------------------------------------------------------------
# Visibility bundle issuance / verification
# ---------------------------------------------------------------------------


def issue_visibility_bundle(
    session: Session,
    *,
    project_id: str,
    run_id: str,
    role: CouncilRole,
    session_id: str,
    content: str,
    source_receipt: str,
    isolation_level: IsolationLevel,
    artifact_root: Path,
    phase: str = "A",
    external_texts: tuple[UntrustedExternalText, ...] = (),
    bundle_id: str | None = None,
) -> VisibilityBundle:
    """Seal a Phase-A envelope addressed to one role session.

    External text is quarantined (kept separate from the trusted ``content``)
    and injected instructions block issuance with ``SECURITY_FINDING``.
    """
    bundle = VisibilityBundle(
        bundle_id=bundle_id or f"vb-{uuid.uuid4().hex[:12]}",
        run_id=run_id,
        role=role,
        session_id=session_id,
        phase=phase,
        content=content,
        content_hash=sha256_hex(content),
        source_receipt=source_receipt,
        isolation_level=isolation_level,
        external_texts=external_texts,
        issued_at=datetime.now(UTC),
    )
    _persist_council_event(
        session,
        event_type=EVENT_VISIBILITY_BUNDLE_ISSUED,
        aggregate_type=VISIBILITY_BUNDLE_AGGREGATE_TYPE,
        aggregate_id=bundle.bundle_id,
        payload={"bundle": bundle.to_event_payload()},
        project_id=project_id,
        artifact_root=artifact_root,
    )
    return bundle


def verify_visibility_bundle(
    bundle: VisibilityBundle,
    *,
    content: str,
    consumer_role: CouncilRole,
    consumer_session_id: str,
) -> tuple[str, ...]:
    """Return blockers; empty means the consumer may trust and read the bundle.

    Checks the source seal (``bundle_hash``), the caller-provided content hash,
    and the (role, session) visibility scope. Any mismatch blocks.
    """
    blockers = list(bundle.verify_integrity())
    if sha256_hex(content) != bundle.content_hash:
        blockers.append("content 与 bundle.content_hash 不一致")
    blockers.extend(
        assert_visibility_scope(
            bundle=bundle,
            consumer_role=consumer_role,
            consumer_session_id=consumer_session_id,
        )
    )
    return tuple(blockers)


# ---------------------------------------------------------------------------
# Event-sourced loaders
# ---------------------------------------------------------------------------


def load_council_run(session: Session, run_id: str, *, artifact_root: Path) -> CouncilRun:
    records = _event_stream(session, COUNCIL_RUN_AGGREGATE_TYPE, run_id)
    if not records:
        raise DomainError(f"council run {run_id!r} has no events", error_code="PROJECT_NOT_FOUND")
    run: CouncilRun | None = None
    for record in records:
        payload = _verified_payload(session, record, artifact_root)
        if record.event_type == EVENT_COUNCIL_RUN_CREATED:
            run = rebuild_dataclass(CouncilRun, payload["run"])
    if run is None:
        raise DomainError(
            f"state of council run {run_id!r} is unrecoverable",
            error_code="PROJECT_STATE_UNRECOVERABLE",
        )
    return run


def load_council_round(session: Session, round_id: str, *, artifact_root: Path) -> CouncilRound:
    records = _event_stream(session, COUNCIL_ROUND_AGGREGATE_TYPE, round_id)
    if not records:
        raise DomainError(
            f"council round {round_id!r} has no events", error_code="PROJECT_NOT_FOUND"
        )
    round_record: CouncilRound | None = None
    for record in records:
        payload = _verified_payload(session, record, artifact_root)
        if record.event_type == EVENT_COUNCIL_ROUND_STARTED:
            round_record = rebuild_dataclass(CouncilRound, payload["round"])
    if round_record is None:
        raise DomainError(
            f"state of council round {round_id!r} is unrecoverable",
            error_code="PROJECT_STATE_UNRECOVERABLE",
        )
    return round_record


def load_role_session(
    session: Session, role_session_id: str, *, artifact_root: Path
) -> RoleSession:
    records = _event_stream(session, ROLE_SESSION_AGGREGATE_TYPE, role_session_id)
    if not records:
        raise DomainError(
            f"role session {role_session_id!r} has no events", error_code="PROJECT_NOT_FOUND"
        )
    role_session: RoleSession | None = None
    for record in records:
        payload = _verified_payload(session, record, artifact_root)
        if record.event_type == EVENT_ROLE_SESSION_REGISTERED:
            role_session = rebuild_dataclass(RoleSession, payload["role_session"])
    if role_session is None:
        raise DomainError(
            f"state of role session {role_session_id!r} is unrecoverable",
            error_code="PROJECT_STATE_UNRECOVERABLE",
        )
    return role_session


def load_visibility_bundle(
    session: Session, bundle_id: str, *, artifact_root: Path
) -> VisibilityBundle:
    records = _event_stream(session, VISIBILITY_BUNDLE_AGGREGATE_TYPE, bundle_id)
    if not records:
        raise DomainError(
            f"visibility bundle {bundle_id!r} has no events", error_code="PROJECT_NOT_FOUND"
        )
    bundle: VisibilityBundle | None = None
    for record in records:
        payload = _verified_payload(session, record, artifact_root)
        if record.event_type == EVENT_VISIBILITY_BUNDLE_ISSUED:
            bundle = rebuild_dataclass(VisibilityBundle, payload["bundle"])
    if bundle is None:
        raise DomainError(
            f"state of visibility bundle {bundle_id!r} is unrecoverable",
            error_code="PROJECT_STATE_UNRECOVERABLE",
        )
    return bundle


__all__ = [
    "COUNCIL_ROUND_AGGREGATE_TYPE",
    "COUNCIL_RUN_AGGREGATE_TYPE",
    "ROLE_SESSION_AGGREGATE_TYPE",
    "VISIBILITY_BUNDLE_AGGREGATE_TYPE",
    "create_council_round",
    "create_council_run",
    "issue_visibility_bundle",
    "load_council_round",
    "load_council_run",
    "load_role_session",
    "load_visibility_bundle",
    "register_role_session",
    "verify_visibility_bundle",
]
