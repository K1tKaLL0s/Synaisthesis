"""Pydantic schemas for incubator stage outputs (blueprint 03, S0/S1).

SeedRecord and NaturalLanguageSpec are the Schema layer: all required fields
are enforced by model validation with extra="forbid". Business rules beyond
field presence live in domain/stage.py validators.
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

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
