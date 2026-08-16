"""M2.9 integration tests for the ENG0->ENG4 vertical slice with architecture review."""

from __future__ import annotations

import dataclasses
from datetime import UTC, datetime
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import select

from synaisthesis.application.engineering_design_service import (
    create_architecture_baseline,
    create_engineering_mission_charter,
    create_engineering_requirements_baseline,
    create_operational_concept_bundle,
    create_option_trade_study,
    load_architecture_baseline,
    load_engineering_charter,
    load_engineering_gate,
    load_operational_concept_bundle,
    load_option_trade_study,
    load_requirements_baseline,
    open_engineering_architecture_review,
    resolve_engineering_architecture_review,
)
from synaisthesis.domain.architecture import (
    ArchitectureComponent,
    ArchitectureDecisionRecord,
    DataContractSet,
    DeploymentAndOperationsDesign,
    InterfaceContractSet,
    StateAndFailureModel,
    ThreatModel,
)
from synaisthesis.domain.engineering import (
    EngineeringDeliveryMode,
    EngineeringGateType,
    EngineeringMissionCharter,
    ExternalDependency,
    OperationalConceptBundle,
    OperationalScenario,
    OptionTradeStudy,
    StakeholderEntry,
    TradeStudyOption,
)
from synaisthesis.domain.enums import (
    EngineeringRouteDecision,
    GateStatus,
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
from synaisthesis.renderers.diagram_renderers import DiagramSource
from synaisthesis.storage.database import init_database
from synaisthesis.storage.repositories.event_repository import DomainEventRecord

NOW = datetime(2026, 8, 17, 2, 0, 0, tzinfo=UTC)
SPEC_HASH = "s" * 64
CONCEPT_HASH = "c" * 64
REVIEW_HASH = "r" * 64
ASSESSMENT_HASH = "a" * 64

REPO_ROOT = Path(__file__).resolve().parents[2]
MIGRATIONS_DIR = REPO_ROOT / "src" / "synaisthesis" / "storage" / "migrations"

BASELINE_SCOPE = {
    "object_domain": ["finite_matrices"],
    "intended_users": ["researchers"],
    "core_functions": ["compute_trace"],
    "data_classification": ["public"],
    "engineering_goals": ["cli_tool"],
}


def _fresh_database(tmp_path: Path):
    db_url = f"sqlite:///{tmp_path / 'eng-slice.db'}"
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


def _conops(charter_hash: str) -> OperationalConceptBundle:
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
            TradeStudyOption(
                option_id="A",
                name="pure python",
                covers_requirements=("R1", "R2"),
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
                normalized_criterion_scores={"cost": 0.6, "coverage": 0.6},
            ),
            TradeStudyOption(
                option_id="B",
                name="c extension",
                covers_requirements=("R1",),
                key_components=(),
                dependencies=(),
                interfaces=(),
                data_paths=(),
                performance_predictions={},
                reliability_predictions={},
                security_predictions={},
                maintainability_predictions={},
                scalability_predictions={},
                implementation_complexity="high",
                personnel_effort="3",
                timeline_cost_infrastructure="costly",
                license_supply_chain_risks=(),
                prototype_spike_suggestions=(),
                unknowns=(),
                evidence_confidence="low",
                normalized_criterion_scores={"cost": 0.9, "coverage": 0.9},
            ),
        ),
        eliminated_option_ids=("B",),
        created_at=NOW,
    )


def _diagram_source() -> DiagramSource:
    return DiagramSource(
        diagram_id="dg-1",
        title="system context",
        version=1,
        input_hash="i" * 64,
        legend="boxes are components",
        node_edge_semantics="solid=call",
        source_text='node n1 "Trace Engine"\nnode n2 "CLI"\nedge n1 n2\n',
        node_component_ids=("n1", "n2"),
    )


