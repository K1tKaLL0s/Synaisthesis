"""Deterministic fake prior-art providers for contract tests and CI (M2.4)."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime

from synaisthesis.domain.qualification import PriorArtQueryRecord
from synaisthesis.providers.prior_art.base import (
    ApplicationProximityFeatures,
    ExternalText,
    PriorArtProviderKind,
    PriorArtQueryRequest,
    ProviderNeighborRecord,
    ProximityFeature,
    TheoryProximityFeatures,
)

_FAKE_ACCESSED_AT = datetime(2026, 8, 16, 0, 0, 0, tzinfo=UTC)
_FAKE_QUERY_EXECUTED_AT = datetime(2026, 8, 16, 0, 1, 0, tzinfo=UTC)


def _feature(value: float, ref: str) -> ProximityFeature:
    return ProximityFeature(value=value, evidence_refs=(ref,))


def _theory(value: float, ref: str) -> TheoryProximityFeatures:
    return TheoryProximityFeatures(
        object_domain=_feature(value, f"{ref}:object_domain"),
        mechanism=_feature(value, f"{ref}:mechanism"),
        assumptions=_feature(value, f"{ref}:assumptions"),
        conclusion=_feature(value, f"{ref}:conclusion"),
    )


def _application(value: float, ref: str) -> ApplicationProximityFeatures:
    return ApplicationProximityFeatures(
        expected_function=_feature(value, f"{ref}:expected_function"),
        use_context=_feature(value, f"{ref}:use_context"),
        input_output=_feature(value, f"{ref}:input_output"),
        system_architecture=_feature(value, f"{ref}:system_architecture"),
        operational_constraints=_feature(value, f"{ref}:operational_constraints"),
        maturity=_feature(value, f"{ref}:maturity"),
    )


def _record(
    *,
    provider_name: str,
    kind: PriorArtProviderKind,
    stable_identifier: str,
    canonical_url: str,
    theory_value: float,
    application_value: float,
) -> ProviderNeighborRecord:
    ref = f"{provider_name}:{stable_identifier}"
    return ProviderNeighborRecord(
        provider_name=provider_name,
        kind=kind,
        stable_identifier=stable_identifier,
        canonical_url=canonical_url,
        metadata_verified=True,
        metadata_verification_receipt=f"{provider_name}:metadata:{stable_identifier}",
        maturity_evidence_refs=(
            f"{ref}:release-record",
            f"{ref}:maintenance-record",
        ),
        theory_features=_theory(theory_value, ref),
        application_features=_application(application_value, ref),
        similarity_evidence_refs=(f"{ref}:similarity-evidence",),
        untrusted_texts=(
            ExternalText(content=f"untrusted abstract for {stable_identifier}", source_ref=ref),
        ),
        accessed_at=_FAKE_ACCESSED_AT,
    )


_ACADEMIC_RECORDS = (
    _record(
        provider_name="OpenAlex",
        kind="academic",
        stable_identifier="openalex:W2001",
        canonical_url="https://example.org/openalex/W2001",
        theory_value=4.0,
        application_value=1.0,
    ),
    _record(
        provider_name="OpenAlex",
        kind="academic",
        stable_identifier="openalex:W2002",
        canonical_url="https://example.org/openalex/W2002",
        theory_value=3.5,
        application_value=1.0,
    ),
    _record(
        provider_name="Crossref",
        kind="academic",
        stable_identifier="doi:10.1000/duplicate",
        canonical_url="https://example.org/openalex/W2001",
        theory_value=4.0,
        application_value=1.0,
    ),
    _record(
        provider_name="Crossref",
        kind="academic",
        stable_identifier="doi:10.1000/c2",
        canonical_url="https://example.org/crossref/c2",
        theory_value=3.0,
        application_value=1.0,
    ),
    _record(
        provider_name="arXiv",
        kind="academic",
        stable_identifier="arxiv:2001.00001",
        canonical_url="https://example.org/arxiv/2001.00001",
        theory_value=2.5,
        application_value=1.0,
    ),
    _record(
        provider_name="arXiv",
        kind="academic",
        stable_identifier="arxiv:2001.00002",
        canonical_url="https://example.org/arxiv/2001.00002",
        theory_value=2.0,
        application_value=1.0,
    ),
)

_ENGINEERING_RECORDS = (
    _record(
        provider_name="GitHub",
        kind="engineering",
        stable_identifier="github:org/repo1",
        canonical_url="https://example.org/github/repo1",
        theory_value=1.0,
        application_value=4.0,
    ),
    _record(
        provider_name="GitHub",
        kind="engineering",
        stable_identifier="github:org/repo2",
        canonical_url="https://example.org/github/repo2",
        theory_value=1.0,
        application_value=3.0,
    ),
    _record(
        provider_name="PyPI",
        kind="engineering",
        stable_identifier="pypi:repo1",
        canonical_url="https://example.org/github/repo1",
        theory_value=1.0,
        application_value=4.0,
    ),
    _record(
        provider_name="PyPI",
        kind="engineering",
        stable_identifier="pypi:repo2",
        canonical_url="https://example.org/pypi/repo2",
        theory_value=1.0,
        application_value=2.5,
    ),
)


@dataclass(frozen=True, slots=True)
class FakePriorArtProvider:
    """A deterministic in-memory provider returning a frozen record corpus."""

    source_name: str
    kind: PriorArtProviderKind
    records: tuple[ProviderNeighborRecord, ...]

    def search(self, query: PriorArtQueryRecord) -> tuple[ProviderNeighborRecord, ...]:
        del query  # query is intentionally unused in the fixed fake corpus
        return self.records


def fake_academic_records() -> tuple[ProviderNeighborRecord, ...]:
    return _ACADEMIC_RECORDS


def fake_engineering_records() -> tuple[ProviderNeighborRecord, ...]:
    return _ENGINEERING_RECORDS


def fake_academic_providers() -> tuple[FakePriorArtProvider, ...]:
    return tuple(
        FakePriorArtProvider(
            source_name=source_name,
            kind="academic",
            records=tuple(
                record for record in _ACADEMIC_RECORDS if record.provider_name == source_name
            ),
        )
        for source_name in ("OpenAlex", "Crossref", "arXiv")
    )


def fake_engineering_providers() -> tuple[FakePriorArtProvider, ...]:
    return tuple(
        FakePriorArtProvider(
            source_name=source_name,
            kind="engineering",
            records=tuple(
                record for record in _ENGINEERING_RECORDS if record.provider_name == source_name
            ),
        )
        for source_name in ("GitHub", "PyPI")
    )


def fake_query_requests() -> tuple[PriorArtQueryRequest, ...]:
    return (
        PriorArtQueryRequest(
            query=PriorArtQueryRecord(
                query_id="fake-academic-query",
                original_text="trace cyclic property matrix proof",
                generated_from=("S1.core_definition", "S1.object_candidates"),
                provider="fake-academic",
                time_range="2015-2026",
                filters=("type:article",),
                page_count=1,
                result_count=20,
                executed_at=_FAKE_QUERY_EXECUTED_AT,
            ),
            kind="academic",
        ),
        PriorArtQueryRequest(
            query=PriorArtQueryRecord(
                query_id="fake-engineering-query",
                original_text="numpy trace invariance numerical linear algebra",
                generated_from=("S1.target_applications", "S1.success_metrics"),
                provider="fake-engineering",
                time_range="2015-2026",
                filters=("type:repository",),
                page_count=1,
                result_count=20,
                executed_at=_FAKE_QUERY_EXECUTED_AT,
            ),
            kind="engineering",
        ),
    )


__all__ = [
    "FakePriorArtProvider",
    "fake_academic_providers",
    "fake_academic_records",
    "fake_engineering_providers",
    "fake_engineering_records",
    "fake_query_requests",
]
