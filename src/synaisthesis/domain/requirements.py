"""ENG2 traceable requirements and acceptance baseline (blueprint 03B, section 5).

Every requirement carries a stable id, a single testable statement, source
references, a measurable threshold (or an explicit UNRESOLVED_THRESHOLD) and a
verification method.  The baseline only passes when source coverage,
verification-method coverage and critical acceptance coverage are all 100% and
no critical conflict/threshold is unresolved.
"""

from __future__ import annotations

import re
from dataclasses import asdict, dataclass
from datetime import datetime
from typing import Any

from synaisthesis.domain.engineering import finalize_artifact_hash
from synaisthesis.domain.enums import StrictStrEnum
from synaisthesis.domain.errors import DomainError
from synaisthesis.domain.event import canonicalize, sha256_hex

#: Unmeasurable adjectives banned by 03B section 5.1.
VAGUE_THRESHOLD_PATTERNS: tuple[str, ...] = (
    "尽量",
    "适当",
    "快速",
    "友好",
    "高性能",
    "尽可能",
    "酌情",
)

_NUMERIC_RE = re.compile(r"^-?\d+(\.\d+)?([eE][+-]?\d+)?$")
_BOOLEAN_ACCEPTANCE = frozenset({"true", "false", "yes", "no", "是", "否"})


class RequirementType(StrictStrEnum):
    """Requirement kinds (03B, section 5.1)."""

    FUNCTIONAL = "FUNCTIONAL"
    INTERFACE = "INTERFACE"
    DATA = "DATA"
    QUALITY = "QUALITY"
    SAFETY = "SAFETY"
    SECURITY = "SECURITY"
    PRIVACY = "PRIVACY"
    COMPLIANCE = "COMPLIANCE"
    OPERATIONS = "OPERATIONS"
    CONSTRAINT = "CONSTRAINT"


class VerificationMethod(StrictStrEnum):
    """Verification methods (03B, section 5.1)."""

    TEST = "TEST"
    ANALYSIS = "ANALYSIS"
    INSPECTION = "INSPECTION"
    DEMONSTRATION = "DEMONSTRATION"


class RequirementPriority(StrictStrEnum):
    """Requirement priority tiers (03B, section 5.1)."""

    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


class RequirementStatus(StrictStrEnum):
    """Requirement lifecycle (03B, sections 5.1/5.4)."""

    ACTIVE = "ACTIVE"
    UNRESOLVED_THRESHOLD = "UNRESOLVED_THRESHOLD"
    SUPERSEDED = "SUPERSEDED"


def _canonical_payload(value: Any) -> dict[str, Any]:
    payload = canonicalize(value)
    if not isinstance(payload, dict):
        raise TypeError("requirements payload must canonicalize to an object")
    return payload


def has_measurable_acceptance(
    *,
    threshold: str | None,
    acceptance_criterion: str | None,
) -> bool:
    """True when a critical requirement has numeric or boolean acceptance (03B, 5.4)."""
    if threshold is not None and bool(_NUMERIC_RE.match(threshold.strip())):
        return True
    if threshold is not None and threshold.strip().lower() in _BOOLEAN_ACCEPTANCE:
        return True
    if acceptance_criterion is not None:
        lowered = acceptance_criterion.strip().lower()
        if lowered in _BOOLEAN_ACCEPTANCE:
            return True
        if bool(_NUMERIC_RE.match(acceptance_criterion.strip())):
            return True
    return False


def _is_vague(statement: str) -> bool:
    return any(pattern in statement for pattern in VAGUE_THRESHOLD_PATTERNS)


