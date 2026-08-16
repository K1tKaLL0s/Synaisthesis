"""Qualification CLI intent adapter (19 §5 M13.3: route-aware RQ0-RQ4).

`qualify` runs the deterministic pipeline over a frozen natural-language
design (spec/mechanism/scope JSON) with the fixture provider corpus; real
provider smoke stays manual per the M13.3 contract.  The full export is
written to `--out` as JSON when requested.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Annotated

import typer

from synaisthesis.agents.auditor import NoveltyAuditor
from synaisthesis.agents.novelty_reviewer import NoveltyReviewer
from synaisthesis.agents.schemas import MechanismSketch, NaturalLanguageSpec, ResearchScopeSpec
from synaisthesis.application.qualification_service import (
    qualification_export_payload,
    run_qualification_pipeline,
)
from synaisthesis.domain.enums import ResearchRoute
from synaisthesis.domain.event import canonical_json
from synaisthesis.domain.qualification import (
    FormalizationCapabilityProfile,
    PriorArtQueryRecord,
)
from synaisthesis.providers.prior_art.base import PriorArtQueryRequest
from synaisthesis.providers.prior_art.fake import (
    fake_academic_providers,
    fake_engineering_providers,
)

app = typer.Typer(no_args_is_help=True, help="Early research qualification (RQ0-RQ4).")


def _queries() -> tuple[PriorArtQueryRequest, ...]:
    now = datetime.now(UTC)
    return (
        PriorArtQueryRequest(
            query=PriorArtQueryRecord(
                query_id="cli-q-academic",
                original_text="academic neighbors from S1/S4 fields",
                generated_from=("S1.core_definition", "S4.central_claims"),
                provider="fake-academic",
                time_range="2015-2026",
                filters=(),
                page_count=1,
                result_count=20,
                executed_at=now,
            ),
            kind="academic",
        ),
        PriorArtQueryRequest(
            query=PriorArtQueryRecord(
                query_id="cli-q-engineering",
                original_text="mature engineering projects from S1/S4 fields",
                generated_from=("S1.expected_functions", "S1.target_applications"),
                provider="fake-engineering",
                time_range="2015-2026",
                filters=(),
                page_count=1,
                result_count=20,
                executed_at=now,
            ),
            kind="engineering",
        ),
    )


def _capability_profile() -> FormalizationCapabilityProfile:
    return FormalizationCapabilityProfile(
        model_profile_id="cli-profile",
        capability_tier="ADVANCED",
        formalization_eval_score=92.0,
        math_schema_valid_rate=0.98,
        source_citation_support=True,
        structured_output_support=True,
        context_budget_sufficient=True,
        capability_evaluated_at=datetime.now(UTC) - timedelta(days=1),
    )


def _reviewer_factories(score: int):
    def uniform(route: ResearchRoute) -> dict[str, int]:
        from synaisthesis.domain.novelty import novelty_policy_for

        return {item.item_id: score for item in novelty_policy_for(route).items}

    def primary(route: ResearchRoute) -> NoveltyReviewer:
        return NoveltyReviewer.create(
            session_id=f"cli-primary-{route.value}",
            route=route,
            model_family="family-a",
            scores=uniform(route),
        )

    def auditor(route: ResearchRoute) -> NoveltyAuditor:
        return NoveltyAuditor.create(
            session_id=f"cli-auditor-{route.value}",
            route=route,
            model_family="family-b",
            scores=uniform(route),
        )

    return primary, auditor


@app.command("qualify")
def qualify(
    project_id: Annotated[str, typer.Option("--project-id", "-p", help="Project id.")],
    spec_json: Annotated[
        Path,
        typer.Option(
            "--spec-json",
            exists=True,
            readable=True,
            help="JSON file with spec/mechanism/scope objects.",
        ),
    ],
    out: Annotated[
        Path | None,
        typer.Option("--out", help="Write the qualification export JSON to this path."),
    ] = None,
    route_decision: Annotated[
        str | None,
        typer.Option("--route-decision", help="ENGINEERING_ROUTE_DECISION value, if any."),
    ] = None,
    score: Annotated[int, typer.Option("--score", help="Uniform reviewer score 0-5.")] = 3,
) -> None:
    """Run route-aware RQ0-RQ4 over a frozen design and export the result."""
    import json

    payload = json.loads(spec_json.read_text(encoding="utf-8"))
    spec = NaturalLanguageSpec(**payload["spec"])
    mechanism = MechanismSketch(**payload["mechanism"])
    scope = ResearchScopeSpec(**payload["scope"])
    primary_factory, auditor_factory = _reviewer_factories(score)
    run = run_qualification_pipeline(
        project_id=project_id,
        research_spec_id=payload.get("research_spec_id", f"rs-{project_id}"),
        spec=spec,
        mechanism=mechanism,
        scope=scope,
        capability_profile=_capability_profile(),
        academic_providers=fake_academic_providers(),
        engineering_providers=fake_engineering_providers(),
        queries=_queries(),
        formalizer_session_id="cli-formalizer",
        assessor_session_id="cli-assessor",
        primary_reviewer_factory=primary_factory,
        auditor_reviewer_factory=auditor_factory,
        route_decision=route_decision,
        user_event_id=f"cli-user:{project_id}",
    )
    export = qualification_export_payload(run)
    if out is not None:
        out.write_text(canonical_json(export), encoding="utf-8")
        typer.echo(f"exported: {out}")
    typer.echo(
        canonical_json(
            {
                "run_id": export["run_id"],
                "route": export["route"],
                "next_target": export["next_target"],
                "gate": export["gate"].get("gate_type") if export["gate"] else None,
                "novelty_total": (
                    export["scores"].get("novelty_total") if export["scores"] else None
                ),
            }
        )
    )
