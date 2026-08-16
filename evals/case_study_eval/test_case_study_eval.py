"""M15.CASE_STUDY.EVAL — case-study evaluation (19 §5 M15).

Recomputes every frozen case-study export bundle deterministically and
compares it field-for-field; runs the real Lean tool on the theory-case
theorem; checks the case-study stories for the required elements and the
absence of fabricated results.
"""

from __future__ import annotations

import json
import re
from datetime import UTC, datetime, timedelta
from pathlib import Path

from synaisthesis.agents.auditor import NoveltyAuditor
from synaisthesis.agents.novelty_reviewer import NoveltyReviewer
from synaisthesis.agents.schemas import MechanismSketch, NaturalLanguageSpec, ResearchScopeSpec
from synaisthesis.application.qualification_service import (
    qualification_export_payload,
    run_qualification_pipeline,
)
from synaisthesis.domain.enums import ResearchRoute
from synaisthesis.domain.novelty import (
    ENGINEERING_NOVELTY_POLICY,
    THEORY_NOVELTY_POLICY,
)
from synaisthesis.domain.qualification import (
    FormalizationCapabilityProfile,
    PriorArtQueryRecord,
)
from synaisthesis.providers.prior_art.base import PriorArtQueryRequest
from synaisthesis.providers.prior_art.fake import (
    fake_academic_providers,
    fake_engineering_providers,
)
from synaisthesis.verifiers.lean.adapter import lean_evidence_ok, run_lean

NOW = datetime(2026, 8, 17, 5, 0, 0, tzinfo=UTC)
ROOT = Path(__file__).resolve().parents[2]
CASE_ROOT = ROOT / "examples" / "real_project_case_study"
EVAL_ROOT = ROOT / "evals" / "case_study_eval"

THEORY_70 = {
    "T1": 4, "T2": 4, "T3": 4, "T4": 4,
    "A1": 3, "A2": 3, "A3": 3, "A4": 3, "A5": 3,
}
ENGINEERING_70 = {
    "E1": 4, "E2": 4, "E3": 3, "E4": 3, "E5": 4,
    "EA1": 3, "EA2": 3, "EA3": 3, "EA4": 4,
}


def _load_design(case_dir: Path):
    payload = json.loads((case_dir / "design.json").read_text(encoding="utf-8"))
    return (
        payload["project_id"],
        payload["research_spec_id"],
        NaturalLanguageSpec(**payload["spec"]),
        MechanismSketch(**payload["mechanism"]),
        ResearchScopeSpec(**payload["scope"]),
    )


