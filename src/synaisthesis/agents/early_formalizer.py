"""Early Formalizer role for RQ2F (deterministic structural assessor, M2.4A)."""

from __future__ import annotations

from dataclasses import dataclass

from synaisthesis.agents.schemas import MechanismSketch, NaturalLanguageSpec, ResearchScopeSpec
from synaisthesis.domain.enums import FormulaOrigin, PredicateVerdict
from synaisthesis.domain.qualification import (
    ASSESSMENT_ROLE_EARLY_FORMALIZER,
    EngineeringFitPredicates,
    FeasibilityPredicate,
    FeasibilityPredicateMatrix,
    FormulaItem,
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


# ---------------------------------------------------------------------------
# RQ2M formula skeleton (deterministic pre-LLM builder; see M2.5 contract)
# ---------------------------------------------------------------------------

FORMULA_TYPE_OBJECT_DOMAIN = "OBJECT_DOMAIN"
FORMULA_TYPE_IO_MAP = "INPUT_OUTPUT_MAP"
FORMULA_TYPE_STATE_TRANSITION = "STATE_TRANSITION"
FORMULA_TYPE_ASSUMPTION = "ASSUMPTION"
FORMULA_TYPE_INVARIANT = "INVARIANT"
FORMULA_TYPE_CORE_CLAIM = "CORE_CLAIM"
FORMULA_TYPE_OBJECTIVE = "OBJECTIVE"
FORMULA_TYPE_FAILURE_WITNESS = "FAILURE_WITNESS"
FORMULA_TYPE_APPLICATION_MAP = "THEORY_APPLICATION_MAP"
FORMULA_TYPE_VERIFICATION_OBLIGATION = "VERIFICATION_OBLIGATION"

REQUIRED_FORMULA_TYPES = frozenset(
    {
        FORMULA_TYPE_OBJECT_DOMAIN,
        FORMULA_TYPE_ASSUMPTION,
        FORMULA_TYPE_CORE_CLAIM,
        FORMULA_TYPE_FAILURE_WITNESS,
        FORMULA_TYPE_APPLICATION_MAP,
    }
)


def build_formula_items(
    *,
    spec: NaturalLanguageSpec,
    mechanism: MechanismSketch,
    scope: ResearchScopeSpec,
    evidence: NeighborEvidenceSet,
) -> tuple[FormulaItem, ...]:
    """Build the deterministic RQ2M formula skeleton.

    This is not a mathematical proof generator. It converts the frozen S1/S2/S4
    materials into the ten 03A formula-type slots with LaTeX placeholders and
    source-field references; later M6.x may replace generation while keeping
    the validation invariants unchanged.
    """
    del evidence  # real evidence-aware generation arrives with LLM providers
    core_claim_latex = r"\forall x\in D,\ A(x)\Rightarrow C(x)"
    return (
        FormulaItem(
            formula_id="f-object-domain",
            formula_type=FORMULA_TYPE_OBJECT_DOMAIN,
            latex=r"x \in \mathcal{X}",
            normalized_math_ast=None,
            symbols_used=("X",),
            source_spec_fields=("S4.object_domain", "S1.object_candidates"),
            assumption_formula_ids=(),
            neighbor_refs=(),
            origin=FormulaOrigin.DERIVED,
            confidence=1.0,
            known_ambiguities=(),
            falsification_or_failure_formula_id="",
        ),
        FormulaItem(
            formula_id="f-assumption",
            formula_type=FORMULA_TYPE_ASSUMPTION,
            latex=r"A(x,\theta)=\bigwedge_i A_i(x,\theta)",
            normalized_math_ast=None,
            symbols_used=("A", "X", "theta"),
            source_spec_fields=("S1.boundary_conditions", "S1.operational_constraints"),
            assumption_formula_ids=(),
            neighbor_refs=(),
            origin=FormulaOrigin.DERIVED,
            confidence=1.0,
            known_ambiguities=(),
            falsification_or_failure_formula_id="",
        ),
        FormulaItem(
            formula_id="f-io-map",
            formula_type=FORMULA_TYPE_IO_MAP,
            latex=r"f: \mathcal{X} \to \mathcal{Y}",
            normalized_math_ast=None,
            symbols_used=("X", "Y"),
            source_spec_fields=("S2.inputs", "S2.outputs"),
            assumption_formula_ids=("f-assumption",),
            neighbor_refs=(),
            origin=FormulaOrigin.DERIVED,
            confidence=1.0,
            known_ambiguities=(),
            falsification_or_failure_formula_id="",
        ),
        FormulaItem(
            formula_id="f-state",
            formula_type=FORMULA_TYPE_STATE_TRANSITION,
            latex=r"s_{t+1}=T(s_t,u_t;\theta)",
            normalized_math_ast=None,
            symbols_used=("s", "u", "theta"),
            source_spec_fields=("S2.state_change",),
            assumption_formula_ids=("f-assumption",),
            neighbor_refs=(),
            origin=FormulaOrigin.DERIVED,
            confidence=0.9,
            known_ambiguities=tuple(mechanism.uncertainty_register),
            falsification_or_failure_formula_id="",
        ),
        FormulaItem(
            formula_id="f-invariant",
            formula_type=FORMULA_TYPE_INVARIANT,
            latex=r"\forall t,\ I(s_t)=1",
            normalized_math_ast=None,
            symbols_used=("I", "s"),
            source_spec_fields=("S2.invariants",),
            assumption_formula_ids=("f-assumption",),
            neighbor_refs=(),
            origin=FormulaOrigin.DERIVED,
            confidence=0.9,
            known_ambiguities=(),
            falsification_or_failure_formula_id="",
        ),
        FormulaItem(
            formula_id="f-core-claim",
            formula_type=FORMULA_TYPE_CORE_CLAIM,
            latex=core_claim_latex,
            normalized_math_ast=None,
            symbols_used=("A", "C"),
            source_spec_fields=("S1.core_definition", "S4.central_claims"),
            assumption_formula_ids=("f-assumption",),
            neighbor_refs=(),
            origin=FormulaOrigin.DERIVED,
            confidence=0.9,
            known_ambiguities=(),
            falsification_or_failure_formula_id="f-failure-witness",
        ),
        FormulaItem(
            formula_id="f-objective",
            formula_type=FORMULA_TYPE_OBJECTIVE,
            latex=r"\theta^*=\arg\min_\theta L(\theta)",
            normalized_math_ast=None,
            symbols_used=("theta",),
            source_spec_fields=("S1.success_metrics",),
            assumption_formula_ids=("f-assumption",),
            neighbor_refs=(),
            origin=FormulaOrigin.DERIVED,
            confidence=0.9,
            known_ambiguities=(),
            falsification_or_failure_formula_id="",
        ),
        FormulaItem(
            formula_id="f-failure-witness",
            formula_type=FORMULA_TYPE_FAILURE_WITNESS,
            latex=r"\exists x\in D,\ A(x)\land\neg C(x)",
            normalized_math_ast=None,
            symbols_used=("A", "C"),
            source_spec_fields=("S2.failure_conditions", "S4.stop_conditions"),
            assumption_formula_ids=("f-assumption",),
            neighbor_refs=(),
            origin=FormulaOrigin.DERIVED,
            confidence=1.0,
            known_ambiguities=(),
            falsification_or_failure_formula_id="",
        ),
        FormulaItem(
            formula_id="f-application-map",
            formula_type=FORMULA_TYPE_APPLICATION_MAP,
            latex=r"\Phi:\mathcal{M}\to\mathcal{A}",
            normalized_math_ast=None,
            symbols_used=("M", "Aspace"),
            source_spec_fields=("S1.target_applications", "S4.engineering_relevance"),
            assumption_formula_ids=(),
            neighbor_refs=(),
            origin=FormulaOrigin.DERIVED,
            confidence=0.8,
            known_ambiguities=(),
            falsification_or_failure_formula_id="",
        ),
        FormulaItem(
            formula_id="f-verification",
            formula_type=FORMULA_TYPE_VERIFICATION_OBLIGATION,
            latex=r"O=\{O_1,\ldots,O_n\}",
            normalized_math_ast=None,
            symbols_used=("O",),
            source_spec_fields=("S4.evidence_requirements", "S4.stop_conditions"),
            assumption_formula_ids=(),
            neighbor_refs=(),
            origin=FormulaOrigin.DERIVED,
            confidence=1.0,
            known_ambiguities=(),
            falsification_or_failure_formula_id="",
        ),
    )


def validate_formula_items(
    *,
    formula_items: tuple[FormulaItem, ...],
    notation_table: tuple[str, ...],
    formula_dependency_graph: dict[str, tuple[str, ...]],
) -> tuple[str, ...]:
    """Deterministic RQ2M formula validation issues (empty means clean)."""
    issues: list[str] = []
    defined_symbols = {
        entry.split(":", 1)[0].strip()
        for entry in notation_table
        if ":" in entry and entry.split(":", 1)[0].strip()
    }
    items_by_id = {item.formula_id: item for item in formula_items}
    types = {item.formula_type for item in formula_items}
    for required in REQUIRED_FORMULA_TYPES:
        if required not in types:
            issues.append(f"缺少必需公式类型 {required}")

    for item in formula_items:
        unknown_symbols = sorted(set(item.symbols_used) - defined_symbols)
        if unknown_symbols:
            issues.append(f"公式 {item.formula_id} 使用了未定义符号: {', '.join(unknown_symbols)}")
        if not item.source_spec_fields:
            issues.append(f"核心公式 {item.formula_id} 缺少源语义字段引用")
        if item.formula_type == FORMULA_TYPE_CORE_CLAIM:
            if "\\" not in item.latex or "Rightarrow" not in item.latex:
                issues.append(f"核心公式 {item.formula_id} 不是 LaTeX 公式")
            failure_id = item.falsification_or_failure_formula_id
            if not failure_id or failure_id not in items_by_id:
                issues.append(f"核心主张 {item.formula_id} 缺少失败/证伪公式")

    visiting: set[str] = set()
    visited: set[str] = set()

    def visit(node: str) -> bool:
        if node in visiting:
            return True
        if node in visited:
            return False
        visiting.add(node)
        for child in formula_dependency_graph.get(node, ()):
            if visit(child):
                return True
        visiting.remove(node)
        visited.add(node)
        return False

    if any(visit(node) for node in formula_dependency_graph):
        issues.append("公式依赖图存在环")
    return tuple(issues)
