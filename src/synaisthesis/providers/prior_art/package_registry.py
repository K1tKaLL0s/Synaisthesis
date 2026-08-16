"""Package registry evidence provider (PyPI/npm style) for engineering neighbors.

Evidence: published release artifact, license metadata and source repository
link.  Download counts are quarantined as untrusted text, never maturity
evidence (19 §5 M13.2 stop condition).
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime

from synaisthesis.providers.prior_art.base import ExternalText
from synaisthesis.providers.prior_art.engineering_base import (
    EngineeringNeighborHit,
    EngineeringNeighborQuery,
)


@dataclass(frozen=True, slots=True)
class PackageEvidence:
    """Concrete evidence lines for one published package."""

    stable_identifier: str
    canonical_url: str
    category: str
    wheel_ref: str
    license_ref: str
    source_repo_ref: str
    function_features: dict[str, tuple[float, str]]
    application_features: dict[str, tuple[float, str]]
    download_text: str = ""


PACKAGE_CORPUS: tuple[PackageEvidence, ...] = (
    PackageEvidence(
        stable_identifier="pkg/formal-contract-toolkit",
        canonical_url="https://pypi.org/project/formal-contract-toolkit/",
        category="contract-tooling",
        wheel_ref="https://pypi.org/project/formal-contract-toolkit/#files",
        license_ref="https://pypi.org/project/formal-contract-toolkit/#license",
        source_repo_ref="https://github.com/example/formal-contract-toolkit",
        function_features={
            "contract_compilation": (
                0.85,
                "https://pypi.org/project/formal-contract-toolkit/#description",
            ),
            "spec_generation": (
                0.7,
                "https://pypi.org/project/formal-contract-toolkit/#description",
            ),
        },
        application_features={
            "milestone_gating": (
                0.8,
                "https://pypi.org/project/formal-contract-toolkit/#description",
            ),
        },
        download_text="1.4 million downloads this month",
    ),
)


class PackageRegistryProvider:
    """Engineering neighbor evidence drawn from package registries."""

    source_name = "package-registry-fixture"

    def __init__(self, corpus: tuple[PackageEvidence, ...] = PACKAGE_CORPUS) -> None:
        self._corpus = corpus

    def search_engineering_neighbors(
        self, query: EngineeringNeighborQuery
    ) -> tuple[EngineeringNeighborHit, ...]:
        hits: list[EngineeringNeighborHit] = []
        for evidence in self._corpus:
            if not self._matches(query, evidence):
                continue
            hit = self._to_hit(evidence)
            if not hit.maturity_evidence:
                raise RuntimeError(f"{evidence.stable_identifier} 无成熟度证据")
            hits.append(hit)
        return tuple(hits)

    @staticmethod
    def _matches(query: EngineeringNeighborQuery, evidence: PackageEvidence) -> bool:
        query_text = f"{query.original_text} {' '.join(query.requirement_refs)}".lower()
        haystack = (evidence.category + " " + " ".join(evidence.function_features)).lower()
        return any(token in haystack for token in ("contract", "spec") if token in query_text)

    @staticmethod
    def _to_hit(evidence: PackageEvidence) -> EngineeringNeighborHit:
        untrusted: list[ExternalText] = []
        if evidence.download_text:
            untrusted.append(
                ExternalText(
                    content=evidence.download_text,
                    source_ref=f"{evidence.canonical_url}#statistics",
                )
            )
        return EngineeringNeighborHit(
            stable_identifier=evidence.stable_identifier,
            canonical_url=evidence.canonical_url,
            category=evidence.category,
            function_features=evidence.function_features,
            application_features=evidence.application_features,
            maturity_evidence=(
                (f"发布产物 {evidence.wheel_ref}", evidence.wheel_ref),
                (f"许可证元数据 {evidence.license_ref}", evidence.license_ref),
                (f"源代码仓库 {evidence.source_repo_ref}", evidence.source_repo_ref),
            ),
            license_ref=evidence.license_ref,
            untrusted_texts=tuple(untrusted),
            accessed_at=datetime(2025, 1, 15, tzinfo=UTC),
        )


__all__ = ["PACKAGE_CORPUS", "PackageEvidence", "PackageRegistryProvider"]
