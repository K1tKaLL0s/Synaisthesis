"""Early Formalizer role for RQ2F (deterministic structural assessor, M2.4A)."""

from __future__ import annotations

from dataclasses import dataclass

from synaisthesis.agents.schemas import MechanismSketch, NaturalLanguageSpec, ResearchScopeSpec
from synaisthesis.domain.enums import PredicateVerdict
from synaisthesis.domain.qualification import (
    ASSESSMENT_ROLE_EARLY_FORMALIZER,
    EngineeringFitPredicates,
    FeasibilityPredicate,
    FeasibilityPredicateMatrix,
    NeighborEvidenceSet,
    TheoryFitPredicates,
    assessment_context_hash,
)


def _pred(
    predicate_id: str,
    verdict: PredicateVerdict,
    refs: tuple[str, ...],
) -> FeasibilityPredicate:
    return FeasibilityPredicate(
        predicate_id=predicate_id,
        verdict=verdict,
        evidence_refs=refs,
    )


def _verdict(pass_condition: bool, fail_condition: bool) -> PredicateVerdict:
    if pass_condition:
        return PredicateVerdict.PASS
    if fail_condition:
        return PredicateVerdict.FAIL
    return PredicateVerdict.UNKNOWN


def assess_feasibility_matrix(
    *,
    role: str,
    session_id: str,
    spec: NaturalLanguageSpec,
    mechanism: MechanismSketch,
    scope: ResearchScopeSpec,
    evidence: NeighborEvidenceSet,
) -> FeasibilityPredicateMatrix:
    """Compute a complete T*/E* predicate matrix with field/evidence references.

    This is the pre-LLM deterministic contract: it checks whether the frozen
    natural-language materials contain enough structure for each predicate.
    Missing material is FAIL or UNKNOWN, never an assumed PASS.
    """
    del role, session_id  # reserved for model-profile isolation in M6.x
    academic_refs = tuple(
        neighbor.stable_identifier for neighbor in evidence.academic_neighbors[:2]
    )
    engineering_refs = tuple(
        neighbor.stable_identifier for neighbor in evidence.engineering_neighbors[:2]
    )

    theory = TheoryFitPredicates(
        tfo=_pred(
            "TFO",
            _verdict(
                bool(scope.object_domain.strip()) and bool(spec.object_candidates),
                not scope.object_domain.strip(),
            ),
            ("S4.object_domain", "S1.object_candidates") + academic_refs,
        ),
        tfr=_pred(
            "TFR",
            _verdict(
                bool(mechanism.inputs)
                and bool(mechanism.outputs)
                and bool(mechanism.state_change.strip())
                and bool(mechanism.invariants),
                not mechanism.state_change.strip() or not mechanism.inputs or not mechanism.outputs,
            ),
            ("S1.core_definition", "S2.inputs", "S2.state_change", "S2.outputs", "S2.invariants"),
        ),
        tfc=_pred(
            "TFC",
            _verdict(
                bool(scope.central_claims)
                and len(scope.central_claims) == len(scope.evidence_requirements),
                not scope.central_claims,
            ),
            ("S4.central_claims", "S4.evidence_requirements") + academic_refs,
        ),
        tfw=_pred(
            "TFW",
            _verdict(
                bool(mechanism.failure_conditions) and bool(scope.stop_conditions),
                not mechanism.failure_conditions and not scope.stop_conditions,
            ),
            ("S2.failure_conditions", "S4.stop_conditions"),
        ),
        tfp=_pred(
            "TFP",
            _verdict(
                bool(spec.expected_functions)
                and bool(spec.target_applications)
                and bool(scope.nearest_neighbor_difference.strip()),
                not spec.expected_functions and not spec.target_applications,
            ),
            (
                "S1.expected_functions",
                "S1.target_applications",
                "S4.nearest_neighbor_difference",
            ),
        ),
    )

    engineering = EngineeringFitPredicates(
        efs=_pred(
            "EFS",
            _verdict(
                bool(spec.intended_users) or bool(spec.target_applications),
                not spec.intended_users and not spec.target_applications,
            ),
            ("S1.intended_users", "S1.target_applications") + engineering_refs,
        ),
        efi=_pred(
            "EFI",
            _verdict(
                bool(mechanism.inputs) and bool(mechanism.outputs),
                not mechanism.inputs or not mechanism.outputs,
            ),
            ("S2.inputs", "S2.outputs"),
        ),
        efa=_pred(
            "EFA",
            _verdict(
                bool(mechanism.state_change.strip())
                and bool(scope.object_domain.strip())
                and bool(scope.engineering_relevance.strip()),
                not mechanism.state_change.strip(),
            ),
            ("S2.state_change", "S4.object_domain", "S4.engineering_relevance"),
        ),
        efm=_pred(
            "EFM",
            _verdict(
                bool(spec.success_metrics) and bool(spec.operational_constraints),
                not spec.success_metrics,
            ),
            ("S1.success_metrics", "S1.operational_constraints"),
        ),
        eff=_pred(
            "EFF",
            _verdict(
                bool(spec.operational_constraints)
                and bool(scope.failure_learning_plan.strip())
                and bool(scope.stop_conditions),
                not spec.operational_constraints,
            ),
            (
                "S1.operational_constraints",
                "S4.failure_learning_plan",
                "S4.stop_conditions",
            )
            + engineering_refs,
        ),
    )
    return FeasibilityPredicateMatrix(theory=theory, engineering=engineering)


@dataclass(frozen=True, slots=True)
class EarlyFormalizer:
    """An isolated EARLY_FORMALIZER assessment session."""

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
    ) -> EarlyFormalizer:
        return cls(
            session_id=session_id,
            role=ASSESSMENT_ROLE_EARLY_FORMALIZER,
            isolated_context_hash=assessment_context_hash(
                role=ASSESSMENT_ROLE_EARLY_FORMALIZER,
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


__all__ = ["EarlyFormalizer", "assess_feasibility_matrix"]
