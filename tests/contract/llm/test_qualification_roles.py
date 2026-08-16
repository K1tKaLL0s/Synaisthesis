"""M6.3 contract tests for the LLM role router and RQ roles."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from synaisthesis.agents.early_formalizer import build_formula_items_from_llm
from synaisthesis.agents.novelty_reviewer import review_scorecard_from_llm
from synaisthesis.agents.schemas import (
    MechanismSketch,
    NaturalLanguageSpec,
    ResearchScopeSpec,
)
from synaisthesis.domain.enums import CapabilityStatus, PriorArtCoverageStatus, ResearchRoute
from synaisthesis.domain.errors import DomainError
from synaisthesis.domain.novelty import NoveltyScorecard
from synaisthesis.domain.qualification import NeighborEvidenceSet
from synaisthesis.providers.llm.base import (
    LLMProvider,
    LLMRequest,
    LLMResponse,
    StructuredOutputError,
)
from synaisthesis.providers.llm.fake_provider import FakeLLMProvider
from synaisthesis.providers.llm.router import (
    CAPABILITY_SCHEMA,
    ROLE_CAPABILITY_EVAL,
    ROLE_EARLY_FORMALIZER,
    ROLE_NOVELTY_AUDITOR,
    ROLE_NOVELTY_PRIMARY,
    LLMRouter,
    capability_profile_from_llm,
)

NOW = datetime(2026, 8, 17, 2, 0, 0, tzinfo=UTC)


class _FormulaStubProvider(LLMProvider):
    """Stub that returns a proper formulas JSON payload for router tests."""

    @property
    def provider_name(self) -> str:
        return "stub-formula"

    @property
    def model_name(self) -> str:
        return "stub-1"

    def complete(self, request: LLMRequest) -> LLMResponse:
        return LLMResponse(
            text='{"formulas": [{"formula_id": "f1", "formula_type": "identity", '
            '"latex": "tr(AB)=tr(BA)", "symbols_used": ["A","B"], '
            '"source_spec_fields": ["S1.core_definition"], '
            '"falsification_or_failure_formula_id": "f2"}]}',
            structured={
                "formulas": [
                    {
                        "formula_id": "f1",
                        "formula_type": "identity",
                        "latex": "tr(AB)=tr(BA)",
                        "symbols_used": ["A", "B"],
                        "source_spec_fields": ["S1.core_definition"],
                        "falsification_or_failure_formula_id": "f2",
                    }
                ]
            },
            model=self.model_name,
        )


class _ScoreStubProvider(LLMProvider):
    """Stub returning a valid scorecard for the engineering novelty policy."""

    @property
    def provider_name(self) -> str:
        return "stub-score"

    @property
    def model_name(self) -> str:
        return "stub-2"

    def complete(self, request: LLMRequest) -> LLMResponse:
        scores = {
            "E1": 4,
            "E2": 4,
            "E3": 3,
            "E4": 3,
            "E5": 3,
            "EA1": 3,
            "EA2": 3,
            "EA3": 3,
            "EA4": 3,
        }
        return LLMResponse(
            text='{"item_scores": {"E1": 4}}',
            structured={"item_scores": scores},
            model=self.model_name,
        )


def _spec() -> NaturalLanguageSpec:
    return NaturalLanguageSpec(
        core_definition="trace cyclic property",
        positive_examples=["A=B=I"],
        non_examples=["non-square"],
        boundary_conditions=["square matrices"],
        object_candidates=["M_n"],
        ambiguous_terms=[],
        explicit_non_goals=["GUI"],
        expected_functions=["trace"],
        target_applications=["linear algebra"],
        intended_users=["researchers"],
        operational_constraints=["offline"],
        success_metrics=["reproducible"],
    )


def _mechanism() -> MechanismSketch:
    return MechanismSketch(
        inputs=["A", "B"],
        state_change="compute tr(AB)",
        outputs=["float"],
        invariants=["shape invariant"],
        failure_conditions=["non-square"],
        causal_claims=["cyclic permutation"],
        merely_descriptive_relations=[],
        uncertainty_register=[],
    )


def _scope() -> ResearchScopeSpec:
    return ResearchScopeSpec(
        main_question="Is tr(AB)=tr(BA)?",
        object_domain="finite matrices",
        non_goals=["floating point"],
        nearest_neighbor_difference="none",
        central_claims=["tr(AB)=tr(BA)"],
        evidence_requirements=["counterexample search"],
        failure_learning_plan="record failure",
        engineering_relevance="numerical libraries",
        stop_conditions=["shape mismatch"],
    )


def _evidence() -> NeighborEvidenceSet:
    return NeighborEvidenceSet(
        search_id="nes-1",
        research_spec_id="rs-1",
        input_spec_hash="s" * 64,
        query_records=(),
        academic_neighbors=(),
        engineering_neighbors=(),
        standards_and_reference_architectures=(),
        patent_neighbors=(),
        metadata_verification_receipts=(),
        inclusion_exclusion_log="",
        unsearched_areas=(),
        coverage_status=PriorArtCoverageStatus.COMPLETE,
        coverage_blockers=(),
        artifact_hash="0" * 64,
    )


def _router(providers: dict[str, LLMProvider], families: dict[str, str]) -> LLMRouter:
    return LLMRouter(providers=providers, families=families)


def test_router_binds_roles_to_providers():
    provider = FakeLLMProvider()
    router = _router(
        {ROLE_EARLY_FORMALIZER: provider},
        {ROLE_EARLY_FORMALIZER: "fake-family"},
    )
    assert router.provider_for(ROLE_EARLY_FORMALIZER) is provider
    with pytest.raises(DomainError) as exc_info:
        router.provider_for("unknown_role")
    assert exc_info.value.error_code == "PROVIDER_UNAVAILABLE"


def test_router_structured_failure_never_touches_state():
    router = _router(
        {ROLE_CAPABILITY_EVAL: FakeLLMProvider(invalid_json=True)},
        {ROLE_CAPABILITY_EVAL: "fake-family"},
    )
    from synaisthesis.providers.llm.base import LLMRequest

    with pytest.raises(StructuredOutputError):
        router.complete_for(
            ROLE_CAPABILITY_EVAL,
            LLMRequest(prompt="capability", structured_schema=CAPABILITY_SCHEMA),
        )


def test_capability_profile_drives_rq0_gate():

    router = _router(
        {ROLE_CAPABILITY_EVAL: FakeLLMProvider()},
        {ROLE_CAPABILITY_EVAL: "fake-family"},
    )
    from synaisthesis.providers.llm.base import LLMRequest

    response = router.complete_for(
        ROLE_CAPABILITY_EVAL,
        LLMRequest(
            prompt="capability",
            structured_schema={
                "type": "object",
                "required": [
                    "capability_tier",
                    "formalization_eval_score",
                    "math_schema_valid_rate",
                    "source_citation_support",
                    "structured_output_support",
                    "context_budget_sufficient",
                ],
                "properties": {},
            },
        ),
    )
    # fake returns strings for required keys -> numeric conversion fails closed
    with pytest.raises(ValueError):
        capability_profile_from_llm(response, model_profile_id="mp-1", evaluated_at=NOW)


def test_no_evidence_never_marks_advanced():
    from synaisthesis.domain.qualification import (
        FormalizationCapabilityProfile,
        evaluate_formalizer_capability,
    )

    profile = FormalizationCapabilityProfile(
        model_profile_id="mp-1",
        capability_tier="BASIC",  # no evidence of ADVANCED
        formalization_eval_score=50.0,
        math_schema_valid_rate=0.5,
        source_citation_support=False,
        structured_output_support=False,
        context_budget_sufficient=False,
        capability_evaluated_at=NOW,
    )
    status, blockers = evaluate_formalizer_capability(profile, evaluated_at=NOW)
    assert status is CapabilityStatus.CAPABILITY_UNAVAILABLE
    assert blockers
    assert "ADVANCED" in blockers[0]


def test_capability_ready_with_full_evidence():
    from synaisthesis.domain.qualification import (
        FormalizationCapabilityProfile,
        evaluate_formalizer_capability,
    )

    profile = FormalizationCapabilityProfile(
        model_profile_id="mp-1",
        capability_tier="ADVANCED",
        formalization_eval_score=95.0,
        math_schema_valid_rate=0.99,
        source_citation_support=True,
        structured_output_support=True,
        context_budget_sufficient=True,
        capability_evaluated_at=NOW,
    )
    status, blockers = evaluate_formalizer_capability(profile, evaluated_at=NOW)
    assert status is CapabilityStatus.CAPABILITY_READY
    assert blockers == ()


def test_llm_formula_items_built_through_router():
    router = _router(
        {ROLE_EARLY_FORMALIZER: _FormulaStubProvider()},
        {ROLE_EARLY_FORMALIZER: "stub-family"},
    )
    items = build_formula_items_from_llm(
        router=router,
        session_id="s-1",
        spec=_spec(),
        mechanism=_mechanism(),
        scope=_scope(),
        evidence=_evidence(),
    )
    assert len(items) == 1
    assert items[0].formula_id == "f1"
    assert items[0].latex == "tr(AB)=tr(BA)"


def test_llm_scorecard_built_through_router_and_independence():
    router = _router(
        {
            ROLE_NOVELTY_PRIMARY: _ScoreStubProvider(),
            ROLE_NOVELTY_AUDITOR: FakeLLMProvider(),
        },
        {
            ROLE_NOVELTY_PRIMARY: "family-stub",
            ROLE_NOVELTY_AUDITOR: "family-fake",
        },
    )
    independent, note = router.reviewer_independence(ROLE_NOVELTY_PRIMARY, ROLE_NOVELTY_AUDITOR)
    assert independent is True
    assert note == "independent"

    scorecard, evidence = review_scorecard_from_llm(
        router=router,
        session_id="rev-1",
        route=ResearchRoute.ENGINEERING,
        role=ROLE_NOVELTY_PRIMARY,
        subject_artifact_id="c-1",
    )
    assert isinstance(scorecard, NoveltyScorecard)
    assert scorecard.item_scores["E1"] == 4
    assert len(evidence) == 9
    assert evidence[0].evidence_refs == ("RQ1:c-1:E1",)


def test_same_family_reviewers_are_degraded():
    router = _router(
        {
            ROLE_NOVELTY_PRIMARY: _ScoreStubProvider(),
            ROLE_NOVELTY_AUDITOR: FakeLLMProvider(),
        },
        {
            ROLE_NOVELTY_PRIMARY: "same-family",
            ROLE_NOVELTY_AUDITOR: "same-family",
        },
    )
    independent, note = router.reviewer_independence(ROLE_NOVELTY_PRIMARY, ROLE_NOVELTY_AUDITOR)
    assert independent is False
    assert "SAME_MODEL_FAMILY" in note


def test_fake_path_still_works_for_ci():
    from synaisthesis.agents.early_formalizer import build_formula_items
    from synaisthesis.agents.novelty_reviewer import NoveltyReviewer

    items = build_formula_items(
        spec=_spec(), mechanism=_mechanism(), scope=_scope(), evidence=_evidence()
    )
    assert len(items) == 10
    reviewer = NoveltyReviewer.create(
        session_id="rev-1", route=ResearchRoute.ENGINEERING, model_family="fake"
    )
    scorecard, evidence = reviewer.score(subject_artifact_id="c-1", subject_artifact_hash="h")
    assert scorecard.item_scores["E1"] == 0
