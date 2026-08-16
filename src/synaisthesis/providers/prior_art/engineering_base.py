"""Engineering neighbor provider contracts (03B section 6.1, 19 §5 M13.2).

Function/application features always carry evidence references; maturity
requires at least two concrete evidence items and popularity (stars,
downloads, marketing) never counts alone.  External text stays quarantined.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Protocol, runtime_checkable

from synaisthesis.domain.errors import DomainError
from synaisthesis.providers.prior_art.base import ExternalText

MIN_MATURITY_EVIDENCE_ITEMS = 2

POPULARITY_MARKERS = ("star", "download", "weekly download", "marketing", "宣传", "星标")


@dataclass(frozen=True, slots=True)
class EngineeringNeighborHit:
    """One engineering neighbor with sourced features and maturity evidence."""

    stable_identifier: str
    canonical_url: str
    category: str
    function_features: dict[str, tuple[float, str]]
    application_features: dict[str, tuple[float, str]]
    maturity_evidence: tuple[tuple[str, str], ...]
    license_ref: str | None = None
    untrusted_texts: tuple[ExternalText, ...] = ()
    accessed_at: datetime | None = None

    def __post_init__(self) -> None:
        for feature_refs in (*self.function_features.values(), *self.application_features.values()):
            _value, ref = feature_refs
            if not ref.strip():
                raise DomainError(
                    f"hit {self.stable_identifier!r} 的功能/应用特征缺少证据引用",
                    error_code="NEIGHBOR_FEATURE_UNSOURCED",
                )

    def to_event_payload(self) -> dict[str, Any]:
        return {
            "stable_identifier": self.stable_identifier,
            "canonical_url": self.canonical_url,
            "category": self.category,
            "function_features": {
                key: list(value) for key, value in self.function_features.items()
            },
            "application_features": {
                key: list(value) for key, value in self.application_features.items()
            },
            "maturity_evidence": [list(item) for item in self.maturity_evidence],
            "license_ref": self.license_ref,
            "untrusted_texts": [
                {"content": text.content, "source_ref": text.source_ref}
                for text in self.untrusted_texts
            ],
            "accessed_at": self.accessed_at.isoformat() if self.accessed_at else None,
        }


@dataclass(frozen=True, slots=True)
class EngineeringNeighborQuery:
    """One ENG3 deep-search query (03B, section 6.1)."""

    query_id: str
    baseline_id: str
    requirement_refs: tuple[str, ...]
    original_text: str
    executed_at: datetime


@runtime_checkable
class EngineeringNeighborProvider(Protocol):
    """Synchronous engineering neighbor provider (M13.2)."""

    @property
    def source_name(self) -> str: ...

    def search_engineering_neighbors(
        self, query: EngineeringNeighborQuery
    ) -> tuple[EngineeringNeighborHit, ...]: ...


def maturity_evidence_check(hit: EngineeringNeighborHit) -> tuple[bool, tuple[str, ...]]:
    """Maturity requires >= 2 evidence items; popularity alone never counts."""
    evidence = hit.maturity_evidence
    if len(evidence) < MIN_MATURITY_EVIDENCE_ITEMS:
        return False, (f"成熟度证据少于 {MIN_MATURITY_EVIDENCE_ITEMS} 项",)
    popularity_only = all(
        any(marker in claim.lower() or marker in ref.lower() for marker in POPULARITY_MARKERS)
        for claim, ref in evidence
    )
    if popularity_only:
        return False, ("成熟度证据全部为 popularity（星标/下载/宣传），不得作为成熟度",)
    return True, ()


def feature_score(
    features: dict[str, tuple[float, str]], weights: dict[str, float]
) -> tuple[float, tuple[str, ...]]:
    """Weighted feature score; every contributing feature must cite a ref."""
    refs: list[str] = []
    total = 0.0
    for key, weight in weights.items():
        entry = features.get(key)
        if entry is None:
            continue
        value, ref = entry
        total += weight * value
        refs.append(ref)
    return total, tuple(refs)


__all__ = [
    "MIN_MATURITY_EVIDENCE_ITEMS",
    "POPULARITY_MARKERS",
    "EngineeringNeighborHit",
    "EngineeringNeighborProvider",
    "EngineeringNeighborQuery",
    "feature_score",
    "maturity_evidence_check",
]
