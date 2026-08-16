"""Early research qualification application service (blueprint 07, section 3).

M2.4 scope: orchestrate synchronous prior-art providers into an immutable
NeighborEvidenceSet, with deterministic deduplication, sorting, ranking and
coverage validation. No database, artifact store, event stream or network I/O
is performed here yet; those capabilities arrive in later storage tasks.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import replace
from datetime import datetime

from synaisthesis.domain.enums import PriorArtCoverageStatus
from synaisthesis.domain.event import sha256_hex
from synaisthesis.domain.qualification import NeighborEvidenceSet
from synaisthesis.providers.prior_art.base import (
    PriorArtProvider,
    PriorArtQueryRequest,
    ProviderNeighborRecord,
)
from synaisthesis.providers.prior_art.normalization import (
    deduplicate_provider_records,
    metadata_receipts,
    sort_provider_records,
    to_prior_art_neighbor,
)

MIN_ACADEMIC_SOURCE_CLASSES = 3
MIN_ENGINEERING_SOURCE_CLASSES = 2
MIN_ACADEMIC_NEIGHBORS = 5
MIN_ENGINEERING_NEIGHBORS = 3
MIN_MATURITY_EVIDENCE_REFS = 2


def _provider_record_kind(record: ProviderNeighborRecord) -> str:
    return record.kind


def _collect_provider_records(
    *,
    academic_providers: Sequence[PriorArtProvider],
    engineering_providers: Sequence[PriorArtProvider],
    queries: tuple[PriorArtQueryRequest, ...],
) -> tuple[list[ProviderNeighborRecord], list[ProviderNeighborRecord], list[str]]:
    academic_records: list[ProviderNeighborRecord] = []
    engineering_records: list[ProviderNeighborRecord] = []
    failures: list[str] = []
    for request in queries:
        providers = academic_providers if request.kind == "academic" else engineering_providers
        if not providers:
            failures.append(f"{request.kind} query has no configured provider")
            continue
        for provider in providers:
            try:
                records = provider.search(request.query)
            except Exception as exc:  # noqa: BLE001 - provider boundary must fail closed
                failures.append(
                    f"provider {getattr(provider, 'source_name', provider)!r} "
                    f"failed with {type(exc).__name__}"
                )
                continue
            for record in records:
                if record.kind != request.kind:
                    failures.append(
                        f"provider {getattr(provider, 'source_name', provider)!r} "
                        f"returned {record.kind!r} record for {request.kind!r} query"
                    )
                    continue
                if request.kind == "academic":
                    academic_records.append(record)
                else:
                    engineering_records.append(record)
    return academic_records, engineering_records, failures


def validate_prior_art_coverage(
    *,
    academic_records: tuple[ProviderNeighborRecord, ...],
    engineering_records: tuple[ProviderNeighborRecord, ...],
    queries: tuple[PriorArtQueryRequest, ...],
    now: datetime | None = None,
) -> tuple[PriorArtCoverageStatus, tuple[str, ...]]:
    """Validate the RQ1 minimum coverage gate (03A, section 3.3).

    Returns COMPLETE only when every default minimum is met. Any deficiency is
    reported as a deterministic blocker tuple and mapped to PARTIAL.
    """
    del now  # reserved for provider freshness checks in later real-provider tasks
    blockers: list[str] = []

    query_kinds = {request.kind for request in queries}
    if "academic" not in query_kinds:
        blockers.append("缺少学术查询方向：必须从 S1/S4 字段分别派生学术查询")
    if "engineering" not in query_kinds:
        blockers.append("缺少工程查询方向：必须从 S1/S4 字段分别派生工程查询")

    academic_sources = {record.provider_name for record in academic_records}
    engineering_sources = {record.provider_name for record in engineering_records}
    if len(academic_sources) < MIN_ACADEMIC_SOURCE_CLASSES:
        blockers.append(
            f"学术来源类别不足：需要至少 {MIN_ACADEMIC_SOURCE_CLASSES} 类，"
            f"当前 {len(academic_sources)} 类"
        )
    if len(engineering_sources) < MIN_ENGINEERING_SOURCE_CLASSES:
        blockers.append(
            f"工程来源类别不足：需要至少 {MIN_ENGINEERING_SOURCE_CLASSES} 类，"
            f"当前 {len(engineering_sources)} 类"
        )

    if len(academic_records) < MIN_ACADEMIC_NEIGHBORS:
        blockers.append(
            f"学术近邻数量不足：去重后需要至少 {MIN_ACADEMIC_NEIGHBORS} 个，"
            f"当前 {len(academic_records)} 个"
        )
    if len(engineering_records) < MIN_ENGINEERING_NEIGHBORS:
        blockers.append(
            f"工程近邻数量不足：去重后需要至少 {MIN_ENGINEERING_NEIGHBORS} 个，"
            f"当前 {len(engineering_records)} 个"
        )

    for record in academic_records + engineering_records:
        if not record.stable_identifier.strip() and not (
            record.canonical_url and record.canonical_url.strip()
        ):
            blockers.append(f"近邻 {record.stable_identifier!r} 缺少可稳定解析的标识符或 URL")
        if not record.metadata_verified:
            blockers.append(f"近邻 {record.stable_identifier!r} metadata_verified=false")
        if record.accessed_at is None:
            blockers.append(f"近邻 {record.stable_identifier!r} 缺少访问时间")
        if (
            _provider_record_kind(record) == "engineering"
            and len(record.maturity_evidence_refs) < MIN_MATURITY_EVIDENCE_REFS
        ):
            blockers.append(
                f"工程近邻 {record.stable_identifier!r} 成熟度证据不足："
                f"至少需要 {MIN_MATURITY_EVIDENCE_REFS} 条引用"
            )

    status = PriorArtCoverageStatus.COMPLETE if not blockers else PriorArtCoverageStatus.PARTIAL
    return status, tuple(blockers)


def neighbor_evidence_content_payload(evidence: NeighborEvidenceSet) -> dict[str, object]:
    """Return the hash-covered semantic payload (artifact_hash excluded)."""
    payload = evidence.to_event_payload()
    payload.pop("artifact_hash", None)
    return payload


def run_prior_art_search(
    *,
    academic_providers: Sequence[PriorArtProvider],
    engineering_providers: Sequence[PriorArtProvider],
    queries: tuple[PriorArtQueryRequest, ...],
    research_spec_id: str,
    input_spec_hash: str,
    search_id: str | None = None,
    unsearched_areas: tuple[str, ...] = (),
    inclusion_exclusion_log: str = "",
    now: datetime | None = None,
) -> NeighborEvidenceSet:
    """Run a synchronous fake/real prior-art search and return RQ1 evidence.

    Provider output is quarantined as data only, deduplicated by stable
    identifier/URL, sorted by route-specific proximity and ranked from 1.
    Provider failures produce FAILED_PROVIDER; data deficiencies produce
    PARTIAL; only a fully passing coverage gate produces COMPLETE.
    """
    ordered_queries = tuple(sorted(queries, key=lambda item: item.query.query_id))
    academic_records, engineering_records, failures = _collect_provider_records(
        academic_providers=academic_providers,
        engineering_providers=engineering_providers,
        queries=ordered_queries,
    )

    academic_unique = deduplicate_provider_records(tuple(academic_records))
    engineering_unique = deduplicate_provider_records(tuple(engineering_records))
    academic_sorted = sort_provider_records(academic_unique, kind="academic")
    engineering_sorted = sort_provider_records(engineering_unique, kind="engineering")
    academic_neighbors = tuple(
        to_prior_art_neighbor(record, rank=index)
        for index, record in enumerate(academic_sorted, start=1)
    )
    engineering_neighbors = tuple(
        to_prior_art_neighbor(record, rank=index)
        for index, record in enumerate(engineering_sorted, start=1)
    )

    coverage_status, coverage_blockers = validate_prior_art_coverage(
        academic_records=academic_unique,
        engineering_records=engineering_unique,
        queries=ordered_queries,
        now=now,
    )
    blockers = list(coverage_blockers)
    if failures:
        coverage_status = PriorArtCoverageStatus.FAILED_PROVIDER
        blockers = failures + blockers

    if search_id is None:
        search_id = "prior-art:" + sha256_hex(
            {
                "research_spec_id": research_spec_id,
                "input_spec_hash": input_spec_hash,
                "query_ids": [item.query.query_id for item in ordered_queries],
                "academic_ids": [item.stable_identifier for item in academic_sorted],
                "engineering_ids": [item.stable_identifier for item in engineering_sorted],
            }
        )

    evidence = NeighborEvidenceSet(
        search_id=search_id,
        research_spec_id=research_spec_id,
        input_spec_hash=input_spec_hash,
        query_records=tuple(item.query for item in ordered_queries),
        academic_neighbors=academic_neighbors,
        engineering_neighbors=engineering_neighbors,
        standards_and_reference_architectures=(),
        patent_neighbors=(),
        metadata_verification_receipts=metadata_receipts(academic_unique + engineering_unique),
        inclusion_exclusion_log=inclusion_exclusion_log,
        unsearched_areas=unsearched_areas,
        coverage_status=coverage_status,
        coverage_blockers=tuple(blockers),
        artifact_hash="0" * 64,
    )
    return replace(
        evidence,
        artifact_hash=sha256_hex(neighbor_evidence_content_payload(evidence)),
    )


__all__ = [
    "MIN_ACADEMIC_NEIGHBORS",
    "MIN_ACADEMIC_SOURCE_CLASSES",
    "MIN_ENGINEERING_NEIGHBORS",
    "MIN_ENGINEERING_SOURCE_CLASSES",
    "MIN_MATURITY_EVIDENCE_REFS",
    "neighbor_evidence_content_payload",
    "run_prior_art_search",
    "validate_prior_art_coverage",
]
