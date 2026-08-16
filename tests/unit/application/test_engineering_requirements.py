"""M2.9 unit tests for ENG0-ENG3 application services (03B sections 1-6)."""

from __future__ import annotations

import dataclasses
from datetime import UTC, datetime
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config

from synaisthesis.application.engineering_design_service import (
    create_engineering_mission_charter,
    create_engineering_requirements_baseline,
    create_operational_concept_bundle,
    create_option_trade_study,
    load_engineering_charter,
    load_operational_concept_bundle,
    load_option_trade_study,
    load_requirements_baseline,
    run_engineering_reference_search,
    select_engineering_technology,
)
from synaisthesis.domain.engineering import (
    EngineeringDeliveryMode,
    EngineeringMissionCharter,
    EngineeringReferenceSet,
    ExternalDependency,
    OperationalConceptBundle,
    OperationalScenario,
    OptionTradeStudy,
    StakeholderEntry,
    TechnologySelectionRecord,
    TradeStudyOption,
)
from synaisthesis.domain.enums import (
    EngineeringRouteDecision,
    NoveltyStatus,
    ProvenanceType,
    ResearchRoute,
)
from synaisthesis.domain.errors import DomainError
from synaisthesis.domain.qualification import (
    EngineeringRouteSelection,
    UserEngineeringConceptApproval,
)
from synaisthesis.domain.requirements import (
    EngineeringRequirement,
    RequirementPriority,
    RequirementType,
    VerificationMethod,
)
from synaisthesis.providers.prior_art.base import EngineeringReferenceQuery
from synaisthesis.providers.prior_art.fake import fake_engineering_reference_providers
from synaisthesis.storage.database import init_database

NOW = datetime(2026, 8, 17, 2, 0, 0, tzinfo=UTC)
SPEC_HASH = "s" * 64
CONCEPT_HASH = "c" * 64
REVIEW_HASH = "r" * 64
ASSESSMENT_HASH = "a" * 64

REPO_ROOT = Path(__file__).resolve().parents[3]
MIGRATIONS_DIR = REPO_ROOT / "src" / "synaisthesis" / "storage" / "migrations"

BASELINE_SCOPE = {
    "object_domain": ["finite_matrices"],
    "intended_users": ["researchers"],
    "core_functions": ["compute_trace"],
    "data_classification": ["public"],
    "engineering_goals": ["cli_tool"],
}


def _fresh_database(tmp_path: Path):
    db_url = f"sqlite:///{tmp_path / 'eng.db'}"
    cfg = Config()
    cfg.set_main_option("script_location", str(MIGRATIONS_DIR))
    cfg.set_main_option("sqlalchemy.url", db_url)
    command.upgrade(cfg, "head")
    _, session_factory = init_database(db_url)
    return session_factory


def _route_selection():
    return EngineeringRouteSelection(
        id="rs-1",
        project_id="p-1",
        feasibility_assessment_id="fa-1",
        decision=EngineeringRouteDecision.TRY_ENGINEERING_PROJECT,
        user_actor_id="u-1",
        decision_event_id="ev-rs",
        bound_assessment_hash=ASSESSMENT_HASH,
        input_spec_hash=SPEC_HASH,
        created_at=NOW,
    )


def _concept_approval():
    return UserEngineeringConceptApproval(
        concept_id="c-1",
        version=1,
        concept_hash=CONCEPT_HASH,
        route_selection_id="rs-1",
        input_spec_hash=SPEC_HASH,
        route=ResearchRoute.ENGINEERING,
        actor=ProvenanceType.USER_DECISION,
        user_event_id="uev-concept",
        decided_at=NOW,
    )


def _charter() -> EngineeringMissionCharter:
    return EngineeringMissionCharter(
        charter_id="ch-1",
        version=1,
        project_id="p-1",
        source_artifact_hashes=(SPEC_HASH, CONCEPT_HASH),
        problem_statement="提供可复算的矩阵迹计算工具",
        stakeholders=("academia",),
        intended_users=("researchers",),
        operational_context="命令行环境",
        system_of_interest_boundary="计算内核",
        objectives=("可复现",),
        non_goals=("GUI",),
        success_metrics=("100% 复现",),
        constraints=("Python 3.11+",),
        assumptions=("离线可用",),
        regulatory_security_ethics_flags=(),
        delivery_mode=EngineeringDeliveryMode.BLUEPRINT_ONLY,
        baseline_scope=dict(BASELINE_SCOPE),
        charter_scope=dict(BASELINE_SCOPE),
        proposed_additions=(),
        created_at=NOW,
    )