def _architecture_inputs():
    return {
        "components": (
            ArchitectureComponent(
                component_id="comp-1", name="core", responsibilities=("compute",)
            ),
            ArchitectureComponent(component_id="comp-2", name="cli", responsibilities=("invoke",)),
        ),
        "views": {"system_context": "two boxes"},
        "interface_contracts": (
            InterfaceContractSet(
                interface_id="if-1", schema_ref="openapi.yaml", version_policy="semver"
            ),
        ),
        "data_contracts": (
            DataContractSet(contract_id="dc-1", schema_ref="x.json", lifecycle="immutable"),
        ),
        "state_and_failure_model": StateAndFailureModel(
            model_id="sf-1",
            states=("idle", "running"),
            errors=("timeout",),
            recovery_actions=("retry",),
            idempotency_boundary="event id",
            concurrency_boundary="per project",
        ),
        "threat_model": ThreatModel(
            model_id="th-1",
            trust_boundaries=("local",),
            threats=("tampering",),
            security_controls=("hash verify",),
        ),
        "deployment_and_operations": DeploymentAndOperationsDesign(
            design_id="do-1",
            topology="single node",
            environment="wsl",
            operations_boundary="cli",
            observability_audit_backup_recovery="logs",
            retirement="archive",
        ),
        "adrs": (
            ArchitectureDecisionRecord(
                adr_id="adr-1",
                title="event sourcing",
                status="ACCEPTED",
                decision="events",
                alternatives_considered=("tables",),
                rationale="replay",
                affected_component_ids=("comp-1",),
                irreversible=True,
            ),
        ),
        "diagram_sources": (_diagram_source(),),
        "node_component_mappings": {"dg-1": {"n1": "comp-1", "n2": "comp-2"}},
    }


