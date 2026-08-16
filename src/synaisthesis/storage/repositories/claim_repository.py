"""Event-sourced claim repository (blueprint 12, storage/repositories/claim_repository.py).

A Claim is persisted as an ordered stream of DomainEvents whose canonical JSON
payloads live in content-addressed artifacts, so the state can always be
rebuilt from the event store (same pattern as project_repository, M1.4).
Loading re-runs the Claim constructor, which re-verifies the artifact hash and
fails closed on tampering.
"""

from __future__ import annotations

import json
from collections.abc import Mapping
from datetime import datetime
from pathlib import Path
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from synaisthesis.domain.claim import (
    CLAIM_AGGREGATE_TYPE,
    EVENT_CLAIM_COMPILED,
    Claim,
    ClaimClass,
    ClaimVerifier,
    build_claim_event,
)
from synaisthesis.domain.errors import DomainError
from synaisthesis.storage.artifact_store import ArtifactRecord
from synaisthesis.storage.hashing import verify_artifact_hash
from synaisthesis.storage.repositories.event_repository import (
    DomainEventRecord,
    append_domain_event,
)


def claim_state_dict(claim: Claim) -> dict[str, Any]:
    """Return the claim state as a canonical JSON-serializable dict."""
    return claim.to_event_payload()


def claim_from_state(state: Mapping[str, Any]) -> Claim:
    """Rebuild a Claim aggregate from a persisted state mapping.

    Reconstructing via the Claim constructor re-runs the atomicity, verifier and
    artifact-hash checks, so a tampered payload never yields a trusted claim.
    """
    return Claim(
        claim_id=str(state["claim_id"]),
        project_id=str(state["project_id"]),
        claim_key=str(state["claim_key"]),
        natural_language_statement=str(state["natural_language_statement"]),
        object_domain=str(state["object_domain"]),
        quantifiers=tuple(str(item) for item in state["quantifiers"]),
        falsification_witness=str(state["falsification_witness"]),
        claim_class=ClaimClass(str(state["claim_class"])),
        verifier=ClaimVerifier(str(state["verifier"])),
        formal_statement_candidate=(
            str(state["formal_statement_candidate"])
            if state.get("formal_statement_candidate") is not None
            else None
        ),
        assumptions=tuple(str(item) for item in state.get("assumptions", ())),
        conclusion=str(state.get("conclusion", "")),
        parent_claim_id=(
            str(state["parent_claim_id"]) if state.get("parent_claim_id") is not None else None
        ),
        importance=str(state.get("importance", "")),
        dependencies=tuple(str(item) for item in state.get("dependencies", ())),
        engineering_relevance=str(state.get("engineering_relevance", "")),
        semantic_critical_fields=tuple(
            str(item) for item in state.get("semantic_critical_fields", ())
        ),
        unverified=bool(state.get("unverified", False)),
        artifact_hash=str(state["artifact_hash"]),
        created_at=(
            datetime.fromisoformat(str(state["created_at"]))
            if state.get("created_at") is not None
            else None
        ),
    )


def save_claim(
    session: Session,
    claim: Claim,
    *,
    project_id: str | None,
    artifact_root: Path,
) -> Claim:
    """Append the claim's state as the next event of its stream."""
    sequence = (
        session.execute(
            select(func.count(DomainEventRecord.id)).where(
                DomainEventRecord.aggregate_type == CLAIM_AGGREGATE_TYPE,
                DomainEventRecord.aggregate_id == claim.claim_id,
            )
        ).scalar_one()
        + 1
    )
    event = build_claim_event(
        EVENT_CLAIM_COMPILED,
        aggregate_type=CLAIM_AGGREGATE_TYPE,
        aggregate_id=claim.claim_id,
        payload={"claim": claim_state_dict(claim)},
        sequence=sequence,
    )
    append_domain_event(
        session,
        event,
        project_id=project_id if project_id is not None else claim.project_id,
        artifact_root=artifact_root,
    )
    return claim


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


def load_claim(session: Session, claim_id: str, *, artifact_root: Path) -> Claim:
    """Replay a claim's ordered event stream and return the rebuilt state.

    Every payload artifact is hash-verified before it is applied, so a missing
    or tampered record never yields a partial or guessed claim state.
    """
    records = (
        session.execute(
            select(DomainEventRecord)
            .where(
                DomainEventRecord.aggregate_type == CLAIM_AGGREGATE_TYPE,
                DomainEventRecord.aggregate_id == claim_id,
            )
            .order_by(DomainEventRecord.id)
        )
        .scalars()
        .all()
    )
    if not records:
        raise DomainError(f"claim {claim_id!r} has no events", error_code="PROJECT_NOT_FOUND")
    claim: Claim | None = None
    for record in records:
        payload = _verified_payload(session, record, artifact_root)
        if record.event_type != EVENT_CLAIM_COMPILED:
            raise DomainError(
                f"unknown event type {record.event_type!r} for claim {claim_id!r}; "
                "state unrecoverable",
                error_code="PROJECT_STATE_UNRECOVERABLE",
            )
        claim = claim_from_state(payload["claim"])
    if claim is None:
        raise DomainError(
            f"state of claim {claim_id!r} is unrecoverable",
            error_code="PROJECT_STATE_UNRECOVERABLE",
        )
    return claim


__all__ = [
    "claim_from_state",
    "claim_state_dict",
    "load_claim",
    "save_claim",
]
