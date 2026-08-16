"""Engineering maturity assessment (19 §5 M13.2).

Requires at least two concrete evidence items per neighbor; popularity
(stars/downloads/marketing) never counts as maturity.  Ranking is
function/application-sourced: every contributing feature value carries an
evidence reference.
"""

from __future__ import annotations

from dataclasses import dataclass

from synaisthesis.domain.errors import DomainError
from synaisthesis.providers.prior_art.engineering_base import (
    EngineeringNeighborHit,
    EngineeringNeighborProvider,
    EngineeringNeighborQuery,
    feature_score,
    maturity_evidence_check,
)


@dataclass(frozen=True, slots=True)
class RankedNeighbor:
    """A neighbor with maturity verdict and a sourced ranking score."""

    hit: EngineeringNeighborHit
    maturity: tuple[str, ...]
    rank_score: float
    rank_refs: tuple[str, ...]


def assess_maturity(hit: EngineeringNeighborHit) -> tuple[str, ...]:
    """Return maturity evidence lines; raise DomainError when insufficient."""
    ok, reasons = maturity_evidence_check(hit)
    if not ok:
        raise DomainError(
            f"邻居 {hit.stable_identifier!r} 成熟度不足: {'; '.join(reasons)}",
            error_code="MATURITY_EVIDENCE_INSUFFICIENT",
        )
    return tuple(f"{claim} ({ref})" for claim, ref in hit.maturity_evidence)


def rank_engineering_neighbors(
    hits: tuple[EngineeringNeighborHit, ...],
    function_weights: dict[str, float],
    application_weights: dict[str, float],
) -> tuple[RankedNeighbor, ...]:
    """Rank by weighted function/application features, every score sourced."""
    ranked: list[RankedNeighbor] = []
    for hit in hits:
        maturity = assess_maturity(hit)
        f_score, f_refs = feature_score(hit.function_features, function_weights)
        a_score, a_refs = feature_score(hit.application_features, application_weights)
        refs = f_refs + a_refs
        if f_score > 0.0 and not f_refs:
            raise DomainError(
                f"邻居 {hit.stable_identifier!r} 功能排序缺乏证据引用",
                error_code="NEIGHBOR_RANK_UNSOURCED",
            )
        if a_score > 0.0 and not a_refs:
            raise DomainError(
                f"邻居 {hit.stable_identifier!r} 应用排序缺乏证据引用",
                error_code="NEIGHBOR_RANK_UNSOURCED",
            )
        ranked.append(
            RankedNeighbor(
                hit=hit,
                maturity=maturity,
                rank_score=f_score + a_score,
                rank_refs=refs,
            )
        )
    return tuple(
        sorted(ranked, key=lambda item: (item.rank_score, item.hit.stable_identifier), reverse=True)
    )


def deduplicate_neighbors(
    hits: tuple[EngineeringNeighborHit, ...],
) -> tuple[EngineeringNeighborHit, ...]:
    """Deduplicate by stable identifier then canonical URL, keeping first."""
    seen_ids: set[str] = set()
    seen_urls: set[str] = set()
    unique: list[EngineeringNeighborHit] = []
    for hit in hits:
        if hit.stable_identifier in seen_ids or hit.canonical_url in seen_urls:
            continue
        seen_ids.add(hit.stable_identifier)
        seen_urls.add(hit.canonical_url)
        unique.append(hit)
    return tuple(unique)


def collect_quarantined_texts(
    hits: tuple[EngineeringNeighborHit, ...],
) -> tuple[tuple[str, str], ...]:
    """All external texts stay quarantined: (content, source_ref) pairs."""
    return tuple((text.content, text.source_ref) for hit in hits for text in hit.untrusted_texts)


def search_all_neighbors(
    query: EngineeringNeighborQuery,
    providers: tuple[EngineeringNeighborProvider, ...],
    function_weights: dict[str, float],
    application_weights: dict[str, float],
) -> tuple[RankedNeighbor, ...]:
    """Query every provider, deduplicate, assess maturity and rank."""
    collected: list[EngineeringNeighborHit] = []
    for provider in providers:
        collected.extend(provider.search_engineering_neighbors(query))
    unique = deduplicate_neighbors(tuple(collected))
    return rank_engineering_neighbors(unique, function_weights, application_weights)


__all__ = [
    "RankedNeighbor",
    "assess_maturity",
    "collect_quarantined_texts",
    "deduplicate_neighbors",
    "rank_engineering_neighbors",
    "search_all_neighbors",
]
