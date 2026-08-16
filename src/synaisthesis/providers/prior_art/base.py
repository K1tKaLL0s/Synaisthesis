"""Prior-art provider contracts and quarantined external content (M2.4)."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Literal, Protocol

from synaisthesis.domain.qualification import PriorArtQueryRecord

PriorArtProviderKind = Literal["academic", "engineering"]


@dataclass(frozen=True, slots=True)
class ExternalText:
    """Untrusted external text (blueprint 08, section 4).

    This is a pure data object. No code in Synaisthesis may eval/exec its
    content or grant it tool authority.
    """

    content: str
    source_ref: str
    untrusted: bool = True


@dataclass(frozen=True, slots=True)
class ProximityFeature:
    """One 0-4 similarity component with mandatory evidence references."""

    value: float
    evidence_refs: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class TheoryProximityFeatures:
    """Academic theory-proximity features (03A, section 3.4)."""

    object_domain: ProximityFeature
    mechanism: ProximityFeature
    assumptions: ProximityFeature
    conclusion: ProximityFeature


@dataclass(frozen=True, slots=True)
class ApplicationProximityFeatures:
    """Engineering application-proximity features (03A, section 3.4)."""

    expected_function: ProximityFeature
    use_context: ProximityFeature
    input_output: ProximityFeature
    system_architecture: ProximityFeature
    operational_constraints: ProximityFeature
    maturity: ProximityFeature


@dataclass(frozen=True, slots=True)
class ProviderNeighborRecord:
    """One raw prior-art hit returned by a provider, before normalization."""

    provider_name: str
    kind: PriorArtProviderKind
    stable_identifier: str
    canonical_url: str | None
    metadata_verified: bool
    metadata_verification_receipt: str
    maturity_evidence_refs: tuple[str, ...]
    theory_features: TheoryProximityFeatures
    application_features: ApplicationProximityFeatures
    similarity_evidence_refs: tuple[str, ...]
    untrusted_texts: tuple[ExternalText, ...]
    accessed_at: datetime


@dataclass(frozen=True, slots=True)
class PriorArtQueryRequest:
    """A directional RQ1 query; kind selects the provider family."""

    query: PriorArtQueryRecord
    kind: PriorArtProviderKind


class PriorArtProvider(Protocol):
    """Synchronous prior-art provider contract."""

    @property
    def source_name(self) -> str: ...

    @property
    def kind(self) -> PriorArtProviderKind: ...

    def search(self, query: PriorArtQueryRecord) -> tuple[ProviderNeighborRecord, ...]: ...
