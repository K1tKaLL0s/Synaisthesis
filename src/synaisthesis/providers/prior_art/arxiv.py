"""arXiv academic prior-art provider adapter (M13.1; 03A §3, 08 §4).

Implements ``PriorArtProvider`` with an injectable raw-HTTP transport and parses
the arXiv Atom feed with stdlib ``xml.etree.ElementTree`` (no external entities
are resolved; feed text stays quarantined as untrusted ExternalText). No real
HTTP client or credentials ship here; the real-network smoke test stays manual.
"""

from __future__ import annotations

import xml.etree.ElementTree as ET
from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime

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
    normalize_arxiv_id,
    parse_time_range,
)

_ARXIV_QUERY_URL = "https://export.arxiv.org/api/query"
_ATOM_NS = "{http://www.w3.org/2005/Atom}"
_DEFAULT_PER_PAGE = 25


def _utcnow() -> datetime:
    return datetime.now(UTC)


def _entry_text(entry: ET.Element, tag: str) -> str | None:
    node = entry.find(f"{_ATOM_NS}{tag}")
    if node is not None and node.text and node.text.strip():
        return node.text.strip()
    return None


def _entry_link(entry: ET.Element) -> str | None:
    for node in entry.findall(f"{_ATOM_NS}link"):
        if node.get("rel") == "alternate":
            href = node.get("href")
            if href:
                return href
    return None


def _stable_identifier(entry: ET.Element, *, source_name: str) -> str:
    normalized = normalize_arxiv_id(_entry_text(entry, "id"))
    if normalized is None:
        raise AcademicProviderError(
            f"{source_name} entry missing a valid arXiv 'id'",
            error_code="PROVIDER_SCHEMA_MISMATCH",
            blocker_type="FAILED_PROVIDER",
        )
    return f"arxiv:{normalized}"


def _parse_entries(raw: str, *, source_name: str) -> list[ET.Element]:
    try:
        root = ET.fromstring(raw)
    except ET.ParseError as exc:
        raise AcademicProviderError(
            f"{source_name} returned a non-Atom/XML payload",
            error_code="PROVIDER_SCHEMA_MISMATCH",
            blocker_type="FAILED_PROVIDER",
        ) from exc
    return root.findall(f"{_ATOM_NS}entry")


@dataclass(frozen=True, slots=True)
class ArxivProvider:
    """arXiv Atom-feed adapter with an injectable raw-HTTP transport."""

    transport: AcademicHttpTransport
    source_name: str = "arXiv"
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
        search_query = query.original_text
        if from_year is not None and to_year is not None:
            search_query = (
                f"{search_query} AND submittedDate:[{from_year}01010000 TO {to_year}12312359]"
            )
        params: tuple[tuple[str, str], ...] = (
            ("search_query", search_query),
            ("start", str((page - 1) * per_page)),
            ("max_results", str(per_page)),
        )

        raw = fetch_provider_text(
            self.transport,
            url=_ARXIV_QUERY_URL,
            params=params,
            source_name=self.source_name,
        )
        entries = _parse_entries(raw, source_name=self.source_name)
        executed_at = query.executed_at if query.executed_at is not None else self.now()
        accessed_at = self.now()

        return tuple(
            self._build_record(
                entry,
                query=query,
                executed_at=executed_at,
                accessed_at=accessed_at,
                page=page,
                per_page=per_page,
                result_count=len(entries),
            )
            for entry in entries
        )

    def _build_record(
        self,
        entry: ET.Element,
        *,
        query: PriorArtQueryRecord,
        executed_at: datetime,
        accessed_at: datetime,
        page: int,
        per_page: int,
        result_count: int | None,
    ) -> ProviderNeighborRecord:
        stable_identifier = _stable_identifier(entry, source_name=self.source_name)
        canonical_url = _entry_link(entry) or (
            f"https://arxiv.org/abs/{stable_identifier.split(':', 1)[1]}"
        )
        return build_academic_neighbor_record(
            provider_name=self.source_name,
            stable_identifier=stable_identifier,
            canonical_url=canonical_url,
            query_id=query.query_id,
            executed_at=executed_at,
            accessed_at=accessed_at,
            page=page,
            per_page=per_page,
            result_count=result_count,
            publication_year=extract_publication_year(_entry_text(entry, "published")),
            title=_entry_text(entry, "title"),
            abstract=_entry_text(entry, "summary"),
        )


__all__ = ["ArxivProvider"]
