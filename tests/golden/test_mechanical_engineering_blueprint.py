"""M2.10 golden tests for the mechanical engineering blueprint (03B, section 8)."""

from __future__ import annotations

import pytest

from synaisthesis.domain.engineering import (
    BLUEPRINT_VAGUE_PATTERNS,
    EngineeringWorkUnitContract,
    MechanicalEngineeringBlueprint,
    blueprint_completeness_blockers,
)
from synaisthesis.domain.errors import DomainError

#: The 14 contract items of 03B section 8.2 (item 1 covers task id + objective).
WORK_UNIT_FIELDS = (
    "task_id",
    "unique_objective",
    "authoritative_inputs",
    "preconditions_gates_environment",
    "allowed_files",
    "forbidden_files",
    "io_contracts",
    "invariants",
    "step_actions",
    "errors_boundaries_compat_rollback",
    "focused_tests",
    "full_checks",
    "acceptance_criteria",
    "stop_escalation_conditions",
    "delivery_format",
)


def _golden_work_unit(task_id: str) -> EngineeringWorkUnitContract:
    return EngineeringWorkUnitContract(
        task_id=task_id,
        unique_objective=f"实现 {task_id} 的 compute_trace 并满足 R1",
        authoritative_inputs=("03B §8.2", "ArchitectureBaseline ab-1"),
        preconditions_gates_environment=("ENGINEERING_ARCHITECTURE_REVIEW 已 APPROVE",),
        allowed_files=("src/core.py",),
        forbidden_files=("src/secret.py", "storage/**"),
        io_contracts=("compute_trace(m: Matrix) -> float",),
        invariants=("输入矩阵不被修改；结果可复算",),
        step_actions=("新增 compute_trace 函数并注册到 core 模块",),
        errors_boundaries_compat_rollback=("非方阵返回 DomainError；无迁移",),
        focused_tests=("tests/unit/core/test_compute_trace.py",),
        full_checks=("pytest / ruff check . / basedpyright",),
        acceptance_criteria=("focused 测试通过且 ruff/basedpyright 无错误",),
        stop_escalation_conditions=("任一验收不通过即停止并上报",),
        delivery_format="diff + 命令回执 + 未验证事项清单",
    )


def _golden_blueprint() -> MechanicalEngineeringBlueprint:
    return MechanicalEngineeringBlueprint(
        blueprint_id="bp-golden",
        version=1,
        project_id="p-1",
        architecture_baseline_id="ab-1",
        architecture_hash="a" * 64,
        project_tree={"src": "实现代码", "tests": "测试", "docs": "文档"},
        file_level_changes={
            "added": ("src/core.py", "src/cli.py", "tests/unit/core/test_compute_trace.py"),
            "modified": (),
            "forbidden": ("src/secret.py",),
        },
        modules_and_symbols={"core": ("compute_trace",), "cli": ("main",)},
        dependency_lock_policy="uv.lock 锁定全部依赖",
        config_secret_env_policy="仅环境变量，密钥不落盘",
        data_migration_rollback_policy="事件溯源，无破坏性迁移",
        runtime_flow_specs={"run": "cli.main -> core.compute_trace -> stdout"},
        non_functional_requirements=("p95 延迟 < 1s",),
        command_templates={
            "test": "pytest tests/ -q",
            "lint": "ruff check . && ruff format --check .",
            "typecheck": "basedpyright",
        },
        traceability={
            "R1": ("d-1", "t-1", "test-1"),
            "R2": ("d-2", "t-2", "test-2"),
        },
        risk_register=("浮点误差导致结果不可复算",),
        stop_and_escalation_conditions=("BLUEPRINT_GAP 即停",),
        pending_generated_artifacts=("README.md", "LICENSE"),
        work_units=(_golden_work_unit("wu-1"), _golden_work_unit("wu-2")),
        escalated_decision_ids=(),
    )


def test_golden_work_units_cover_all_14_contract_items():
    for work_unit in _golden_blueprint().work_units:
        for field_name in WORK_UNIT_FIELDS:
            value = getattr(work_unit, field_name)
            assert value, f"{work_unit.task_id}.{field_name} 为空"
        for field_name in ("step_actions", "acceptance_criteria"):
            for item in getattr(work_unit, field_name):
                assert not any(pattern in item for pattern in BLUEPRINT_VAGUE_PATTERNS), (
                    f"{work_unit.task_id}.{field_name} 含模糊措辞：{item!r}"
                )


def test_golden_blueprint_passes_completeness_gate():
    blueprint = _golden_blueprint()
    blockers = blueprint_completeness_blockers(
        blueprint,
        requirements_total=2,
        requirements_to_design=2,
        requirements_to_task=2,
        critical_requirements_total=2,
        critical_requirements_to_test=2,
        public_interfaces_total=1,
        public_interfaces_with_schema=1,
        unresolved_product_decisions=0,
        unresolved_architecture_decisions=0,
        broken_diagram_references=0,
    )
    assert blockers == ()


def test_golden_blueprint_fails_on_any_gap():
    blueprint = _golden_blueprint()
    blockers = blueprint_completeness_blockers(
        blueprint,
        requirements_total=2,
        requirements_to_design=1,  # design gap
        requirements_to_task=2,
        critical_requirements_total=2,
        critical_requirements_to_test=1,  # critical test gap
        public_interfaces_total=1,
        public_interfaces_with_schema=0,  # schema gap
        unresolved_product_decisions=1,
        unresolved_architecture_decisions=1,
        broken_diagram_references=2,
    )
    assert len(blockers) >= 5


def test_vague_work_unit_is_rejected():
    with pytest.raises(DomainError) as exc_info:
        EngineeringWorkUnitContract(
            task_id="wu-bad",
            unique_objective="改进模块",
            authoritative_inputs=(),
            preconditions_gates_environment=(),
            allowed_files=(),
            forbidden_files=(),
            io_contracts=(),
            invariants=(),
            step_actions=("适当修改相关代码，视情况补充测试",),
            errors_boundaries_compat_rollback=(),
            focused_tests=(),
            full_checks=(),
            acceptance_criteria=("运行良好",),
            stop_escalation_conditions=(),
            delivery_format="",
        )
    assert exc_info.value.error_code == "WORK_UNIT_INVALID"


def test_golden_blueprint_hash_is_content_bound():
    first = _golden_blueprint()
    second = _golden_blueprint()
    assert first.artifact_hash == second.artifact_hash
    assert first.to_event_payload()["work_units"][0]["task_id"] == "wu-1"
    assert first.content_payload() != first.to_event_payload()
