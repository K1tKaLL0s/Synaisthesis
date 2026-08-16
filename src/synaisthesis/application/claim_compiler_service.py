"""Claim compiler application service (blueprint 02 §8, 04 §1, 07 §4; M4.1).

``compile_claims`` turns candidate claim inputs into atomic Claim records. It
detects MIXED statements — multiple top-level propositions joined by and/or
without an explicit atomic declaration — splits them through their explicit
``atomic_parts``, and rejects anything that cannot form an unambiguous atomic
proposition. Persistence is delegated to ``claim_repository``.
"""

from __future__ import annotations

import uuid
from collections.abc import Sequence
from datetime import datetime
from pathlib import Path
from typing import Any

from sqlalchemy.orm import Session

from synaisthesis.agents.schemas import ClaimCandidate
from synaisthesis.domain.claim import Claim, ClaimClass
from synaisthesis.domain.claim_contract import (
    CLAIM_CONTRACT_AGGREGATE_TYPE,
    EVENT_CLAIM_CONTRACT_FROZEN,
    EVENT_CLAIM_CONTRACT_REVISED,
    ClaimContract,
    claim_contract_blockers,
)
from synaisthesis.domain.enums import ProvenanceType
from synaisthesis.domain.errors import DomainError
from synaisthesis.domain.event import sha256_hex
from synaisthesis.storage.repositories.claim_repository import (
    load_claim,
    save_claim,
)

#: Connectors that split a statement into multiple propositions at top level
#: (outside any bracket pair). Order is length-descending so "并且" wins over
#: "且" and English " and " / " or " are matched as whole words.
_CLAUSE_CONNECTORS: tuple[str, ...] = (
    " and ",
    " or ",
    "并且",
    "以及",
    "且",
    "或",
    "；",
    ";",
)

_OPEN_BRACKETS = "([{"
_CLOSE_BRACKETS = ")]}"


def split_propositions(statement: str) -> tuple[str, ...]:
    """Split a statement into top-level propositions on and/or connectors.

    Only connectors at bracket depth zero split; text inside ``()``, ``[]`` or
    ``{}`` is protected. A single-proposition statement returns a one-tuple of
    the stripped statement.
    """
    text = statement.strip()
    if not text:
        return ()
    spans: list[tuple[int, int]] = []
    depth = 0
    index = 0
    while index < len(text):
        char = text[index]
        if char in _OPEN_BRACKETS:
            depth += 1
            index += 1
            continue
        if char in _CLOSE_BRACKETS:
            depth = max(0, depth - 1)
            index += 1
            continue
        if depth == 0:
            for connector in _CLAUSE_CONNECTORS:
                if text.startswith(connector, index):
                    spans.append((index, index + len(connector)))
                    index += len(connector)
                    break
            else:
                index += 1
            continue
        index += 1

    if not spans:
        return (text,)

    parts: list[str] = []
    cursor = 0
    for start, end in spans:
        part = text[cursor:start].strip()
        if part:
            parts.append(part)
        cursor = end
    tail = text[cursor:].strip()
    if tail:
        parts.append(tail)
    return tuple(parts) if parts else (text,)


def is_mixed_statement(statement: str) -> bool:
    """Return True when the statement contains multiple splittable propositions."""
    return len(split_propositions(statement)) > 1


def classify_claim(statement: str, declared: ClaimClass) -> ClaimClass:
    """Return MIXED for a compound statement, otherwise the declared class."""
    if is_mixed_statement(statement):
        return ClaimClass.MIXED
    return declared


def split_claim_into_atomic_units(statement: str) -> tuple[str, ...]:
    """Return the atomic propositions of a MIXED statement (07 §4)."""
    return split_propositions(statement)


def _default_claim_key(statement: str) -> str:
    return f"claim-{sha256_hex(statement)[:12]}"


def _build_claim(
    candidate: ClaimCandidate,
    *,
    project_id: str,
    parent_claim_id: str | None,
) -> Claim:
    statement = candidate.statement.strip()
    return Claim(
        claim_id=candidate.claim_id or uuid.uuid4().hex,
        project_id=project_id,
        claim_key=candidate.claim_key or _default_claim_key(statement),
        natural_language_statement=statement,
        object_domain=candidate.object_domain.strip(),
        quantifiers=tuple(quantifier.strip() for quantifier in candidate.quantifiers),
        falsification_witness=(candidate.falsification_witness or "").strip(),
        claim_class=candidate.claim_class,
        verifier=candidate.verifier,
        formal_statement_candidate=candidate.formal_statement_candidate,
        assumptions=tuple(candidate.assumptions),
        conclusion=candidate.conclusion,
        parent_claim_id=parent_claim_id,
        dependencies=tuple(candidate.dependencies),
        engineering_relevance=candidate.engineering_relevance,
        semantic_critical_fields=tuple(candidate.semantic_critical_fields),
        unverified=candidate.unverified,
    )


