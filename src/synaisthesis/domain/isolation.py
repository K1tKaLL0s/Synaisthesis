"""Council role isolation domain (blueprint 04 §3, 08 §3/§4/§7, 06 role_sessions; M6.2).

This module owns the three-track council isolation primitives:

- ``IsolationLevel`` (08 §3) with the deterministic ``SESSION`` floor that the
  Support/Oppose/Independent tracks must satisfy;
- ``ModelFamilyFingerprint`` and the same-model-family degradation rule (08 §7);
- ``VisibilityBundle``: a sealed, hash-bound envelope addressed to exactly one
  role session. Its ``bundle_hash`` covers the content, the content hash, the
  source receipt and the audience, so the source of Phase-A output is provable
  and tampering fails closed;
- ``UntrustedExternalText``: the equivalent quarantine object for external
  content (08 §4); injected instructions are detected and block issuance.

It is deliberately persistence-free and provider-free: no SQLAlchemy, Alembic,
pydantic or HTTP imports are allowed here (matching the sibling domain modules).
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime
from typing import Any

from synaisthesis.domain.enums import IndependenceStatus, StrictStrEnum
from synaisthesis.domain.errors import DomainError
from synaisthesis.domain.event import DomainEvent, canonicalize, sha256_hex

# ---------------------------------------------------------------------------
# Stable enumerations
# ---------------------------------------------------------------------------


class IsolationLevel(StrictStrEnum):
    """Isolation strength tiers (blueprint 08, section 3)."""

    BEHAVIORAL = "BEHAVIORAL"
    SESSION = "SESSION"
    MODEL = "MODEL"
    WORKSPACE = "WORKSPACE"
    PROCESS = "PROCESS"
    CONTAINER = "CONTAINER"
    CREDENTIAL = "CREDENTIAL"


class CouncilRole(StrictStrEnum):
    """The three isolated council tracks (blueprint 04, section 3)."""

    SUPPORT = "SUPPORT"
    OPPOSE = "OPPOSE"
    INDEPENDENT = "INDEPENDENT"


class CouncilRunStatus(StrictStrEnum):
    """Council run lifecycle; M6.2 only opens runs, M7.1 owns transitions."""

    CREATED = "CREATED"


class RoleSessionStatus(StrictStrEnum):
    """role_sessions.session_status (blueprint 06); M6.2 registers sessions."""

    REGISTERED = "REGISTERED"


#: Ranked order so ``isolation_at_least`` can compare tiers deterministically.
ISOLATION_ORDER: tuple[IsolationLevel, ...] = tuple(IsolationLevel)

#: Support/Oppose/Independent at least require SESSION (08 §3).
MINIMUM_TRACK_ISOLATION: IsolationLevel = IsolationLevel.SESSION

#: External-text instruction markers that quarantine rejects (08 §4).
INJECTION_MARKERS: tuple[str, ...] = (
    "ignore previous instructions",
    "ignore all previous instructions",
    "disregard prior instructions",
    "disregard all instructions",
    "do not follow",
    "you are now",
    "override system",
    "system prompt",
)

# ---------------------------------------------------------------------------
# Event catalog
# ---------------------------------------------------------------------------

EVENT_COUNCIL_RUN_CREATED = "CouncilRunCreated"
EVENT_COUNCIL_ROUND_STARTED = "CouncilRoundStarted"
EVENT_ROLE_SESSION_REGISTERED = "RoleSessionRegistered"
EVENT_VISIBILITY_BUNDLE_ISSUED = "VisibilityBundleIssued"

COUNCIL_EVENT_TYPES: frozenset[str] = frozenset(
    {
        EVENT_COUNCIL_RUN_CREATED,
        EVENT_COUNCIL_ROUND_STARTED,
        EVENT_ROLE_SESSION_REGISTERED,
        EVENT_VISIBILITY_BUNDLE_ISSUED,
    }
)


def build_council_event(
    event_type: str,
    *,
    aggregate_type: str,
    aggregate_id: str,
    payload: dict[str, Any],
    sequence: int,
) -> DomainEvent:
    """Build an immutable council DomainEvent with a stable event hash."""
    if event_type not in COUNCIL_EVENT_TYPES:
        raise DomainError(
            f"unknown council event type {event_type!r}",
            error_code="UNKNOWN_EVENT_TYPE",
        )
    return DomainEvent(
        aggregate_type=aggregate_type,
        aggregate_id=aggregate_id,
        event_type=event_type,
        payload=payload,
        sequence=sequence,
    )


def _canonical_payload(value: Any) -> dict[str, Any]:
    payload = canonicalize(value)
    if not isinstance(payload, dict):
        raise TypeError("isolation payload must canonicalize to an object")
    return payload


def isolation_at_least(level: IsolationLevel, floor: IsolationLevel) -> bool:
    """Return True when ``level`` is at least as strong as ``floor`` (08 §3)."""
    return ISOLATION_ORDER.index(level) >= ISOLATION_ORDER.index(floor)


# ---------------------------------------------------------------------------
# Model family independence (08 §7)
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class ModelFamilyFingerprint:
    """The provider + model family that determines cross-review independence."""

    provider: str
    family: str

    def __post_init__(self) -> None:
        for field_name in ("provider", "family"):
            if not getattr(self, field_name).strip():
                raise DomainError(
                    f"model family fingerprint missing {field_name}",
                    error_code="MODEL_FAMILY_INVALID",
                )

    def to_event_payload(self) -> dict[str, Any]:
        return _canonical_payload(asdict(self))


def same_family(a: ModelFamilyFingerprint, b: ModelFamilyFingerprint) -> bool:
    """Two profiles are the same family only on the same provider AND family."""
    return a.provider == b.provider and a.family == b.family


@dataclass(frozen=True, slots=True)
class ModelIndependenceAssessment:
    """Cross-review independence result (08 §7)."""

    producer: ModelFamilyFingerprint
    reviewer: ModelFamilyFingerprint
    degraded: bool
    status: IndependenceStatus
    rationale: str

    def to_event_payload(self) -> dict[str, Any]:
        return _canonical_payload(asdict(self))


def assess_model_independence(
    *,
    producer: ModelFamilyFingerprint,
    reviewer: ModelFamilyFingerprint,
) -> ModelIndependenceAssessment:
    """Same-family cross-review is degraded, never silently independent (08 §7)."""
    if same_family(producer, reviewer):
        return ModelIndependenceAssessment(
            producer=producer,
            reviewer=reviewer,
            degraded=True,
            status=IndependenceStatus.SAME_MODEL_FAMILY,
            rationale="同模型家族互评，独立性降级（SAME_MODEL_FAMILY）",
        )
    return ModelIndependenceAssessment(
        producer=producer,
        reviewer=reviewer,
        degraded=False,
        status=IndependenceStatus.INDEPENDENT_VERIFIED,
        rationale="两角色使用不同模型家族，模型层独立性成立",
    )


# ---------------------------------------------------------------------------
# External content quarantine (08 §4)
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class UntrustedExternalText:
    """Equivalent quarantine object for external content (08 §4).

    External text is pure data: no Synaisthesis code may eval/exec its content
    or grant it tool authority. It must always be marked ``untrusted=True``.
    """

    content: str
    source_ref: str
    untrusted: bool = True

    def __post_init__(self) -> None:
        if not self.source_ref.strip():
            raise DomainError(
                "external text requires a source_ref",
                error_code="EXTERNAL_TEXT_INVALID",
            )
        if not self.untrusted:
            raise DomainError(
                "外部内容必须标记 untrusted，不得作为可信内容进入 bundle",
                error_code="EXTERNAL_TEXT_INVALID",
            )

    def to_event_payload(self) -> dict[str, Any]:
        return _canonical_payload(asdict(self))


def detect_injected_instructions(text: str) -> tuple[str, ...]:
    """Return the injection markers found in untrusted text (08 §4)."""
    lowered = text.lower()
    return tuple(marker for marker in INJECTION_MARKERS if marker in lowered)


# ---------------------------------------------------------------------------
# Council run / round base (06 council_runs / council_rounds)
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class CouncilRun:
    """One council run record (06 council_runs); M7.1 owns round transitions."""

    run_id: str
    claim_contract_id: str
    configured_rounds: int
    primary_model_profile_id: str
    auditor_model_profile_id: str
    delegation_policy_id: str
    budget_policy_id: str
    current_round: int = 0
    status: CouncilRunStatus = CouncilRunStatus.CREATED
    started_at: datetime | None = None
    ended_at: datetime | None = None

    def __post_init__(self) -> None:
        for field_name in (
            "run_id",
            "claim_contract_id",
            "primary_model_profile_id",
            "auditor_model_profile_id",
            "delegation_policy_id",
            "budget_policy_id",
        ):
            if not getattr(self, field_name).strip():
                raise DomainError(
                    f"council run missing {field_name}",
                    error_code="COUNCIL_RUN_INVALID",
                )
        if self.configured_rounds < 1:
            raise DomainError(
                "configured_rounds must be >= 1",
                error_code="COUNCIL_RUN_INVALID",
            )
        if self.current_round < 0:
            raise DomainError(
                "current_round must be >= 0",
                error_code="COUNCIL_RUN_INVALID",
            )

    def to_event_payload(self) -> dict[str, Any]:
        return _canonical_payload(asdict(self))


@dataclass(frozen=True, slots=True)
class CouncilRound:
    """One council round record (06 council_rounds).

    ``valid`` defaults to False; the effective-round rules in 04 §7 are M7.1's
    responsibility and are intentionally not evaluated here.
    """

    round_id: str
    run_id: str
    round_number: int
    valid: bool = False
    start_revision_id: str | None = None
    end_revision_id: str | None = None
    outcome: str | None = None
    stability_score: float | None = None
    snapshot_artifact_id: str | None = None

    def __post_init__(self) -> None:
        if not self.round_id.strip() or not self.run_id.strip():
            raise DomainError(
                "council round requires round_id and run_id",
                error_code="COUNCIL_ROUND_INVALID",
            )
        if self.round_number < 1:
            raise DomainError(
                "round_number must be >= 1",
                error_code="COUNCIL_ROUND_INVALID",
            )

    def to_event_payload(self) -> dict[str, Any]:
        return _canonical_payload(asdict(self))


# ---------------------------------------------------------------------------
# Role session (06 role_sessions)
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class RoleSession:
    """One registered isolated role session (06 role_sessions)."""

    role_session_id: str
    run_id: str
    role: CouncilRole
    model_profile_id: str
    visibility_policy_id: str
    isolation_level: IsolationLevel
    model_fingerprint: ModelFamilyFingerprint
    round_id: str | None = None
    isolated_context_hash: str | None = None
    session_status: RoleSessionStatus = RoleSessionStatus.REGISTERED

    def _context_payload(self) -> dict[str, Any]:
        return {
            "run_id": self.run_id,
            "role": self.role.value,
            "model_profile_id": self.model_profile_id,
            "visibility_policy_id": self.visibility_policy_id,
            "isolation_level": self.isolation_level.value,
            "model_fingerprint": asdict(self.model_fingerprint),
        }

    def __post_init__(self) -> None:
        for field_name in (
            "role_session_id",
            "run_id",
            "model_profile_id",
            "visibility_policy_id",
        ):
            if not getattr(self, field_name).strip():
                raise DomainError(
                    f"role session missing {field_name}",
                    error_code="ROLE_SESSION_INVALID",
                )
        if not isolation_at_least(self.isolation_level, MINIMUM_TRACK_ISOLATION):
            raise DomainError(
                f"{self.role.value} 轨道至少要求 SESSION 隔离，当前为 {self.isolation_level.value}",
                error_code="ISOLATION_LEVEL_INSUFFICIENT",
            )
        expected = sha256_hex(self._context_payload())
        if self.isolated_context_hash is not None and self.isolated_context_hash != expected:
            raise DomainError(
                "isolated_context_hash does not match the isolation context",
                error_code="ARTIFACT_HASH_MISMATCH",
            )
        object.__setattr__(self, "isolated_context_hash", expected)

    def to_event_payload(self) -> dict[str, Any]:
        return _canonical_payload(asdict(self))


# ---------------------------------------------------------------------------
# Visibility bundle (08 §4/§7; 04 §3 Phase A)
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class VisibilityBundle:
    """A sealed, hash-bound envelope addressed to one role session.

    ``bundle_hash`` covers the content, its hash, the source receipt and the
    audience, so the source of the Phase-A output is provable: changing the
    content or the source receipt invalidates the seal.
    """

    bundle_id: str
    run_id: str
    role: CouncilRole
    session_id: str
    phase: str
    content: str
    content_hash: str
    source_receipt: str
    isolation_level: IsolationLevel
    external_texts: tuple[UntrustedExternalText, ...] = ()
    bundle_hash: str | None = None
    issued_at: datetime | None = None

    def __post_init__(self) -> None:
        for field_name in ("bundle_id", "run_id", "session_id", "source_receipt"):
            if not getattr(self, field_name).strip():
                raise DomainError(
                    f"visibility bundle missing {field_name}",
                    error_code="VISIBILITY_BUNDLE_INVALID",
                )
        if not self.content.strip():
            raise DomainError(
                "visibility bundle requires non-empty content",
                error_code="VISIBILITY_BUNDLE_INVALID",
            )
        if self.phase not in {"A", "B"}:
            raise DomainError(
                f"visibility bundle phase must be 'A' or 'B', got {self.phase!r}",
                error_code="VISIBILITY_BUNDLE_INVALID",
            )
        expected_content_hash = sha256_hex(self.content)
        if self.content_hash != expected_content_hash:
            raise DomainError(
                "content_hash does not match the bundle content",
                error_code="VISIBILITY_BUNDLE_HASH_MISMATCH",
            )
        for external in self.external_texts:
            injected = detect_injected_instructions(external.content)
            if injected:
                raise DomainError(
                    "外部内容包含可疑指令，禁止进入 visibility bundle："
                    + ", ".join(repr(marker) for marker in injected),
                    error_code="SECURITY_FINDING",
                )
        expected_bundle_hash = sha256_hex(self.content_payload())
        if self.bundle_hash is not None and self.bundle_hash != expected_bundle_hash:
            raise DomainError(
                "bundle_hash does not match the visibility bundle content",
                error_code="ARTIFACT_HASH_MISMATCH",
            )
        object.__setattr__(self, "bundle_hash", expected_bundle_hash)

    def content_payload(self) -> dict[str, Any]:
        """Return the hash-covered content (bundle_hash/issued_at excluded)."""
        payload = asdict(self)
        payload.pop("bundle_hash", None)
        payload.pop("issued_at", None)
        return _canonical_payload(payload)

    def verify_integrity(self) -> tuple[str, ...]:
        """Return blockers; empty means the source seal is intact."""
        if self.bundle_hash is None or self.bundle_hash != sha256_hex(self.content_payload()):
            return ("bundle_hash 与内容不一致（来源不可证明）",)
        return ()

    def to_event_payload(self) -> dict[str, Any]:
        return _canonical_payload(asdict(self))


def assert_visibility_scope(
    *,
    bundle: VisibilityBundle,
    consumer_role: CouncilRole,
    consumer_session_id: str,
) -> tuple[str, ...]:
    """Return blockers; empty means the consumer may read the bundle.

    A visibility bundle is addressed to exactly one (role, session). Any other
    consumer — in particular another Phase-A track — is blocked.
    """
    blockers: list[str] = []
    if consumer_role is not bundle.role:
        blockers.append(
            f"{consumer_role.value} 角色不得读取 {bundle.role.value} 的 "
            f"Phase {bundle.phase} visibility bundle"
        )
    if consumer_session_id != bundle.session_id:
        blockers.append("session_id 不匹配：bundle 未签发给该会话")
    return tuple(blockers)


__all__ = [
    "COUNCIL_EVENT_TYPES",
    "EVENT_COUNCIL_ROUND_STARTED",
    "EVENT_COUNCIL_RUN_CREATED",
    "EVENT_ROLE_SESSION_REGISTERED",
    "EVENT_VISIBILITY_BUNDLE_ISSUED",
    "INJECTION_MARKERS",
    "ISOLATION_ORDER",
    "MINIMUM_TRACK_ISOLATION",
    "CouncilRole",
    "CouncilRound",
    "CouncilRun",
    "CouncilRunStatus",
    "IsolationLevel",
    "ModelFamilyFingerprint",
    "ModelIndependenceAssessment",
    "RoleSession",
    "RoleSessionStatus",
    "UntrustedExternalText",
    "VisibilityBundle",
    "assert_visibility_scope",
    "assess_model_independence",
    "build_council_event",
    "detect_injected_instructions",
    "isolation_at_least",
    "same_family",
]
