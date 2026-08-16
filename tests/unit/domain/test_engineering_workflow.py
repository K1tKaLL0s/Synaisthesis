"""M2.8 domain tests for the ENG0-ENG10 engineering workflow domain (03B)."""

from __future__ import annotations

import dataclasses
from datetime import UTC, datetime

import pytest

from synaisthesis.domain.engineering import (
    BLUEPRINT_VAGUE_PATTERNS,
    EARLIEST_ROLLBACK,
    STAGE_ORDER,
    ApplicationDirection,
    ApplicationDirectionPortfolio,
    ApplicationHorizon,
    EngineeringArtifactStatus,
    EngineeringChangeKind,
    EngineeringDeliveryAcceptanceDecision,
    EngineeringDeliveryMode,
    EngineeringDeliveryStatus,
    EngineeringGateType,
    EngineeringMissionCharter,
    EngineeringProfileChoice,
    EngineeringStageId,
    EngineeringWorkUnitContract,
    ExtensionRoadmap,
    ExtensionRoadmapItem,
    FormalManuscriptDecision,
    MechanicalEngineeringBlueprint,
    OperationalConceptBundle,
    OperationalScenario,
    OptionTradeStudy,
    PrototypeExecutionAuthorizationDecision,
    RejectedOptionLog,
    StakeholderEntry,
    TechnologySelectionRecord,
    TradeStudyOption,
    build_engineering_event,
    charter_scope_changes,
    conops_blockers,
    delivery_status_for_stage,
    eng0_entry_blockers,
    engineering_next_stage,
    engineering_regression_check,
    superseded,
    trade_study_blockers,
    validate_technology_selection,
)
from synaisthesis.domain.enums import (
    EngineeringRouteDecision,
    NoveltyStatus,
    ProvenanceType,
    ResearchRoute,
)
from synaisthesis.domain.errors import DomainError
from synaisthesis.domain.gate import (
    EngineeringGate,
    EngineeringGateBinding,
    engineering_allowed_decisions_for_gate,
)
from synaisthesis.domain.novelty import LowNoveltyOverride
from synaisthesis.domain.qualification import (
    EngineeringRouteSelection,
    UserEngineeringConceptApproval,
)

NOW = datetime(2026, 8, 17, 2, 0, 0, tzinfo=UTC)
SPEC_HASH = "s" * 64
CONCEPT_HASH = "c" * 64
REVIEW_HASH = "r" * 64
ASSESSMENT_HASH = "a" * 64

BASELINE_SCOPE = {
    "object_domain": ["finite_matrices"],
    "intended_users": ["researchers"],
    "core_functions": ["compute_trace"],
    "data_classification": ["public"],
    "engineering_goals": ["cli_tool"],
}


def _route_selection(
    decision: EngineeringRouteDecision = EngineeringRouteDecision.TRY_ENGINEERING_PROJECT,
):
    return EngineeringRouteSelection(
        id="rs-1",
        project_id="p-1",
        feasibility_assessment_id="fa-1",
        decision=decision,
        user_actor_id="u-1",
        decision_event_id="ev-rs",
        bound_assessment_hash=ASSESSMENT_HASH,
        input_spec_hash=SPEC_HASH,
        created_at=NOW,
    )


def _concept_approval(concept_hash: str = CONCEPT_HASH, route_selection_id: str = "rs-1"):
    return UserEngineeringConceptApproval(
        concept_id="c-1",
        version=1,
        concept_hash=concept_hash,
        route_selection_id=route_selection_id,
        input_spec_hash=SPEC_HASH,
        route=ResearchRoute.ENGINEERING,
        actor=ProvenanceType.USER_DECISION,
        user_event_id="uev-concept",
        decided_at=NOW,
    )


def _override(review_hash: str = REVIEW_HASH):
    return LowNoveltyOverride(
        review_id="nr-1",
        route=ResearchRoute.ENGINEERING,
        review_artifact_hash=review_hash,
        actor=ProvenanceType.USER_DECISION,
        user_event_id="uev-override",
        decided_at=NOW,
    )


def _entry_blockers(**overrides):
    params = {
        "bound_input_spec_hash": SPEC_HASH,
        "current_input_spec_hash": SPEC_HASH,
        "route_selection": _route_selection(),
        "concept_approval": _concept_approval(),
        "concept_hash": CONCEPT_HASH,
        "novelty_status": NoveltyStatus.ENGINEERING_NOVELTY_QUALIFIED,
        "novelty_review_hash": REVIEW_HASH,
        "override": None,
        "open_gate_types": (),
    }
    params.update(overrides)
    return eng0_entry_blockers(**params)


