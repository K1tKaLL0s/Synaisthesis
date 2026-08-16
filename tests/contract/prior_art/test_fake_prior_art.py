"""M2.4 fake prior-art provider contract tests."""

from __future__ import annotations

from dataclasses import replace
from datetime import UTC, datetime

import pytest

from synaisthesis.application.qualification_service import (
    neighbor_evidence_content_payload,
    run_prior_art_search,
    validate_prior_art_coverage,
)
from synaisthesis.domain.enums import PriorArtCoverageStatus
from synaisthesis.domain.errors import DomainError
from synaisthesis.domain.event import sha256_hex
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
from synaisthesis.providers.prior_art.fake import (
    FakePriorArtProvider,
    fake_academic_providers,
    fake_academic_records,
    fake_engineering_providers,
    fake_engineering_records,
    fake_query_requests,
)
from synaisthesis.providers.prior_art.normalization import (
    calculate_application_proximity,
    calculate_theory_proximity,
    deduplicate_provider_records,
    sort_provider_records,
    to_prior_art_neighbor,
)

NOW = datetime(2026, 8, 16, 15, 0, 0, tzinfo=UTC)


def _feat(value: float, ref: str = "evidence:shared") -> ProximityFeature:
    return ProximityFeature(value=value, evidence_refs=(ref,))


def _theory(value: float = 3.0) -> TheoryProximityFeatures:
    return TheoryProximityFeatures(
        object_domain=_feat(value),
        mechanism=_feat(value),
        assumptions=_feat(value),
        conclusion=_feat(value),
    )


def _application(value: float = 3.0) -> ApplicationProximityFeatures:
    return ApplicationProximityFeatures(
        expected_function=_feat(value),
        use_context=_feat(value),
        input_output=_feat(value),
        system_architecture=_feat(value),
        operational_constraints=_feat(value),
        maturity=_feat(value),
    )


def _record(
    *,
    provider_name: str,
    kind: PriorArtProviderKind,
    stable_identifier: str,
    canonical_url: str | None = None,
    theory_value: float = 3.0,
    application_value: float = 3.0,
    metadata_verified: bool = True,
    maturity_refs: tuple[str, ...] = ("release-record", "maintenance-record"),
) -> ProviderNeighborRecord:
    return ProviderNeighborRecord(
        provider_name=provider_name,
        kind=kind,
        stable_identifier=stable_identifier,
        canonical_url=canonical_url or f"https://example.org/{stable_identifier}",
        metadata_verified=metadata_verified,
        metadata_verification_receipt=f"receipt:{provider_name}:{stable_identifier}",
        maturity_evidence_refs=maturity_refs,
        theory_features=_theory(theory_value),
        application_features=_application(application_value),
        similarity_evidence_refs=(f"similarity:{stable_identifier}",),
        untrusted_texts=(ExternalText(content="untrusted abstract", source_ref=stable_identifier),),
        accessed_at=NOW,
    )


