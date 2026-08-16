"""Stable academic prior-art deduplication (M13.1; 19 §5 M13.1, 03A §3.3)."""

from __future__ import annotations

from collections.abc import Iterable

from synaisthesis.providers.prior_art.base import ProviderNeighborRecord
from synaisthesis.providers.prior_art.normalization import normalize_doi


def _stable_identifier_key(record: ProviderNeighborRecord) -> str | None:
    value = record.stable_identifier.strip().casefold()
    return value or None


def _doi_key(record: ProviderNeighborRecord) -> str | None:
    return normalize_doi(record.stable_identifier) or normalize_doi(record.canonical_url)


def _url_key(record: ProviderNeighborRecord) -> str | None:
    value = (record.canonical_url or "").strip().casefold()
    return value or None


def deduplicate_academic_records(
    records: Iterable[ProviderNeighborRecord],
) -> tuple[ProviderNeighborRecord, ...]:
    """Deduplicate academic records by stable identifier, DOI or URL.

    Keeps the first occurrence in input order, so the result is deterministic
    and recomputable for a fixed input order. A DOI match wins even when two
    providers expose the same work under different stable identifiers or
    landing URLs.
    """
    seen_ids: set[str] = set()
    seen_dois: set[str] = set()
    seen_urls: set[str] = set()
    deduped: list[ProviderNeighborRecord] = []
    for record in records:
        stable = _stable_identifier_key(record)
        doi = _doi_key(record)
        url = _url_key(record)
        if (
            (stable is not None and stable in seen_ids)
            or (doi is not None and doi in seen_dois)
            or (url is not None and url in seen_urls)
        ):
            continue
        if stable is not None:
            seen_ids.add(stable)
        if doi is not None:
            seen_dois.add(doi)
        if url is not None:
            seen_urls.add(url)
        deduped.append(record)
    return tuple(deduped)


__all__ = ["deduplicate_academic_records"]