def _charter(**overrides):
    params = {
        "charter_id": "ch-1",
        "version": 1,
        "project_id": "p-1",
        "source_artifact_hashes": (SPEC_HASH, CONCEPT_HASH),
        "problem_statement": "提供可复算的矩阵迹计算工具",
        "stakeholders": ("academia",),
        "intended_users": ("researchers",),
        "operational_context": "命令行环境",
        "system_of_interest_boundary": "计算内核",
        "objectives": ("可复现",),
        "non_goals": ("GUI",),
        "success_metrics": ("100% 复现",),
        "constraints": ("Python 3.11+",),
        "assumptions": ("离线可用",),
        "regulatory_security_ethics_flags": (),
        "delivery_mode": EngineeringDeliveryMode.BLUEPRINT_ONLY,
        "baseline_scope": dict(BASELINE_SCOPE),
        "charter_scope": dict(BASELINE_SCOPE),
        "proposed_additions": (),
    }
    params.update(overrides)
    return EngineeringMissionCharter(**params)


# ---------------------------------------------------------------------------
# ENG0 entry precondition (03B section 1.1)
# ---------------------------------------------------------------------------


def test_eng0_requires_user_route_decision():
    blockers = _entry_blockers(route_selection=None)
    assert blockers
    assert any("工程路线未由用户选择" in blocker for blocker in blockers)
    blockers = _entry_blockers(
        route_selection=_route_selection(EngineeringRouteDecision.REVISE_FOR_THEORY)
    )
    assert any("TRY_ENGINEERING_PROJECT" in blocker for blocker in blockers)


def test_eng0_rejects_non_engineering_novelty():
    blockers = _entry_blockers(novelty_status=NoveltyStatus.NOVELTY_QUALIFIED)
    assert any("ENGINEERING_NOVELTY_QUALIFIED" in blocker for blocker in blockers)
    blockers = _entry_blockers(novelty_status=NoveltyStatus.NOVELTY_RESEARCH_REQUIRED)
    assert blockers


def test_eng0_allows_engineering_qualified():
    assert _entry_blockers() == ()


def test_eng0_allows_bound_user_override():
    blockers = _entry_blockers(
        novelty_status=NoveltyStatus.USER_OVERRIDDEN_BELOW_THRESHOLD,
        override=_override(),
    )
    assert blockers == ()


def test_eng0_rejects_unbound_or_stale_override():
    blockers = _entry_blockers(
        novelty_status=NoveltyStatus.USER_OVERRIDDEN_BELOW_THRESHOLD,
        override=_override(review_hash="x" * 64),
    )
    assert blockers
    blockers = _entry_blockers(
        novelty_status=NoveltyStatus.USER_OVERRIDDEN_BELOW_THRESHOLD,
        override=_override(),
        novelty_review_hash=None,
    )
    assert blockers


def test_eng0_rejects_changed_s1_s4_hash():
    blockers = _entry_blockers(current_input_spec_hash="t" * 64)
    assert any("S1/S4" in blocker for blocker in blockers)


def test_eng0_rejects_missing_concept_approval_or_hash_mismatch():
    assert _entry_blockers(concept_approval=None)
    blockers = _entry_blockers(concept_hash="z" * 64)
    assert any("concept hash" in blocker for blocker in blockers)


def test_eng0_rejects_unresolved_gates():
    blockers = _entry_blockers(open_gate_types=("PRIVACY_GATE", "ETHICS_GATE"))
    assert any("PRIVACY_GATE" in blocker for blocker in blockers)


# ---------------------------------------------------------------------------
# ENG0 charter (03B section 3)
# ---------------------------------------------------------------------------


def test_charter_accepts_unchanged_baseline():
    charter = _charter()
    assert charter.artifact_hash
    assert len(charter.artifact_hash) == 64
    assert charter.status is EngineeringArtifactStatus.ACTIVE


def test_charter_rejects_unrecorded_scope_change():
    scope = dict(BASELINE_SCOPE)
    scope["core_functions"] = ["compute_trace", "deploy_cloud"]
    with pytest.raises(DomainError) as exc_info:
        _charter(charter_scope=scope)
    assert exc_info.value.error_code == "ENGINEERING_SCOPE_CHANGE"