def _conops(charter_hash: str = "0" * 64) -> OperationalConceptBundle:
    return OperationalConceptBundle(
        conops_id="co-1",
        version=1,
        project_id="p-1",
        charter_id="ch-1",
        input_spec_hash=SPEC_HASH,
        charter_hash=charter_hash,
        stakeholder_map=(
            StakeholderEntry(
                stakeholder_id="st-1",
                role="operator",
                responsibility_boundary="run",
                is_operator=True,
                intended_user_refs=("u-1",),
            ),
        ),
        scenarios=(
            OperationalScenario(
                scenario_id="sc-1",
                expected_function_refs=("f-1",),
                stakeholder_role_refs=("operator",),
                precondition="ready",
                trigger="invoke",
                main_flow=("run",),
                alternate_flow=("retry",),
                postcondition="done",
            ),
        ),
        system_context="single CLI",
        external_systems=(
            ExternalDependency(
                dependency_id="d-1", owner="owner", failure_mode="down", fallback="retry"
            ),
        ),
        data_sources=(),
        trust_boundaries=("local",),
        human_intervention_points=("review",),
        environment_assumptions=("offline",),
        quality_requirements=("latency",),
        unresolved_issues=(),
        decision_owners=("user",),
        expected_functions=("f-1",),
        intended_user_ids=("u-1",),
        intent_refs=("intent-1", "intent-2"),
        created_at=NOW,
    )


def _requirement(req_id: str, source_refs: tuple[str, ...]) -> EngineeringRequirement:
    return EngineeringRequirement(
        requirement_id=req_id,
        type=RequirementType.QUALITY,
        statement="系统在 1 秒内返回结果",
        source_refs=source_refs,
        priority=RequirementPriority.CRITICAL,
        rationale="why",
        precondition="ready",
        inputs=(),
        expected_behavior_output="result",
        measurement_method="latency",
        unit="s",
        threshold="1",
        tolerance=None,
        verification_method=VerificationMethod.TEST,
        acceptance_criterion="latency <= 1s",
        owner="team",
        dependency_refs=(),
        conflict_refs=(),
    )


def _charter_entry(session_factory, artifact_root: Path):
    with session_factory() as session:
        charter = create_engineering_mission_charter(
            session,
            project_id="p-1",
            bound_input_spec_hash=SPEC_HASH,
            current_input_spec_hash=SPEC_HASH,
            route_selection=_route_selection(),
            concept_approval=_concept_approval(),
            concept_hash=CONCEPT_HASH,
            novelty_status=NoveltyStatus.ENGINEERING_NOVELTY_QUALIFIED,
            novelty_review_hash=REVIEW_HASH,
            override=None,
            open_gate_types=(),
            charter=_charter(),
            artifact_root=artifact_root,
        )
        session.commit()
    return charter


# ---------------------------------------------------------------------------
# ENG0 entry enforcement at the service layer
# ---------------------------------------------------------------------------


def test_charter_service_requires_user_route_decision(tmp_path):
    session_factory = _fresh_database(tmp_path)
    with session_factory() as session, pytest.raises(DomainError) as exc_info:
        create_engineering_mission_charter(
            session,
            project_id="p-1",
            bound_input_spec_hash=SPEC_HASH,
            current_input_spec_hash=SPEC_HASH,
            route_selection=None,
            concept_approval=_concept_approval(),
            concept_hash=CONCEPT_HASH,
            novelty_status=NoveltyStatus.ENGINEERING_NOVELTY_QUALIFIED,
            novelty_review_hash=REVIEW_HASH,
            override=None,
            open_gate_types=(),
            charter=_charter(),
            artifact_root=tmp_path / "artifacts",
        )
    assert exc_info.value.error_code == "ENGINEERING_ROUTE_DECISION_REQUIRED"


