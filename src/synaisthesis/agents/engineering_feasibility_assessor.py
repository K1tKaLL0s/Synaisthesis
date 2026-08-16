"""Engineering Feasibility Assessor role for RQ2F (M2.4A)."""

from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import datetime

from synaisthesis.agents.early_formalizer import assess_feasibility_matrix
from synaisthesis.agents.schemas import MechanismSketch, NaturalLanguageSpec, ResearchScopeSpec
from synaisthesis.domain.enums import (
    EngineeringConceptStatus,
    EngineeringRouteDecision,
)
from synaisthesis.domain.errors import DomainError
from synaisthesis.domain.event import sha256_hex
from synaisthesis.domain.qualification import (
    ASSESSMENT_ROLE_ENGINEERING_FEASIBILITY_ASSESSOR,
    EngineeringConceptBundle,
    EngineeringRouteSelection,
    FeasibilityPredicateMatrix,
    FormalizationFeasibilityAssessment,
    NeighborEvidenceSet,
    assessment_context_hash,
)


@dataclass(frozen=True, slots=True)
class EngineeringFeasibilityAssessor:
    """An isolated ENGINEERING_FEASIBILITY_ASSESSOR assessment session."""

    session_id: str
    role: str
    isolated_context_hash: str

    @classmethod
    def create(
        cls,
        *,
        session_id: str,
        spec: NaturalLanguageSpec,
        mechanism: MechanismSketch,
        scope: ResearchScopeSpec,
        evidence: NeighborEvidenceSet,
    ) -> EngineeringFeasibilityAssessor:
        return cls(
            session_id=session_id,
            role=ASSESSMENT_ROLE_ENGINEERING_FEASIBILITY_ASSESSOR,
            isolated_context_hash=assessment_context_hash(
                role=ASSESSMENT_ROLE_ENGINEERING_FEASIBILITY_ASSESSOR,
                session_id=session_id,
                input_spec_hash=evidence.input_spec_hash,
                neighbor_evidence_set_id=evidence.search_id,
            ),
        )

    def assess(
        self,
        spec: NaturalLanguageSpec,
        mechanism: MechanismSketch,
        scope: ResearchScopeSpec,
        evidence: NeighborEvidenceSet,
    ) -> FeasibilityPredicateMatrix:
        return assess_feasibility_matrix(
            role=self.role,
            session_id=self.session_id,
            spec=spec,
            mechanism=mechanism,
            scope=scope,
            evidence=evidence,
        )


__all__ = [
    "EngineeringFeasibilityAssessor",
    "build_engineering_concept_bundle",
    "engineering_concept_content_payload",
]


def engineering_concept_content_payload(
    bundle: EngineeringConceptBundle,
) -> dict[str, object]:
    """Return the hash-covered RQ2E content (derived fields excluded)."""
    payload = bundle.to_event_payload()
    for key in ("artifact_hash", "status"):
        payload.pop(key, None)
    return payload


def build_engineering_concept_bundle(
    *,
    route_selection: EngineeringRouteSelection,
    feasibility_assessment: FormalizationFeasibilityAssessment,
    spec: NaturalLanguageSpec,
    mechanism: MechanismSketch,
    scope: ResearchScopeSpec,
    evidence: NeighborEvidenceSet,
    assessor_session_id: str,
    concept_id: str | None = None,
    version: int = 1,
    at: datetime | None = None,
) -> EngineeringConceptBundle:
    """Build an RQ2E candidate bundle from a hash-bound engineering route."""
    del assessor_session_id  # reserved for model-profile session isolation
    if route_selection.decision is not EngineeringRouteDecision.TRY_ENGINEERING_PROJECT:
        raise DomainError(
            "engineering concept build requires TRY_ENGINEERING_PROJECT",
            error_code="ENGINEERING_ROUTE_DECISION_REQUIRED",
        )
    if (
        route_selection.bound_assessment_hash != feasibility_assessment.artifact_hash
        or route_selection.input_spec_hash != feasibility_assessment.input_spec_hash
        or evidence.input_spec_hash != feasibility_assessment.input_spec_hash
    ):
        raise DomainError(
            "route selection, assessment or evidence hash binding is stale",
            error_code="STALE_ROUTE_SELECTION",
        )

    requirement_predicates = (
        *(f"R{index}: {function}" for index, function in enumerate(spec.expected_functions)),
        *(
            f"R{len(spec.expected_functions) + index}: {constraint}"
            for index, constraint in enumerate(spec.operational_constraints)
        ),
    )
    requirement_ids = tuple(item.split(":", 1)[0].strip() for item in requirement_predicates)
    quality_metric_formulas = tuple(
        f"Q{index}(z) comparator_{index} UNRESOLVED_THRESHOLD; unit=unspecified"
        for index in range(len(spec.success_metrics))
    )
    unresolved_thresholds = tuple(f"Q{index}" for index in range(len(spec.success_metrics)))
    traceability_relation = {
        requirement_id: (f"D{index}:design obligation", f"V{index}:verification obligation")
        for index, requirement_id in enumerate(requirement_ids)
    }
    bundle = EngineeringConceptBundle(
        concept_id=concept_id or "ec-" + evidence.search_id,
        version=version,
        research_spec_id=feasibility_assessment.research_spec_id,
        input_spec_hash=feasibility_assessment.input_spec_hash,
        route_selection_id=route_selection.id,
        feasibility_assessment_id=feasibility_assessment.assessment_id,
        neighbor_evidence_set_id=evidence.search_id,
        notation_table=(
            "X: input space",
            "Y: output space",
            "C: operational constraints",
            "s: state",
            "u: control input",
            "e: environment",
        ),
        system_boundary_model={
            "actors": tuple(spec.intended_users),
            "external_systems": ("external library",),
            "trust_zones": ("untrusted_external", "platform"),
        },
        actors_and_use_cases=tuple(spec.target_applications),
        input_output_contracts=("F: X \times C \to Y",),
        state_transition_formulas=("s_{t+1} = T(s_t, u_t, e_t)",),
        requirement_predicates=requirement_predicates,
        quality_metric_formulas=quality_metric_formulas,
        architecture_graph_candidate={
            "type": "component_graph",
            "vertices": ("input_boundary", "compute_core", "output_boundary"),
            "edges": (
                ("input_boundary", "compute_core"),
                ("compute_core", "output_boundary"),
            ),
        },
        traceability_relation=traceability_relation,
        verification_obligations=(
            *(
                f"V{index}: verify requirement {requirement_id}"
                for index, requirement_id in enumerate(requirement_ids)
            ),
            "V-failure: detect failure conditions and execute recovery",
        ),
        neighbor_difference_matrix=(f"{scope.nearest_neighbor_difference} -> R0",),
        assumptions_and_constraints=tuple(spec.operational_constraints),
        unresolved_thresholds=unresolved_thresholds,
        plain_language_explanation=(
            "engineering concept candidate only; not implemented or validated",
        ),
        artifact_hash="0" * 64,
        status=EngineeringConceptStatus.ENGINEERING_CONCEPT_CANDIDATE,
    )
    return replace(
        bundle,
        artifact_hash=sha256_hex(engineering_concept_content_payload(bundle)),
    )


__all__ = [
    "EngineeringFeasibilityAssessor",
    "build_engineering_concept_bundle",
    "engineering_concept_content_payload",
]