@dataclass(frozen=True, slots=True)
class EngineeringRequirement:
    """One requirement (03B, section 5.1)."""

    requirement_id: str
    type: RequirementType
    statement: str
    source_refs: tuple[str, ...]
    priority: RequirementPriority
    rationale: str
    precondition: str
    inputs: tuple[str, ...]
    expected_behavior_output: str
    measurement_method: str
    unit: str
    threshold: str | None
    tolerance: str | None
    verification_method: VerificationMethod
    acceptance_criterion: str
    owner: str
    dependency_refs: tuple[str, ...]
    conflict_refs: tuple[str, ...]
    status: RequirementStatus = RequirementStatus.ACTIVE
    content_hash: str | None = None

    def __post_init__(self) -> None:
        if not self.requirement_id.strip() or not self.statement.strip():
            raise DomainError(
                "requirement requires id and statement",
                error_code="REQUIREMENT_INVALID",
            )
        if self.status is RequirementStatus.UNRESOLVED_THRESHOLD:
            if self.threshold is not None and self.threshold.strip():
                raise DomainError(
                    f"requirement {self.requirement_id!r} 标记 UNRESOLVED_THRESHOLD 但携带阈值",
                    error_code="REQUIREMENT_INVALID",
                )
        elif (self.threshold is None or not self.threshold.strip()) and _is_vague(self.statement):
            raise DomainError(
                f"requirement {self.requirement_id!r} 含无阈值形容词且没有阈值："
                f"{self.statement!r}；必须标记 UNRESOLVED_THRESHOLD 或给出可测阈值",
                error_code="REQUIREMENT_UNRESOLVED_THRESHOLD",
            )
        expected_hash = sha256_hex(self.content_payload())
        if self.content_hash is not None and self.content_hash != expected_hash:
            raise DomainError(
                f"content_hash of requirement {self.requirement_id!r} does not match content",
                error_code="ARTIFACT_HASH_MISMATCH",
            )
        object.__setattr__(self, "content_hash", expected_hash)

    def content_payload(self) -> dict[str, Any]:
        payload = asdict(self)
        payload.pop("content_hash", None)
        return _canonical_payload(payload)

    def to_event_payload(self) -> dict[str, Any]:
        return _canonical_payload(asdict(self))


@dataclass(frozen=True, slots=True)
class RequirementsBaseline:
    """ENG2 requirements baseline (03B, section 5.3)."""

    baseline_id: str
    version: int
    project_id: str
    conops_id: str
    input_spec_hash: str
    conops_hash: str
    source_refs_required: tuple[str, ...]
    requirements: tuple[EngineeringRequirement, ...]
    artifact_hash: str | None = None
    status: str = "ACTIVE"
    created_at: datetime | None = None

    def __post_init__(self) -> None:
        seen: set[str] = set()
        for requirement in self.requirements:
            if requirement.requirement_id in seen:
                raise DomainError(
                    f"duplicate requirement id {requirement.requirement_id!r}",
                    error_code="REQUIREMENT_INVALID",
                )
            seen.add(requirement.requirement_id)
        finalize_artifact_hash(self)

    def content_payload(self) -> dict[str, Any]:
        payload = asdict(self)
        payload.pop("artifact_hash", None)
        payload.pop("status", None)
        return _canonical_payload(payload)

    def to_event_payload(self) -> dict[str, Any]:
        return _canonical_payload(asdict(self))

    @property
    def critical_requirement_ids(self) -> tuple[str, ...]:
        return tuple(
            requirement.requirement_id
            for requirement in self.requirements
            if requirement.priority is RequirementPriority.CRITICAL
        )


