"""Claim compiler domain (blueprint 02 §8, 04 §1, 06 §claim_units; M4.1).

This module owns the atomic claim unit and the claim-related enumerations:
the seven ClaimClass values (02 §8), the intended ClaimVerifier values
(LEAN/Z3/PYTHON_SANDBOX/MANUAL/NONE), and the immutable Claim record. It is
deliberately persistence-free and provider-free: no SQLAlchemy, Alembic,
pydantic or HTTP imports are allowed here.

Blueprint 04 §1 lists ``intended_verifiers`` (plural); M4.1's acceptance
criterion and M4.2's freeze contract name a single primary ``verifier``, so the
MVP records that one verifier. ``NONE`` must be explicitly declared unverified
via ``unverified=True``; otherwise the claim fails closed with
``CLAIM_VERIFIER_MISSING``.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime
from typing import Any, cast

from synaisthesis.domain.enums import StrictStrEnum
from synaisthesis.domain.errors import DomainError
from synaisthesis.domain.event import DomainEvent, canonicalize, sha256_hex


class ClaimClass(StrictStrEnum):
    """ClaimUnit classification and tool routing (blueprint 02, section 8)."""

    FORMAL = "FORMAL"
    FINITE_CONSTRAINT = "FINITE_CONSTRAINT"
    COMPUTATIONAL = "COMPUTATIONAL"
    EMPIRICAL = "EMPIRICAL"
    ENGINEERING = "ENGINEERING"
    LITERATURE_NOVELTY = "LITERATURE_NOVELTY"
    MIXED = "MIXED"


class ClaimVerifier(StrictStrEnum):
    """Intended verifier for one claim; NONE requires an explicit unverified flag."""

    LEAN = "LEAN"
    Z3 = "Z3"
    PYTHON_SANDBOX = "PYTHON_SANDBOX"
    MANUAL = "MANUAL"
    NONE = "NONE"


CLAIM_AGGREGATE_TYPE = "Claim"
EVENT_CLAIM_COMPILED = "ClaimCompiled"
CLAIM_EVENT_TYPES: frozenset[str] = frozenset({EVENT_CLAIM_COMPILED})


def _canonical_payload(value: Any) -> dict[str, Any]:
    payload = canonicalize(value)
    if not isinstance(payload, dict):
        raise TypeError("claim payload must canonicalize to an object")
    return cast(dict[str, Any], payload)


def build_claim_event(
    event_type: str,
    *,
    aggregate_type: str,
    aggregate_id: str,
    payload: dict[str, Any],
    sequence: int,
) -> DomainEvent:
    """Build an immutable claim DomainEvent with a stable event hash."""
    if event_type not in CLAIM_EVENT_TYPES:
        raise DomainError(
            f"unknown claim event type {event_type!r}",
            error_code="UNKNOWN_EVENT_TYPE",
        )
    return DomainEvent(
        aggregate_type=aggregate_type,
        aggregate_id=aggregate_id,
        event_type=event_type,
        payload=payload,
        sequence=sequence,
    )


def _finalize_artifact_hash(claim: Claim) -> None:
    """Auto-compute the hash field, or verify a caller-provided value.

    The hash covers the semantic content of the claim (everything except
    ``artifact_hash`` and the metadata timestamp ``created_at``), so two claims
    with identical semantics share a hash regardless of when they were built.
    """
    expected = sha256_hex(claim.content_payload())
    if claim.artifact_hash is not None and claim.artifact_hash != expected:
        raise DomainError(
            "artifact_hash does not match the claim content",
            error_code="ARTIFACT_HASH_MISMATCH",
        )
    object.__setattr__(claim, "artifact_hash", expected)


@dataclass(frozen=True, slots=True)
class Claim:
    """One atomic claim unit (blueprint 04 §1, 06 §claim_units).

    A Claim may only carry an atomic (non-MIXED) class; MIXED statements must
    be split before a Claim is constructed.  Every claim requires an object
    domain, at least one quantifier, a falsification witness and a verifier.
    """

    claim_id: str
    project_id: str
    claim_key: str
    natural_language_statement: str
    object_domain: str
    quantifiers: tuple[str, ...]
    falsification_witness: str
    claim_class: ClaimClass
    verifier: ClaimVerifier
    formal_statement_candidate: str | None = None
    assumptions: tuple[str, ...] = ()
    conclusion: str = ""
    parent_claim_id: str | None = None
    importance: str = ""
    dependencies: tuple[str, ...] = ()
    engineering_relevance: str = ""
    semantic_critical_fields: tuple[str, ...] = ()
    unverified: bool = False
    artifact_hash: str | None = None
    created_at: datetime | None = None

    def __post_init__(self) -> None:
        for field_name in (
            "claim_id",
            "claim_key",
            "natural_language_statement",
            "object_domain",
            "falsification_witness",
        ):
            if not getattr(self, field_name).strip():
                raise DomainError(
                    f"claim {self.claim_id!r} 缺少 {field_name}，无法形成无歧义原子命题",
                    error_code="CLAIM_NOT_ATOMIC",
                )
        if not self.quantifiers or any(not quantifier.strip() for quantifier in self.quantifiers):
            raise DomainError(
                f"claim {self.claim_id!r} 缺少量词，无法形成无歧义原子命题",
                error_code="CLAIM_NOT_ATOMIC",
            )
        if self.claim_class is ClaimClass.MIXED:
            raise DomainError(
                f"claim {self.claim_id!r} 是 MIXED 主张，必须先拆分为原子 Claim",
                error_code="CLAIM_MIXED",
            )
        if self.verifier is ClaimVerifier.NONE and not self.unverified:
            raise DomainError(
                f"claim {self.claim_id!r} 的 verifier 为 NONE，必须显式声明为未验证 "
                "(unverified=True)",
                error_code="CLAIM_VERIFIER_MISSING",
            )
        _finalize_artifact_hash(self)

    def content_payload(self) -> dict[str, Any]:
        """Return the hash-covered semantic content (metadata excluded)."""
        payload = asdict(self)
        payload.pop("artifact_hash", None)
        payload.pop("created_at", None)
        return _canonical_payload(payload)

    def to_event_payload(self) -> dict[str, Any]:
        return _canonical_payload(asdict(self))

    @property
    def is_atomic(self) -> bool:
        return self.claim_class is not ClaimClass.MIXED


def claim_blockers(claim: Claim) -> tuple[str, ...]:
    """Re-run the atomicity/verifier rules without constructing a new instance.

    Useful when a caller needs the issue list instead of an exception; the
    Claim constructor itself already fails closed on the same rules.
    """
    blockers: list[str] = []
    if claim.claim_class is ClaimClass.MIXED:
        blockers.append("MIXED 主张必须先拆分为原子 Claim")
    if not claim.object_domain.strip():
        blockers.append("缺少 object_domain")
    if not claim.quantifiers or any(not quantifier.strip() for quantifier in claim.quantifiers):
        blockers.append("缺少量词")
    if not claim.falsification_witness.strip():
        blockers.append("缺少证伪见证")
    if claim.verifier is ClaimVerifier.NONE and not claim.unverified:
        blockers.append("verifier=NONE 必须显式声明为未验证")
    return tuple(blockers)


__all__ = [
    "CLAIM_AGGREGATE_TYPE",
    "CLAIM_EVENT_TYPES",
    "EVENT_CLAIM_COMPILED",
    "Claim",
    "ClaimClass",
    "ClaimVerifier",
    "build_claim_event",
    "claim_blockers",
]