def test_charter_accepts_recorded_proposed_addition():
    scope = dict(BASELINE_SCOPE)
    scope["core_functions"] = ["compute_trace", "deploy_cloud"]
    charter = _charter(charter_scope=scope, proposed_additions=("deploy_cloud",))
    assert charter.artifact_hash


def test_charter_rejects_undecided_build_mode():
    with pytest.raises(DomainError) as exc_info:
        _charter(delivery_mode=EngineeringDeliveryMode.BUILD_AND_EVALUATE)
    assert exc_info.value.error_code == "ENGINEERING_DELIVERY_MODE_INVALID"


def test_charter_hash_tamper_detected():
    with pytest.raises(DomainError) as exc_info:
        _charter(artifact_hash="0" * 64)
    assert exc_info.value.error_code == "ARTIFACT_HASH_MISMATCH"


def test_artifact_is_immutable_and_supersede_preserves_history():
    charter = _charter()
    superseded_charter = superseded(charter)
    assert superseded_charter.status is EngineeringArtifactStatus.SUPERSEDED
    assert charter.status is EngineeringArtifactStatus.ACTIVE
    with pytest.raises(dataclasses.FrozenInstanceError):
        charter.problem_statement = "mutated"  # type: ignore[misc]


# ---------------------------------------------------------------------------
# ENG1 ConOps (03B section 4)
# ---------------------------------------------------------------------------


