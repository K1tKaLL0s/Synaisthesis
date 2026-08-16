"""M13.1 academic prior-art provider contract tests (19 §5 M13.1).

Tests run against frozen fixtures and an injectable transport boundary; no
real network or credentials are used.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, replace
from datetime import UTC, datetime

import pytest

from synaisthesis.application.qualification_service import run_prior_art_search
from synaisthesis.domain.enums import PriorArtCoverageStatus
from synaisthesis.domain.errors import DomainError
from synaisthesis.domain.qualification import PriorArtQueryRecord
from synaisthesis.providers.prior_art.arxiv import ArxivProvider
from synaisthesis.providers.prior_art.base import (
    ApplicationProximityFeatures,
    ExternalText,
    PriorArtQueryRequest,
    ProviderNeighborRecord,
    ProximityFeature,
    TheoryProximityFeatures,
)
from synaisthesis.providers.prior_art.crossref import CrossrefProvider
from synaisthesis.providers.prior_art.deduplication import deduplicate_academic_records
from synaisthesis.providers.prior_art.fake import fake_engineering_providers
from synaisthesis.providers.prior_art.normalization import (
    extract_publication_year,
    normalize_arxiv_id,
    normalize_author_names,
    normalize_doi,
    parse_time_range,
)
from synaisthesis.providers.prior_art.openalex import OpenAlexProvider

NOW = datetime(2026, 8, 18, 12, 0, 0, tzinfo=UTC)

OPENALEX_JSON = json.dumps(
    {
        "meta": {"count": 2, "page": 1, "per_page": 25},
        "results": [
            {
                "id": "https://openalex.org/W2001",
                "doi": "https://doi.org/10.1000/openalex-w2001",
                "display_name": "Trace cyclic property matrix proof",
                "publication_year": 2020,
                "primary_location": {"landing_page_url": "https://example.org/openalex/W2001"},
            },
            {
                "id": "https://openalex.org/W2002",
                "doi": "https://doi.org/10.1000/openalex-w2002",
                "display_name": "Numerical trace invariance",
                "publication_year": 2018,
                "primary_location": {"landing_page_url": "https://example.org/openalex/W2002"},
            },
        ],
    }
)

CROSSREF_JSON = json.dumps(
    {
        "message": {
            "total-results": 2,
            "items": [
                {
                    "DOI": "10.1000/crossref-1",
                    "title": ["Cyclic property matrices"],
                    "URL": "https://example.org/crossref/1",
                    "published": {"date-parts": [[2019, 3, 15]]},
                    "author": [{"family": "Doe", "given": "Jane"}],
                    "abstract": "untrusted crossref abstract",
                },
                {
                    "DOI": "10.1000/crossref-2",
                    "title": ["Trace invariance in linear algebra"],
                    "URL": "https://example.org/crossref/2",
                    "published": {"date-parts": [[2021]]},
                },
            ],
        }
    }
)

ARXIV_XML = """<?xml version="1.0" encoding="UTF-8"?>
<feed xmlns="http://www.w3.org/2005/Atom">
  <entry>
    <id>http://arxiv.org/abs/2001.00001v2</id>
    <title>Deterministic trace pipelines</title>
    <link rel="alternate" href="https://arxiv.org/abs/2001.00001"/>
    <published>2020-01-15T00:00:00Z</published>
    <summary>untrusted arxiv abstract</summary>
  </entry>
  <entry>
    <id>http://arxiv.org/abs/2001.00002</id>
    <title>Matrix trace cyclic property</title>
    <link rel="alternate" href="https://arxiv.org/abs/2001.00002"/>
    <published>2022-02-01T00:00:00Z</published>
    <summary>second arxiv abstract</summary>
  </entry>
