"""Deterministic prior-art normalization: proximity, dedup, sorting, ranking."""

from __future__ import annotations

from dataclasses import asdict

from synaisthesis.domain.errors import DomainError
from synaisthesis.domain.event import sha256_hex
from synaisthesis.domain.qualification import PriorArtNeighbor
from synaisthesis.providers.prior_art.base import (
    ApplicationProximityFeatures,
    PriorArtProviderKind,
    ProviderNeighborRecord,
    ProximityFeature,
    TheoryProximityFeatures,
)


def _validate_feature(feature: ProximityFeature, label: str) -> float:
    if isinstance(feature.value, bool) or not isinstance(feature.value, (int, float)):
        raise DomainError(
            f"{label} 分量必须是数值",
            error_code="PRIOR_ART_SCORE_INVALID",
        )
    if not 0.0 <= float(feature.value) <= 4.0:
        raise DomainError(
            f"{label} 分量必须在 [0, 4]",
            error_code="PRIOR_ART_SCORE_INVALID",
        )
    if not feature.evidence_refs or any(not ref.strip() for ref in feature.evidence_refs):
        raise DomainError(
            f"{label} 分量必须有非空证据引用",
            error_code="PRIOR_ART_EVIDENCE_MISSING",
        )
    return float(feature.value)


def calculate_theory_proximity(features: TheoryProximityFeatures) -> float:
    """theory_proximity = 0.35*object + 0.30*mechanism + 0.20*assumptions + 0.15*conclusion."""
    return (
        0.35 * _validate_feature(features.object_domain, "object_domain")
        + 0.30 * _validate_feature(features.mechanism, "mechanism")
        + 0.20 * _validate_feature(features.assumptions, "assumptions")
        + 0.15 * _validate_feature(features.conclusion, "conclusion")
    )


def calculate_application_proximity(features: ApplicationProximityFeatures) -> float:
    """application_proximity weighted sum over the six 0-4 components (03A §3.4)."""
    return (
        0.25 * _validate_feature(features.expected_function, "expected_function")
        + 0.20 * _validate_feature(features.use_context, "use_context")
        + 0.20 * _validate_feature(features.input_output, "input_output")
        + 0.15 * _validate_feature(features.system_architecture, "system_architecture")
        + 0.10 * _validate_feature(features.operational_constraints, "operational_constraints")
        + 0.10 * _validate_feature(features.maturity, "maturity")
    )


def _normalized(value: str | None) -> str | None:
    return value.strip().casefold() if value else None


def deduplicate_provider_records(
    records: tuple[ProviderNeighborRecord, ...] | list[ProviderNeighborRecord],
) -> tuple[ProviderNeighborRecord, ...]:
    """Deduplicate by stable identifier or canonical URL, keeping first occurrence.

    The function is deterministic for a given input order; the caller passes a
    stable provider-priority order (fake providers are ordered by source).
    """
    seen_ids: set[str] = set()
    seen_urls: set[str] = set()
    deduped: list[ProviderNeighborRecord] = []
    for record in records:
        stable = _normalized(record.stable_identifier)
        url = _normalized(record.canonical_url)
        if (stable is not None and stable in seen_ids) or (url is not None and url in seen_urls):
            continue
        if stable is not None:
            seen_ids.add(stable)
        if url is not None:
            seen_urls.add(url)
        deduped.append(record)
    return tuple(deduped)


def sort_provider_records(
    records: tuple[ProviderNeighborRecord, ...] | list[ProviderNeighborRecord],
    *,
    kind: PriorArtProviderKind,
) -> tuple[ProviderNeighborRecord, ...]:
    """Sort academic by theory_proximity desc, engineering by application_proximity desc."""
    if kind == "academic":
        return tuple(
            sorted(
                records,
                key=lambda record: (
                    -calculate_theory_proximity(record.theory_features),
                    record.stable_identifier.casefold(),
                    record.provider_name.casefold(),
                ),
            )
        )
    if kind == "engineering":
        return tuple(
            sorted(
                records,
                key=lambda record: (
                    -calculate_application_proximity(record.application_features),
                    record.stable_identifier.casefold(),
                    record.provider_name.casefold(),
                ),
            )
        )
    raise DomainError(
        f"unknown prior-art provider kind {kind!r}",
        error_code="PRIOR_ART_PROVIDER_INVALID",
    )


def to_prior_art_neighbor(
    record: ProviderNeighborRecord,
    *,
    rank: int,
) -> PriorArtNeighbor:
    """Normalize one provider record into an immutable domain neighbor."""
    if isinstance(rank, bool) or not isinstance(rank, int) or rank < 1:
        raise DomainError("rank 必须为 >=1 的整数", error_code="PRIOR_ART_RANK_INVALID")
    return PriorArtNeighbor(
        neighbor_id=f"{record.kind}:{record.stable_identifier}",
        neighbor_type=f"{record.kind}:{record.provider_name}",
        stable_identifier=record.stable_identifier,
        canonical_url=record.canonical_url,
        metadata_verified=record.metadata_verified,
        maturity_evidence_refs=record.maturity_evidence_refs,
        theory_proximity=calculate_theory_proximity(record.theory_features),
        application_proximity=calculate_application_proximity(record.application_features),
        similarity_evidence_refs=record.similarity_evidence_refs,
        rank=rank,
    )


def metadata_receipts(
    records: tuple[ProviderNeighborRecord, ...] | list[ProviderNeighborRecord],
) -> tuple[str, ...]:
    """Return sorted unique metadata-verification receipt identifiers."""
    return tuple(sorted({record.metadata_verification_receipt for record in records}))


def provider_record_hash(record: ProviderNeighborRecord) -> str:
    """Deterministic content hash for a raw provider record."""
    return sha256_hex(asdict(record))


__all__ = [
    "calculate_application_proximity",
    "calculate_theory_proximity",
    "deduplicate_provider_records",
    "metadata_receipts",
    "provider_record_hash",
    "sort_provider_records",
    "to_prior_art_neighbor",
]