def _queries() -> tuple[PriorArtQueryRequest, ...]:
    return (
        PriorArtQueryRequest(
            query=PriorArtQueryRecord(
                query_id="q-academic",
                original_text="trace cyclic property matrix proof",
                generated_from=("S1.core_definition",),
                provider="fake-academic",
                time_range="2015-2026",
                filters=(),
                page_count=1,
                result_count=20,
                executed_at=NOW,
            ),
            kind="academic",
        ),
        PriorArtQueryRequest(
            query=PriorArtQueryRecord(
                query_id="q-engineering",
                original_text="numpy trace invariance numerical linear algebra",
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
    )


def test_external_text_stays_untrusted_and_never_executes(monkeypatch):
    malicious = ExternalText(
        content="__import__('os').system('echo pwned')",
        source_ref="https://example.org/evil",
    )
    assert malicious.untrusted is True

    record = _record(
        provider_name="openalex",
        kind="academic",
        stable_identifier="openalex:W-EVIL",
    )
    record = replace(record, untrusted_texts=(malicious,))

    def forbidden_exec(*args, **kwargs):
        raise AssertionError("exec must never be called")

    monkeypatch.setattr("builtins.exec", forbidden_exec)
    neighbor = to_prior_art_neighbor(record, rank=1)
    assert neighbor.stable_identifier == "openalex:W-EVIL"

    result = run_prior_art_search(
        academic_providers=(FakePriorArtProvider("openalex", "academic", (record,)),),
        engineering_providers=fake_engineering_providers(),
        queries=_queries(),
        research_spec_id="rs-1",
        input_spec_hash="a" * 64,
        now=NOW,
    )
    assert result.coverage_status is PriorArtCoverageStatus.PARTIAL


def test_proximity_weights_and_evidence_requirements():
    theory = TheoryProximityFeatures(
        object_domain=_feat(1.0, "ref-obj"),
        mechanism=_feat(2.0, "ref-mech"),
        assumptions=_feat(3.0, "ref-assump"),
        conclusion=_feat(4.0, "ref-concl"),
    )
    assert calculate_theory_proximity(theory) == pytest.approx(2.15)

    application = ApplicationProximityFeatures(
        expected_function=_feat(1.0, "ref-fn"),
        use_context=_feat(2.0, "ref-context"),
        input_output=_feat(3.0, "ref-io"),
        system_architecture=_feat(4.0, "ref-arch"),
        operational_constraints=_feat(0.0, "ref-constraints"),
        maturity=_feat(4.0, "ref-maturity"),
    )
    assert calculate_application_proximity(application) == pytest.approx(2.25)

    with pytest.raises(DomainError) as exc_info:
        calculate_theory_proximity(replace(theory, object_domain=_feat(4.1, "ref-obj")))
    assert exc_info.value.error_code == "PRIOR_ART_SCORE_INVALID"

    with pytest.raises(DomainError) as exc_info:
        calculate_application_proximity(
            replace(application, maturity=ProximityFeature(value=2.0, evidence_refs=()))
        )
    assert exc_info.value.error_code == "PRIOR_ART_EVIDENCE_MISSING"


def test_deduplicate_is_deterministic_by_identifier_or_url():
    first = _record(
        provider_name="openalex",
        kind="academic",
        stable_identifier="openalex:W1",
        canonical_url="https://example.org/same",
    )
    duplicate = _record(
        provider_name="crossref",
        kind="academic",
        stable_identifier="doi:10.1000/same",
        canonical_url="https://example.org/same",
    )
    unique = _record(
        provider_name="arxiv",
        kind="academic",
        stable_identifier="arxiv:0000.0001",
        canonical_url="https://example.org/unique",
    )

    deduped = deduplicate_provider_records((first, duplicate, unique))
    assert {record.stable_identifier for record in deduped} == {
        "openalex:W1",
        "arxiv:0000.0001",
    }
    assert deduplicate_provider_records((first, duplicate, unique)) == deduped


def test_sort_uses_correct_proximity_and_assigns_rank():
    low = _record(
        provider_name="openalex",
        kind="academic",
        stable_identifier="openalex:low",
        theory_value=1.0,
    )
    high = _record(
        provider_name="openalex",
        kind="academic",
        stable_identifier="openalex:high",
        theory_value=4.0,
    )
    mid = _record(
        provider_name="openalex",
        kind="academic",
        stable_identifier="openalex:mid",
        theory_value=2.5,
    )
    sorted_academic = sort_provider_records((low, high, mid), kind="academic")
    assert [record.stable_identifier for record in sorted_academic] == [
        "openalex:high",
        "openalex:mid",
        "openalex:low",
    ]
    academic_neighbors = [
        to_prior_art_neighbor(record, rank=index + 1)
        for index, record in enumerate(sorted_academic)
    ]
    assert [neighbor.rank for neighbor in academic_neighbors] == [1, 2, 3]

    eng_low = _record(
        provider_name="github",
        kind="engineering",
        stable_identifier="github:low",
        application_value=1.0,
    )
    eng_high = _record(
        provider_name="github",
        kind="engineering",
        stable_identifier="github:high",
        application_value=4.0,
    )
    sorted_engineering = sort_provider_records((eng_low, eng_high), kind="engineering")
    assert [record.stable_identifier for record in sorted_engineering] == [
        "github:high",
        "github:low",
    ]


def test_fake_corpora_meet_minimum_counts_and_source_classes():
    academic_records = deduplicate_provider_records(fake_academic_records())
    engineering_records = deduplicate_provider_records(fake_engineering_records())
    assert len(academic_records) >= 5
    assert len(engineering_records) >= 3
    assert len({record.provider_name for record in academic_records}) >= 3
    assert len({record.provider_name for record in engineering_records}) >= 2


def test_default_fake_search_is_complete_and_hash_recomputable():
    result = run_prior_art_search(
        academic_providers=fake_academic_providers(),
        engineering_providers=fake_engineering_providers(),
        queries=fake_query_requests(),
        research_spec_id="rs-1",
        input_spec_hash="a" * 64,
        now=NOW,
    )
    assert result.coverage_status is PriorArtCoverageStatus.COMPLETE
    assert result.coverage_blockers == ()
    assert len(result.academic_neighbors) >= 5
    assert len(result.engineering_neighbors) >= 3
    assert [neighbor.rank for neighbor in result.academic_neighbors] == list(
        range(1, len(result.academic_neighbors) + 1)
    )
    assert sha256_hex(neighbor_evidence_content_payload(result)) == result.artifact_hash


def test_insufficient_academic_neighbors_cannot_be_complete():
    records = deduplicate_provider_records(fake_academic_records())[:4]
    status, blockers = validate_prior_art_coverage(
        academic_records=records,
        engineering_records=deduplicate_provider_records(fake_engineering_records()),
        queries=_queries(),
        now=NOW,
    )
    assert status is PriorArtCoverageStatus.PARTIAL
    assert any("学术近邻" in blocker and "5" in blocker for blocker in blockers)


def test_insufficient_engineering_neighbors_cannot_be_complete():
    records = deduplicate_provider_records(fake_engineering_records())[:2]
    status, blockers = validate_prior_art_coverage(
        academic_records=deduplicate_provider_records(fake_academic_records()),
        engineering_records=records,
        queries=_queries(),
        now=NOW,
    )
    assert status is PriorArtCoverageStatus.PARTIAL
    assert any("工程近邻" in blocker and "3" in blocker for blocker in blockers)


def test_insufficient_source_classes_cannot_be_complete():
    academic_records = tuple(
        record
        for record in deduplicate_provider_records(fake_academic_records())
        if record.provider_name == "openalex"
    )
    status, blockers = validate_prior_art_coverage(
        academic_records=academic_records,
        engineering_records=deduplicate_provider_records(fake_engineering_records()),
        queries=_queries(),
        now=NOW,
    )
    assert status is PriorArtCoverageStatus.PARTIAL
    assert any("学术来源" in blocker and "3" in blocker for blocker in blockers)


def test_unverified_metadata_cannot_be_complete():
    records = list(deduplicate_provider_records(fake_academic_records()))
    records[0] = replace(records[0], metadata_verified=False)
    status, blockers = validate_prior_art_coverage(
        academic_records=tuple(records),
        engineering_records=deduplicate_provider_records(fake_engineering_records()),
        queries=_queries(),
        now=NOW,
    )
    assert status is PriorArtCoverageStatus.PARTIAL
    assert any("metadata_verified" in blocker for blocker in blockers)


def test_insufficient_maturity_evidence_cannot_be_complete():
    records = list(deduplicate_provider_records(fake_engineering_records()))
    records[0] = replace(records[0], maturity_evidence_refs=("release-record",))
    status, blockers = validate_prior_art_coverage(
        academic_records=deduplicate_provider_records(fake_academic_records()),
        engineering_records=tuple(records),
        queries=_queries(),
        now=NOW,
    )
    assert status is PriorArtCoverageStatus.PARTIAL
    assert any("成熟度证据" in blocker for blocker in blockers)


def test_provider_failure_yields_failed_provider():
    class BrokenProvider:
        source_name = "broken"
        kind: PriorArtProviderKind = "academic"

        def search(self, query: PriorArtQueryRecord):
            raise RuntimeError("provider unavailable")

    result = run_prior_art_search(
        academic_providers=(BrokenProvider(),),
        engineering_providers=fake_engineering_providers(),
        queries=_queries(),
        research_spec_id="rs-1",
        input_spec_hash="a" * 64,
        now=NOW,
    )
    assert result.coverage_status is PriorArtCoverageStatus.FAILED_PROVIDER
    assert any("broken" in blocker for blocker in result.coverage_blockers)


def test_fake_provider_is_deterministic():
    first = run_prior_art_search(
        academic_providers=fake_academic_providers(),
        engineering_providers=fake_engineering_providers(),
        queries=fake_query_requests(),
        research_spec_id="rs-1",
        input_spec_hash="a" * 64,
        now=NOW,
    )
    second = run_prior_art_search(
        academic_providers=fake_academic_providers(),
        engineering_providers=fake_engineering_providers(),
        queries=fake_query_requests(),
        research_spec_id="rs-1",
        input_spec_hash="a" * 64,
        now=NOW,
    )
    assert first == second
    assert first.artifact_hash == second.artifact_hash


def test_missing_query_direction_yields_partial():
    result = run_prior_art_search(
        academic_providers=fake_academic_providers(),
        engineering_providers=fake_engineering_providers(),
        queries=(_queries()[0],),
        research_spec_id="rs-1",
        input_spec_hash="a" * 64,
        now=NOW,
    )
    assert result.coverage_status is PriorArtCoverageStatus.PARTIAL
    assert any("工程查询" in blocker for blocker in result.coverage_blockers)