def _queries() -> tuple[PriorArtQueryRequest, ...]:
    return (
        PriorArtQueryRequest(
            query=PriorArtQueryRecord(
                query_id="case-q-academic",
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
                query_id="case-q-engineering",
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
        model_profile_id="case-profile",
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


def _reviewer_factories(route_scores: dict[ResearchRoute, dict[str, int]]):
    def primary(route: ResearchRoute) -> NoveltyReviewer:
        return NoveltyReviewer.create(
            session_id=f"case-primary-{route.value}",
            route=route,
            model_family="family-a",
            scores=_item_scores(route, route_scores[route]),
        )

    def auditor(route: ResearchRoute) -> NoveltyAuditor:
        return NoveltyAuditor.create(
            session_id=f"case-auditor-{route.value}",
            route=route,
            model_family="family-b",
            scores=_item_scores(route, route_scores[route]),
        )

    return primary, auditor


def _recompute(
    case_dir: Path,
    *,
    run_id: str,
    route_decision: str | None = None,
    review_decision: str = "APPROVE",
) -> dict:
    project_id, research_spec_id, spec, mechanism, scope = _load_design(case_dir)
    primary, auditor = _reviewer_factories(
        {
            ResearchRoute.THEORY: THEORY_70,
            ResearchRoute.ENGINEERING: ENGINEERING_70,
        }
    )
    run = run_qualification_pipeline(
        run_id=run_id,
        project_id=project_id,
        research_spec_id=research_spec_id,
        spec=spec,
        mechanism=mechanism,
        scope=scope,
        capability_profile=_capability_profile(),
        academic_providers=fake_academic_providers(),
        engineering_providers=fake_engineering_providers(),
        queries=_queries(),
        formalizer_session_id="case-formalizer",
        assessor_session_id="case-assessor",
        primary_reviewer_factory=primary,
        auditor_reviewer_factory=auditor,
        route_decision=route_decision,
        review_decision=review_decision,
        at=NOW,
    )
    return qualification_export_payload(run)


def _assert_export_matches(frozen_path: Path, recomputed: dict) -> None:
    frozen = json.loads(frozen_path.read_text(encoding="utf-8"))
    assert frozen == recomputed, (
        f"{frozen_path.name} 复算结果与冻结导出不一致；Bundle 不可复算"
    )


# ---------------------------------------------------------------------------
# Theory case: failure, fix, gate, real tool, RQ0-RQ4
# ---------------------------------------------------------------------------


def test_theory_case_phase1_failure_export_recomputes() -> None:
    export = _recompute(
        CASE_ROOT / "theory_case",
        run_id="case-theory-phase1",
        review_decision="REQUEST_REVISION",
    )
    _assert_export_matches(CASE_ROOT / "theory_case" / "phase1_revision_export.json", export)
    assert export["next_target"] is None
    assert export["gate"]["gate_type"] == "EARLY_FORMALIZATION_REVIEW"
    assert export["gate"]["status"] == "RESOLVED"


def test_theory_case_phase2_approved_export_recomputes() -> None:
    export = _recompute(
        CASE_ROOT / "theory_case",
        run_id="case-theory-phase2",
        review_decision="APPROVE",
    )
    _assert_export_matches(CASE_ROOT / "theory_case" / "phase2_approved_export.json", export)
    assert export["route"] == "THEORY"
    assert export["next_target"] == "S5"
    assert export["scores"]["novelty_total"] == 70


def test_theory_case_real_lean_tool() -> None:
    source = (
        CASE_ROOT / "theory_case" / "lean" / "trace_cyclic.lean"
    ).read_text(encoding="utf-8")
    result = run_lean(source)
    assert result.exit_code == 0, result.stderr
    assert lean_evidence_ok(result)
    assert result.statement_hash and len(result.statement_hash) == 64
    assert result.tool_version


def test_theory_case_story_has_required_elements() -> None:
    story = (CASE_ROOT / "theory_case" / "story.md").read_text(encoding="utf-8")
    for marker in (
        "RQ0",
        "RQ1",
        "RQ2F",
        "RQ2M",
        "RQ3M",
        "RQ4M",
        "REQUEST_REVISION",
        "APPROVE",
        "EARLY_FORMALIZATION_REVIEW",
        "真实工具",
        "失败",
        "修复",
        "可复算",
    ):
        assert marker in story, f"理论案例 story.md 缺少 {marker!r}"


# ---------------------------------------------------------------------------
# Engineering case: user route split, ENG0-ENG10 BLUEPRINT_ONLY, no fiction
# ---------------------------------------------------------------------------


def test_engineering_case_export_recomputes() -> None:
    export = _recompute(
        CASE_ROOT / "engineering_case",
        run_id="case-engineering",
        route_decision="TRY_ENGINEERING_PROJECT",
        review_decision="APPROVE",
    )
    _assert_export_matches(CASE_ROOT / "engineering_case" / "export.json", export)
    assert export["route"] == "ENGINEERING"
    assert export["next_target"] == "ENG0"
    assert export["scores"]["novelty_total"] == 70
    assert (
        export["feasibility_matrix"]["route_classification"]
        == "ENGINEERING_PROJECT_CANDIDATE"
    )


def test_engineering_case_story_has_user_split_and_blueprint_only() -> None:
    story = (CASE_ROOT / "engineering_case" / "story.md").read_text(encoding="utf-8")
    for marker in (
        "ENGINEERING_ROUTE_DECISION",
        "TRY_ENGINEERING_PROJECT",
        "ENG0",
        "ENG10",
        "BLUEPRINT_ONLY",
        "无虚构结果",
        "可复算",
        "ENGINEERING_PROJECT_CANDIDATE",
    ):
        assert marker in story, f"工程案例 story.md 缺少 {marker!r}"


def test_engineering_case_story_has_no_fabricated_results() -> None:
    story = (CASE_ROOT / "engineering_case" / "story.md").read_text(encoding="utf-8")
    # no percentage/throughput/latency claims anywhere in the story
    assert "%" not in story
    assert re.search(r"\d+\s*(ms|GB|倍|TPS)", story) is None
    assert "benchmark 达到" not in story


# ---------------------------------------------------------------------------
# Dataset integrity
# ---------------------------------------------------------------------------


def test_dataset_json_matches_case_files() -> None:
    dataset = json.loads((EVAL_ROOT / "dataset.json").read_text(encoding="utf-8"))
    assert dataset["schema_version"] == "1.0.0"
    expected_files = {
        "examples/real_project_case_study/theory_case/phase1_revision_export.json",
        "examples/real_project_case_study/theory_case/phase2_approved_export.json",
        "examples/real_project_case_study/theory_case/lean/trace_cyclic.lean",
        "examples/real_project_case_study/engineering_case/export.json",
    }
    for relative in expected_files:
        assert (ROOT / relative).exists(), relative
    for case_dir in ("theory_case", "engineering_case"):
        design = json.loads(
            (CASE_ROOT / case_dir / "design.json").read_text(encoding="utf-8")
        )
        assert design["spec"]["core_definition"]
        assert design["mechanism"]["inputs"]
        assert design["scope"]["main_question"]