def _compile_candidate(
    candidate: ClaimCandidate,
    *,
    project_id: str,
    parent_claim_id: str | None = None,
) -> tuple[Claim, ...]:
    statement = candidate.statement.strip()
    if not statement:
        raise DomainError(
            "claim statement 不能为空，无法形成无歧义原子命题",
            error_code="CLAIM_NOT_ATOMIC",
        )
    if is_mixed_statement(statement):
        if candidate.atomic:
            raise DomainError(
                f"statement 含多个可拆命题却声明 atomic：{statement!r}",
                error_code="CLAIM_NOT_ATOMIC",
            )
        if candidate.claim_class is not ClaimClass.MIXED:
            raise DomainError(
                f"statement 含多个可拆命题但 claim_class="
                f"{candidate.claim_class.value}，必须先拆分为 MIXED",
                error_code="CLAIM_MIXED",
            )
        parts = candidate.atomic_parts or ()
        if not parts:
            raise DomainError(
                "MIXED 主张必须通过 atomic_parts 显式拆分为原子 Claim；无法形成无歧义原子命题",
                error_code="CLAIM_MIXED",
            )
        base_key = candidate.claim_key or _default_claim_key(statement)
        compiled: list[Claim] = []
        for index, part in enumerate(parts, start=1):
            child = part.model_copy(update={"claim_key": part.claim_key or f"{base_key}@{index}"})
            compiled.extend(
                _compile_candidate(
                    child,
                    project_id=project_id,
                    parent_claim_id=candidate.claim_id or base_key,
                )
            )
        return tuple(compiled)

    return (_build_claim(candidate, project_id=project_id, parent_claim_id=parent_claim_id),)


def compile_claims(
    candidates: Sequence[ClaimCandidate],
    *,
    project_id: str,
) -> tuple[Claim, ...]:
    """Compile candidate inputs into atomic Claim records.

    MIXED candidates are split through their ``atomic_parts`` and never emitted
    themselves; every returned Claim carries an object domain, quantifiers, a
    falsification witness and a verifier (the Claim constructor fails closed
    otherwise).
    """
    claims: list[Claim] = []
    for candidate in candidates:
        claims.extend(_compile_candidate(candidate, project_id=project_id))
    return tuple(claims)


def save_compiled_claims(
    session: Session,
    *,
    project_id: str,
    claims: Sequence[Claim],
    artifact_root: Path,
) -> tuple[Claim, ...]:
    """Persist already-compiled atomic claims via the claim repository."""
    return tuple(
        save_claim(session, claim, project_id=project_id, artifact_root=artifact_root)
        for claim in claims
    )


# ---------------------------------------------------------------------------
# M4.2 — claim contract freeze and revision (04 section 2)
# ---------------------------------------------------------------------------


def _claim_hashes(claim: Claim) -> tuple[str, str]:
    natural_language_hash = sha256_hex({"statement": claim.natural_language_statement})
    formal_statement_hash = sha256_hex({"formal": claim.formal_statement_candidate or ""})
    return natural_language_hash, formal_statement_hash


def _persist_claim_contract_event(
    session: Session,
    *,
    event_type: str,
    contract: ClaimContract,
    project_id: str,
    artifact_root: Path,
    sequence: int,
) -> None:
    from synaisthesis.domain.claim_contract import build_claim_contract_event
    from synaisthesis.storage.repositories.event_repository import append_domain_event

    event = build_claim_contract_event(
        event_type,
        aggregate_type=CLAIM_CONTRACT_AGGREGATE_TYPE,
        aggregate_id=contract.contract_id,
        payload={"claim_contract": contract.to_event_payload()},
        sequence=sequence,
    )
    append_domain_event(session, event, project_id=project_id, artifact_root=artifact_root)


def _claim_contract_stream(session: Session, contract_id: str) -> list[Any]:
    from sqlalchemy import select

    from synaisthesis.storage.repositories.event_repository import DomainEventRecord

    return list(
        session.execute(
            select(DomainEventRecord)
            .where(
                DomainEventRecord.aggregate_type == CLAIM_CONTRACT_AGGREGATE_TYPE,
                DomainEventRecord.aggregate_id == contract_id,
            )
            .order_by(DomainEventRecord.id)
        )
        .scalars()
        .all()
    )