def _conops(**overrides):
    from synaisthesis.domain.engineering import ExternalDependency

    params = {
        "conops_id": "co-1",
        "version": 1,
        "project_id": "p-1",
        "charter_id": "ch-1",
        "input_spec_hash": SPEC_HASH,
        "charter_hash": "c" * 64,
        "stakeholder_map": (
            StakeholderEntry(
                stakeholder_id="st-1",
                role="operator",
                responsibility_boundary="run",
                is_operator=True,
                intended_user_refs=("u-1",),
            ),
        ),
        "scenarios": (
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
        "system_context": "single CLI",
        "external_systems": (
            ExternalDependency(
                dependency_id="d-1", owner="owner", failure_mode="down", fallback="retry"
            ),
        ),
        "data_sources": (),
        "trust_boundaries": ("local",),
        "human_intervention_points": ("review",),
        "environment_assumptions": ("offline",),
        "quality_requirements": ("latency",),
        "unresolved_issues": (),
        "decision_owners": ("user",),
        "expected_functions": ("f-1",),
        "intended_user_ids": ("u-1",),
        "intent_refs": ("intent-1",),
    }
    params.update(overrides)
    return OperationalConceptBundle(**params)


def test_conops_blocks_uncovered_function_and_unmapped_user():
    from synaisthesis.domain.engineering import ExternalDependency

    bundle = _conops(
        expected_functions=("f-1", "f-2"),
        external_systems=(
            ExternalDependency(dependency_id="d-1", owner="", failure_mode="", fallback=""),
        ),
    )
    blockers = conops_blockers(bundle)
    assert any("f-2" in blocker for blocker in blockers)
    assert any("d-1" in blocker for blocker in blockers)


def test_conops_blocks_scenario_without_trust_zone():
    from synaisthesis.domain.engineering import ExternalDependency

    bundle = _conops(
        external_systems=(
            ExternalDependency(
                dependency_id="d-1", owner="owner", failure_mode="down", fallback="retry"
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
                external_dependency_refs=("d-1",),
                trust_zone=None,
            ),
        ),
    )
    blockers = conops_blockers(bundle)
    assert any("trust zone" in blocker for blocker in blockers)


def test_conops_passes_when_complete():
    from synaisthesis.domain.engineering import ExternalDependency

    bundle = _conops(
        external_systems=(
            ExternalDependency(
                dependency_id="d-1", owner="owner", failure_mode="down", fallback="retry"
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
                external_dependency_refs=("d-1",),
                trust_zone="local",
            ),
        ),
    )
    assert conops_blockers(bundle) == ()


# ---------------------------------------------------------------------------
# ENG3 trade study (03B section 6)
# ---------------------------------------------------------------------------


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


def _study(**overrides):
    params = {
        "study_id": "ts-1",
        "version": 1,
        "project_id": "p-1",
        "requirements_baseline_id": "rb-1",
        "critical_requirement_ids": ("R1", "R2"),
        "criteria": ("cost", "coverage"),
        "weights": {"cost": 0.5, "coverage": 0.5},
        "weights_derivation_ref": "rb-1#weights",
        "options": (
            _option("A", ("R1", "R2"), 0.6, 0.6),
            _option("B", ("R1",), 0.9, 0.9),
        ),
        "eliminated_option_ids": ("B",),
    }
    params.update(overrides)
    return OptionTradeStudy(**params)


def test_trade_study_weights_must_sum_to_one():
    with pytest.raises(DomainError) as exc_info:
        _study(weights={"cost": 0.5, "coverage": 0.6})
    assert exc_info.value.error_code == "TRADE_STUDY_INVALID"


def test_trade_study_hard_eliminates_uncovered_critical():
    study = _study()
    assert study.eliminated_option_ids == ("B",)
    assert study.weighted_score("B") > study.weighted_score("A")
    assert study.eligible_ranking() == ("A",)
    assert trade_study_blockers(study, "rb-1") == ()


def test_trade_study_blockers_when_elimination_not_recorded():
    study = _study(eliminated_option_ids=())
    blockers = trade_study_blockers(study, "rb-1")
    assert blockers


def test_technology_selection_binds_study_hash_and_never_eliminated_option():
    study = _study()
    valid = TechnologySelectionRecord(
        selection_id="sel-1",
        study_id="ts-1",
        study_hash=study.artifact_hash or "",
        selected_option_id="A",
        rationale="covers all critical requirements",
        created_at=NOW,
    )
    assert validate_technology_selection(valid, study) == ()
    stale = TechnologySelectionRecord(
        selection_id="sel-2",
        study_id="ts-1",
        study_hash="0" * 64,
        selected_option_id="A",
        rationale="stale",
        created_at=NOW,
    )
    assert validate_technology_selection(stale, study)
    eliminated = TechnologySelectionRecord(
        selection_id="sel-3",
        study_id="ts-1",
        study_hash=study.artifact_hash or "",
        selected_option_id="B",
        rationale="nope",
        created_at=NOW,
    )
    assert validate_technology_selection(eliminated, study)


# ---------------------------------------------------------------------------
# ENG5 blueprint (03B section 8)
# ---------------------------------------------------------------------------


def test_work_unit_rejects_vague_wording():
    assert BLUEPRINT_VAGUE_PATTERNS
    with pytest.raises(DomainError) as exc_info:
        EngineeringWorkUnitContract(
            task_id="wu-1",
            unique_objective="实现 trace 计算",
            authoritative_inputs=("03B",),
            preconditions_gates_environment=(),
            allowed_files=("src/x.py",),
            forbidden_files=(),
            io_contracts=(),
            invariants=(),
            step_actions=("适当修改相关文件",),
            errors_boundaries_compat_rollback=(),
            focused_tests=(),
            full_checks=(),
            acceptance_criteria=("pytest 通过",),
            stop_escalation_conditions=("失败即停",),
            delivery_format="diff",
        )
    assert exc_info.value.error_code == "WORK_UNIT_INVALID"


def _work_unit(task_id: str, stop: tuple[str, ...] = ("失败即停",)):
    return EngineeringWorkUnitContract(
        task_id=task_id,
        unique_objective="实现 " + task_id,
        authoritative_inputs=("03B",),
        preconditions_gates_environment=(),
        allowed_files=(),
        forbidden_files=(),
        io_contracts=(),
        invariants=(),
        step_actions=("新增函数 compute_trace",),
        errors_boundaries_compat_rollback=(),
        focused_tests=(),
        full_checks=(),
        acceptance_criteria=("focused 测试通过",),
        stop_escalation_conditions=stop,
        delivery_format="diff",
    )


def _blueprint(**overrides):
    params = {
        "blueprint_id": "bp-1",
        "version": 1,
        "project_id": "p-1",
        "architecture_baseline_id": "ab-1",
        "architecture_hash": "a" * 64,
        "project_tree": {"src": "implementation"},
        "file_level_changes": {"added": ("src/x.py",)},
        "modules_and_symbols": {"x": ("compute_trace",)},
        "dependency_lock_policy": "uv.lock",
        "config_secret_env_policy": "env only",
        "data_migration_rollback_policy": "events",
        "runtime_flow_specs": {"run": "trace"},
        "non_functional_requirements": ("latency",),
        "command_templates": {"test": "pytest"},
        "traceability": {"R1": ("design-1", "task-1", "test-1")},
        "risk_register": ("risk-1",),
        "stop_and_escalation_conditions": ("blocker 即停",),
        "pending_generated_artifacts": ("README.md",),
        "work_units": (_work_unit("wu-1"),),
    }
    params.update(overrides)
    return MechanicalEngineeringBlueprint(**params)


def test_blueprint_gate_blockers():
    from synaisthesis.domain.engineering import blueprint_completeness_blockers

    blueprint = _blueprint(work_units=(_work_unit("wu-1", stop=()),))
    blockers = blueprint_completeness_blockers(
        blueprint,
        requirements_total=2,
        requirements_to_design=1,
        requirements_to_task=1,
        critical_requirements_total=1,
        critical_requirements_to_test=0,
        public_interfaces_total=1,
        public_interfaces_with_schema=0,
        unresolved_product_decisions=1,
        unresolved_architecture_decisions=0,
        broken_diagram_references=1,
    )
    assert blockers
    assert any("tasks_with_stop_condition" in blocker for blocker in blockers)
    assert any("unresolved_product_decisions" in blocker for blocker in blockers)


def test_blueprint_gate_passes_when_complete():
    from synaisthesis.domain.engineering import blueprint_completeness_blockers

    blockers = blueprint_completeness_blockers(
        _blueprint(),
        requirements_total=1,
        requirements_to_design=1,
        requirements_to_task=1,
        critical_requirements_total=1,
        critical_requirements_to_test=1,
        public_interfaces_total=0,
        public_interfaces_with_schema=0,
        unresolved_product_decisions=0,
        unresolved_architecture_decisions=0,
        broken_diagram_references=0,
    )
    assert blockers == ()


# ---------------------------------------------------------------------------
# ENG7 roadmap (03B section 10)
# ---------------------------------------------------------------------------


def test_application_direction_requires_metrics_barriers_and_evidence():
    base = {
        "direction_id": "ad-1",
        "users_stakeholders": ("researchers",),
        "problem_and_scenarios": "batch trace",
        "required_capabilities": ("compute",),
        "current_coverage": "partial",
        "conditions": ("offline",),
        "measurable_value_metrics": ("p50 latency",),
        "adoption_barriers": ("training",),
        "failure_modes": ("numeric overflow",),
        "evidence_tier": "BLUEPRINT_ONLY",
        "horizon": ApplicationHorizon.NEXT,
    }
    with pytest.raises(DomainError) as exc_info:
        ApplicationDirection(**{**base, "measurable_value_metrics": ()})
    assert exc_info.value.error_code == "APPLICATION_DIRECTION_INVALID"
    with pytest.raises(DomainError):
        ApplicationDirection(**{**base, "adoption_barriers": ()})
    with pytest.raises(DomainError):
        ApplicationDirection(**{**base, "evidence_tier": ""})
    assert ApplicationDirection(**base).direction_id == "ad-1"


def test_extension_roadmap_requires_rationale():
    with pytest.raises(DomainError) as exc_info:
        ExtensionRoadmapItem(
            extension_id="ex-1",
            goal="distributed mode",
            non_goals=(),
            trigger_conditions=("scale",),
            affected_refs=("R1",),
            compatibility_migration_strategy="v2 api",
            dependencies=(),
            risk_cost_level="high",
            reversibility="low",
            adr_or_task_suggestion="ADR-9",
            no_premature_coupling_rationale="",
        )
    assert exc_info.value.error_code == "EXTENSION_ROADMAP_INVALID"


def test_roadmap_artifacts_finalize_hash():
    portfolio = ApplicationDirectionPortfolio(
        portfolio_id="pf-1",
        version=1,
        project_id="p-1",
        directions=(
            ApplicationDirection(
                direction_id="ad-1",
                users_stakeholders=("researchers",),
                problem_and_scenarios="batch trace",
                required_capabilities=("compute",),
                current_coverage="partial",
                conditions=("offline",),
                measurable_value_metrics=("p50 latency",),
                adoption_barriers=("training",),
                failure_modes=("overflow",),
                evidence_tier="BLUEPRINT_ONLY",
                horizon=ApplicationHorizon.NEXT,
            ),
        ),
    )
    roadmap = ExtensionRoadmap(
        roadmap_id="rm-1",
        version=1,
        project_id="p-1",
        items=(
            ExtensionRoadmapItem(
                extension_id="ex-1",
                goal="distributed mode",
                non_goals=(),
                trigger_conditions=("scale",),
                affected_refs=("R1",),
                compatibility_migration_strategy="v2 api",
                dependencies=(),
                risk_cost_level="high",
                reversibility="low",
                adr_or_task_suggestion="ADR-9",
                no_premature_coupling_rationale="接口 v2 预留扩展点",
            ),
        ),
    )
    assert portfolio.artifact_hash is not None and len(portfolio.artifact_hash) == 64
    assert roadmap.artifact_hash is not None and len(roadmap.artifact_hash) == 64


# ---------------------------------------------------------------------------
# Stage mapping and events
# ---------------------------------------------------------------------------


def test_delivery_status_mapping_and_next_stage():
    assert delivery_status_for_stage(EngineeringStageId.ENG0) is (
        EngineeringDeliveryStatus.MISSION_BASELINING
    )
    assert delivery_status_for_stage(EngineeringStageId.ENG4) is (
        EngineeringDeliveryStatus.ARCHITECTURE_DESIGNING
    )
    assert delivery_status_for_stage(EngineeringStageId.ENG10) is (
        EngineeringDeliveryStatus.DELIVERY_AUDITING
    )
    chain = []
    stage: EngineeringStageId | None = EngineeringStageId.ENG0
    while stage is not None:
        chain.append(stage)
        stage = engineering_next_stage(stage)
    assert chain == list(STAGE_ORDER)
    assert engineering_next_stage(EngineeringStageId.ENG10) is None


def test_engineering_event_catalog():
    event = build_engineering_event(
        "EngineeringStageOpened",
        aggregate_type="EngineeringWorkflowRun",
        aggregate_id="run-1",
        payload={"stage": "ENG0"},
        sequence=1,
    )
    assert event.event_type == "EngineeringStageOpened"
    with pytest.raises(DomainError) as exc_info:
        build_engineering_event(
            "NotARealEvent",
            aggregate_type="x",
            aggregate_id="y",
            payload={},
            sequence=1,
        )
    assert exc_info.value.error_code == "UNKNOWN_EVENT_TYPE"


# ---------------------------------------------------------------------------
# Engineering gates (03B sections 7.4/11.4/13.3)
# ---------------------------------------------------------------------------


def _architecture_gate() -> EngineeringGate:
    return EngineeringGate(
        gate_id="gate-ar-1",
        project_id="p-1",
        gate_type=EngineeringGateType.ENGINEERING_ARCHITECTURE_REVIEW,
        binding=EngineeringGateBinding(
            gate_type=EngineeringGateType.ENGINEERING_ARCHITECTURE_REVIEW,
            artifact_id="ab-1",
            version=1,
            artifact_hash="a" * 64,
            bound_hashes={
                "requirements": "r" * 64,
                "trade_study": "t" * 64,
                "architecture": "a" * 64,
            },
        ),
    )


def test_architecture_review_gate_requires_real_user():
    gate = _architecture_gate()
    allowed = engineering_allowed_decisions_for_gate(
        EngineeringGateType.ENGINEERING_ARCHITECTURE_REVIEW
    )
    assert "APPROVE_BASELINE" in allowed
    assert "RETURN_TO_TRADE_STUDY" in allowed
    with pytest.raises(DomainError) as exc_info:
        gate.resolve(
            decision="APPROVE_BASELINE",
            actor=ProvenanceType.ASSISTANT_PROPOSAL,
            user_event_id="ev-1",
            at=NOW,
        )
    assert exc_info.value.error_code == "CONFIRMATION_REQUIRES_USER_EVENT"
    with pytest.raises(DomainError) as exc_info:
        gate.resolve(
            decision="MAYBE",
            actor=ProvenanceType.USER_DECISION,
            user_event_id="ev-1",
            at=NOW,
        )
    assert exc_info.value.error_code == "INVALID_GATE_DECISION"
    resolved = gate.resolve(
        decision="APPROVE_BASELINE",
        actor=ProvenanceType.USER_DECISION,
        user_event_id="ev-1",
        at=NOW,
    )
    assert resolved.decision == "APPROVE_BASELINE"
    assert resolved.resolved_at == NOW


def test_formal_manuscript_decision_gate():
    gate = EngineeringGate(
        gate_id="gate-fm-1",
        project_id="p-1",
        gate_type=EngineeringGateType.FORMAL_MANUSCRIPT_DECISION,
        binding=EngineeringGateBinding(
            gate_type=EngineeringGateType.FORMAL_MANUSCRIPT_DECISION,
            artifact_id="ms-1",
            version=1,
            artifact_hash="m" * 64,
            bound_hashes={"master_manuscript": "m" * 64, "delivery": "d" * 64},
        ),
    )
    for decision in (
        FormalManuscriptDecision.KEEP_MASTER_ONLY.value,
        FormalManuscriptDecision.WRITE_FORMAL_MANUSCRIPT.value,
    ):
        assert (
            gate.resolve(
                decision=decision,
                actor=ProvenanceType.USER_DECISION,
                user_event_id="ev-2",
                at=NOW,
            ).decision
            == decision
        )


def test_profile_selection_and_delivery_acceptance_decisions():
    profile_decisions = engineering_allowed_decisions_for_gate(
        EngineeringGateType.PUBLICATION_PROFILE_SELECTION
    )
    assert EngineeringProfileChoice.ENG_IEEE_TSE.value in profile_decisions
    assert EngineeringProfileChoice.ENG_ARXIV_PREPRINT.value in profile_decisions
    acceptance = engineering_allowed_decisions_for_gate(
        EngineeringGateType.ENGINEERING_DELIVERY_ACCEPTANCE
    )
    assert EngineeringDeliveryAcceptanceDecision.ACCEPT.value in acceptance
    prototype = engineering_allowed_decisions_for_gate(
        EngineeringGateType.PROTOTYPE_EXECUTION_AUTHORIZATION
    )
    assert PrototypeExecutionAuthorizationDecision.AUTHORIZE.value in prototype


def test_engineering_gate_binding_requires_hashes():
    with pytest.raises(DomainError) as exc_info:
        EngineeringGateBinding(
            gate_type=EngineeringGateType.ENGINEERING_ARCHITECTURE_REVIEW,
            artifact_id="ab-1",
            version=1,
            artifact_hash="a" * 64,
            bound_hashes={},
        )
    assert exc_info.value.error_code == "GATE_BINDING_INVALID"


# ---------------------------------------------------------------------------
# Regression mapping (03B section 14)
# ---------------------------------------------------------------------------


def test_regression_mapping_is_deterministic_and_earliest():
    for kind, stage in EARLIEST_ROLLBACK.items():
        result = engineering_regression_check((kind,))
        assert result.requires_regression
        assert result.earliest_rollback_stage is stage
        assert result.status is EngineeringDeliveryStatus.NEEDS_REGRESSION
    s1_result = engineering_regression_check((EngineeringChangeKind.S1_S4_CORE_SEMANTICS,))
    assert s1_result.requires_reentry


def test_regression_combined_change_takes_earliest_stage():
    result = engineering_regression_check(
        (
            EngineeringChangeKind.VENUE_GUIDANCE_UPDATE,
            EngineeringChangeKind.REQUIREMENT_OR_THRESHOLD,
        )
    )
    assert result.earliest_rollback_stage is EngineeringStageId.ENG2
    assert result.requires_reentry is False


def test_regression_no_change_is_no_op():
    result = engineering_regression_check(())
    assert result.requires_regression is False
    assert result.earliest_rollback_stage is None


def test_scope_change_detector():
    assert (
        charter_scope_changes(
            baseline_scope=BASELINE_SCOPE,
            charter_scope=BASELINE_SCOPE,
            proposed_additions=(),
        )
        == ()
    )
    scope = dict(BASELINE_SCOPE)
    scope["intended_users"] = ["clinicians"]
    changes = charter_scope_changes(
        baseline_scope=BASELINE_SCOPE,
        charter_scope=scope,
        proposed_additions=(),
    )
    assert changes == ("intended_users",)


def test_rejected_option_log_serializes():
    log = RejectedOptionLog(study_id="ts-1", rejected_options=(("B", "不覆盖 R2"),))
    assert log.to_event_payload()["rejected_options"] == [["B", "不覆盖 R2"]]
