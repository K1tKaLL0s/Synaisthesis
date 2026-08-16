"""M2.10 unit tests for the ENG5 blueprint completeness service and export bundle."""

from __future__ import annotations

import dataclasses
from datetime import UTC, datetime
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config

from synaisthesis.application.engineering_design_service import (
    create_architecture_baseline,
    create_engineering_mission_charter,
    create_engineering_requirements_baseline,
    create_mechanical_engineering_blueprint,
    create_operational_concept_bundle,
    create_option_trade_study,
    load_mechanical_engineering_blueprint,
    open_engineering_architecture_review,
    resolve_engineering_architecture_review,
)
from synaisthesis.domain.architecture import (
    ArchitectureBaseline,
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
    EngineeringMissionCharter,
    EngineeringWorkUnitContract,
    ExternalDependency,
    MechanicalEngineeringBlueprint,
    OperationalConceptBundle,
    OperationalScenario,
    OptionTradeStudy,
    StakeholderEntry,
    TradeStudyOption,
    blueprint_completeness_blockers,
    validate_decision_escalation,
)
from synaisthesis.domain.enums import (
    EngineeringRouteDecision,
    NoveltyStatus,
    ProvenanceType,
    ResearchRoute,
)
from synaisthesis.domain.errors import DomainError
from synaisthesis.domain.gate import EngineeringGate
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
from synaisthesis.domain.traceability import (
    RequirementsTraceabilityMatrix,
    TraceabilityEdge,
    TraceableElementType,
    TraceRelation,
)
from synaisthesis.renderers.diagram_renderers import DiagramSource
from synaisthesis.storage.database import init_database
from synaisthesis.storage.export_bundle import (
    MANIFEST_ROLE_DIAGRAM_RENDERED,
    MANIFEST_ROLE_EXECUTIVE_SUMMARY,
    ExportBundle,
    verify_export_bundle,
)

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
    db_url = f"sqlite:///{tmp_path / 'eng10.db'}"
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


def _matrix() -> RequirementsTraceabilityMatrix:
    edges = []
    for index, (req_id, design, task, test) in enumerate(
        (
            ("R1", "d-1", "t-1", "test-1"),
            ("R2", "d-2", "t-2", "test-2"),
        ),
        start=1,
    ):
        edges.extend(
            [
                TraceabilityEdge(
                    edge_id=f"e{index}a",
                    project_id="p-1",
                    from_type=TraceableElementType.REQUIREMENT,
                    from_id=req_id,
                    relation=TraceRelation.TRACES_TO,
                    to_type=TraceableElementType.DESIGN,
                    to_id=design,
                    baseline_version=1,
                ),
                TraceabilityEdge(
                    edge_id=f"e{index}b",
                    project_id="p-1",
                    from_type=TraceableElementType.REQUIREMENT,
                    from_id=req_id,
                    relation=TraceRelation.TRACES_TO,
                    to_type=TraceableElementType.TASK,
                    to_id=task,
                    baseline_version=1,
                ),
                TraceabilityEdge(
                    edge_id=f"e{index}c",
                    project_id="p-1",
                    from_type=TraceableElementType.REQUIREMENT,
                    from_id=req_id,
                    relation=TraceRelation.VERIFIES,
                    to_type=TraceableElementType.TEST,
                    to_id=test,
                    baseline_version=1,
                ),
            ]
        )
    return RequirementsTraceabilityMatrix(
        matrix_id="tm-1", project_id="p-1", baseline_version=1, edges=tuple(edges)
    )


def _work_unit(task_id: str, stop: tuple[str, ...] = ("失败即停",)) -> EngineeringWorkUnitContract:
    return EngineeringWorkUnitContract(
        task_id=task_id,
        unique_objective="实现 " + task_id,
        authoritative_inputs=("03B §8",),
        preconditions_gates_environment=("前置 Gate 通过",),
        allowed_files=("src/core.py",),
        forbidden_files=("src/secret.py",),
        io_contracts=("compute_trace(m) -> float",),
        invariants=("不修改输入矩阵",),
        step_actions=("新增 compute_trace 函数",),
        errors_boundaries_compat_rollback=("类型错误返回 DomainError",),
        focused_tests=("test_compute_trace.py",),
        full_checks=("pytest/ruff/basedpyright",),
        acceptance_criteria=("focused 测试通过",),
        stop_escalation_conditions=stop,
        delivery_format="diff + 命令回执",
    )


