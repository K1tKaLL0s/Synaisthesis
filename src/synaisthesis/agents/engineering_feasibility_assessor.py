"""Engineering Feasibility Assessor role for RQ2F (M2.4A)."""

from __future__ import annotations

from dataclasses import dataclass

from synaisthesis.agents.early_formalizer import assess_feasibility_matrix
from synaisthesis.agents.schemas import MechanismSketch, NaturalLanguageSpec, ResearchScopeSpec
from synaisthesis.domain.qualification import (
    ASSESSMENT_ROLE_ENGINEERING_FEASIBILITY_ASSESSOR,
    FeasibilityPredicateMatrix,
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


__all__ = ["EngineeringFeasibilityAssessor"]