def test_charter_service_rejects_theory_novelty(tmp_path):
    session_factory = _fresh_database(tmp_path)
    with session_factory() as session, pytest.raises(DomainError) as exc_info:
        create_engineering_mission_charter(
            session,
            project_id="p-1",
            bound_input_spec_hash=SPEC_HASH,
            current_input_spec_hash=SPEC_HASH,
            route_selection=_route_selection(),
            concept_approval=_concept_approval(),
            concept_hash=CONCEPT_HASH,
            novelty_status=NoveltyStatus.NOVELTY_QUALIFIED,
            novelty_review_hash=REVIEW_HASH,
            override=None,
            open_gate_types=(),
            charter=_charter(),
            artifact_root=tmp_path / "artifacts",
        )
    assert exc_info.value.error_code == "ENGINEERING_NOVELTY_REQUIRED"


def test_charter_round_trip_via_events(tmp_path):
    session_factory = _fresh_database(tmp_path)
    charter = _charter_entry(session_factory, tmp_path / "artifacts")
    with session_factory() as session:
        reloaded = load_engineering_charter(session, "ch-1", artifact_root=tmp_path / "artifacts")
    assert reloaded == charter
    assert reloaded.artifact_hash == charter.artifact_hash


# ---------------------------------------------------------------------------
# ENG1 ConOps service
# ---------------------------------------------------------------------------


def test_conops_requires_charter_hash_binding(tmp_path):
    session_factory = _fresh_database(tmp_path)
    artifact_root = tmp_path / "artifacts"
    charter = _charter_entry(session_factory, artifact_root)
    with session_factory() as session, pytest.raises(DomainError) as exc_info:
        create_operational_concept_bundle(
            session,
            project_id="p-1",
            charter=charter,
            conops=_conops(),  # charter_hash is all-zero -> mismatch
            artifact_root=artifact_root,
        )
    assert exc_info.value.error_code == "CONOPS_CHARTER_MISMATCH"


def test_conops_round_trip_via_events(tmp_path):
    session_factory = _fresh_database(tmp_path)
    artifact_root = tmp_path / "artifacts"
    charter = _charter_entry(session_factory, artifact_root)
    if charter.artifact_hash is None:
        raise AssertionError("charter hash missing")
    if charter.artifact_hash is None:
        raise AssertionError("charter hash missing")
    conops = _conops(charter.artifact_hash)
    with session_factory() as session:
        saved = create_operational_concept_bundle(
            session,
            project_id="p-1",
            charter=charter,
            conops=conops,
            artifact_root=artifact_root,
        )
        session.commit()
    with session_factory() as session:
        reloaded = load_operational_concept_bundle(session, "co-1", artifact_root=artifact_root)
    assert reloaded == saved


# ---------------------------------------------------------------------------
# ENG2 requirements baseline service
# ---------------------------------------------------------------------------


def _persisted_conops(session_factory, artifact_root: Path):
    charter = _charter_entry(session_factory, artifact_root)
    if charter.artifact_hash is None:
        raise AssertionError("charter hash missing")
    if charter.artifact_hash is None:
        raise AssertionError("charter hash missing")
    conops = _conops(charter.artifact_hash)
    with session_factory() as session:
        saved = create_operational_concept_bundle(
            session,
            project_id="p-1",
            charter=charter,
            conops=conops,
            artifact_root=artifact_root,
        )
        session.commit()
    return saved


def test_requirements_baseline_blocks_incomplete_source_coverage(tmp_path):
    session_factory = _fresh_database(tmp_path)
    artifact_root = tmp_path / "artifacts"
    conops = _persisted_conops(session_factory, artifact_root)
    with session_factory() as session, pytest.raises(DomainError) as exc_info:
        create_engineering_requirements_baseline(
            session,
            project_id="p-1",
            conops=conops,
            requirements=(_requirement("R1", ("intent-1",)),),  # intent-2 uncovered
            artifact_root=artifact_root,
        )
    assert exc_info.value.error_code == "REQUIREMENTS_BASELINE_BLOCKED"