</feed>
"""


@dataclass(frozen=True, slots=True)
class FrozenTransport:
    body: str

    def get_text(self, url: str, *, params: tuple[tuple[str, str], ...]) -> str:
        del url, params
        return self.body


@dataclass(frozen=True, slots=True)
class FailingTransport:
    error: Exception

    def get_text(self, url: str, *, params: tuple[tuple[str, str], ...]) -> str:
        del url, params
        raise self.error


def _query() -> PriorArtQueryRecord:
    return PriorArtQueryRecord(
        query_id="q-academic",
        original_text="trace cyclic property matrix proof",
        generated_from=("S1.core_definition",),
        provider="openalex",
        time_range="2015-2026",
        filters=(),
        page_count=1,
        result_count=20,
        executed_at=NOW,
    )


def _feat(value: float = 0.0, ref: str = "evidence:shared") -> ProximityFeature:
    return ProximityFeature(value=value, evidence_refs=(ref,))


def _record(
    *,
    stable_identifier: str,
    canonical_url: str | None,
    provider_name: str = "openalex",
) -> ProviderNeighborRecord:
    return ProviderNeighborRecord(
        provider_name=provider_name,
        kind="academic",
        stable_identifier=stable_identifier,
        canonical_url=canonical_url,
        metadata_verified=True,
        metadata_verification_receipt=f"receipt:{provider_name}:{stable_identifier}",
        maturity_evidence_refs=(),
        theory_features=TheoryProximityFeatures(_feat(), _feat(), _feat(), _feat()),
        application_features=ApplicationProximityFeatures(
            _feat(), _feat(), _feat(), _feat(), _feat(), _feat()
        ),
        similarity_evidence_refs=(f"similarity:{stable_identifier}",),
        untrusted_texts=(ExternalText(content="untrusted", source_ref=stable_identifier),),
        accessed_at=NOW,
    )


def _providers() -> tuple[OpenAlexProvider, CrossrefProvider, ArxivProvider]:
    return (
        OpenAlexProvider(transport=FrozenTransport(OPENALEX_JSON), now=lambda: NOW),
        CrossrefProvider(transport=FrozenTransport(CROSSREF_JSON), now=lambda: NOW),
        ArxivProvider(transport=FrozenTransport(ARXIV_XML), now=lambda: NOW),
    )


def test_openalex_provider_returns_traceable_records():
    provider = OpenAlexProvider(transport=FrozenTransport(OPENALEX_JSON), now=lambda: NOW)
    records = provider.search(_query())
    assert len(records) == 2

    first = records[0]
    assert first.kind == "academic"
    assert first.provider_name == "OpenAlex"
    assert first.stable_identifier == "openalex:W2001"
    assert first.canonical_url == "https://example.org/openalex/W2001"
    assert first.metadata_verified is True
    assert first.accessed_at == NOW
    receipt = first.metadata_verification_receipt
    assert "query=q-academic" in receipt
    assert "page=1" in receipt
    assert "per_page=20" in receipt
    assert "results=2" in receipt
    assert f"executed={NOW.isoformat()}" in receipt
    assert "record=openalex:W2001" in receipt
    assert "year=2020" in receipt


def test_crossref_provider_normalizes_doi_and_keeps_abstract_untrusted():
    provider = CrossrefProvider(transport=FrozenTransport(CROSSREF_JSON), now=lambda: NOW)
    records = provider.search(_query())
    assert len(records) == 2

    first = records[0]
    assert first.kind == "academic"
    assert first.provider_name == "Crossref"
    assert first.stable_identifier == "doi:10.1000/crossref-1"
    assert first.canonical_url == "https://example.org/crossref/1"
    assert "record=doi:10.1000/crossref-1" in first.metadata_verification_receipt
    assert "year=2019" in first.metadata_verification_receipt
    abstract_texts = [
        text for text in first.untrusted_texts if text.source_ref.endswith(":abstract")
    ]
    assert len(abstract_texts) == 1
    assert abstract_texts[0].content == "untrusted crossref abstract"
    assert abstract_texts[0].untrusted is True


def test_arxiv_provider_parses_atom_and_strips_version_suffix():
    provider = ArxivProvider(transport=FrozenTransport(ARXIV_XML), now=lambda: NOW)
    records = provider.search(_query())
    assert len(records) == 2

    first = records[0]
    assert first.kind == "academic"
    assert first.provider_name == "arXiv"
    assert first.stable_identifier == "arxiv:2001.00001"
    assert first.canonical_url == "https://arxiv.org/abs/2001.00001"
    assert "year=2020" in first.metadata_verification_receipt
    assert any(text.content == "untrusted arxiv abstract" for text in first.untrusted_texts)


def test_all_academic_external_text_stays_untrusted():
    for provider in _providers():
        for record in provider.search(_query()):
            assert record.untrusted_texts, record.stable_identifier
            for text in record.untrusted_texts:
                assert isinstance(text, ExternalText)
                assert text.untrusted is True
                assert text.source_ref


def test_malicious_external_text_is_never_executed(monkeypatch):
    body = json.dumps(
        {
            "message": {
                "total-results": 1,
                "items": [
                    {
                        "DOI": "10.1000/evil",
                        "title": ["Evil"],
                        "abstract": "__import__('os').system('echo pwned')",
                    }
                ],
            }
        }
    )
    provider = CrossrefProvider(transport=FrozenTransport(body), now=lambda: NOW)

    def forbidden_exec(*args, **kwargs):
        raise AssertionError("exec must never be called")

    monkeypatch.setattr("builtins.exec", forbidden_exec)
    records = provider.search(_query())
    assert records[0].untrusted_texts[1].content.startswith("__import__")
    assert records[0].untrusted_texts[1].untrusted is True


def test_deduplicate_academic_records_by_identifier_doi_and_url():
    by_doi = _record(
        stable_identifier="openalex:W1",
        canonical_url="https://doi.org/10.1000/w1",
        provider_name="openalex",
    )
    doi_dup = _record(
        stable_identifier="doi:10.1000/w1", canonical_url=None, provider_name="crossref"
    )
    by_url = _record(
        stable_identifier="arxiv:2001.00001",
        canonical_url="https://example.org/same",
        provider_name="arxiv",
    )
    url_dup = _record(
        stable_identifier="arxiv:2001.00002",
        canonical_url="https://example.org/same",
        provider_name="arxiv",
    )
    id_dup = _record(
        stable_identifier="openalex:W1",
        canonical_url="https://example.org/other",
        provider_name="openalex",
    )
    unique = _record(
        stable_identifier="openalex:W3",
        canonical_url="https://example.org/unique",
        provider_name="openalex",
    )

    corpus = (by_doi, doi_dup, by_url, url_dup, id_dup, unique)
    deduped = deduplicate_academic_records(corpus)
    assert [record.stable_identifier for record in deduped] == [
        "openalex:W1",
        "arxiv:2001.00001",
        "openalex:W3",
    ]
    assert deduplicate_academic_records(corpus) == deduped


def test_transport_failure_is_structured_blocked_network():
    provider = OpenAlexProvider(
        transport=FailingTransport(RuntimeError("dns timeout")), now=lambda: NOW
    )
    with pytest.raises(DomainError) as exc_info:
        provider.search(_query())
    assert exc_info.value.error_code == "BLOCKED_NETWORK"
    assert exc_info.value.blocker_type == "BLOCKED_NETWORK"


def test_malformed_json_is_structured_failed_provider():
    provider = CrossrefProvider(transport=FrozenTransport("{not json"), now=lambda: NOW)
    with pytest.raises(DomainError) as exc_info:
        provider.search(_query())
    assert exc_info.value.error_code == "PROVIDER_SCHEMA_MISMATCH"
    assert exc_info.value.blocker_type == "FAILED_PROVIDER"


def test_missing_required_metadata_is_structured_failed_provider():
    body = json.dumps({"message": {"items": [{"title": ["no DOI"]}]}})
    provider = CrossrefProvider(transport=FrozenTransport(body), now=lambda: NOW)
    with pytest.raises(DomainError) as exc_info:
        provider.search(_query())
    assert exc_info.value.error_code == "PROVIDER_SCHEMA_MISMATCH"
    assert exc_info.value.blocker_type == "FAILED_PROVIDER"


def test_empty_query_is_structured_failed_provider():
    provider = OpenAlexProvider(transport=FrozenTransport(OPENALEX_JSON), now=lambda: NOW)
    with pytest.raises(DomainError) as exc_info:
        provider.search(replace(_query(), original_text="   "))
    assert exc_info.value.error_code == "PROVIDER_QUERY_INVALID"
    assert exc_info.value.blocker_type == "FAILED_PROVIDER"


def test_normalization_helpers_are_deterministic():
    assert normalize_doi("https://doi.org/10.1000/XYZ") == "10.1000/xyz"
    assert normalize_doi("doi:10.1000/xyz") == "10.1000/xyz"
    assert normalize_doi("not-a-doi") is None
    assert normalize_arxiv_id("http://arxiv.org/abs/2001.00001v2") == "2001.00001"
    assert normalize_arxiv_id("arxiv:2001.00001v2") == "2001.00001"
    assert extract_publication_year("2020-01-01T00:00:00Z") == 2020
    assert extract_publication_year({"date-parts": [[2019, 3, 15]]}) == 2019
    assert normalize_author_names([{"family": "Doe", "given": "Jane"}, "Jane Doe"]) == ("Jane Doe",)
    assert parse_time_range("2015-2026") == (2015, 2026)
    assert parse_time_range("2015") == (2015, 2015)
    assert parse_time_range("") == (None, None)

    with pytest.raises(DomainError):
        parse_time_range("2026-2015")
    with pytest.raises(DomainError):
        parse_time_range("garbage")


def test_academic_providers_integrate_to_complete_coverage():
    result = run_prior_art_search(
        academic_providers=_providers(),
        engineering_providers=fake_engineering_providers(),
        queries=(
            PriorArtQueryRequest(query=_query(), kind="academic"),
            PriorArtQueryRequest(
                query=PriorArtQueryRecord(
                    query_id="q-engineering",
                    original_text="numpy trace invariance",
                    generated_from=("S1.target_applications",),
                    provider="fake-engineering",
                    time_range="2015-2026",
                    filters=(),
                    page_count=1,
                    result_count=20,
                    executed_at=NOW,
                ),
                kind="engineering",
            ),
        ),
        research_spec_id="rs-1",
        input_spec_hash="a" * 64,
        now=NOW,
    )
    assert result.coverage_status is PriorArtCoverageStatus.COMPLETE
    assert result.coverage_blockers == ()
    assert len(result.academic_neighbors) >= 5
    academic_sources = {
        neighbor.neighbor_type.split(":")[1] for neighbor in result.academic_neighbors
    }
    assert academic_sources == {"OpenAlex", "Crossref", "arXiv"}
