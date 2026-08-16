"""Engineering standards and reference-architecture evidence (03B ENG3; 19 §5 M13.4).

Traceability contract: every reference-set entry carries a stable identifier,
official URL, accessed time and concrete evidence references.  Star counts,
downloads or marketing text never count as evidence (03B, section 6.1).
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any, Literal

from synaisthesis.domain.errors import DomainError
from synaisthesis.providers.prior_art.engineering_base import (
    EngineeringNeighborHit,
    EngineeringNeighborProvider,
    EngineeringNeighborQuery,
)

StandardsCategory = Literal["STANDARD", "REFERENCE_ARCHITECTURE", "GOVERNMENT_GUIDELINE"]
ReferenceSourceCategory = Literal[
    "REPOSITORY",
    "STANDARD",
    "REFERENCE_ARCHITECTURE",
    "OFFICIAL_DOCS",
    "GOVERNMENT_GUIDELINE",
]


@dataclass(frozen=True, slots=True)
class EngineeringStandardEvidence:
    """One standard / reference-architecture / guideline with traceable refs."""

    standard_id: str
    organization: str
    title: str
    version: str
    category: StandardsCategory
    official_url: str
    accessed_at: datetime
    evidence_refs: tuple[str, ...]

    def __post_init__(self) -> None:
        if not self.official_url.startswith("http"):
            raise DomainError(
                f"standard {self.standard_id!r} 必须引用官方 URL",
                error_code="REFERENCE_UNSOURCED",
            )
        if not self.evidence_refs or any(not ref.strip() for ref in self.evidence_refs):
            raise DomainError(
                f"standard {self.standard_id!r} 缺少证据引用",
                error_code="REFERENCE_EVIDENCE_MISSING",
            )

    def to_event_payload(self) -> dict[str, Any]:
        return {
            "standard_id": self.standard_id,
            "organization": self.organization,
            "title": self.title,
            "version": self.version,
            "category": self.category,
            "official_url": self.official_url,
            "accessed_at": self.accessed_at.isoformat(),
            "evidence_refs": list(self.evidence_refs),
        }


_STANDARD_ACCESSED_AT = datetime(2025, 1, 20, tzinfo=UTC)

STANDARDS_CORPUS: tuple[EngineeringStandardEvidence, ...] = (
    EngineeringStandardEvidence(
        standard_id="standard/iso-iec-25010",
        organization="ISO/IEC",
        title="Systems and software Quality Requirements and Evaluation (SQuaRE)",
        version="25010:2023",
        category="STANDARD",
        official_url="https://www.iso.org/standard/78175.html",
        accessed_at=_STANDARD_ACCESSED_AT,
        evidence_refs=(
            "https://www.iso.org/standard/78175.html#quality-model",
            "https://www.iso.org/standard/78175.html#functional-suitability",
        ),
    ),
    EngineeringStandardEvidence(
        standard_id="standard/nist-ssdf",
        organization="NIST",
        title="Secure Software Development Framework",
        version="SSDF 1.1",
        category="GOVERNMENT_GUIDELINE",
        official_url="https://csrc.nist.gov/publications/detail/sp/800-218/final",
        accessed_at=_STANDARD_ACCESSED_AT,
        evidence_refs=(
            "https://csrc.nist.gov/publications/detail/sp/800-218/final#practices",
            "https://csrc.nist.gov/publications/detail/sp/800-218/final#tasks",
        ),
    ),
    EngineeringStandardEvidence(
        standard_id="arch/reference-traceability-architecture",
        organization="IEEE",
        title="Systems and software engineering — Architecture description",
        version="ISO/IEC/IEEE 42010:2022",
        category="REFERENCE_ARCHITECTURE",
        official_url="https://www.iso.org/standard/50508.html",
        accessed_at=_STANDARD_ACCESSED_AT,
        evidence_refs=(
            "https://www.iso.org/standard/50508.html#architecture-viewpoints",
            "https://www.iso.org/standard/50508.html#architecture-frameworks",
        ),
    ),
)


class StandardsProvider:
    """Deterministic engineering standards provider (fixture corpus injectable)."""

    source_name = "standards-fixture"

    def __init__(self, corpus: tuple[EngineeringStandardEvidence, ...] = STANDARDS_CORPUS) -> None:
        self._corpus = corpus

    def search_standards(self, query_text: str) -> tuple[EngineeringStandardEvidence, ...]:
        lowered = query_text.lower()
        return tuple(
            item
            for item in self._corpus
            if any(
                token in lowered
                for token in ("trace", "quality", "secure", "architecture", "reference")
            )
        )


@dataclass(frozen=True, slots=True)
class EngineeringReferenceEntry:
    """One traceable ENG3 reference-set entry (03B, section 6.1)."""

    category: ReferenceSourceCategory
    stable_identifier: str
    canonical_url: str
    accessed_at: datetime
    evidence_refs: tuple[str, ...]

    def __post_init__(self) -> None:
        if not self.canonical_url.startswith("http"):
            raise DomainError(
                f"reference {self.stable_identifier!r} 必须引用官方 URL",
                error_code="REFERENCE_UNSOURCED",
            )
        if not self.evidence_refs:
            raise DomainError(
                f"reference {self.stable_identifier!r} 缺少证据引用",
                error_code="REFERENCE_EVIDENCE_MISSING",
            )

    def to_event_payload(self) -> dict[str, Any]:
        return {
            "category": self.category,
            "stable_identifier": self.stable_identifier,
            "canonical_url": self.canonical_url,
            "accessed_at": self.accessed_at.isoformat(),
            "evidence_refs": list(self.evidence_refs),
        }


def _hit_to_entry(
    hit: EngineeringNeighborHit, category: ReferenceSourceCategory
) -> EngineeringReferenceEntry:
    feature_refs = tuple(
        ref for _value, ref in (*hit.function_features.values(), *hit.application_features.values())
    )
    maturity_refs = tuple(ref for _claim, ref in hit.maturity_evidence)
    return EngineeringReferenceEntry(
        category=category,
        stable_identifier=hit.stable_identifier,
        canonical_url=hit.canonical_url,
        accessed_at=hit.accessed_at or _STANDARD_ACCESSED_AT,
        evidence_refs=feature_refs + maturity_refs,
    )


def build_engineering_reference_set(
    *,
    query: EngineeringNeighborQuery,
    standards_provider: StandardsProvider,
    repository_provider: EngineeringNeighborProvider | None = None,
    official_docs_provider: EngineeringNeighborProvider | None = None,
    now: datetime | None = None,
) -> tuple[EngineeringReferenceEntry, ...]:
    """Assemble the ENG3 reference set with fully traceable entries.

    Repositories and official documentation come from the M13.2 neighbor
    providers; standards/reference architectures come from the standards
    provider.  Entries are deduplicated by (category, stable_identifier, URL)
    and every entry must cite concrete evidence references.
    """
    del now  # entries keep their own accessed_at
    entries: list[EngineeringReferenceEntry] = []
    if repository_provider is not None:
        entries.extend(
            _hit_to_entry(hit, "REPOSITORY")
            for hit in repository_provider.search_engineering_neighbors(query)
        )
    if official_docs_provider is not None:
        entries.extend(
            _hit_to_entry(hit, "OFFICIAL_DOCS")
            for hit in official_docs_provider.search_engineering_neighbors(query)
        )
    entries.extend(
        EngineeringReferenceEntry(
            category=item.category,
            stable_identifier=item.standard_id,
            canonical_url=item.official_url,
            accessed_at=item.accessed_at,
            evidence_refs=item.evidence_refs,
        )
        for item in standards_provider.search_standards(query.original_text)
    )

    seen: set[tuple[str, str, str]] = set()
    unique: list[EngineeringReferenceEntry] = []
    for entry in entries:
        key = (entry.category, entry.stable_identifier, entry.canonical_url)
        if key in seen:
            continue
        seen.add(key)
        unique.append(entry)

    repositories = sum(1 for entry in unique if entry.category == "REPOSITORY")
    standards = sum(1 for entry in unique if entry.category in {"STANDARD", "GOVERNMENT_GUIDELINE"})
    architectures = sum(1 for entry in unique if entry.category == "REFERENCE_ARCHITECTURE")
    if repositories < 1 or standards < 1 or architectures < 1:
        raise DomainError(
            "ENG3 参考集不完整：仓库/标准/参考架构证据必须各至少一项",
            error_code="ENGINEERING_REFERENCE_SET_INCOMPLETE",
        )
    return tuple(unique)


__all__ = [
    "EngineeringReferenceEntry",
    "EngineeringStandardEvidence",
    "ReferenceSourceCategory",
    "STANDARDS_CORPUS",
    "StandardsCategory",
    "StandardsProvider",
    "build_engineering_reference_set",
]
