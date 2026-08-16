"""Pydantic schemas for incubator stage outputs (blueprint 03, S0/S1).

SeedRecord and NaturalLanguageSpec are the Schema layer: all required fields
are enforced by model validation with extra="forbid". Business rules beyond
field presence live in domain/stage.py validators.
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from synaisthesis.domain.claim import ClaimClass, ClaimVerifier
from synaisthesis.domain.enums import EarlyFormalizationStatus, FormulaOrigin


class SeedRecord(BaseModel):
    """S0 output: the user's raw inspiration, faithfully preserved (03, S0)."""

    model_config = ConfigDict(extra="forbid")

    raw_input: str = Field(min_length=1)
    source_type: str = Field(min_length=1)
    user_intent_guess: str | None = None
    observation: str
    interpretation: str
    observation_interpretation_separated: bool = False
    key_ambiguity: str | None = None
    user_corrections: list[str] = Field(default_factory=list)
    attachments: list[str] = Field(default_factory=list)


class NaturalLanguageSpec(BaseModel):
    """S1 output: the structured natural-language definition (03, S1).

    user_confirmed may only become True through the user-confirmation path in
    the incubation service; the schema default keeps it False.
    """

    model_config = ConfigDict(extra="forbid")

    core_definition: str = Field(min_length=1)
    positive_examples: list[str]
    non_examples: list[str]
    boundary_conditions: list[str]
    object_candidates: list[str]
    ambiguous_terms: list[str]
    explicit_non_goals: list[str]
    expected_functions: list[str]
    target_applications: list[str]
    intended_users: list[str]
    operational_constraints: list[str]
    success_metrics: list[str]
    assistant_proposed: bool = False
    user_confirmed: bool = False


class MechanismSketch(BaseModel):
    """S2 output: mechanism sketch without correlation-as-causation (03, S2)."""

    model_config = ConfigDict(extra="forbid")

    inputs: list[str]
    state_change: str = Field(min_length=1)
    outputs: list[str]
    invariants: list[str]
    failure_conditions: list[str]
    causal_claims: list[str]
    merely_descriptive_relations: list[str]
    uncertainty_register: list[str]


class PriorWorkMap(BaseModel):
    """S3 output: traceable prior-work map with academic and engineering seeds.

    search_queries uses the stable keys "academic" and "engineering" (M2.2
    WorkUnitContract GAP-1); no additional status field is invented (GAP-5).
    """

    model_config = ConfigDict(extra="forbid")

    search_queries: dict[str, list[str]]
    sources: list[str]
    nearest_theories: list[str]
    same_object_different_method: list[str]
    same_method_different_object: list[str]
    conflicts: list[str]
    terminology_candidates: list[str]
    retrieval_scope: str = Field(min_length=1)
    unsearched_areas: list[str]
    literature_hits: list[str]
    mature_engineering_projects: list[str]
    engineering_maturity_evidence: list[str]
    function_application_neighbors: list[str]
    metadata_verified: bool


class ResearchScopeSpec(BaseModel):
    """S4 output: re-normalized research scope (03, S4).

    user_confirmed_scope may only become True through the real-user-event
    confirmation path in the incubation service.
    """

    model_config = ConfigDict(extra="forbid")

    main_question: str = Field(min_length=1)
    object_domain: str = Field(min_length=1)
    non_goals: list[str]
    nearest_neighbor_difference: str = Field(min_length=1)
    central_claims: list[str]
    evidence_requirements: list[str]
    failure_learning_plan: str = Field(min_length=1)
    engineering_relevance: str = Field(min_length=1)
    stop_conditions: list[str]
    user_confirmed_scope: bool = False


class FormulaItemModel(BaseModel):
    """RQ2M formula item schema (03A, section 5.3)."""

    model_config = ConfigDict(extra="forbid")

    formula_id: str = Field(min_length=1)
    formula_type: str = Field(min_length=1)
    latex: str = Field(min_length=1)
    normalized_math_ast: str | None = None
    symbols_used: list[str]
    source_spec_fields: list[str]
    assumption_formula_ids: list[str]
    neighbor_refs: list[str]
    origin: FormulaOrigin = FormulaOrigin.MODEL_PROPOSAL
    confidence: float | None = None
    known_ambiguities: list[str]
    falsification_or_failure_formula_id: str


class EarlyFormalizationBundleModel(BaseModel):
    """RQ2M bundle schema (03A, section 5.2)."""

    model_config = ConfigDict(extra="forbid")

    formalization_id: str = Field(min_length=1)
    version: int = Field(ge=1)
    research_spec_id: str = Field(min_length=1)
    input_spec_hash: str = Field(min_length=64)
    feasibility_assessment_id: str = Field(min_length=1)
    neighbor_evidence_set_id: str = Field(min_length=1)
    formalizer_profile_or_import_id: str = Field(min_length=1)
    notation_table: list[str]
    formula_items: list[FormulaItemModel]
    formula_dependency_graph: dict[str, list[str]]
    semantic_alignment_matrix: list[str]
    neighbor_difference_matrix: list[str]
    uncertainty_register: list[str]
    plain_language_explanation: list[str]
    validator_results: list[str]
    artifact_hash: str = Field(min_length=64)
    status: EarlyFormalizationStatus


class MinimalCaseBundle(BaseModel):
    """S5 output schema (03, S5)."""

    model_config = ConfigDict(extra="forbid")

    input: str = Field(min_length=1)
    control_or_baseline: str = Field(min_length=1)
    expected_output: str = Field(min_length=1)
    failure_condition: str = Field(min_length=1)
    reproduction_steps: list[str]
    actually_executed: bool = False
    execution_receipt_id: str | None = None
    toy_or_real: str = Field(min_length=1)
    limitations: list[str]


