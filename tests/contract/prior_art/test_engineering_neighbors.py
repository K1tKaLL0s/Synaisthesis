"""M13.2.ENGINEERING.PROVIDERS focused contract tests (19 §5).

Acceptance: neighbor function/application ranking is sourced; maturity needs
at least two evidence items; external text stays quarantined; popularity is
never treated as novelty/maturity.
"""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from synaisthesis.domain.errors import DomainError
from synaisthesis.providers.prior_art.engineering_base import (
    EngineeringNeighborHit,
    EngineeringNeighborProvider,
    EngineeringNeighborQuery,
    maturity_evidence_check,
)
from synaisthesis.providers.prior_art.maturity import (
    assess_maturity,
    collect_quarantined_texts,
    deduplicate_neighbors,
    search_all_neighbors,
)
from synaisthesis.providers.prior_art.official_docs import OfficialDocsProvider
from synaisthesis.providers.prior_art.package_registry import PackageRegistryProvider
from synaisthesis.providers.prior_art.repository_registry import RepositoryRegistryProvider


def _query(
    original_text: str = "contract binding with provenance trace",
) -> EngineeringNeighborQuery:
    return EngineeringNeighborQuery(
        query_id="q-1",
        baseline_id="baseline-2025-01",
        requirement_refs=("REQ-BINDING-1", "REQ-TRACE-2"),
        original_text=original_text,
        executed_at=datetime(2025, 1, 15, tzinfo=UTC),
    )


FUNCTION_WEIGHTS = {
    "contract_compilation": 1.0,
    "deterministic_hash": 0.8,
    "change_provenance": 0.9,
    "session_binding": 0.7,
}
APPLICATION_WEIGHTS = {
    "spec_traceability": 1.0,
    "milestone_gating": 0.6,
    "audit_reconstruction": 0.9,
}


def test_blueprint_provider_files_exposed() -> None:
    providers: tuple[EngineeringNeighborProvider, ...] = (
        RepositoryRegistryProvider(),
        PackageRegistryProvider(),
        OfficialDocsProvider(),
    )
    assert [p.source_name for p in providers] == [
        "repository-registry-fixture",
        "package-registry-fixture",
        "official-docs-fixture",
    ]
    hits = search_all_neighbors(_query(), providers, FUNCTION_WEIGHTS, APPLICATION_WEIGHTS)
    assert len(hits) >= 3


def test_every_hit_has_at_least_two_maturity_evidence_items() -> None:
    for provider in (
        RepositoryRegistryProvider(),
        PackageRegistryProvider(),
        OfficialDocsProvider(),
    ):
        for hit in provider.search_engineering_neighbors(_query()):
            assert len(hit.maturity_evidence) >= 2, f"{hit.stable_identifier} 成熟度证据不足"
            assert all(ref.startswith("http") for _, ref in hit.maturity_evidence)


def test_function_and_application_features_are_sourced() -> None:
    for provider in (
        RepositoryRegistryProvider(),
        PackageRegistryProvider(),
        OfficialDocsProvider(),
    ):
        for hit in provider.search_engineering_neighbors(_query()):
            for ref in (
                *hit.function_features.values(),
                *hit.application_features.values(),
            ):
                _value, source = ref
                assert source.startswith("http"), f"{hit.stable_identifier} 特征无来源"


def test_unsourced_feature_is_rejected_at_construction() -> None:
    with pytest.raises(DomainError) as exc:
        EngineeringNeighborHit(
            stable_identifier="bad/unsourced",
            canonical_url="https://example.org/bad",
            category="test",
            function_features={"contract_compilation": (0.9, "   ")},
            application_features={},
            maturity_evidence=(("a", "https://a"), ("b", "https://b")),
        )
    assert exc.value.error_code == "NEIGHBOR_FEATURE_UNSOURCED"


def test_maturity_requires_at_least_two_items() -> None:
    hit = EngineeringNeighborHit(
        stable_identifier="repo/one-evidence",
        canonical_url="https://github.com/example/one",
        category="binding-specification",
        function_features={"contract_compilation": (0.5, "https://github.com/example/one#f")},
        application_features={},
        maturity_evidence=(
            (
                "发布 https://github.com/example/one/releases/tag/v1",
                "https://github.com/example/one/releases/tag/v1",
            ),
        ),
    )
    ok, reasons = maturity_evidence_check(hit)
    assert not ok
    assert any("少于 2 项" in reason for reason in reasons)
    with pytest.raises(DomainError) as exc:
        assess_maturity(hit)
    assert exc.value.error_code == "MATURITY_EVIDENCE_INSUFFICIENT"


