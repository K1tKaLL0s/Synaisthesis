"""Crossref academic prior-art provider adapter (M13.1; 03A §3, 08 §4).

Implements ``PriorArtProvider`` with an injectable raw-HTTP transport. No real
HTTP client or credentials ship here; tests inject frozen fixtures and the
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
    extract_publication_year,
    fetch_provider_text,
    normalize_doi,
    parse_provider_json,
    parse_time_range,
)

_CROSSREF_WORKS_URL = "https://api.crossref.org/works"
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


def _extract_items(payload: Any, *, source_name: str) -> list[Any]:
    if not isinstance(payload, Mapping):
        raise AcademicProviderError(
            f"{source_name} returned a non-object payload",
            error_code="PROVIDER_SCHEMA_MISMATCH",
            blocker_type="FAILED_PROVIDER",
        )
    message = payload.get("message")
    if not isinstance(message, Mapping):
        raise AcademicProviderError(
            f"{source_name} payload missing a 'message' object",
            error_code="PROVIDER_SCHEMA_MISMATCH",
            blocker_type="FAILED_PROVIDER",
        )
    items = message.get("items")
    if not isinstance(items, list):
        raise AcademicProviderError(
            f"{source_name} message missing an 'items' list",
            error_code="PROVIDER_SCHEMA_MISMATCH",
            blocker_type="FAILED_PROVIDER",
        )
    return items


def _stable_identifier(item: Any, *, source_name: str) -> str:
    doi = normalize_doi(_string_field(item, "DOI"))
    if doi is None:
        raise AcademicProviderError(
            f"{source_name} result missing a valid 'DOI'",
            error_code="PROVIDER_SCHEMA_MISMATCH",
            blocker_type="FAILED_PROVIDER",
        )
    return f"doi:{doi}"


def _title(item: Any) -> str | None:
    if not isinstance(item, Mapping):
        return None
    titles = item.get("title")
    if isinstance(titles, list):
        for candidate in titles:
            if isinstance(candidate, str) and candidate.strip():
                return candidate.strip()
    return None


def _abstract(item: Any) -> str | None:
    return _string_field(item, "abstract")


@dataclass(frozen=True, slots=True)
class CrossrefProvider:
    """Crossref works adapter with an injectable raw-HTTP transport."""

    transport: AcademicHttpTransport
    source_name: str = "Crossref"
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
            ("query.bibliographic", query.original_text),
            ("rows", str(per_page)),
            ("offset", str((page - 1) * per_page)),
        ]
        if from_year is not None and to_year is not None:
            params.append(
                ("filter", f"from-pub-date:{from_year}-01-01,until-pub-date:{to_year}-12-31")
            )

        raw = fetch_provider_text(
            self.transport,
            url=_CROSSREF_WORKS_URL,
            params=tuple(params),
            source_name=self.source_name,
        )
        payload = parse_provider_json(raw, source_name=self.source_name)
        items = _extract_items(payload, source_name=self.source_name)
        message = payload.get("message") if isinstance(payload, Mapping) else None
        result_count = (
            _int_field(message, "total-results") if isinstance(message, Mapping) else None
        )
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
            for item in items
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
        published = item.get("published") if isinstance(item, Mapping) else None
        return build_academic_neighbor_record(
            provider_name=self.source_name,
            stable_identifier=stable_identifier,
            canonical_url=_string_field(item, "URL"),
            query_id=query.query_id,
            executed_at=executed_at,
            accessed_at=accessed_at,
            page=page,
            per_page=per_page,
            result_count=result_count,
            publication_year=extract_publication_year(published),
            title=_title(item),
            abstract=_abstract(item),
        )


__all__ = ["CrossrefProvider"]
