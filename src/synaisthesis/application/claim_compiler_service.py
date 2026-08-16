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
from pathlib import Path

from sqlalchemy.orm import Session

from synaisthesis.agents.schemas import ClaimCandidate
from synaisthesis.domain.claim import Claim, ClaimClass
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


__all__ = [
    "classify_claim",
    "compile_claims",
    "is_mixed_statement",
    "load_claim",
    "save_compiled_claims",
    "split_claim_into_atomic_units",
    "split_propositions",
]