def _blueprint(architecture: ArchitectureBaseline, **overrides) -> MechanicalEngineeringBlueprint:
    params = {
        "blueprint_id": "bp-1",
        "version": 1,
        "project_id": "p-1",
        "architecture_baseline_id": architecture.baseline_id,
        "architecture_hash": architecture.artifact_hash or "",
        "project_tree": {"src": "implementation"},
        "file_level_changes": {"added": ("src/core.py", "src/cli.py")},
        "modules_and_symbols": {"core": ("compute_trace",)},
        "dependency_lock_policy": "uv.lock",
        "config_secret_env_policy": "env only",
        "data_migration_rollback_policy": "events",
        "runtime_flow_specs": {"run": "cli -> core"},
        "non_functional_requirements": ("latency",),
        "command_templates": {"test": "pytest"},
        "traceability": {
            "R1": ("d-1", "t-1", "test-1"),
            "R2": ("d-2", "t-2", "test-2"),
        },
        "risk_register": ("risk-1",),
        "stop_and_escalation_conditions": ("blocker 即停",),
        "pending_generated_artifacts": ("README.md",),
        "work_units": (_work_unit("wu-1"), _work_unit("wu-2")),
        "escalated_decision_ids": (),
    }
    params.update(overrides)
    return MechanicalEngineeringBlueprint(**params)