def requirements_baseline_blockers(baseline: RequirementsBaseline) -> tuple[str, ...]:
    """Return ENG2 pass-criteria blockers (03B, section 5.4)."""
    blockers: list[str] = []
    covered = {ref for requirement in baseline.requirements for ref in requirement.source_refs}
    required = set(baseline.source_refs_required)
    if required and not required.issubset(covered):
        blockers.append("source_coverage 未达 100%：" + ", ".join(sorted(required - covered)))
    critical_without_acceptance = [
        requirement.requirement_id
        for requirement in baseline.requirements
        if requirement.priority is RequirementPriority.CRITICAL
        and not has_measurable_acceptance(
            threshold=requirement.threshold,
            acceptance_criterion=requirement.acceptance_criterion,
        )
    ]
    if critical_without_acceptance:
        blockers.append(
            "critical_requirement_with_numeric_or_boolean_acceptance 未达 100%："
            + ", ".join(critical_without_acceptance)
        )
    critical_conflicts = {
        conflict
        for requirement in baseline.requirements
        if requirement.priority is RequirementPriority.CRITICAL
        for conflict in requirement.conflict_refs
    }
    if critical_conflicts:
        blockers.append(
            "unresolved_critical_conflicts 非 0：" + ", ".join(sorted(critical_conflicts))
        )
    unresolved_critical = [
        requirement.requirement_id
        for requirement in baseline.requirements
        if requirement.priority is RequirementPriority.CRITICAL
        and requirement.status is RequirementStatus.UNRESOLVED_THRESHOLD
    ]
    if unresolved_critical:
        blockers.append("unresolved_critical_thresholds 非 0：" + ", ".join(unresolved_critical))
    return tuple(blockers)


@dataclass(frozen=True, slots=True)
class AcceptanceCriterion:
    """One acceptance criterion (03B, sections 5.1/5.3)."""

    criterion_id: str
    requirement_id: str
    acceptance_criterion: str
    verification_method: VerificationMethod
    measurement_method: str
    unit: str
    threshold: str | None
    tolerance: str | None

    def to_event_payload(self) -> dict[str, Any]:
        return _canonical_payload(asdict(self))


@dataclass(frozen=True, slots=True)
class AcceptanceCriteriaCatalog:
    """ENG2 acceptance criteria catalog (03B, section 5.3)."""

    catalog_id: str
    project_id: str
    baseline_id: str
    criteria: tuple[AcceptanceCriterion, ...]

    def __post_init__(self) -> None:
        seen: set[str] = set()
        for criterion in self.criteria:
            if criterion.criterion_id in seen:
                raise DomainError(
                    f"duplicate acceptance criterion {criterion.criterion_id!r}",
                    error_code="ACCEPTANCE_CATALOG_INVALID",
                )
            seen.add(criterion.criterion_id)

    def to_event_payload(self) -> dict[str, Any]:
        return _canonical_payload(asdict(self))


def acceptance_catalog_blockers(
    catalog: AcceptanceCriteriaCatalog, baseline: RequirementsBaseline
) -> tuple[str, ...]:
    """Every requirement must have at least one acceptance criterion (03B, 5.3)."""
    covered = {criterion.requirement_id for criterion in catalog.criteria}
    missing = [
        requirement.requirement_id
        for requirement in baseline.requirements
        if requirement.requirement_id not in covered
    ]
    if missing:
        return ("requirements without acceptance criteria: " + ", ".join(missing),)
    return ()


@dataclass(frozen=True, slots=True)
class QualityAttributeScenario:
    """One ISO/IEC 25010-derived quality scenario with project threshold (03B, 5.2)."""

    scenario_id: str
    quality_characteristic: str
    statement: str
    project_threshold: str
    evidence_refs: tuple[str, ...]

    def __post_init__(self) -> None:
        if not self.project_threshold.strip() or not self.evidence_refs:
            raise DomainError(
                f"quality scenario {self.scenario_id!r} 必须带项目阈值与逐项证据",
                error_code="QUALITY_SCENARIO_INVALID",
            )

    def to_event_payload(self) -> dict[str, Any]:
        return _canonical_payload(asdict(self))


@dataclass(frozen=True, slots=True)
class QualityAttributeScenarioSet:
    """ENG2 quality scenario set (03B, section 5.3)."""

    set_id: str
    project_id: str
    scenarios: tuple[QualityAttributeScenario, ...]

    def to_event_payload(self) -> dict[str, Any]:
        return _canonical_payload(asdict(self))


