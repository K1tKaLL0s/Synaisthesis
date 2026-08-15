"""Pydantic schemas for incubator stage outputs (blueprint 03, S0/S1).

SeedRecord and NaturalLanguageSpec are the Schema layer: all required fields
are enforced by model validation with extra="forbid". Business rules beyond
field presence live in domain/stage.py validators.
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


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
