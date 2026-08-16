"""M13.3.RQ.PRODUCTION_E2E integration tests (19 §5 M13.3).

A real natural-language design runs route-aware RQ0-RQ4: theory/engineering
route 70 auto-continues to S5/ENG0; 69 returns the run to the user; export
carries sources, feasibility matrix, route, formalization, scores and gate;
partial coverage never auto-passes.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy.orm import Session

from synaisthesis.agents.auditor import NoveltyAuditor
from synaisthesis.agents.novelty_reviewer import NoveltyReviewer
from synaisthesis.agents.schemas import MechanismSketch, NaturalLanguageSpec, ResearchScopeSpec
from synaisthesis.application.fidelity_service import FidelityConfig
from synaisthesis.application.qualification_service import (
    qualification_export_payload,
    run_qualification_pipeline,
)
from synaisthesis.domain.enums import (
    NoveltyStatus,
    QualificationGateType,
    QualifiedNextTarget,
    ResearchRoute,
)
from synaisthesis.domain.errors import DomainError
from synaisthesis.domain.novelty import (
    ENGINEERING_NOVELTY_POLICY,
    THEORY_NOVELTY_POLICY,
)
from synaisthesis.domain.qualification import (
    FormalizationCapabilityProfile,
    PriorArtQueryRecord,
)
from synaisthesis.interfaces.mcp.tools import TOOL_QUALIFY_DESIGN, call_tool
from synaisthesis.orchestration.nodes.qualification_nodes import qualification_pipeline_node
from synaisthesis.providers.prior_art.base import PriorArtQueryRequest
from synaisthesis.providers.prior_art.fake import (
    FakePriorArtProvider,
    fake_academic_providers,
    fake_engineering_providers,
)
from synaisthesis.storage.database import init_database

NOW = datetime(2026, 8, 17, 3, 0, 0, tzinfo=UTC)
REPO_ROOT = Path(__file__).resolve().parents[2]
MIGRATIONS_DIR = REPO_ROOT / "src" / "synaisthesis" / "storage" / "migrations"


# ---------------------------------------------------------------------------
# Natural-language designs (S1/S2/S4 frozen content)
# ---------------------------------------------------------------------------


def _theory_design() -> tuple[NaturalLanguageSpec, MechanismSketch, ResearchScopeSpec]:
    spec = NaturalLanguageSpec(
        core_definition="Cyclic trace invariance: the trace of a matrix product is "
        "preserved under cyclic permutation of the factors.",
        positive_examples=["tr(AB) = tr(BA)", "tr(ABC) = tr(CAB)"],
        non_examples=["tr(AB) = tr(A)tr(B)"],
        boundary_conditions=["finite square matrices over a field"],
        object_candidates=["finite square matrices"],
        ambiguous_terms=["trace"],
        explicit_non_goals=["non-square matrices"],
        expected_functions=["preserve trace under cyclic shift"],
        target_applications=["automated linear algebra verification"],
        intended_users=["verification researchers"],
        operational_constraints=["deterministic, no sampling"],
        success_metrics=["100% verified traces"],
    )
    mechanism = MechanismSketch(
        inputs=["square matrices A, B"],
        state_change="apply a cyclic permutation to the product factors",
        outputs=["trace equality claim"],
        invariants=["trace invariant under cyclic shift"],
        failure_conditions=["non-multiplicable shapes"],
        causal_claims=["cyclic shift preserves the trace"],
        merely_descriptive_relations=[],
        uncertainty_register=["field characteristic edge cases"],
    )
    scope = ResearchScopeSpec(
        main_question="Is cyclic trace invariance formally provable?",
        object_domain="finite matrix trace algebra",
        non_goals=["asymptotic complexity"],
        nearest_neighbor_difference="trace invariance stated as a theorem with proof obligations",
        central_claims=["tr(AB) = tr(BA)"],
        evidence_requirements=["one formal proof obligation"],
        failure_learning_plan="record counterexamples in the failure register",
        engineering_relevance="trace-verification tooling reuse",
        stop_conditions=["counterexample found"],
    )
    return spec, mechanism, scope


def _engineering_design() -> tuple[NaturalLanguageSpec, MechanismSketch, ResearchScopeSpec]:
    spec, mechanism, scope = _theory_design()
    # Remove theory core material so TFC fails; engineering material stays.
    scope = scope.model_copy(update={"central_claims": [], "evidence_requirements": []})
    return spec, mechanism, scope


# ---------------------------------------------------------------------------
# Providers, capability, reviewers
# ---------------------------------------------------------------------------


def _queries() -> tuple[PriorArtQueryRequest, ...]:
    return (
        PriorArtQueryRequest(
            query=PriorArtQueryRecord(
                query_id="e2e-q-academic",
                original_text="trace cyclic property matrix proof",
                generated_from=("S1.core_definition", "S4.central_claims"),
                provider="fake-academic",
                time_range="2015-2026",
                filters=(),
                page_count=1,
                result_count=20,
                executed_at=NOW,
            ),
            kind="academic",
        ),
        PriorArtQueryRequest(
            query=PriorArtQueryRecord(
                query_id="e2e-q-engineering",
                original_text="trace invariance verification tooling",
                generated_from=("S1.expected_functions", "S1.target_applications"),
                provider="fake-engineering",
                time_range="2015-2026",
                filters=(),
                page_count=1,
                result_count=20,
                executed_at=NOW,
            ),
            kind="engineering",
        ),
    )


def _capability_profile() -> FormalizationCapabilityProfile:
    return FormalizationCapabilityProfile(
        model_profile_id="e2e-profile",
        capability_tier="ADVANCED",
        formalization_eval_score=92.0,
        math_schema_valid_rate=0.98,
        source_citation_support=True,
        structured_output_support=True,
        context_budget_sufficient=True,
        capability_evaluated_at=NOW - timedelta(days=1),
    )


def _item_scores(route: ResearchRoute, scores: dict[str, int]) -> dict[str, int]:
    policy = THEORY_NOVELTY_POLICY if route is ResearchRoute.THEORY else ENGINEERING_NOVELTY_POLICY
    return {item.item_id: scores.get(item.item_id, 0) for item in policy.items}


def _theory_70() -> dict[str, int]:
    return {
        "T1": 4,
        "T2": 4,
        "T3": 4,
        "T4": 4,
        "A1": 3,
        "A2": 3,
        "A3": 3,
        "A4": 3,
        "A5": 3,
    }


def _theory_69() -> dict[str, int]:
    return {
        "T1": 4,
        "T2": 4,
        "T3": 4,
        "T4": 4,
        "A1": 4,
        "A2": 3,
        "A3": 3,
        "A4": 2,
        "A5": 1,
    }


def _engineering_70() -> dict[str, int]:
    return {
        "E1": 4,
        "E2": 4,
        "E3": 3,
        "E4": 3,
        "E5": 4,
        "EA1": 3,
        "EA2": 3,
        "EA3": 3,
        "EA4": 4,
    }


def _reviewer_factories(scores_by_route: dict[ResearchRoute, dict[str, int]]):
    def primary(route: ResearchRoute) -> NoveltyReviewer:
        return NoveltyReviewer.create(
            session_id=f"e2e-primary-{route.value}",
            route=route,
            model_family="family-a",
            scores=_item_scores(route, scores_by_route[route]),
        )

    def auditor(route: ResearchRoute) -> NoveltyAuditor:
        return NoveltyAuditor.create(
            session_id=f"e2e-auditor-{route.value}",
            route=route,
            model_family="family-b",
            scores=_item_scores(route, scores_by_route[route]),
        )

    return primary, auditor


def _run(**overrides):
    spec, mechanism, scope = overrides.pop("design") if "design" in overrides else _theory_design()
    params = {
        "run_id": "e2e-run-1",
        "project_id": "p-e2e",
        "research_spec_id": "rs-e2e",
        "spec": spec,
        "mechanism": mechanism,
        "scope": scope,
        "capability_profile": _capability_profile(),
        "academic_providers": fake_academic_providers(),
        "engineering_providers": fake_engineering_providers(),
        "queries": _queries(),
        "formalizer_session_id": "e2e-formalizer",
        "assessor_session_id": "e2e-assessor",
        "primary_reviewer_factory": _reviewer_factories(
            {ResearchRoute.THEORY: _theory_70(), ResearchRoute.ENGINEERING: _engineering_70()}
        )[0],
        "auditor_reviewer_factory": _reviewer_factories(
            {ResearchRoute.THEORY: _theory_70(), ResearchRoute.ENGINEERING: _engineering_70()}
        )[1],
        "review_decision": "APPROVE",
        "at": NOW,
    }
    params.update(overrides)
    return run_qualification_pipeline(**params)


# ---------------------------------------------------------------------------
# E2E scenarios
# ---------------------------------------------------------------------------


def test_theory_route_70_auto_enters_s5() -> None:
    run = _run()
    assert run.route is ResearchRoute.THEORY
    assert run.next_target is QualifiedNextTarget.S5
    assert run.user_gate is None
    assert run.formula_bundle is not None
    assert run.user_formalization_approval is not None
    assert run.novelty_review is not None
    assert run.novelty_review.status is NoveltyStatus.NOVELTY_QUALIFIED
    assert run.novelty_review.novelty_total == 70

    export = qualification_export_payload(run)
    assert export["route"] == "THEORY"
    assert export["next_target"] == "S5"
    assert export["gate"] is None
    sources = export["sources"]
    assert len(sources["query_records"]) == 2
    assert len(sources["academic_neighbors"]) >= 5
    assert len(sources["engineering_neighbors"]) >= 3
    assert sources["coverage_status"] == "COMPLETE"
    matrix = export["feasibility_matrix"]
    assert matrix["route_classification"] in {"HYBRID_FIT", "PURE_THEORY_FIT"}
    assert len(matrix["theory"]) == 5 and len(matrix["engineering"]) == 5
    formalization = export["formalization"]
    assert formalization is not None and len(formalization["artifact_hash"]) == 64
    scores = export["scores"]
    assert scores is not None and scores["novelty_total"] == 70


def test_theory_route_69_returns_to_user() -> None:
    primary, auditor = _reviewer_factories(
        {ResearchRoute.THEORY: _theory_69(), ResearchRoute.ENGINEERING: _engineering_70()}
    )
    run = _run(primary_reviewer_factory=primary, auditor_reviewer_factory=auditor)
    assert run.next_target is None
    assert run.user_gate is not None
    assert run.user_gate.gate_type is QualificationGateType.LOW_NOVELTY_RESEARCH_DECISION
    assert run.novelty_review is not None
    assert run.novelty_review.status is NoveltyStatus.NOVELTY_RESEARCH_REQUIRED
    assert run.novelty_review.novelty_total == 69
    export = qualification_export_payload(run)
    assert export["gate"]["gate_type"] == "LOW_NOVELTY_RESEARCH_DECISION"
    assert export["scores"]["novelty_total"] == 69


def test_engineering_route_70_auto_enters_eng0() -> None:
    spec, mechanism, scope = _engineering_design()
    run = _run(
        design=(spec, mechanism, scope),
        route_decision="TRY_ENGINEERING_PROJECT",
    )
    assert run.route is ResearchRoute.ENGINEERING
    assert run.route_selection is not None
    assert run.concept_bundle is not None
    assert run.user_engineering_concept_approval is not None
    assert run.novelty_review is not None
    assert run.novelty_review.status is NoveltyStatus.ENGINEERING_NOVELTY_QUALIFIED
    assert run.novelty_review.novelty_total == 70
    assert run.next_target is QualifiedNextTarget.ENG0
    assert run.user_gate is None

    export = qualification_export_payload(run)
    assert export["route"] == "ENGINEERING"
    assert export["next_target"] == "ENG0"
    assert export["engineering_concept"] is not None
    assert export["feasibility_matrix"]["route_classification"] == "ENGINEERING_PROJECT_CANDIDATE"
    assert export["scores"]["novelty_total"] == 70


def test_engineering_candidate_requires_user_route_decision() -> None:
    spec, mechanism, scope = _engineering_design()
    run = _run(design=(spec, mechanism, scope), route_decision=None)
    assert run.next_target is None
    assert run.user_gate is not None
    assert run.user_gate.gate_type is QualificationGateType.ENGINEERING_ROUTE_DECISION
    assert run.route is None


def test_partial_coverage_never_auto_passes() -> None:
    spec, mechanism, scope = _engineering_design()
    with pytest.raises(DomainError) as exc_info:
        _run(
            design=(spec, mechanism, scope),
            academic_providers=(FakePriorArtProvider("openalex", "academic", ()),),
            route_decision="TRY_ENGINEERING_PROJECT",
        )
    assert exc_info.value.error_code == "RQ1_COVERAGE_INCOMPLETE"


def test_pipeline_node_wraps_service() -> None:
    run = qualification_pipeline_node(
        run_id="e2e-node-1",
        project_id="p-e2e",
        research_spec_id="rs-e2e",
        spec=_theory_design()[0],
        mechanism=_theory_design()[1],
        scope=_theory_design()[2],
        capability_profile=_capability_profile(),
        academic_providers=fake_academic_providers(),
        engineering_providers=fake_engineering_providers(),
        queries=_queries(),
        formalizer_session_id="e2e-formalizer",
        assessor_session_id="e2e-assessor",
        primary_reviewer_factory=_reviewer_factories(
            {ResearchRoute.THEORY: _theory_70(), ResearchRoute.ENGINEERING: _engineering_70()}
        )[0],
        auditor_reviewer_factory=_reviewer_factories(
            {ResearchRoute.THEORY: _theory_70(), ResearchRoute.ENGINEERING: _engineering_70()}
        )[1],
        at=NOW,
    )
    assert run.next_target is QualifiedNextTarget.S5


def _fresh_database(tmp_path: Path):
    db_url = f"sqlite:///{tmp_path / 'mcp.db'}"
    cfg = Config()
    cfg.set_main_option("script_location", str(MIGRATIONS_DIR))
    cfg.set_main_option("sqlalchemy.url", db_url)
    command.upgrade(cfg, "head")
    _, session_factory = init_database(db_url)
    return session_factory


def test_mcp_adapter_returns_qualification_export(tmp_path: Path) -> None:
    session_factory = _fresh_database(tmp_path)
    spec, mechanism, scope = _theory_design()
    with session_factory() as session:
        assert isinstance(session, Session)
        export = call_tool(
            session,
            tool_name=TOOL_QUALIFY_DESIGN,
            arguments={
                "project_id": "p-mcp",
                "research_spec_id": "rs-mcp",
                "spec": spec.model_dump(mode="json"),
                "mechanism": mechanism.model_dump(mode="json"),
                "scope": scope.model_dump(mode="json"),
                "primary_scores": _theory_70(),
                "auditor_scores": _theory_70(),
            },
            fidelity=FidelityConfig(signing_key=b"test-key-0123456789abcdef", now_fn=lambda: NOW),
            artifact_root=tmp_path / "artifacts",
        )
    assert export["next_target"] == "S5"
    assert export["scores"]["novelty_total"] == 70


def test_cli_adapter_writes_export(tmp_path: Path) -> None:
    from typer.testing import CliRunner

    from synaisthesis.interfaces.cli.main import app

    spec, mechanism, scope = _theory_design()
    spec_file = tmp_path / "design.json"
    spec_file.write_text(
        json.dumps(
            {
                "research_spec_id": "rs-cli",
                "spec": spec.model_dump(mode="json"),
                "mechanism": mechanism.model_dump(mode="json"),
                "scope": scope.model_dump(mode="json"),
            }
        ),
        encoding="utf-8",
    )
    out_file = tmp_path / "export.json"
    result = CliRunner().invoke(
        app,
        [
            "qualify",
            "qualify",
            "--project-id",
            "p-cli",
            "--spec-json",
            str(spec_file),
            "--out",
            str(out_file),
            "--score",
            "4",
        ],
    )
    assert result.exit_code == 0, result.output
    export = json.loads(out_file.read_text(encoding="utf-8"))
    assert export["route"] == "THEORY"
    assert export["next_target"] == "S5"