@dataclass(frozen=True, slots=True)
class SecurityPrivacyComplianceObligation:
    """One NIST SSDF / AI-obligation mapping (03B, section 5.2)."""

    obligation_id: str
    framework: str  # e.g. NIST SSDF Prepare/Protect/Produce/Respond
    responsibility: str
    artifact: str
    verification: str
    ai_data_source: str | None = None
    ai_provider_boundary: str | None = None
    ai_known_failures: str | None = None
    ai_human_oversight: str | None = None
    ai_drift: str | None = None
    ai_misuse_scenarios: str | None = None

    def __post_init__(self) -> None:
        if (
            not self.responsibility.strip()
            or not self.artifact.strip()
            or not self.verification.strip()
        ):
            raise DomainError(
                f"obligation {self.obligation_id!r} 必须映射责任、工件与验证",
                error_code="OBLIGATION_INVALID",
            )
        if "AI" in self.framework.upper() or any(
            value is not None
            for value in (
                self.ai_data_source,
                self.ai_provider_boundary,
                self.ai_known_failures,
            )
        ):
            for field_name in (
                "ai_data_source",
                "ai_provider_boundary",
                "ai_known_failures",
                "ai_human_oversight",
                "ai_drift",
                "ai_misuse_scenarios",
            ):
                if getattr(self, field_name) is None:
                    raise DomainError(
                        f"AI obligation {self.obligation_id!r} 缺少 {field_name}",
                        error_code="OBLIGATION_INVALID",
                    )

    def to_event_payload(self) -> dict[str, Any]:
        return _canonical_payload(asdict(self))


@dataclass(frozen=True, slots=True)
class SecurityPrivacyComplianceObligationSet:
    """ENG2 security/privacy/compliance obligation set (03B, section 5.3)."""

    set_id: str
    project_id: str
    obligations: tuple[SecurityPrivacyComplianceObligation, ...]

    def to_event_payload(self) -> dict[str, Any]:
        return _canonical_payload(asdict(self))


class DecisionStatus(StrictStrEnum):
    """Unresolved decision register statuses (03B, section 5.3)."""

    OPEN = "OPEN"
    RESOLVED = "RESOLVED"


@dataclass(frozen=True, slots=True)
class UnresolvedDecision:
    """One recorded decision with owner (03B, section 5.3)."""

    decision_id: str
    description: str
    owner: str
    critical: bool
    status: DecisionStatus = DecisionStatus.OPEN

    def to_event_payload(self) -> dict[str, Any]:
        return _canonical_payload(asdict(self))


@dataclass(frozen=True, slots=True)
class UnresolvedDecisionRegister:
    """ENG2 unresolved decision register (03B, section 5.3)."""

    register_id: str
    project_id: str
    decisions: tuple[UnresolvedDecision, ...]

    def to_event_payload(self) -> dict[str, Any]:
        return _canonical_payload(asdict(self))


def unresolved_decision_blockers(register: UnresolvedDecisionRegister) -> tuple[str, ...]:
    """Critical open decisions block the baseline (03B, section 5.4)."""
    critical_open = [
        decision.decision_id
        for decision in register.decisions
        if decision.critical and decision.status is DecisionStatus.OPEN
    ]
    if critical_open:
        return ("unresolved_critical_conflicts 非 0：" + ", ".join(critical_open),)
    return ()


__all__ = [
    "AcceptanceCriteriaCatalog",
    "AcceptanceCriterion",
    "DecisionStatus",
    "EngineeringRequirement",
    "QualityAttributeScenario",
    "QualityAttributeScenarioSet",
    "RequirementPriority",
    "RequirementStatus",
    "RequirementType",
    "RequirementsBaseline",
    "SecurityPrivacyComplianceObligation",
    "SecurityPrivacyComplianceObligationSet",
    "UnresolvedDecision",
    "UnresolvedDecisionRegister",
    "VAGUE_THRESHOLD_PATTERNS",
    "VerificationMethod",
    "acceptance_catalog_blockers",
    "has_measurable_acceptance",
    "requirements_baseline_blockers",
    "unresolved_decision_blockers",
]
