"""Official documentation evidence provider (specs/standards/vendor docs).

Official-source verification for engineering neighbors (03B §6.1, 19 §5
M13.2): canonical spec/API/installation references, never marketing text.
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
class OfficialDocEvidence:
    """Concrete evidence lines for one official documentation set."""

    stable_identifier: str
    canonical_url: str
    category: str
    spec_ref: str
    api_ref: str
    install_ref: str
    function_features: dict[str, tuple[float, str]]
    application_features: dict[str, tuple[float, str]]
    press_text: str = ""


OFFICIAL_DOCS_CORPUS: tuple[OfficialDocEvidence, ...] = (
    OfficialDocEvidence(
        stable_identifier="docs/contract-spec-2024",
        canonical_url="https://example.org/spec/contract-2024",
        category="standards",
        spec_ref="https://example.org/spec/contract-2024#normative",
        api_ref="https://example.org/spec/contract-2024#api",
        install_ref="https://example.org/spec/contract-2024#installation",
        function_features={
            "contract_compilation": (0.95, "https://example.org/spec/contract-2024#normative"),
            "deterministic_hash": (0.9, "https://example.org/spec/contract-2024#normative"),
        },
        application_features={
            "spec_traceability": (0.95, "https://example.org/spec/contract-2024#normative"),
        },
        press_text="named best practice of the year by industry press",
    ),
    OfficialDocEvidence(
        stable_identifier="docs/provenance-vendor-manual",
        canonical_url="https://docs.example.com/provenance/v1",
        category="vendor-manual",
        spec_ref="https://docs.example.com/provenance/v1#spec",
        api_ref="https://docs.example.com/provenance/v1#api",
        install_ref="https://docs.example.com/provenance/v1#install",
        function_features={
            "change_provenance": (0.9, "https://docs.example.com/provenance/v1#spec"),
            "session_binding": (0.8, "https://docs.example.com/provenance/v1#api"),
        },
        application_features={
            "audit_reconstruction": (0.9, "https://docs.example.com/provenance/v1#api"),
        },
        press_text="",
    ),
)


class OfficialDocsProvider:
    """Engineering neighbor evidence drawn from official documentation."""

    source_name = "official-docs-fixture"

    def __init__(self, corpus: tuple[OfficialDocEvidence, ...] = OFFICIAL_DOCS_CORPUS) -> None:
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
    def _matches(query: EngineeringNeighborQuery, evidence: OfficialDocEvidence) -> bool:
        query_text = f"{query.original_text} {' '.join(query.requirement_refs)}".lower()
        haystack = (evidence.category + " " + " ".join(evidence.function_features)).lower()
        tokens = ("contract", "spec", "provenance")
        return any(token in haystack for token in tokens if token in query_text)

    @staticmethod
    def _to_hit(evidence: OfficialDocEvidence) -> EngineeringNeighborHit:
        untrusted: list[ExternalText] = []
        if evidence.press_text:
            untrusted.append(
                ExternalText(
                    content=evidence.press_text,
                    source_ref=f"{evidence.canonical_url}#press",
                )
            )
        return EngineeringNeighborHit(
            stable_identifier=evidence.stable_identifier,
            canonical_url=evidence.canonical_url,
            category=evidence.category,
            function_features=evidence.function_features,
            application_features=evidence.application_features,
            maturity_evidence=(
                (f"规范章节 {evidence.spec_ref}", evidence.spec_ref),
                (f"API 参考 {evidence.api_ref}", evidence.api_ref),
                (f"安装指南 {evidence.install_ref}", evidence.install_ref),
            ),
            license_ref=None,
            untrusted_texts=tuple(untrusted),
            accessed_at=datetime(2025, 1, 15, tzinfo=UTC),
        )


__all__ = ["OFFICIAL_DOCS_CORPUS", "OfficialDocEvidence", "OfficialDocsProvider"]