def test_requirements_baseline_blocks_critical_without_threshold(tmp_path):
    session_factory = _fresh_database(tmp_path)
    artifact_root = tmp_path / "artifacts"
    conops = _persisted_conops(session_factory, artifact_root)
    bad = EngineeringRequirement(
        requirement_id="R1",
        type=RequirementType.QUALITY,
        statement="系统返回结果",
        source_refs=("intent-1", "intent-2"),
        priority=RequirementPriority.CRITICAL,
        rationale="why",
        precondition="ready",
        inputs=(),
        expected_behavior_output="result",
        measurement_method="latency",
        unit="s",
        threshold=None,
        tolerance=None,
        verification_method=VerificationMethod.TEST,
        acceptance_criterion="低延迟",
        owner="team",
        dependency_refs=(),
        conflict_refs=(),
    )
    with session_factory() as session, pytest.raises(DomainError) as exc_info:
        create_engineering_requirements_baseline(
            session,
            project_id="p-1",
            conops=conops,
            requirements=(bad,),
            artifact_root=artifact_root,
        )
    assert exc_info.value.error_code == "REQUIREMENTS_BASELINE_BLOCKED"


def test_requirements_baseline_round_trip_via_events(tmp_path):
    session_factory = _fresh_database(tmp_path)
    artifact_root = tmp_path / "artifacts"
    conops = _persisted_conops(session_factory, artifact_root)
    requirements = (
        _requirement("R1", ("intent-1", "intent-2")),
        _requirement("R2", ("intent-1",)),
    )
    with session_factory() as session:
        saved = create_engineering_requirements_baseline(
            session,
            project_id="p-1",
            conops=conops,
            requirements=requirements,
            artifact_root=artifact_root,
            baseline_id="rb-1",
        )
        session.commit()
    with session_factory() as session:
        reloaded = load_requirements_baseline(session, "rb-1", artifact_root=artifact_root)
    assert reloaded == saved
    assert reloaded.requirements[0].type is RequirementType.QUALITY
    assert reloaded.requirements[0].priority is RequirementPriority.CRITICAL
    assert reloaded.requirements[0].verification_method is VerificationMethod.TEST
    assert reloaded.requirements[0].content_hash == saved.requirements[0].content_hash


# ---------------------------------------------------------------------------
# ENG3 reference search and trade study
# ---------------------------------------------------------------------------


def test_reference_search_dedupes_and_covers_all_categories():
    query = EngineeringReferenceQuery(
        query_id="ref-q-1",
        baseline_id="rb-1",
        requirement_refs=("R1",),
        original_text="trace computation library",
        categories=("repository", "documentation", "standard", "paper", "registry"),
        executed_at=NOW,
    )
    reference_set = run_engineering_reference_search(
        providers=fake_engineering_reference_providers(),
        query=query,
        project_id="p-1",
        requirements_baseline_id="rb-1",
    )
    assert isinstance(reference_set, EngineeringReferenceSet)
    # GitHub mirror duplicate is dropped: 6 corpus hits -> 5 unique
    assert len(reference_set.references) == 5
    categories = {reference.reference_type for reference in reference_set.references}
    assert categories == {"repository", "documentation", "standard", "paper", "registry"}
    assert reference_set.artifact_hash is not None
    assert len(reference_set.artifact_hash) == 64


def _option(
    option_id: str, covers: tuple[str, ...], cost: float, coverage: float
) -> TradeStudyOption:
    return TradeStudyOption(
        option_id=option_id,
        name=option_id,
        covers_requirements=covers,
        key_components=(),
        dependencies=(),
        interfaces=(),
        data_paths=(),
        performance_predictions={},
        reliability_predictions={},
        security_predictions={},
        maintainability_predictions={},
        scalability_predictions={},
        implementation_complexity="low",
        personnel_effort="1",
        timeline_cost_infrastructure="cheap",
        license_supply_chain_risks=(),
        prototype_spike_suggestions=(),
        unknowns=(),
        evidence_confidence="medium",
        normalized_criterion_scores={"cost": cost, "coverage": coverage},
    )