def _run_slice(
    session_factory,
    artifact_root: Path,
    *,
    approve: bool = True,
    matrix: RequirementsTraceabilityMatrix | None = None,
) -> tuple[ArchitectureBaseline, EngineeringGate, RequirementsTraceabilityMatrix]:
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
        conops = create_operational_concept_bundle(
            session,
            project_id="p-1",
            charter=charter,
            conops=_conops(charter.artifact_hash or ""),
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
        if approve:
            gate = resolve_engineering_architecture_review(
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
    return architecture, gate, matrix if matrix is not None else _matrix()


def _create_blueprint(
    session_factory,
    artifact_root: Path,
    *,
    approve: bool = True,
    matrix: RequirementsTraceabilityMatrix | None = None,
    blueprint: MechanicalEngineeringBlueprint | None = None,
    ordinary_decision_ids: tuple[str, ...] = (),
):
    architecture, gate, matrix = _run_slice(
        session_factory, artifact_root, approve=approve, matrix=matrix
    )
    blueprint = blueprint if blueprint is not None else _blueprint(architecture)
    with session_factory() as session:
        saved = create_mechanical_engineering_blueprint(
            session,
            project_id="p-1",
            architecture=architecture,
            architecture_approval=gate,
            matrix=matrix,
            blueprint=blueprint,
            ordinary_decision_ids=ordinary_decision_ids,
            artifact_root=artifact_root,
        )
        session.commit()
    return architecture, gate, matrix, saved


# ---------------------------------------------------------------------------
# Blueprint Completeness Gate (03B, section 8.3)
# ---------------------------------------------------------------------------


def test_blueprint_requires_approved_architecture(tmp_path):
    session_factory = _fresh_database(tmp_path)
    artifact_root = tmp_path / "artifacts"
    architecture, gate, matrix = _run_slice(session_factory, artifact_root, approve=False)
    with session_factory() as session, pytest.raises(DomainError) as exc_info:
        create_mechanical_engineering_blueprint(
            session,
            project_id="p-1",
            architecture=architecture,
            architecture_approval=gate,
            matrix=matrix,
            blueprint=_blueprint(architecture),
            artifact_root=artifact_root,
        )
    assert exc_info.value.error_code == "ENGINEERING_ARCHITECTURE_REVIEW_REQUIRED"


def test_blueprint_requires_three_hash_binding_of_approval(tmp_path):
    session_factory = _fresh_database(tmp_path)
    artifact_root = tmp_path / "artifacts"
    architecture, gate, matrix = _run_slice(session_factory, artifact_root, approve=True)
    other = dataclasses.replace(architecture, requirements_hash="0" * 64, artifact_hash=None)
    with session_factory() as session, pytest.raises(DomainError) as exc_info:
        create_mechanical_engineering_blueprint(
            session,
            project_id="p-1",
            architecture=other,
            architecture_approval=gate,
            matrix=matrix,
            blueprint=_blueprint(other),
            artifact_root=artifact_root,
        )
    assert exc_info.value.error_code == "ENGINEERING_ARCHITECTURE_REVIEW_REQUIRED"


def test_blueprint_blocks_trace_gap_for_critical_test(tmp_path):
    session_factory = _fresh_database(tmp_path)
    artifact_root = tmp_path / "artifacts"
    matrix = _matrix()
    # R2 loses its test edge -> critical->test coverage < 100%
    matrix = dataclasses.replace(
        matrix,
        edges=tuple(
            edge
            for edge in matrix.edges
            if not (edge.from_id == "R2" and edge.to_type.value == "TEST")
        ),
    )
    with pytest.raises(DomainError) as exc_info:
        _create_blueprint(session_factory, artifact_root, matrix=matrix)
    assert exc_info.value.error_code == "BLUEPRINT_GAP"


def test_blueprint_blocks_work_unit_without_stop_condition(tmp_path):
    session_factory = _fresh_database(tmp_path)
    artifact_root = tmp_path / "artifacts"
    architecture, gate, matrix = _run_slice(session_factory, artifact_root, approve=True)
    blueprint = _blueprint(
        architecture,
        work_units=(_work_unit("wu-1", stop=()), _work_unit("wu-2")),
    )
    with session_factory() as session, pytest.raises(DomainError) as exc_info:
        create_mechanical_engineering_blueprint(
            session,
            project_id="p-1",
            architecture=architecture,
            architecture_approval=gate,
            matrix=matrix,
            blueprint=blueprint,
            artifact_root=artifact_root,
        )
    assert exc_info.value.error_code == "BLUEPRINT_GAP"
    assert "tasks_with_stop_condition" in str(exc_info.value)


def test_blueprint_blocks_escalated_ordinary_choice(tmp_path):
    session_factory = _fresh_database(tmp_path)
    artifact_root = tmp_path / "artifacts"
    architecture, gate, matrix = _run_slice(session_factory, artifact_root, approve=True)
    blueprint = _blueprint(architecture, escalated_decision_ids=("naming-style",))
    with session_factory() as session, pytest.raises(DomainError) as exc_info:
        create_mechanical_engineering_blueprint(
            session,
            project_id="p-1",
            architecture=architecture,
            architecture_approval=gate,
            matrix=matrix,
            blueprint=blueprint,
            ordinary_decision_ids=("naming-style", "formatting"),
            artifact_root=artifact_root,
        )
    assert exc_info.value.error_code == "BLUEPRINT_GAP"


def test_blueprint_round_trip_when_complete(tmp_path):
    session_factory = _fresh_database(tmp_path)
    artifact_root = tmp_path / "artifacts"
    architecture, gate, matrix, saved = _create_blueprint(session_factory, artifact_root)
    assert saved.architecture_hash == architecture.artifact_hash
    assert saved.work_units[0].task_id == "wu-1"
    with session_factory() as session:
        reloaded = load_mechanical_engineering_blueprint(
            session, "bp-1", artifact_root=artifact_root
        )
    assert reloaded == saved
    assert reloaded.escalated_decision_ids == ()


def test_decision_escalation_rule():
    assert (
        validate_decision_escalation(
            escalated_decision_ids=("public-api",),
            ordinary_decision_ids=("naming",),
        )
        == ()
    )
    blockers = validate_decision_escalation(
        escalated_decision_ids=("naming",),
        ordinary_decision_ids=("naming",),
    )
    assert blockers
    assert "普通实现选择不得上抛" in blockers[0]


def test_blueprint_completeness_blocker_metrics():
    blockers = blueprint_completeness_blockers(
        _blueprint_for_metrics(),
        requirements_total=2,
        requirements_to_design=1,
        requirements_to_task=2,
        critical_requirements_total=2,
        critical_requirements_to_test=2,
        public_interfaces_total=1,
        public_interfaces_with_schema=1,
        unresolved_product_decisions=1,
        unresolved_architecture_decisions=0,
        broken_diagram_references=0,
    )
    assert any("requirements_traced_to_design" in blocker for blocker in blockers)
    assert any("unresolved_product_decisions" in blocker for blocker in blockers)


def _blueprint_for_metrics() -> MechanicalEngineeringBlueprint:
    return MechanicalEngineeringBlueprint(
        blueprint_id="bp-m",
        version=1,
        project_id="p-1",
        architecture_baseline_id="ab-1",
        architecture_hash="a" * 64,
        project_tree={"src": "impl"},
        file_level_changes={"added": ("src/x.py",)},
        modules_and_symbols={},
        dependency_lock_policy="uv.lock",
        config_secret_env_policy="env",
        data_migration_rollback_policy="events",
        runtime_flow_specs={},
        non_functional_requirements=(),
        command_templates={},
        traceability={},
        risk_register=(),
        stop_and_escalation_conditions=(),
        pending_generated_artifacts=(),
        work_units=(_work_unit("wu-1"),),
    )


# ---------------------------------------------------------------------------
# Export bundle (03B, section 13.2)
# ---------------------------------------------------------------------------


def test_export_bundle_verifies_and_is_deterministic():
    files = {
        "01_executive_summary.md": b"# Summary\n",
        "07_implementation_blueprint/project_tree.md": b"src/ -> implementation\n",
        "06_diagrams/rendered/context.svg": b"<svg/>\n",
    }
    first = ExportBundle.create(bundle_id="b-1", project_id="p-1", files=files)
    second = ExportBundle.create(bundle_id="b-1", project_id="p-1", files=files)
    assert first == second
    assert first.bundle_hash == second.bundle_hash
    assert verify_export_bundle(first, files) == ()
    roles = {item.path: item.role for item in first.items}
    assert roles["01_executive_summary.md"] == MANIFEST_ROLE_EXECUTIVE_SUMMARY
    assert roles["06_diagrams/rendered/context.svg"] == MANIFEST_ROLE_DIAGRAM_RENDERED


def test_export_bundle_detects_tamper():
    files = {
        "01_executive_summary.md": b"# Summary\n",
        "07_implementation_blueprint/project_tree.md": b"src/ -> implementation\n",
    }
    bundle = ExportBundle.create(bundle_id="b-1", project_id="p-1", files=files)
    tampered = dict(files)
    tampered["01_executive_summary.md"] = b"# Tampered\n"
    blockers = verify_export_bundle(bundle, tampered)
    assert any("checksum" in blocker for blocker in blockers)
    missing = verify_export_bundle(bundle, {})
    assert any("缺失" in blocker for blocker in missing)
