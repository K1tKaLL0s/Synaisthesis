"""M13.4 ENG3 engineering reference-set contract tests (19 §5 M13.4).

Traceability: every entry carries a stable identifier, official URL, accessed
time and concrete evidence references; popularity text never counts as
evidence; repositories/standards/reference architectures must all be present.
"""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from synaisthesis.domain.errors import DomainError
from synaisthesis.providers.prior_art.engineering_base import (
    EngineeringNeighborHit,
    EngineeringNeighborQuery,
)
from synaisthesis.providers.prior_art.official_docs import OfficialDocsProvider
from synaisthesis.providers.prior_art.repository_registry import RepositoryRegistryProvider
from synaisthesis.providers.prior_art.standards import (
    STANDARDS_CORPUS,
    EngineeringReferenceEntry,
    EngineeringStandardEvidence,
    StandardsProvider,
    build_engineering_reference_set,
)

NOW = datetime(2026, 8, 17, 0, 0, 0, tzinfo=UTC)


def _query() -> EngineeringNeighborQuery:
    return EngineeringNeighborQuery(
        query_id="q-refset",
        baseline_id="baseline-2025-01",
        requirement_refs=("REQ-TRACE-1", "REQ-SECURE-2"),
        original_text="contract specification with provenance trace and reference architecture",
        executed_at=NOW,
    )


def _standards() -> StandardsProvider:
    return StandardsProvider()


def _full_set(**overrides) -> tuple[EngineeringReferenceEntry, ...]:
    params = {
        "query": _query(),
        "standards_provider": _standards(),
        "repository_provider": RepositoryRegistryProvider(),
        "official_docs_provider": OfficialDocsProvider(),
    }
    params.update(overrides)
    return build_engineering_reference_set(**params)


def test_standards_corpus_is_officially_sourced() -> None:
    for item in STANDARDS_CORPUS:
        assert isinstance(item, EngineeringStandardEvidence)
        assert item.official_url.startswith("http")
        assert item.evidence_refs and all(ref.startswith("http") for ref in item.evidence_refs)
        assert item.accessed_at is not None
        assert item.version


def test_reference_set_has_all_required_categories() -> None:
    entries = _full_set()
    categories = {entry.category for entry in entries}
    assert {"REPOSITORY", "STANDARD", "REFERENCE_ARCHITECTURE", "OFFICIAL_DOCS"} <= categories
    counts = {category: 0 for category in ("REPOSITORY", "STANDARD", "REFERENCE_ARCHITECTURE")}
    for entry in entries:
        if entry.category in counts:
            counts[entry.category] += 1
    assert counts["REPOSITORY"] >= 1
    assert counts["STANDARD"] >= 1
    assert counts["REFERENCE_ARCHITECTURE"] >= 1


def test_every_entry_is_traceable() -> None:
    for entry in _full_set():
        assert entry.stable_identifier
        assert entry.canonical_url.startswith("http")
        assert entry.accessed_at is not None
        assert entry.evidence_refs
        assert all(ref.startswith("http") for ref in entry.evidence_refs)
        # popularity markers never appear in evidence
        for ref in entry.evidence_refs:
            assert "star" not in ref.lower()
            assert "download" not in ref.lower()


def test_dedup_by_category_identifier_and_url() -> None:
    class DuplicateHitProvider:
        source_name = "duplicate-hit"

        def search_engineering_neighbors(self, query):
            del query
            return (RepositoryRegistryProvider().search_engineering_neighbors(_query())[0],) * 2

    entries = _full_set(repository_provider=DuplicateHitProvider())
    identifiers = [entry.stable_identifier for entry in entries if entry.category == "REPOSITORY"]
    assert len(identifiers) == len(set(identifiers))


def test_incomplete_reference_set_is_blocked() -> None:
    only_standards = StandardsProvider(
        corpus=tuple(item for item in STANDARDS_CORPUS if item.category != "REFERENCE_ARCHITECTURE")
    )
    with pytest.raises(DomainError) as exc_info:
        _full_set(
            repository_provider=None,
            official_docs_provider=None,
            standards_provider=only_standards,
        )
    assert exc_info.value.error_code == "ENGINEERING_REFERENCE_SET_INCOMPLETE"


def test_unreferenced_standard_is_rejected() -> None:
    with pytest.raises(DomainError) as exc_info:
        EngineeringStandardEvidence(
            standard_id="standard/no-refs",
            organization="X",
            title="No refs",
            version="1.0",
            category="STANDARD",
            official_url="https://example.org/no-refs",
            accessed_at=NOW,
            evidence_refs=(),
        )
    assert exc_info.value.error_code == "REFERENCE_EVIDENCE_MISSING"


def test_unsourced_reference_entry_is_rejected() -> None:
    with pytest.raises(DomainError) as exc_info:
        EngineeringReferenceEntry(
            category="STANDARD",
            stable_identifier="standard/bad",
            canonical_url="not-a-url",
            accessed_at=NOW,
            evidence_refs=("https://example.org/evidence",),
        )
    assert exc_info.value.error_code == "REFERENCE_UNSOURCED"


def test_hit_to_entry_uses_only_concrete_evidence() -> None:
    hit = EngineeringNeighborHit(
        stable_identifier="repo/evidence-only",
        canonical_url="https://github.com/example/evidence-only",
        category="binding-specification",
        function_features={
            "contract_compilation": (0.9, "https://github.com/example/evidence-only#feature")
        },
        application_features={},
        maturity_evidence=(
            (
                "发布 https://github.com/example/evidence-only/releases/v1",
                "https://github.com/example/evidence-only/releases/v1",
            ),
            (
                "测试 https://github.com/example/evidence-only/tests",
                "https://github.com/example/evidence-only/tests",
            ),
        ),
        untrusted_texts=(),
        accessed_at=NOW,
    )
    provider = type("OneHit", (), {"source_name": "one-hit"})
    provider.search_engineering_neighbors = lambda query: (hit,)  # type: ignore[attr-defined]

    entries = _full_set(repository_provider=provider)
    entry = next(e for e in entries if e.category == "REPOSITORY")
    assert all(ref.startswith("http") for ref in entry.evidence_refs)
    assert len(entry.evidence_refs) == 3