def _study() -> OptionTradeStudy:
    return OptionTradeStudy(
        study_id="ts-1",
        version=1,
        project_id="p-1",
        requirements_baseline_id="rb-1",
        critical_requirement_ids=("R1", "R2"),
        criteria=("cost", "coverage"),
        weights={"cost": 0.5, "coverage": 0.5},
        weights_derivation_ref="rb-1#weights",
        options=(
            _option("A", ("R1", "R2"), 0.6, 0.6),
            _option("B", ("R1",), 0.9, 0.9),
        ),
        eliminated_option_ids=("B",),
        created_at=NOW,
    )


def test_trade_study_service_blocks_missing_hard_elimination(tmp_path):
    session_factory = _fresh_database(tmp_path)
    artifact_root = tmp_path / "artifacts"
    conops = _persisted_conops(session_factory, artifact_root)
    requirements = (
        _requirement("R1", ("intent-1", "intent-2")),
        _requirement("R2", ("intent-1",)),
    )
    with session_factory() as session:
        baseline = create_engineering_requirements_baseline(
            session,
            project_id="p-1",
            conops=conops,
            requirements=requirements,
            artifact_root=artifact_root,
            baseline_id="rb-1",
        )
        session.commit()
    study = _study()
    with session_factory() as session, pytest.raises(DomainError) as exc_info:
        create_option_trade_study(
            session,
            project_id="p-1",
            baseline=baseline,
            study=dataclasses.replace(study, eliminated_option_ids=(), artifact_hash=None),
            artifact_root=artifact_root,
        )
    assert exc_info.value.error_code == "TRADE_STUDY_BLOCKED"


def test_trade_study_round_trip_and_selection(tmp_path):
    session_factory = _fresh_database(tmp_path)
    artifact_root = tmp_path / "artifacts"
    conops = _persisted_conops(session_factory, artifact_root)
    requirements = (
        _requirement("R1", ("intent-1", "intent-2")),
        _requirement("R2", ("intent-1",)),
    )
    with session_factory() as session:
        baseline = create_engineering_requirements_baseline(
            session,
            project_id="p-1",
            conops=conops,
            requirements=requirements,
            artifact_root=artifact_root,
            baseline_id="rb-1",
        )
        study = create_option_trade_study(
            session,
            project_id="p-1",
            baseline=baseline,
            study=_study(),
            artifact_root=artifact_root,
        )
        record = TechnologySelectionRecord(
            selection_id="sel-1",
            study_id="ts-1",
            study_hash=study.artifact_hash or "",
            selected_option_id="A",
            rationale="覆盖全部 Critical requirements",
            created_at=NOW,
        )
        select_engineering_technology(
            session,
            project_id="p-1",
            record=record,
            study=study,
            artifact_root=artifact_root,
        )
        session.commit()
    with session_factory() as session:
        reloaded = load_option_trade_study(session, "ts-1", artifact_root=artifact_root)
    assert reloaded == study
    assert reloaded.weights == {"cost": 0.5, "coverage": 0.5}
    assert reloaded.eligible_ranking() == ("A",)
    assert reloaded.options[1].option_id == "B"


def test_technology_selection_rejects_stale_study_hash(tmp_path):
    session_factory = _fresh_database(tmp_path)
    artifact_root = tmp_path / "artifacts"
    conops = _persisted_conops(session_factory, artifact_root)
    requirements = (
        _requirement("R1", ("intent-1", "intent-2")),
        _requirement("R2", ("intent-1",)),
    )
    with session_factory() as session:
        baseline = create_engineering_requirements_baseline(
            session,
            project_id="p-1",
            conops=conops,
            requirements=requirements,
            artifact_root=artifact_root,
            baseline_id="rb-1",
        )
        study = create_option_trade_study(
            session,
            project_id="p-1",
            baseline=baseline,
            study=_study(),
            artifact_root=artifact_root,
        )
        stale = TechnologySelectionRecord(
            selection_id="sel-2",
            study_id="ts-1",
            study_hash="0" * 64,
            selected_option_id="A",
            rationale="stale",
            created_at=NOW,
        )
        with pytest.raises(DomainError) as exc_info:
            select_engineering_technology(
                session,
                project_id="p-1",
                record=stale,
                study=study,
                artifact_root=artifact_root,
            )
    assert exc_info.value.error_code == "TRADE_STUDY_BLOCKED"