class MinimalCaseBundleModel(MinimalCaseBundle):
    """Alias retaining the schema name used by prompt/API contracts."""


class TheoryKernel(BaseModel):
    """S6 output: core unified theory kernel (03, S6).

    candidate_mechanism is the theory's explanatory proposal; predictions and
    explanations are separate fields and explanation fluency is never evidence.
    """

    model_config = ConfigDict(extra="forbid")

    candidate_mechanism: str = Field(min_length=1)
    competing_explanations: list[str]
    examples: list[str]
    counterexamples: list[str]
    invariants: list[str]
    boundaries: list[str]
    predictions: list[str]
    discarded_alternatives: list[str]
    discard_reasons: list[str]
    unresolved_conflicts: list[str]


class FormalizationPlanClaim(BaseModel):
    """One S7 claim with object domain, quantifiers and falsification witness."""

    model_config = ConfigDict(extra="forbid")

    claim_id: str = Field(min_length=1)
    statement: str = Field(min_length=1)
    object_domain: str = Field(min_length=1)
    quantifiers: list[str]
    falsification_witness: str = Field(min_length=1)


class FormalizationPlan(BaseModel):
    """S7 output: independent formalization plan (03, S7).

    Consumes the user-approved RQ2M early-formalization bundle but stands on
    its own: every claim carries object domain, quantifiers and a
    falsification witness; dependency graph is acyclic or explicitly
    recursive; intended tools are chosen or NOT_APPLICABLE.
    """

    model_config = ConfigDict(extra="forbid")

    object_domain: str = Field(min_length=1)
    symbols: list[str]
    definitions: list[str]
    assumptions: list[str]
    quantifiers: list[str]
    claims: list[FormalizationPlanClaim]
    dependency_graph: dict[str, list[str]]
    proof_paths: list[str]
    counterexample_paths: list[str]
    intended_tools: list[str]
    formalization_uncertainties: list[str]
    proof_candidate_artifacts: list[str]


class PreFreezeAttackReport(BaseModel):
    """S8 output: bounded pre-freeze readiness attack (03, S8).

    Only one or two attack rounds are allowed; the full ten-round Council is
    never started here.  freeze_readiness requires every critical issue to be
    resolved or explicitly blocked.
    """

    model_config = ConfigDict(extra="forbid")

    attack_rounds: int = Field(ge=1, le=2)
    internal_attacks: list[str]
    external_attacks: list[str]
    obvious_counterexamples: list[str]
    boundary_failures: list[str]
    definition_holes: list[str]
    quantifier_risks: list[str]
    tool_feasibility: list[str]
    claim_atomicity: list[str]
    recommended_split: list[str]
    freeze_readiness: bool = False
    critical_issues_resolved: bool = False
    critical_issues_blocked: bool = False
    rollback_targets: list[str] = Field(default_factory=list)


class OpenQuestionRecord(BaseModel):
    """One S9 open question entry (03, S9)."""

    model_config = ConfigDict(extra="forbid")

    question_id: str = Field(min_length=1)
    statement: str = Field(min_length=1)
    origin: str = Field(min_length=1)
    why_open: str = Field(min_length=1)
    known_failed_attempts: list[str]
    falsification_path: str = Field(min_length=1)
    next_action: str = Field(min_length=1)
    dependency_claims: list[str]
    status: str = Field(min_length=1)


class OpenQuestionRegistry(BaseModel):
    """S9 output: open question registry (03, S9)."""

    model_config = ConfigDict(extra="forbid")

    registry_id: str = Field(min_length=1)
    entries: list[OpenQuestionRecord]


class HandoffTask(BaseModel):
    """One S10 downstream task with input/output/threshold (03, S10)."""

    model_config = ConfigDict(extra="forbid")

    task_id: str = Field(min_length=1)
    title: str = Field(min_length=1)
    track: str = Field(min_length=1)
    input: str = Field(min_length=1)
    output: str = Field(min_length=1)
    threshold: str = Field(min_length=1)


class ResearchHandoffBundle(BaseModel):
    """S10 output: research handoff bundle (03, S10)."""

    model_config = ConfigDict(extra="forbid")

    frozen_terms: list[str]
    evidence_summary: list[str]
    current_versions: dict[str, str]
    open_questions: list[str]
    downstream_tasks: list[HandoffTask]
    verification_thresholds: list[str]
    proof_track: list[str]
    experiment_track: list[str]
    engineering_track: list[str]
    writing_track: list[str]
    artifact_manifest: list[str]
    unresolved_gates: list[str]


class ClaimCandidate(BaseModel):
    """One claim-compiler input (02 §8, 04 §1, 07 §4; M4.1).

    An atomic candidate carries a single-proposition statement plus the four
    required claim fields (object domain, quantifiers, falsification witness,
    verifier). A MIXED candidate declares ``claim_class=MIXED`` and supplies its
    atomic split as ``atomic_parts``; the compiler never invents per-clause
    falsification witnesses.
    """

    model_config = ConfigDict(extra="forbid")

    statement: str = Field(min_length=1)
    object_domain: str = Field(min_length=1)
    quantifiers: list[str] = Field(default_factory=list)
    claim_class: ClaimClass
    verifier: ClaimVerifier = ClaimVerifier.NONE
    falsification_witness: str | None = None
    formal_statement_candidate: str | None = None
    assumptions: list[str] = Field(default_factory=list)
    conclusion: str = ""
    claim_key: str | None = None
    claim_id: str | None = None
    dependencies: list[str] = Field(default_factory=list)
    engineering_relevance: str = ""
    semantic_critical_fields: list[str] = Field(default_factory=list)
    unverified: bool = False
    atomic: bool = False
    atomic_parts: list[ClaimCandidate] | None = None
