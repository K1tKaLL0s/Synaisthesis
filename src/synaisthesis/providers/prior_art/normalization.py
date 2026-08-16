"""Deterministic prior-art normalization: proximity, dedup, sorting, ranking."""

from __future__ import annotations

import json
from collections.abc import Mapping, Sequence
from dataclasses import asdict
from datetime import datetime
from typing import Any, Protocol

from synaisthesis.domain.errors import DomainError
from synaisthesis.domain.event import sha256_hex
from synaisthesis.domain.qualification import PriorArtNeighbor
from synaisthesis.providers.prior_art.base import (
    ApplicationProximityFeatures,
    ExternalText,
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


# ---------------------------------------------------------------------------
# Academic metadata normalization and injectable provider boundary (M13.1)
# ---------------------------------------------------------------------------


class AcademicHttpTransport(Protocol):
    """Injectable raw-HTTP boundary for academic prior-art providers (M13.1).

    M13.1 ships no real HTTP client and no credentials; callers inject this
    boundary and the real-network smoke test stays manual. ``get_text`` must
    raise on any transport failure (DNS, timeout, HTTP status, rate limit);
    providers convert that into a structured ``BLOCKED_NETWORK`` blocker.
    """

    def get_text(self, url: str, *, params: tuple[tuple[str, str], ...]) -> str: ...


class AcademicProviderError(DomainError):
    """Structured academic-provider failure; never fabricates neighbors."""

    def __init__(self, message: str, *, error_code: str, blocker_type: str, **kwargs: Any) -> None:
        super().__init__(message, error_code=error_code, blocker_type=blocker_type, **kwargs)


def fetch_provider_text(
    transport: AcademicHttpTransport,
    *,
    url: str,
    params: tuple[tuple[str, str], ...],
    source_name: str,
) -> str:
    """Fetch raw text through the injectable transport, failing closed.

    Any transport exception becomes a structured BLOCKED_NETWORK blocker so a
    dead network can never look like an empty (or fabricated) result set.
    """
    try:
        return transport.get_text(url, params=params)
    except AcademicProviderError:
        raise
    except Exception as exc:  # noqa: BLE001 - transport boundary must fail closed
        raise AcademicProviderError(
            f"{source_name} network request blocked: {type(exc).__name__}",
            error_code="BLOCKED_NETWORK",
            blocker_type="BLOCKED_NETWORK",
            recoverable=True,
        ) from exc


def parse_provider_json(raw: str, *, source_name: str) -> Any:
    """Parse a provider payload as JSON, mapping malformed input to FAILED_PROVIDER."""
    try:
        return json.loads(raw)
    except (ValueError, TypeError) as exc:
        raise AcademicProviderError(
            f"{source_name} returned a non-JSON payload",
            error_code="PROVIDER_SCHEMA_MISMATCH",
            blocker_type="FAILED_PROVIDER",
        ) from exc


def normalize_doi(value: str | None) -> str | None:
    """Return a canonical lowercase DOI with resolver prefixes stripped, else None."""
    if value is None:
        return None
    text = value.strip()
    if not text:
        return None
    lowered = text.casefold()
    for prefix in (
        "https://doi.org/",
        "http://doi.org/",
        "https://dx.doi.org/",
        "http://dx.doi.org/",
        "doi:",
    ):
        if lowered.startswith(prefix):
            text = text[len(prefix) :]
            break
    normalized = text.strip().casefold()
    if not normalized.startswith("10.") or "/" not in normalized:
        return None
    return normalized


def normalize_arxiv_id(value: str | None) -> str | None:
    """Return a canonical arXiv id (e.g. ``2001.00001``) without version suffix."""
    if value is None:
        return None
    text = value.strip()
    if not text:
        return None
    lowered = text.casefold()
    for prefix in ("arxiv:", "https://arxiv.org/abs/", "http://arxiv.org/abs/"):
        if lowered.startswith(prefix):
            text = text[len(prefix) :]
            break
    for index, char in enumerate(text):
        if index > 0 and char in "vV" and text[index + 1 :].isdigit():
            text = text[:index]
            break
    normalized = text.strip().casefold()
    return normalized or None


def extract_publication_year(value: Any) -> int | None:
    """Extract a 4-digit publication year from an int/str/date-parts structure."""
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value if 1000 <= value <= 9999 else None
    if isinstance(value, str):
        text = value.strip()
        if len(text) >= 4 and text[:4].isdigit():
            year = int(text[:4])
            return year if 1000 <= year <= 9999 else None
        return None
    if isinstance(value, Mapping):
        date_parts = value.get("date-parts")
        if isinstance(date_parts, Sequence) and not isinstance(date_parts, (str, bytes)):
            for part in date_parts:
                year = extract_publication_year(part)
                if year is not None:
                    return year
        return None
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
        for item in value:
            year = extract_publication_year(item)
            if year is not None:
                return year
        return None
    return None


def normalize_author_names(authors: Any) -> tuple[str, ...]:
    """Return deduplicated, non-empty author names in order, else ()."""
    if authors is None:
        return ()
    if isinstance(authors, (str, bytes)):
        name = str(authors).strip()
        return (name,) if name else ()
    if not isinstance(authors, Sequence):
        return ()
    names: list[str] = []
    seen: set[str] = set()
    for item in authors:
        if isinstance(item, Mapping):
            given = str(item.get("given") or "").strip()
            family = str(item.get("family") or "").strip()
            name = " ".join(part for part in (given, family) if part)
        elif isinstance(item, str):
            name = item.strip()
        else:
            continue
        if not name:
            continue
        key = name.casefold()
        if key not in seen:
            seen.add(key)
            names.append(name)
    return tuple(names)


def _is_year(text: str) -> bool:
    return len(text) == 4 and text.isdigit()


def parse_time_range(time_range: str) -> tuple[int | None, int | None]:
    """Parse ``YYYY`` or ``YYYY-YYYY`` into inclusive (from_year, to_year)."""
    text = (time_range or "").strip()
    if not text:
        return None, None
    parts = [part.strip() for part in text.split("-") if part.strip()]
    if len(parts) == 1 and _is_year(parts[0]):
        return int(parts[0]), int(parts[0])
    if len(parts) == 2 and _is_year(parts[0]) and _is_year(parts[1]):
        from_year, to_year = int(parts[0]), int(parts[1])
        if from_year <= to_year:
            return from_year, to_year
    raise AcademicProviderError(
        f"invalid time_range {time_range!r}; expected 'YYYY' or 'YYYY-YYYY'",
        error_code="PROVIDER_QUERY_INVALID",
        blocker_type="FAILED_PROVIDER",
    )


def metadata_verification_receipt(
    *,
    provider_name: str,
    stable_identifier: str,
    query_id: str,
    executed_at: datetime,
    page: int | None,
    per_page: int | None,
    result_count: int | None,
    publication_year: int | None = None,
) -> str:
    """Return a deterministic, traceable metadata receipt (19 §5 M13.1; 08 §13).

    The receipt binds one record to its query, pagination window, execution
    time and verification, so every neighbor's provenance can be recomputed.
    """
    year_component = f":year={publication_year}" if publication_year is not None else ""
    return (
        f"{provider_name}:metadata"
        f":query={query_id}"
        f":page={page}"
        f":per_page={per_page}"
        f":results={result_count}"
        f":executed={executed_at.isoformat()}"
        f":record={stable_identifier}"
        f"{year_component}"
    )


def build_academic_neighbor_record(
    *,
    provider_name: str,
    stable_identifier: str,
    canonical_url: str | None,
    query_id: str,
    executed_at: datetime,
    accessed_at: datetime,
    page: int | None,
    per_page: int | None,
    result_count: int | None,
    publication_year: int | None = None,
    title: str | None = None,
    abstract: str | None = None,
) -> ProviderNeighborRecord:
    """Normalize one retrieved academic metadata item into a provider record.

    Retrieval does not score semantic proximity, so every theory/application
    feature is 0.0 with the metadata receipt as its evidence reference; RQ2F
    assessment assigns the real proximity values later. External title/abstract
    text stays quarantined as untrusted ExternalText.
    """
    receipt = metadata_verification_receipt(
        provider_name=provider_name,
        stable_identifier=stable_identifier,
        query_id=query_id,
        executed_at=executed_at,
        page=page,
        per_page=per_page,
        result_count=result_count,
        publication_year=publication_year,
    )
    untrusted_texts: list[ExternalText] = []
    if title:
        untrusted_texts.append(
            ExternalText(content=title, source_ref=f"{provider_name}:{stable_identifier}:title")
        )
    if abstract:
        untrusted_texts.append(
            ExternalText(
                content=abstract, source_ref=f"{provider_name}:{stable_identifier}:abstract"
            )
        )
    return ProviderNeighborRecord(
        provider_name=provider_name,
        kind="academic",
        stable_identifier=stable_identifier,
        canonical_url=canonical_url,
        metadata_verified=True,
        metadata_verification_receipt=receipt,
        maturity_evidence_refs=(),
        theory_features=TheoryProximityFeatures(
            object_domain=ProximityFeature(value=0.0, evidence_refs=(receipt,)),
            mechanism=ProximityFeature(value=0.0, evidence_refs=(receipt,)),
            assumptions=ProximityFeature(value=0.0, evidence_refs=(receipt,)),
            conclusion=ProximityFeature(value=0.0, evidence_refs=(receipt,)),
        ),
        application_features=ApplicationProximityFeatures(
            expected_function=ProximityFeature(value=0.0, evidence_refs=(receipt,)),
            use_context=ProximityFeature(value=0.0, evidence_refs=(receipt,)),
            input_output=ProximityFeature(value=0.0, evidence_refs=(receipt,)),
            system_architecture=ProximityFeature(value=0.0, evidence_refs=(receipt,)),
            operational_constraints=ProximityFeature(value=0.0, evidence_refs=(receipt,)),
            maturity=ProximityFeature(value=0.0, evidence_refs=(receipt,)),
        ),
        similarity_evidence_refs=(receipt,),
        untrusted_texts=tuple(untrusted_texts),
        accessed_at=accessed_at,
    )


__all__ = [
    "AcademicHttpTransport",
    "AcademicProviderError",
    "build_academic_neighbor_record",
    "calculate_application_proximity",
    "calculate_theory_proximity",
    "deduplicate_provider_records",
    "extract_publication_year",
    "fetch_provider_text",
    "metadata_receipts",
    "metadata_verification_receipt",
    "normalize_arxiv_id",
    "normalize_author_names",
    "normalize_doi",
    "parse_provider_json",
    "parse_time_range",
    "provider_record_hash",
    "sort_provider_records",
    "to_prior_art_neighbor",
]
