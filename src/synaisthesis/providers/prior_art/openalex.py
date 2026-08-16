"""OpenAlex academic prior-art provider adapter (M13.1; 03A §3, 08 §4).

Implements ``PriorArtProvider`` with an injectable raw-HTTP transport. No real
HTTP client or credentials ship here: tests inject frozen fixtures and the
real-network smoke test stays manual (19 §5 M13.1 stop condition).
"""

from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

from synaisthesis.domain.qualification import PriorArtQueryRecord
from synaisthesis.providers.prior_art.base import (
    PriorArtProviderKind,
    ProviderNeighborRecord,
)
from synaisthesis.providers.prior_art.normalization import (
    AcademicHttpTransport,
    AcademicProviderError,
    build_academic_neighbor_record,
    fetch_provider_text,
    parse_provider_json,
    parse_time_range,
)

_OPENALEX_WORKS_URL = "https://api.openalex.org/works"
_DEFAULT_PER_PAGE = 25


def _utcnow() -> datetime:
    return datetime.now(UTC)


def _string_field(item: Any, key: str) -> str | None:
    if not isinstance(item, Mapping):
        return None
    value = item.get(key)
    if isinstance(value, str) and value.strip():
        return value.strip()
    return None


def _int_field(item: Any, key: str) -> int | None:
    if not isinstance(item, Mapping):
        return None
    value = item.get(key)
    if isinstance(value, int) and not isinstance(value, bool):
        return value
    return None


def _extract_results(payload: Any, *, source_name: str) -> list[Any]:
    if not isinstance(payload, Mapping):
        raise AcademicProviderError(
            f"{source_name} returned a non-object payload",
            error_code="PROVIDER_SCHEMA_MISMATCH",
            blocker_type="FAILED_PROVIDER",
        )
    results = payload.get("results")
    if not isinstance(results, list):
        raise AcademicProviderError(
            f"{source_name} payload missing a 'results' list",
            error_code="PROVIDER_SCHEMA_MISMATCH",
            blocker_type="FAILED_PROVIDER",
        )
    return results


def _stable_identifier(item: Any, *, source_name: str) -> str:
    openalex_id = _string_field(item, "id")
    if openalex_id is None:
        raise AcademicProviderError(
            f"{source_name} result missing an 'id'",
            error_code="PROVIDER_SCHEMA_MISMATCH",
            blocker_type="FAILED_PROVIDER",
        )
    suffix = openalex_id.rstrip("/").rsplit("/", 1)[-1]
    return f"openalex:{suffix}"


def _canonical_url(item: Any, *, stable_identifier: str) -> str | None:
    if isinstance(item, Mapping):
        primary = item.get("primary_location")
        if isinstance(primary, Mapping):
            landing = _string_field(primary, "landing_page_url")
            if landing is not None:
                return landing
    suffix = stable_identifier.split(":", 1)[-1]
    return f"https://openalex.org/{suffix}"


@dataclass(frozen=True, slots=True)
class OpenAlexProvider:
    """OpenAlex works adapter with an injectable raw-HTTP transport."""

    transport: AcademicHttpTransport
    source_name: str = "OpenAlex"
    kind: PriorArtProviderKind = "academic"
    now: Callable[[], datetime] = _utcnow

    def search(self, query: PriorArtQueryRecord) -> tuple[ProviderNeighborRecord, ...]:
        if not query.original_text.strip():
            raise AcademicProviderError(
                f"{self.source_name} query requires a non-empty original_text",
                error_code="PROVIDER_QUERY_INVALID",
                blocker_type="FAILED_PROVIDER",
            )
        page = query.page_count or 1
        per_page = query.result_count or _DEFAULT_PER_PAGE
        from_year, to_year = parse_time_range(query.time_range)
        params: list[tuple[str, str]] = [
            ("search", query.original_text),
            ("page", str(page)),
            ("per-page", str(per_page)),
        ]
        if from_year is not None and to_year is not None:
            params.append(
                ("filter", f"from_publication_date:{from_year},to_publication_date:{to_year}")
            )

        raw = fetch_provider_text(
            self.transport,
            url=_OPENALEX_WORKS_URL,
            params=tuple(params),
            source_name=self.source_name,
        )
        payload = parse_provider_json(raw, source_name=self.source_name)
        results = _extract_results(payload, source_name=self.source_name)
        meta = payload.get("meta") if isinstance(payload, Mapping) else None
        result_count = _int_field(meta, "count") if isinstance(meta, Mapping) else None
        executed_at = query.executed_at if query.executed_at is not None else self.now()
        accessed_at = self.now()

        return tuple(
            self._build_record(
                item,
                query=query,
                executed_at=executed_at,
                accessed_at=accessed_at,
                page=page,
                per_page=per_page,
                result_count=result_count,
            )
            for item in results
        )

    def _build_record(
        self,
        item: Any,
        *,
        query: PriorArtQueryRecord,
        executed_at: datetime,
        accessed_at: datetime,
        page: int,
        per_page: int,
        result_count: int | None,
    ) -> ProviderNeighborRecord:
        stable_identifier = _stable_identifier(item, source_name=self.source_name)
        return build_academic_neighbor_record(
            provider_name=self.source_name,
            stable_identifier=stable_identifier,
            canonical_url=_canonical_url(item, stable_identifier=stable_identifier),
            query_id=query.query_id,
            executed_at=executed_at,
            accessed_at=accessed_at,
            page=page,
            per_page=per_page,
            result_count=result_count,
            publication_year=_int_field(item, "publication_year"),
            title=_string_field(item, "display_name"),
        )


__all__ = ["OpenAlexProvider"]
