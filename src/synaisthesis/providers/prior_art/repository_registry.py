"""Repository evidence provider (GitHub/GitLab style) for engineering neighbors.

Deterministic fixture corpus in the spirit of 03B §6.1 / 19 §5 M13.2: every hit
carries release, test-suite and architecture-document evidence; popularity
(star counts) is exposed only as an untrusted text and never as maturity
evidence.
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
class RepositoryEvidence:
    """Concrete evidence lines for one repository."""

    stable_identifier: str
    canonical_url: str
    category: str
    release_ref: str
    test_ref: str
    architecture_ref: str
    license_ref: str
    function_features: dict[str, tuple[float, str]]
    application_features: dict[str, tuple[float, str]]
    marketing_text: str = ""


REPOSITORY_CORPUS: tuple[RepositoryEvidence, ...] = (
    RepositoryEvidence(
        stable_identifier="repo/hyperbinding-core",
        canonical_url="https://github.com/example/hyperbinding-core",
        category="binding-specification",
        release_ref="https://github.com/example/hyperbinding-core/releases/tag/v2.4.0",
        test_ref="https://github.com/example/hyperbinding-core/tree/v2.4.0/tests",
        architecture_ref="https://github.com/example/hyperbinding-core/blob/v2.4.0/docs/architecture.md",
        license_ref="https://github.com/example/hyperbinding-core/blob/v2.4.0/LICENSE",
        function_features={
            "contract_compilation": (
                0.9,
                "https://github.com/example/hyperbinding-core/blob/v2.4.0/docs/features.md#contract-compilation",
            ),
            "deterministic_hash": (
                0.8,
                "https://github.com/example/hyperbinding-core/blob/v2.4.0/docs/features.md#deterministic-hash",
            ),
        },
        application_features={
            "spec_traceability": (
                0.9,
                "https://github.com/example/hyperbinding-core/blob/v2.4.0/docs/application.md#traceability",
            ),
            "milestone_gating": (
                0.7,
                "https://github.com/example/hyperbinding-core/blob/v2.4.0/docs/application.md#gating",
            ),
        },
        marketing_text="starred by 12k developers, trending this month",
    ),
    RepositoryEvidence(
        stable_identifier="repo/delta-provenance",
        canonical_url="https://gitlab.com/example/delta-provenance",
        category="provenance",
        release_ref="https://gitlab.com/example/delta-provenance/-/releases/v1.9.1",
        test_ref="https://gitlab.com/example/delta-provenance/-/tree/v1.9.1/test",
        architecture_ref="https://gitlab.com/example/delta-provenance/-/blob/v1.9.1/docs/design.md",
        license_ref="https://gitlab.com/example/delta-provenance/-/blob/v1.9.1/LICENSE",
        function_features={
            "change_provenance": (
                0.85,
                "https://gitlab.com/example/delta-provenance/-/blob/v1.9.1/docs/design.md#provenance",
            ),
            "session_binding": (
                0.75,
                "https://gitlab.com/example/delta-provenance/-/blob/v1.9.1/docs/design.md#session-binding",
            ),
        },
        application_features={
            "audit_reconstruction": (
                0.85,
                "https://gitlab.com/example/delta-provenance/-/blob/v1.9.1/docs/design.md#audit",
            ),
        },
        marketing_text="most downloaded provenance library",
    ),
)


class RepositoryRegistryProvider:
    """Engineering neighbor evidence drawn from repository registries."""

    source_name = "repository-registry-fixture"

    def __init__(self, corpus: tuple[RepositoryEvidence, ...] = REPOSITORY_CORPUS) -> None:
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
    def _matches(query: EngineeringNeighborQuery, evidence: RepositoryEvidence) -> bool:
        query_text = f"{query.original_text} {' '.join(query.requirement_refs)}".lower()
        haystack = (
            evidence.category
            + " "
            + " ".join(evidence.function_features)
            + " "
            + " ".join(evidence.application_features)
        ).lower()
        tokens = ("binding", "contract", "provenance", "trace")
        return any(token in haystack for token in tokens if token in query_text)

    @staticmethod
    def _to_hit(evidence: RepositoryEvidence) -> EngineeringNeighborHit:
        untrusted: list[ExternalText] = []
        if evidence.marketing_text:
            untrusted.append(
                ExternalText(
                    content=evidence.marketing_text,
                    source_ref=f"{evidence.canonical_url}#readme",
                )
            )
        return EngineeringNeighborHit(
            stable_identifier=evidence.stable_identifier,
            canonical_url=evidence.canonical_url,
            category=evidence.category,
            function_features=evidence.function_features,
            application_features=evidence.application_features,
            maturity_evidence=(
                (f"发布 {evidence.release_ref}", evidence.release_ref),
                (f"测试套件 {evidence.test_ref}", evidence.test_ref),
                (f"架构文档 {evidence.architecture_ref}", evidence.architecture_ref),
            ),
            license_ref=evidence.license_ref,
            untrusted_texts=tuple(untrusted),
            accessed_at=datetime(2025, 1, 15, tzinfo=UTC),
        )


__all__ = ["REPOSITORY_CORPUS", "RepositoryEvidence", "RepositoryRegistryProvider"]