def freeze_claim_contract(
    session: Session,
    *,
    project_id: str,
    claim: Claim,
    tool_plan: tuple[str, ...],
    network_policy: str,
    data_policy: str,
    budget_policy: str,
    allowed_semantic_delta: str,
    approval_policy: str,
    model_role_assignments: tuple[str, ...],
    actor: ProvenanceType,
    user_event_id: str,
    at: datetime,
    artifact_root: Path,
    contract_id: str | None = None,
    stop_conditions: tuple[str, ...] = (),
    output_scope: str = "",
    baseline_snapshot: str = "",
) -> ClaimContract:
    """Freeze an atomic claim into an immutable ClaimContract (04 section 2).

    Only a real user event may confirm the freeze; the contract_hash covers
    semantics, tool plan, budget and policies.  The claim itself must already
    be atomic (the Claim constructor enforces this).
    """
    from synaisthesis.domain.claim_contract import (
        ClaimContract,
    )
    from synaisthesis.domain.gate import assert_claim_acceptance_decision
    from synaisthesis.domain.qualification import is_user_actor

    if not is_user_actor(actor):
        raise DomainError(
            "冻结 ClaimContract 需要真实用户事件",
            error_code="CLAIM_FREEZE_REQUIRES_USER_EVENT",
        )
    assert_claim_acceptance_decision("ACCEPT")
    natural_language_hash, formal_statement_hash = _claim_hashes(claim)
    contract = ClaimContract(
        contract_id=contract_id or f"cc-{uuid.uuid4().hex[:12]}",
        claim_id=claim.claim_id,
        claim_revision_id=claim.claim_id,
        version=1,
        natural_language_hash=natural_language_hash,
        formal_statement_hash=formal_statement_hash,
        object_domain_snapshot=claim.object_domain,
        assumption_snapshot=claim.assumptions,
        conclusion_snapshot=claim.conclusion or claim.natural_language_statement,
        baseline_snapshot=baseline_snapshot,
        stop_conditions=stop_conditions,
        output_scope=output_scope,
        tool_plan=tool_plan,
        network_policy=network_policy,
        data_policy=data_policy,
        budget_policy=budget_policy,
        allowed_semantic_delta=allowed_semantic_delta,
        approval_policy=approval_policy,
        artifact_manifest_hash=claim.artifact_hash or "",
        model_role_assignments=model_role_assignments,
        user_confirmed=True,
        frozen_at=at,
        created_at=at,
    )
    blockers = claim_contract_blockers(contract)
    if blockers:
        raise DomainError(
            "CLAIM_CONTRACT_INVALID: " + "; ".join(blockers),
            error_code="CLAIM_CONTRACT_INVALID",
        )
    _persist_claim_contract_event(
        session,
        event_type=EVENT_CLAIM_CONTRACT_FROZEN,
        contract=contract,
        project_id=project_id,
        artifact_root=artifact_root,
        sequence=len(_claim_contract_stream(session, contract.contract_id)) + 1,
    )
    return contract


def revise_claim_contract(
    session: Session,
    *,
    project_id: str,
    current: ClaimContract,
    actor: ProvenanceType,
    user_event_id: str,
    at: datetime,
    artifact_root: Path,
    **changes: Any,
) -> ClaimContract:
    """Create a new frozen version; the old contract is never modified (04 §2)."""
    import dataclasses

    from synaisthesis.domain.qualification import is_user_actor

    if not is_user_actor(actor):
        raise DomainError(
            "修订 ClaimContract 需要真实用户事件",
            error_code="CLAIM_FREEZE_REQUIRES_USER_EVENT",
        )
    immutable_fields = {"contract_id", "claim_id", "claim_revision_id", "version"}
    touched = immutable_fields & set(changes)
    if touched:
        raise DomainError(
            f"不得修改不可变字段：{', '.join(sorted(touched))}",
            error_code="CLAIM_CONTRACT_FROZEN",
        )
    revised = dataclasses.replace(
        current,
        version=current.version + 1,
        supersedes_id=current.contract_id,
        contract_hash=None,
        frozen_at=at,
        created_at=at,
        **changes,
    )
    _persist_claim_contract_event(
        session,
        event_type=EVENT_CLAIM_CONTRACT_REVISED,
        contract=revised,
        project_id=project_id,
        artifact_root=artifact_root,
        sequence=len(_claim_contract_stream(session, revised.contract_id)) + 1,
    )
    return revised


def load_claim_contract(
    session: Session, contract_id: str, *, artifact_root: Path
) -> ClaimContract:
    """Replay a ClaimContract from its hash-verified event payload."""
    import json

    from synaisthesis.domain.claim_contract import (
        ClaimContract,
    )
    from synaisthesis.storage.artifact_store import ArtifactRecord
    from synaisthesis.storage.hashing import verify_artifact_hash

    records = _claim_contract_stream(session, contract_id)
    if not records:
        raise DomainError(
            f"claim contract {contract_id!r} has no events",
            error_code="PROJECT_NOT_FOUND",
        )
    contract: ClaimContract | None = None
    for record in records:
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
                f"payload artifact of event {record.id} is missing or "
                "tampered; state unrecoverable",
                error_code="ARTIFACT_HASH_MISMATCH",
            )
        payload = json.loads(path.read_text(encoding="utf-8"))
        if record.event_type in {EVENT_CLAIM_CONTRACT_FROZEN, EVENT_CLAIM_CONTRACT_REVISED}:
            from synaisthesis.application.engineering_design_service import rebuild_dataclass

            contract = rebuild_dataclass(ClaimContract, payload["claim_contract"])
    if contract is None:
        raise DomainError(
            f"state of {contract_id!r} is unrecoverable",
            error_code="PROJECT_STATE_UNRECOVERABLE",
        )
    return contract


__all__ = [
    "classify_claim",
    "compile_claims",
    "freeze_claim_contract",
    "is_mixed_statement",
    "load_claim",
    "load_claim_contract",
    "revise_claim_contract",
    "save_compiled_claims",
    "split_claim_into_atomic_units",
    "split_propositions",
]