@pytest.mark.parametrize(
    "claims",
    [
        (
            ("starred by 12k developers", "https://github.com/example/x#stars"),
            ("starred weekly by 200", "https://github.com/example/x#stars-weekly"),
        ),
        (
            ("1.4 million downloads this month", "https://pypi.org/p/x#statistics"),
            ("weekly download 90k", "https://pypi.org/p/x#statistics-weekly"),
        ),
        (
            ("marketing page claims best practice", "https://example.org/x#press"),
            ("marketing award shortlist 2024", "https://example.org/x#awards"),
        ),
    ],
)
def test_popularity_alone_is_never_maturity(claims: tuple[tuple[str, str], ...]) -> None:
    hit = EngineeringNeighborHit(
        stable_identifier=f"repo/popularity-{len(claims)}",
        canonical_url="https://example.org/popular",
        category="test",
        function_features={"contract_compilation": (0.9, "https://example.org/f")},
        application_features={},
        maturity_evidence=claims,
    )
    ok, reasons = maturity_evidence_check(hit)
    assert not ok
    assert any("popularity" in reason for reason in reasons)
    with pytest.raises(DomainError) as exc:
        assess_maturity(hit)
    assert exc.value.error_code == "MATURITY_EVIDENCE_INSUFFICIENT"


def test_mixed_popularity_plus_concrete_evidence_passes() -> None:
    hit = EngineeringNeighborHit(
        stable_identifier="repo/mixed",
        canonical_url="https://github.com/example/mixed",
        category="binding-specification",
        function_features={"contract_compilation": (0.9, "https://github.com/example/mixed#f")},
        application_features={"spec_traceability": (0.8, "https://github.com/example/mixed#a")},
        maturity_evidence=(
            (
                "发布 https://github.com/example/mixed/releases/tag/v1",
                "https://github.com/example/mixed/releases/tag/v1",
            ),
            (
                "测试套件 https://github.com/example/mixed/tree/v1/tests",
                "https://github.com/example/mixed/tree/v1/tests",
            ),
            ("starred by 12k developers", "https://github.com/example/mixed#stars"),
        ),
    )
    assert maturity_evidence_check(hit) == (True, ())
    assert len(assess_maturity(hit)) == 3


def test_ranking_is_function_application_sourced() -> None:
    hits = search_all_neighbors(
        _query(),
        (RepositoryRegistryProvider(), PackageRegistryProvider(), OfficialDocsProvider()),
        FUNCTION_WEIGHTS,
        APPLICATION_WEIGHTS,
    )
    assert hits == tuple(sorted(hits, key=lambda r: r.rank_score, reverse=True))
    for ranked in hits:
        assert ranked.rank_score > 0.0
        assert ranked.rank_refs, f"{ranked.hit.stable_identifier} 排序分数无来源"
        assert all(ref.startswith("http") for ref in ranked.rank_refs)


def test_unsourced_feature_blocks_ranking() -> None:
    with pytest.raises(DomainError) as exc:
        EngineeringNeighborHit(
            stable_identifier="repo/no-ref-score",
            canonical_url="https://github.com/example/no-ref",
            category="binding-specification",
            function_features={"contract_compilation": (1.0, "")},
            application_features={},
            maturity_evidence=(
                (
                    "发布 https://github.com/example/no-ref/releases/tag/v1",
                    "https://github.com/example/no-ref/releases/tag/v1",
                ),
                (
                    "测试套件 https://github.com/example/no-ref/tree/v1/tests",
                    "https://github.com/example/no-ref/tree/v1/tests",
                ),
            ),
        )
    assert exc.value.error_code == "NEIGHBOR_FEATURE_UNSOURCED"


def test_external_text_stays_quarantined() -> None:
    hits = search_all_neighbors(
        _query(),
        (RepositoryRegistryProvider(), PackageRegistryProvider(), OfficialDocsProvider()),
        FUNCTION_WEIGHTS,
        APPLICATION_WEIGHTS,
    )
    quarantined = collect_quarantined_texts(tuple(r.hit for r in hits))
    assert quarantined, "应至少隔离一条外部文本"
    for content, source_ref in quarantined:
        assert content and source_ref
        # popularity 文本只存在于隔离区，绝不进入成熟度/排序
        assert all("starred" not in line for line in tuple(r.maturity for r in hits))
        assert all("downloads" not in line for line in tuple(r.maturity for r in hits))


def test_deduplicate_by_identifier_and_url() -> None:
    base = RepositoryRegistryProvider().search_engineering_neighbors(_query())
    assert base
    duplicate = base[0]
    extra = base[1] if len(base) > 1 else duplicate
    merged = deduplicate_neighbors((duplicate, duplicate, duplicate, extra))
    assert len(merged) == len(set(h.stable_identifier for h in merged))
    assert merged[0].stable_identifier == duplicate.stable_identifier


def test_search_all_providers_ranks_with_sources() -> None:
    query = _query("spec traceability milestone gating")
    ranked = search_all_neighbors(
        query,
        (RepositoryRegistryProvider(), PackageRegistryProvider(), OfficialDocsProvider()),
        FUNCTION_WEIGHTS,
        APPLICATION_WEIGHTS,
    )
    if not ranked:
        pytest.fail("no ranked neighbors")
    top = ranked[0]
    allowed = {"binding-specification", "contract-tooling", "standards", "vendor-manual"}
    assert top.hit.category in allowed
    assert "spec_traceability" in top.hit.application_features
