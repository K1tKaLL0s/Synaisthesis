"""M2.11 integration tests: ENG8 -> ENG10 delivery and export (03B sections 11-13)."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config

from synaisthesis.application.engineering_delivery_audit_service import (
    engineering_delivery_readiness_blockers,
    open_engineering_delivery_acceptance,
    resolve_engineering_delivery_acceptance,
    run_engineering_delivery_audit,
)
from synaisthesis.application.engineering_design_service import (
    create_architecture_baseline,
    create_engineering_mission_charter,
    create_engineering_requirements_baseline,
    create_mechanical_engineering_blueprint,
    create_operational_concept_bundle,
    create_option_trade_study,
    open_engineering_architecture_review,
    resolve_engineering_architecture_review,
)
from synaisthesis.application.publication_service import (
    audit_engineering_master_manuscript,
    create_engineering_master_manuscript,
    create_venue_adapted_manuscript,
    open_formal_manuscript_decision,
    open_publication_profile_selection,
    resolve_formal_manuscript_decision,
    resolve_publication_profile_selection,
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
    EngineeringDeliveryStatus,
    EngineeringMissionCharter,
    EngineeringWorkUnitContract,
    ExternalDependency,
    MechanicalEngineeringBlueprint,
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
from synaisthesis.domain.gate import EngineeringGate
from synaisthesis.domain.publication import (
    AUTHOR_INPUT_NEEDS,
    ClaimEvidenceEntry,
    ClaimEvidenceMatrix,
    EngineeringEvidenceTier,
    EngineeringMasterManuscript,
    EngineeringPaperType,
    VenueComplianceEntry,
    VenueComplianceMatrix,
    VenueComplianceStatus,
)
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
from synaisthesis.publication.adaptation import VenueAdaptedManuscriptStatus
from synaisthesis.renderers.diagram_renderers import DiagramSource
from synaisthesis.storage.database import init_database
from synaisthesis.storage.export_bundle import ExportBundle, verify_export_bundle

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

AUTHOR_FIELDS = (
    "author_contributions",
    "ai_use_disclosure",
    "funding",
    "conflicts",
    "acknowledgements",
)


def _fresh_database(tmp_path: Path):
    db_url = f"sqlite:///{tmp_path / 'delivery.db'}"
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


def _work_unit(task_id: str) -> EngineeringWorkUnitContract:
    return EngineeringWorkUnitContract(
        task_id=task_id,
        unique_objective="实现 " + task_id,
        authoritative_inputs=("03B §8",),
        preconditions_gates_environment=("架构已批准",),
        allowed_files=("src/core.py",),
        forbidden_files=(),
        io_contracts=("compute_trace(m) -> float",),
        invariants=("不修改输入",),
        step_actions=("新增 compute_trace 函数",),
        errors_boundaries_compat_rollback=("类型错误返回 DomainError",),
        focused_tests=("test_compute_trace.py",),
        full_checks=("pytest/ruff/basedpyright",),
        acceptance_criteria=("focused 测试通过",),
        stop_escalation_conditions=("失败即停",),
        delivery_format="diff + 回执",
    )


def _blueprint(architecture: ArchitectureBaseline) -> MechanicalEngineeringBlueprint:
    return MechanicalEngineeringBlueprint(
        blueprint_id="bp-1",
        version=1,
        project_id="p-1",
        architecture_baseline_id=architecture.baseline_id,
        architecture_hash=architecture.artifact_hash or "",
        project_tree={"src": "implementation"},
        file_level_changes={"added": ("src/core.py",)},
        modules_and_symbols={"core": ("compute_trace",)},
        dependency_lock_policy="uv.lock",
        config_secret_env_policy="env only",
        data_migration_rollback_policy="events",
        runtime_flow_specs={"run": "cli -> core"},
        non_functional_requirements=("latency",),
        command_templates={"test": "pytest"},
        traceability={"R1": ("d-1", "t-1", "test-1"), "R2": ("d-2", "t-2", "test-2")},
        risk_register=("float error",),
        stop_and_escalation_conditions=("BLUEPRINT_GAP 即停",),
        pending_generated_artifacts=("README.md",),
        work_units=(_work_unit("wu-1"), _work_unit("wu-2")),
    )


def _manuscript() -> EngineeringMasterManuscript:
    return EngineeringMasterManuscript(
        manuscript_id="ms-1",
        version=1,
        project_id="p-1",
        paper_type=EngineeringPaperType.DESIGN_ARTICLE,
        evidence_tier=EngineeringEvidenceTier.BLUEPRINT_ONLY,
        title="Design of a reproducible trace tool",
        abstract="abstract",
        keywords=("design",),
        statement_of_need="need",
        related_work_neighbors=("n1",),
        requirements_conops_design="section",
        method_architecture="section",
        vv_methods="section",
        results="no results",
        comparison_with_baseline="none",
        threats_limitations="limits",
        application_extension="none",
        security_privacy_ethics="none",
        data_availability="none",
        reproducibility_instructions="steps",
        conclusion="conclusion",
        references=("r1",),
        author_contributions=AUTHOR_INPUT_NEEDS,
        ai_use_disclosure=AUTHOR_INPUT_NEEDS,
        funding=AUTHOR_INPUT_NEEDS,
        conflicts=AUTHOR_INPUT_NEEDS,
        acknowledgements=AUTHOR_INPUT_NEEDS,
        author_input_status={field: AUTHOR_INPUT_NEEDS for field in AUTHOR_FIELDS},
        claim_ids=("claim-1",),
    )


def _claim_matrix() -> ClaimEvidenceMatrix:
    return ClaimEvidenceMatrix(
        matrix_id="cem-1",
        project_id="p-1",
        entries=(
            ClaimEvidenceEntry(
                claim_id="claim-1",
                statement="蓝图覆盖所有关键需求（计划）",
                source_requirement_id="R1",
                design_element_id="d-1",
                evidence_receipt_id=None,
                figure_table_ref=None,
                citation_ref=None,
            ),
        ),
    )


def _run_to_blueprint(session_factory, artifact_root: Path):
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
        approval = resolve_engineering_architecture_review(
            session,
            gate=gate,
            decision="APPROVE_BASELINE",
            actor=ProvenanceType.USER_DECISION,
            user_event_id="uev-approve",
            current_baseline=architecture,
            at=NOW,
            artifact_root=artifact_root,
        )
        blueprint = create_mechanical_engineering_blueprint(
            session,
            project_id="p-1",
            architecture=architecture,
            architecture_approval=approval,
            matrix=_matrix(),
            blueprint=_blueprint(architecture),
            artifact_root=artifact_root,
        )
        session.commit()
    return blueprint


def _run_to_audited_master(session_factory, artifact_root: Path):
    _run_to_blueprint(session_factory, artifact_root)
    with session_factory() as session:
        manuscript = create_engineering_master_manuscript(
            session,
            project_id="p-1",
            manuscript=_manuscript(),
            claim_matrix=_claim_matrix(),
            artifact_root=artifact_root,
        )
        audited = audit_engineering_master_manuscript(
            session,
            project_id="p-1",
            manuscript=manuscript,
            auditor_session_id="auditor-1",
            draft_generator_session_ids=("generator-1",),
            findings=(("MINOR", "措辞建议"),),
            artifact_root=artifact_root,
        )
        session.commit()
    return audited


def _resolve_formal(session_factory, artifact_root: Path, decision: str) -> EngineeringGate:
    manuscript = _run_to_audited_master(session_factory, artifact_root)
    with session_factory() as session:
        gate = open_formal_manuscript_decision(
            session,
            project_id="p-1",
            manuscript=manuscript,
            delivery_hash="d" * 64,
            artifact_root=artifact_root,
            gate_id="gate-fm-1",
        )
        resolved = resolve_formal_manuscript_decision(
            session,
            gate=gate,
            decision=decision,
            actor=ProvenanceType.USER_DECISION,
            user_event_id="uev-fm",
            manuscript=manuscript,
            at=NOW,
            artifact_root=artifact_root,
        )
        session.commit()
    return resolved


def test_keep_master_only_full_delivery_and_export(tmp_path):
    session_factory = _fresh_database(tmp_path)
    artifact_root = tmp_path / "artifacts"
    formal = _resolve_formal(session_factory, artifact_root, "KEEP_MASTER_ONLY")
    assert formal.decision == "KEEP_MASTER_ONLY"

    with session_factory() as session:
        status, blockers = run_engineering_delivery_audit(
            session,
            project_id="p-1",
            auditor_session_id="delivery-auditor",
            draft_generator_session_ids=("generator-1", "auditor-1"),
            findings=(("INFO", "none"),),
            artifact_root=artifact_root,
        )
        session.commit()
    assert status is EngineeringDeliveryStatus.ENGINEERING_DELIVERY_CANDIDATE
    assert blockers == ()

    readiness = engineering_delivery_readiness_blockers(
        stages_not_blocked=True,
        blueprint_gate_ok=True,
        diagrams_rerenderable=True,
        vv_plans_complete=True,
        master_complete=True,
        master_audited_and_delivered=True,
        keep_master_only=True,
        formal_requested=False,
        profile_fresh=True,
        compliance_ok=True,
        no_fabricated_results=True,
        audit_clean=True,
        acceptance_bound=False,
    )
    assert readiness  # acceptance is not yet bound

    files = {
        "00_manifest.yaml": b"manifest: placeholder\n",
        "01_executive_summary.md": b"# Summary\n",
        "07_implementation_blueprint/project_tree.md": b"src/ -> implementation\n",
        "11_publication/master_manuscript.md": b"# Master\n",
        "11_publication/master_audit.yaml": b"audit: clean\n",
        "11_publication/formal_manuscript_decision.yaml": b"decision: KEEP_MASTER_ONLY\n",
        "14_checksums.sha256": b"",
    }
    bundle = ExportBundle.create(bundle_id="delivery-1", project_id="p-1", files=files)
    assert verify_export_bundle(bundle, files) == ()
    roles = {item.path: item.role for item in bundle.items}
    assert roles["11_publication/master_manuscript.md"] == "master_manuscript"
    assert roles["14_checksums.sha256"] == "checksums"

    with session_factory() as session:
        gate = open_engineering_delivery_acceptance(
            session,
            project_id="p-1",
            manifest_hash=bundle.bundle_hash,
            artifact_root=artifact_root,
            gate_id="gate-da-1",
        )
        accepted = resolve_engineering_delivery_acceptance(
            session,
            gate=gate,
            decision="ACCEPT",
            actor=ProvenanceType.USER_DECISION,
            user_event_id="uev-accept",
            current_manifest_hash=bundle.bundle_hash,
            at=NOW,
            artifact_root=artifact_root,
        )
        session.commit()
    assert accepted.status is GateStatus.RESOLVED

    final_readiness = engineering_delivery_readiness_blockers(
        stages_not_blocked=True,
        blueprint_gate_ok=True,
        diagrams_rerenderable=True,
        vv_plans_complete=True,
        master_complete=True,
        master_audited_and_delivered=True,
        keep_master_only=True,
        formal_requested=False,
        profile_fresh=True,
        compliance_ok=True,
        no_fabricated_results=True,
        audit_clean=True,
        acceptance_bound=True,
    )
    assert final_readiness == ()


def test_acceptance_invalidated_by_manifest_change(tmp_path):
    session_factory = _fresh_database(tmp_path)
    artifact_root = tmp_path / "artifacts"
    _resolve_formal(session_factory, artifact_root, "KEEP_MASTER_ONLY")
    files = {"01_executive_summary.md": b"# Summary\n"}
    bundle = ExportBundle.create(bundle_id="delivery-2", project_id="p-1", files=files)
    with session_factory() as session:
        gate = open_engineering_delivery_acceptance(
            session,
            project_id="p-1",
            manifest_hash=bundle.bundle_hash,
            artifact_root=artifact_root,
            gate_id="gate-da-1",
        )
        with pytest.raises(DomainError) as exc_info:
            resolve_engineering_delivery_acceptance(
                session,
                gate=gate,
                decision="ACCEPT",
                actor=ProvenanceType.USER_DECISION,
                user_event_id="uev-accept",
                current_manifest_hash="0" * 64,  # manifest changed
                at=NOW,
                artifact_root=artifact_root,
            )
    assert exc_info.value.error_code == "STALE_DELIVERY_ACCEPTANCE"


def test_write_path_selects_profile_and_adapts(tmp_path):
    session_factory = _fresh_database(tmp_path)
    artifact_root = tmp_path / "artifacts"
    write_gate = _resolve_formal(session_factory, artifact_root, "WRITE_FORMAL_MANUSCRIPT")
    assert write_gate.decision == "WRITE_FORMAL_MANUSCRIPT"

    manuscript = _run_to_audited_master(session_factory, artifact_root)
    with session_factory() as session:
        selection = open_publication_profile_selection(
            session,
            project_id="p-1",
            formal_decision=write_gate,
            manuscript=manuscript,
            artifact_root=artifact_root,
            gate_id="gate-ps-1",
        )
        resolved, profile = resolve_publication_profile_selection(
            session,
            gate=selection,
            decision="ENG_IEEE_TSE",
            actor=ProvenanceType.USER_DECISION,
            user_event_id="uev-ps",
            project_kind="software",
            now=NOW,
            manuscript=manuscript,
            software_evidence=None,
            artifact_root=artifact_root,
        )
        assert resolved.decision == "ENG_IEEE_TSE"
        assert profile.profile_id == "ENG_IEEE_TSE"

        adapted = create_venue_adapted_manuscript(
            session,
            project_id="p-1",
            manuscript=manuscript,
            profile=profile,
            compliance_matrix=VenueComplianceMatrix(
                matrix_id="cm-1",
                project_id="p-1",
                profile_id="ENG_IEEE_TSE",
                entries=(
                    VenueComplianceEntry(
                        requirement_id="template",
                        status=VenueComplianceStatus.PASS,
                        evidence_ref="section 3",
                    ),
                ),
            ),
            adapted_text="# Adapted for TSE\n",
            artifact_root=artifact_root,
        )
        session.commit()
    assert adapted.status is VenueAdaptedManuscriptStatus.FORMAL_MANUSCRIPT_READY
    assert adapted.master_hash == manuscript.master_hash
    assert adapted.profile_id == "ENG_IEEE_TSE"


def test_arxiv_path_is_package_ready_only(tmp_path):
    session_factory = _fresh_database(tmp_path)
    artifact_root = tmp_path / "artifacts"
    write_gate = _resolve_formal(session_factory, artifact_root, "WRITE_FORMAL_MANUSCRIPT")
    manuscript = _run_to_audited_master(session_factory, artifact_root)
    with session_factory() as session:
        selection = open_publication_profile_selection(
            session,
            project_id="p-1",
            formal_decision=write_gate,
            manuscript=manuscript,
            artifact_root=artifact_root,
            gate_id="gate-ps-1",
        )
        resolved, arxiv = resolve_publication_profile_selection(
            session,
            gate=selection,
            decision="ENG_ARXIV_PREPRINT",
            actor=ProvenanceType.USER_DECISION,
            user_event_id="uev-ps",
            project_kind="software",
            now=NOW,
            manuscript=manuscript,
            software_evidence=None,
            artifact_root=artifact_root,
        )
        adapted = create_venue_adapted_manuscript(
            session,
            project_id="p-1",
            manuscript=manuscript,
            profile=arxiv,
            compliance_matrix=VenueComplianceMatrix(
                matrix_id="cm-2",
                project_id="p-1",
                profile_id="ENG_ARXIV_PREPRINT",
                entries=(
                    VenueComplianceEntry(
                        requirement_id="preprint",
                        status=VenueComplianceStatus.NOT_APPLICABLE,
                        evidence_ref=None,
                    ),
                ),
            ),
            adapted_text="# Preprint\n",
            artifact_root=artifact_root,
        )
        session.commit()
    assert adapted.status is VenueAdaptedManuscriptStatus.ARXIV_PACKAGE_READY
