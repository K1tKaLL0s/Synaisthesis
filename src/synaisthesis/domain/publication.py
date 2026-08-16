"""Engineering manuscript evidence policy and compliance status (03B, sections 11-12).

Paper type is derived from the evidence tier (03B, section 11.1); a
BLUEPRINT_ONLY project may never claim implementation or measured results.
Every substantive claim binds a claim id with a real receipt (or is PLANNED),
and author-owned fields must be explicitly USER_PROVIDED instead of
fabricated placeholders (03B, section 11.2).
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime
from typing import Any

from synaisthesis.domain.engineering import finalize_artifact_hash
from synaisthesis.domain.enums import StrictStrEnum
from synaisthesis.domain.errors import DomainError
from synaisthesis.domain.event import canonicalize


def _canonical_payload(value: Any) -> dict[str, Any]:
    payload = canonicalize(value)
    if not isinstance(payload, dict):
        raise TypeError("publication payload must canonicalize to an object")
    return payload


class EngineeringEvidenceTier(StrictStrEnum):
    """Evidence tiers driving allowed paper types (03B, section 11.1)."""

    BLUEPRINT_ONLY = "BLUEPRINT_ONLY"
    PROTOTYPE_ENGINEERING_VERIFIED = "PROTOTYPE_ENGINEERING_VERIFIED"
    PROTOTYPE_VV_VERIFIED = "PROTOTYPE_VV_VERIFIED"
    MATURE_OPEN_SOURCE = "MATURE_OPEN_SOURCE"


class EngineeringPaperType(StrictStrEnum):
    """Engineering manuscript paper types (03B, sections 9.1/11.1)."""

    DESIGN_ARTICLE = "DESIGN_ARTICLE"
    PROTOCOL_ARTICLE = "PROTOCOL_ARTICLE"
    DESIGN_ARTICLE_DRAFT = "DESIGN_ARTICLE_DRAFT"
    PROTOCOL_MANUSCRIPT_DRAFT = "PROTOCOL_MANUSCRIPT_DRAFT"
    SYSTEMS_ARTICLE = "SYSTEMS_ARTICLE"
    METHODS_ARTICLE = "METHODS_ARTICLE"
    FULL_ENGINEERING_RESEARCH_ARTICLE = "FULL_ENGINEERING_RESEARCH_ARTICLE"
    RESEARCH_SOFTWARE_ARTICLE = "RESEARCH_SOFTWARE_ARTICLE"


#: paper types allowed per evidence tier (03B, section 11.1).
ALLOWED_PAPER_TYPES: dict[EngineeringEvidenceTier, frozenset[EngineeringPaperType]] = {
    EngineeringEvidenceTier.BLUEPRINT_ONLY: frozenset(
        {
            EngineeringPaperType.DESIGN_ARTICLE,
            EngineeringPaperType.PROTOCOL_ARTICLE,
            EngineeringPaperType.DESIGN_ARTICLE_DRAFT,
            EngineeringPaperType.PROTOCOL_MANUSCRIPT_DRAFT,
        }
    ),
    EngineeringEvidenceTier.PROTOTYPE_ENGINEERING_VERIFIED: frozenset(
        {
            EngineeringPaperType.SYSTEMS_ARTICLE,
            EngineeringPaperType.METHODS_ARTICLE,
        }
    ),
    EngineeringEvidenceTier.PROTOTYPE_VV_VERIFIED: frozenset(
        {EngineeringPaperType.FULL_ENGINEERING_RESEARCH_ARTICLE}
    ),
    EngineeringEvidenceTier.MATURE_OPEN_SOURCE: frozenset(
        {EngineeringPaperType.RESEARCH_SOFTWARE_ARTICLE}
    ),
}

#: Deterministic claim markers that require a real receipt (03B, section 11.2).
COMPLETION_CLAIM_MARKERS: tuple[str, ...] = (
    "已验证",
    "证明",
    "结果表明",
    "优于",
    "提升",
    "IMPLEMENTED",
    "VERIFIED",
    "BETTER_THAN",
)

AUTHOR_FIELDS: tuple[str, ...] = (
    "author_contributions",
    "ai_use_disclosure",
    "funding",
    "conflicts",
    "acknowledgements",
)

AUTHOR_INPUT_NEEDS = "NEEDS_AUTHOR_INPUT"
AUTHOR_INPUT_PROVIDED = "USER_PROVIDED"


def paper_type_allowed_by_evidence(
    paper_type: EngineeringPaperType,
    evidence_tier: EngineeringEvidenceTier,
) -> bool:
    """03B section 11.1: evidence decides the paper type."""
    return paper_type in ALLOWED_PAPER_TYPES[evidence_tier]


class ClaimStatus(StrictStrEnum):
    """Claim evidence status (03B, sections 9.3/11.2)."""

    SUPPORTED = "SUPPORTED"
    PLANNED = "PLANNED"
    UNSUPPORTED = "UNSUPPORTED"


@dataclass(frozen=True, slots=True)
class ClaimEvidenceEntry:
    """One claim-to-evidence binding (03B, section 11.2)."""

    claim_id: str
    statement: str
    source_requirement_id: str | None
    design_element_id: str | None
    evidence_receipt_id: str | None
    figure_table_ref: str | None
    citation_ref: str | None
    status: ClaimStatus = ClaimStatus.PLANNED

    def __post_init__(self) -> None:
        if not self.claim_id.strip() or not self.statement.strip():
            raise DomainError(
                "claim requires claim_id and statement",
                error_code="CLAIM_EVIDENCE_INVALID",
            )
        if self.status is ClaimStatus.SUPPORTED and not self.evidence_receipt_id:
            raise DomainError(
                f"claim {self.claim_id!r} 标记 SUPPORTED 但没有真实回执",
                error_code="MANUSCRIPT_CLAIM_UNSUPPORTED",
            )

    def to_event_payload(self) -> dict[str, Any]:
        return _canonical_payload(asdict(self))


@dataclass(frozen=True, slots=True)
class ClaimEvidenceMatrix:
    """ENG6/ENG8 claim evidence matrix (03B, section 9.3)."""

    matrix_id: str
    project_id: str
    entries: tuple[ClaimEvidenceEntry, ...]

    def __post_init__(self) -> None:
        seen: set[str] = set()
        for entry in self.entries:
            if entry.claim_id in seen:
                raise DomainError(
                    f"duplicate claim id {entry.claim_id!r}",
                    error_code="CLAIM_EVIDENCE_INVALID",
                )
            seen.add(entry.claim_id)

    def to_event_payload(self) -> dict[str, Any]:
        return _canonical_payload(asdict(self))

    def entry(self, claim_id: str) -> ClaimEvidenceEntry | None:
        return next(
            (entry for entry in self.entries if entry.claim_id == claim_id),
            None,
        )


def manuscript_claim_blockers(
    matrix: ClaimEvidenceMatrix, claims: tuple[str, ...]
) -> tuple[str, ...]:
    """Claims using completion tense without a receipt are unsupported (03B, 11.2)."""
    blockers: list[str] = []
    for claim_id in claims:
        entry = matrix.entry(claim_id)
        if entry is None:
            blockers.append(f"claim {claim_id!r} 未在 ClaimEvidenceMatrix 中登记")
            continue
        if entry.evidence_receipt_id is None and any(
            marker in entry.statement for marker in COMPLETION_CLAIM_MARKERS
        ):
            blockers.append(
                f"claim {claim_id!r} 使用完成时态但没有真实回执，必须删除或降级为 PLANNED"
            )
    return tuple(blockers)


class EngineeringManuscriptAuditStatus(StrictStrEnum):
    """Master manuscript audit status (03B, section 11.3)."""

    NOT_AUDITED = "NOT_AUDITED"
    AUDITED_WITH_FINDINGS = "AUDITED_WITH_FINDINGS"
    AUDITED_CLEAN = "AUDITED_CLEAN"


@dataclass(frozen=True, slots=True)
class EngineeringMasterManuscript:
    """ENG8 journal-neutral master manuscript (03B, section 11.2)."""

    manuscript_id: str
    version: int
    project_id: str
    paper_type: EngineeringPaperType
    evidence_tier: EngineeringEvidenceTier
    title: str
    abstract: str
    keywords: tuple[str, ...]
    statement_of_need: str
    related_work_neighbors: tuple[str, ...]
    requirements_conops_design: str
    method_architecture: str
    vv_methods: str
    results: str
    comparison_with_baseline: str
    threats_limitations: str
    application_extension: str
    security_privacy_ethics: str
    data_availability: str
    reproducibility_instructions: str
    conclusion: str
    references: tuple[str, ...]
    author_contributions: str
    ai_use_disclosure: str
    funding: str
    conflicts: str
    acknowledgements: str
    author_input_status: dict[str, str]
    claim_ids: tuple[str, ...]
    master_hash: str | None = None
    status: str = "DRAFT"
    audit_status: EngineeringManuscriptAuditStatus = EngineeringManuscriptAuditStatus.NOT_AUDITED
    created_at: datetime | None = None

    def __post_init__(self) -> None:
        if not paper_type_allowed_by_evidence(self.paper_type, self.evidence_tier):
            raise DomainError(
                f"paper_type {self.paper_type.value} 不允许于 evidence tier "
                f"{self.evidence_tier.value}",
                error_code="MANUSCRIPT_PAPER_TYPE_INVALID",
            )
        for field_name in AUTHOR_FIELDS:
            value = getattr(self, field_name)
            status = self.author_input_status.get(field_name)
            if value and value != AUTHOR_INPUT_NEEDS and status != AUTHOR_INPUT_PROVIDED:
                raise DomainError(
                    f"manuscript 字段 {field_name!r} 非空但未标记 USER_PROVIDED；"
                    "不得生成虚构作者输入",
                    error_code="MANUSCRIPT_AUTHOR_INPUT_INVALID",
                )
            if not value and status != AUTHOR_INPUT_NEEDS:
                raise DomainError(
                    f"manuscript 字段 {field_name!r} 为空必须标记 NEEDS_AUTHOR_INPUT",
                    error_code="MANUSCRIPT_AUTHOR_INPUT_INVALID",
                )
        finalize_artifact_hash(self, field="master_hash")

    def content_payload(self) -> dict[str, Any]:
        payload = asdict(self)
        payload.pop("master_hash", None)
        payload.pop("status", None)
        payload.pop("audit_status", None)
        return _canonical_payload(payload)

    def to_event_payload(self) -> dict[str, Any]:
        return _canonical_payload(asdict(self))


def master_manuscript_blockers(
    manuscript: EngineeringMasterManuscript,
    claim_matrix: ClaimEvidenceMatrix,
) -> tuple[str, ...]:
    """Audit and claim checks before ENGINEERING_MASTER_MANUSCRIPT_READY (03B, 11.3)."""
    blockers: list[str] = []
    if manuscript.audit_status is not EngineeringManuscriptAuditStatus.AUDITED_CLEAN:
        blockers.append("母稿尚未由未参与生成的独立 Auditor 审计通过")
    claim_blockers = manuscript_claim_blockers(claim_matrix, manuscript.claim_ids)
    blockers.extend(claim_blockers)
    return tuple(blockers)


class TheoryEvidenceTier(StrictStrEnum):
    """Theory evidence tiers (03C, section 4.3)."""

    PROVED_AND_SEMANTICALLY_ACCEPTED = "PROVED_AND_SEMANTICALLY_ACCEPTED"
    FORMALLY_VERIFIED = "FORMALLY_VERIFIED"
    COMPUTER_ASSISTED_PROOF = "COMPUTER_ASSISTED_PROOF"
    COUNTEREXAMPLE_OR_NEGATIVE_RESULT = "COUNTEREXAMPLE_OR_NEGATIVE_RESULT"
    PARTIAL_THEORY = "PARTIAL_THEORY"
    DESIGN_ONLY = "DESIGN_ONLY"


class TheoryPaperType(StrictStrEnum):
    """Theory paper types (03C, section 4.3)."""

    FULL_THEORY_ARTICLE = "FULL_THEORY_ARTICLE"
    FORMALIZED_THEORY_ARTICLE = "FORMALIZED_THEORY_ARTICLE"
    COMPUTER_ASSISTED_THEORY_ARTICLE = "COMPUTER_ASSISTED_THEORY_ARTICLE"
    NEGATIVE_RESULT_ARTICLE = "NEGATIVE_RESULT_ARTICLE"
    RESEARCH_NOTE = "RESEARCH_NOTE"
    CONJECTURE_OR_OPEN_PROBLEM_ARTICLE = "CONJECTURE_OR_OPEN_PROBLEM_ARTICLE"
    THEORY_PROTOCOL_OR_PROGRAMME_DRAFT = "THEORY_PROTOCOL_OR_PROGRAMME_DRAFT"


THEORY_ALLOWED_PAPER_TYPES: dict[TheoryEvidenceTier, frozenset[TheoryPaperType]] = {
    TheoryEvidenceTier.PROVED_AND_SEMANTICALLY_ACCEPTED: frozenset(
        {TheoryPaperType.FULL_THEORY_ARTICLE}
    ),
    TheoryEvidenceTier.FORMALLY_VERIFIED: frozenset({TheoryPaperType.FORMALIZED_THEORY_ARTICLE}),
    TheoryEvidenceTier.COMPUTER_ASSISTED_PROOF: frozenset(
        {TheoryPaperType.COMPUTER_ASSISTED_THEORY_ARTICLE}
    ),
    TheoryEvidenceTier.COUNTEREXAMPLE_OR_NEGATIVE_RESULT: frozenset(
        {TheoryPaperType.NEGATIVE_RESULT_ARTICLE}
    ),
    TheoryEvidenceTier.PARTIAL_THEORY: frozenset(
        {
            TheoryPaperType.RESEARCH_NOTE,
            TheoryPaperType.CONJECTURE_OR_OPEN_PROBLEM_ARTICLE,
        }
    ),
    TheoryEvidenceTier.DESIGN_ONLY: frozenset({TheoryPaperType.THEORY_PROTOCOL_OR_PROGRAMME_DRAFT}),
}


def theory_paper_type_allowed_by_evidence(
    paper_type: TheoryPaperType, evidence_tier: TheoryEvidenceTier
) -> bool:
    """03C section 4.3: evidence tier decides the allowed theory paper type."""
    return paper_type in THEORY_ALLOWED_PAPER_TYPES[evidence_tier]


class TheoryManuscriptAuditStatus(StrictStrEnum):
    """Theory master manuscript audit lifecycle (03C, section 6)."""

    NOT_AUDITED = "NOT_AUDITED"
    AUDITED_WITH_FINDINGS = "AUDITED_WITH_FINDINGS"
    AUDITED_CLEAN = "AUDITED_CLEAN"
    BLOCKED_THEORY_MASTER_MANUSCRIPT = "BLOCKED_THEORY_MASTER_MANUSCRIPT"


class VenueComplianceStatus(StrictStrEnum):
    """Compliance matrix statuses (03B, section 12.3)."""

    PASS = "PASS"
    FAIL = "FAIL"
    NEEDS_AUTHOR_INPUT = "NEEDS_AUTHOR_INPUT"
    NOT_APPLICABLE = "NOT_APPLICABLE"
    STALE_GUIDANCE = "STALE_GUIDANCE"


@dataclass(frozen=True, slots=True)
class VenueComplianceEntry:
    """One compliance requirement verdict (03B, section 12.3)."""

    requirement_id: str
    status: VenueComplianceStatus
    evidence_ref: str | None = None

    def __post_init__(self) -> None:
        if self.status is VenueComplianceStatus.PASS and not self.evidence_ref:
            raise DomainError(
                f"compliance entry {self.requirement_id!r} PASS 必须引用稿件位置或工件证据",
                error_code="COMPLIANCE_MATRIX_INVALID",
            )

    def to_event_payload(self) -> dict[str, Any]:
        return _canonical_payload(asdict(self))


@dataclass(frozen=True, slots=True)
class VenueComplianceMatrix:
    """ENG9 compliance matrix (03B, section 12.3)."""

    matrix_id: str
    project_id: str
    profile_id: str
    entries: tuple[VenueComplianceEntry, ...]

    def to_event_payload(self) -> dict[str, Any]:
        return _canonical_payload(asdict(self))


def compliance_blockers(matrix: VenueComplianceMatrix) -> tuple[str, ...]:
    """FAIL/STALE_GUIDANCE entries block a submission candidate (03B, section 13.3)."""
    blockers: list[str] = []
    for entry in matrix.entries:
        if entry.status is VenueComplianceStatus.FAIL:
            blockers.append(f"compliance {entry.requirement_id!r} FAIL")
        if entry.status is VenueComplianceStatus.STALE_GUIDANCE:
            blockers.append(
                f"compliance {entry.requirement_id!r} STALE_GUIDANCE，需重新检索官方指南"
            )
    return tuple(blockers)


__all__ = [
    "ALLOWED_PAPER_TYPES",
    "THEORY_ALLOWED_PAPER_TYPES",
    "TheoryEvidenceTier",
    "TheoryManuscriptAuditStatus",
    "TheoryPaperType",
    "theory_paper_type_allowed_by_evidence",
    "AUTHOR_FIELDS",
    "AUTHOR_INPUT_NEEDS",
    "AUTHOR_INPUT_PROVIDED",
    "COMPLETION_CLAIM_MARKERS",
    "ClaimEvidenceEntry",
    "ClaimEvidenceMatrix",
    "ClaimStatus",
    "EngineeringEvidenceTier",
    "EngineeringManuscriptAuditStatus",
    "EngineeringMasterManuscript",
    "EngineeringPaperType",
    "VenueComplianceEntry",
    "VenueComplianceMatrix",
    "VenueComplianceStatus",
    "compliance_blockers",
    "manuscript_claim_blockers",
    "master_manuscript_blockers",
    "paper_type_allowed_by_evidence",
]