def _run_slice(session_factory, artifact_root: Path):
    """Run ENG0-ENG4 and return the artifacts."""
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
        if charter.artifact_hash is None:
            raise AssertionError("charter hash missing")
        conops = create_operational_concept_bundle(
            session,
            project_id="p-1",
            charter=charter,
            conops=_conops(charter.artifact_hash),
            artifact_root=artifact_root,
        )
        baseline = create_engineering_requirements_baseline(
            session,
            project_id="p-1",
            conops=conops,
            requirements=(
                _requirement("R1", ("intent-1", "intent-2")),
                _requirement("R2", ("intent-1",)),
            ),
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
        architecture = create_architecture_baseline(
            session,
            project_id="p-1",
            requirements_baseline=baseline,
            trade_study=study,
            artifact_root=artifact_root,
            baseline_id="ab-1",
            **_architecture_inputs(),
        )
        gate = open_engineering_architecture_review(
            session,
            project_id="p-1",
            baseline=architecture,
            artifact_root=artifact_root,
            gate_id="gate-ar-1",
        )
        session.commit()
    return charter, conops, baseline, study, architecture, gate


def test_vertical_slice_persists_and_replays(tmp_path):
    session_factory = _fresh_database(tmp_path)
    artifact_root = tmp_path / "artifacts"
    charter, conops, baseline, study, architecture, gate = _run_slice(
        session_factory, artifact_root
    )

    with session_factory() as session:
        assert load_engineering_charter(session, "ch-1", artifact_root=artifact_root) == charter
        assert (
            load_operational_concept_bundle(session, "co-1", artifact_root=artifact_root) == conops
        )
        assert load_requirements_baseline(session, "rb-1", artifact_root=artifact_root) == baseline
        assert load_option_trade_study(session, "ts-1", artifact_root=artifact_root) == study
        assert (
            load_architecture_baseline(session, "ab-1", artifact_root=artifact_root) == architecture
        )
        reloaded_gate = load_engineering_gate(session, "gate-ar-1", artifact_root=artifact_root)
    assert reloaded_gate == gate
    assert reloaded_gate.gate_type is EngineeringGateType.ENGINEERING_ARCHITECTURE_REVIEW
    assert reloaded_gate.binding.bound_hashes["architecture"] == architecture.artifact_hash

    # diagram source and SVG are stored as artifacts, not just in memory
    diagram = architecture.diagrams[0]
    assert (artifact_root / diagram.source_path).exists()
    assert (artifact_root / diagram.rendered_svg_path).exists()
    assert diagram.stable_id_mapping == {"n1": "comp-1", "n2": "comp-2"}
    assert diagram.render_receipt.startswith("render:dg-1:")


def test_architecture_review_requires_real_user_and_current_binding(tmp_path):
    session_factory = _fresh_database(tmp_path)
    artifact_root = tmp_path / "artifacts"
    _charter, _conops, _baseline, _study, architecture, gate = _run_slice(
        session_factory, artifact_root
    )

    with session_factory() as session, pytest.raises(DomainError) as exc_info:
        resolve_engineering_architecture_review(
            session,
            gate=gate,
            decision="APPROVE_BASELINE",
            actor=ProvenanceType.ASSISTANT_PROPOSAL,
            user_event_id="ev-1",
            current_baseline=architecture,
            at=NOW,
            artifact_root=artifact_root,
        )
    assert exc_info.value.error_code == "CONFIRMATION_REQUIRES_USER_EVENT"

    # any of the three hashes changes -> old binding invalid
    stale = dataclasses.replace(architecture, requirements_hash="0" * 64, artifact_hash=None)
    with session_factory() as session, pytest.raises(DomainError) as exc_info:
        resolve_engineering_architecture_review(
            session,
            gate=gate,
            decision="APPROVE_BASELINE",
            actor=ProvenanceType.USER_DECISION,
            user_event_id="ev-2",
            current_baseline=stale,
            at=NOW,
            artifact_root=artifact_root,
        )
    assert exc_info.value.error_code == "STALE_ARCHITECTURE_BINDING"


def test_architecture_review_approve_resolves_and_persists(tmp_path):
    session_factory = _fresh_database(tmp_path)
    artifact_root = tmp_path / "artifacts"
    _charter, _conops, _baseline, _study, architecture, gate = _run_slice(
        session_factory, artifact_root
    )

    with session_factory() as session:
        resolved = resolve_engineering_architecture_review(
            session,
            gate=gate,
            decision="APPROVE_BASELINE",
            actor=ProvenanceType.USER_DECISION,
            user_event_id="uev-approve",
            current_baseline=architecture,
            at=NOW,
            artifact_root=artifact_root,
        )
        session.commit()
    assert resolved.status is GateStatus.RESOLVED
    assert resolved.decision == "APPROVE_BASELINE"

    with session_factory() as session:
        reloaded = load_engineering_gate(session, "gate-ar-1", artifact_root=artifact_root)
        events = (
            session.execute(
                select(DomainEventRecord).where(DomainEventRecord.aggregate_id == "gate-ar-1")
            )
            .scalars()
            .all()
        )
    assert reloaded.status is GateStatus.RESOLVED
    assert reloaded.decision == "APPROVE_BASELINE"
    assert [event.event_type for event in events] == [
        "EngineeringGateOpened",
        "EngineeringGateResolved",
    ]


def test_architecture_gate_rejects_invalid_decision(tmp_path):
    session_factory = _fresh_database(tmp_path)
    artifact_root = tmp_path / "artifacts"
    _charter, _conops, _baseline, _study, architecture, gate = _run_slice(
        session_factory, artifact_root
    )
    with session_factory() as session, pytest.raises(DomainError) as exc_info:
        resolve_engineering_architecture_review(
            session,
            gate=gate,
            decision="MAYBE",
            actor=ProvenanceType.USER_DECISION,
            user_event_id="ev-3",
            current_baseline=architecture,
            at=NOW,
            artifact_root=artifact_root,
        )
    assert exc_info.value.error_code == "INVALID_GATE_DECISION"


def test_node_path_enforces_same_preconditions(tmp_path):
    from synaisthesis.orchestration.nodes.engineering_nodes import (
        eng0_charter_node,
        eng2_requirements_node,
    )

    session_factory = _fresh_database(tmp_path)
    artifact_root = tmp_path / "artifacts"
    with session_factory() as session, pytest.raises(DomainError) as exc_info:
        eng0_charter_node(
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
            artifact_root=artifact_root,
        )
    assert exc_info.value.error_code == "ENGINEERING_ROUTE_DECISION_REQUIRED"

    # node requires a persisted ConOps before ENG2
    with session_factory() as session, pytest.raises(DomainError) as exc_info:
        eng2_requirements_node(
            session,
            project_id="p-1",
            conops_id="missing-co",
            requirements=(_requirement("R1", ("intent-1",)),),
            artifact_root=artifact_root,
        )
    assert exc_info.value.error_code == "CONOPS_REQUIRED"
