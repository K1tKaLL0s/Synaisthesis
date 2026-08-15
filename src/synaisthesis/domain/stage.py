"""StageRun aggregate and stage contracts (blueprint 06, 03).

StageRun records one incubator stage execution. StageContract encodes the
blueprint 03 section 1 contract fields; the S0/S1 business validators express
the blueprint rules as pure, framework-free functions (duck-typed on the
Schema objects from agents/schemas.py — the domain layer must not import
them).
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import datetime
from typing import Any

from synaisthesis.domain.enums import StageGateStatus, StageId
from synaisthesis.domain.errors import ConflictError


@dataclass(frozen=True, slots=True)
class StageRun:
    """An immutable record of one incubator stage execution."""

    id: str
    project_id: str
    stage_id: StageId
    started_at: datetime
    input_artifact_ids: tuple[str, ...] = ()
    output_artifact_id: str | None = None
    status: StageGateStatus = StageGateStatus.NOT_TESTED
    prompt_version: str | None = None
    model_invocation_ids: tuple[str, ...] = ()
    ended_at: datetime | None = None

    @property
    def is_finished(self) -> bool:
        return self.ended_at is not None

    def complete(
        self,
        *,
        status: StageGateStatus,
        output_artifact_id: str,
        ended_at: datetime,
    ) -> StageRun:
        """Return a finished copy of this run."""
        if self.ended_at is not None:
            raise ConflictError(f"stage run {self.id} is already finished")
        return replace(
            self,
            status=status,
            output_artifact_id=output_artifact_id,
            ended_at=ended_at,
        )


@dataclass(frozen=True, slots=True)
class StageContract:
    """The 15 contract fields every stage must define (blueprint 03, section 1)."""

    stage_id: StageId
    objective: str
    required_inputs: tuple[str, ...]
    output_artifact_type: str
    required_fields: tuple[str, ...]
    validators: tuple[str, ...]
    tool_requirements: tuple[str, ...]
    human_gate_policy: str
    pass_criteria: tuple[str, ...]
    partial_criteria: tuple[str, ...]
    blocked_criteria: tuple[str, ...]
    allowed_next_stages: tuple[StageId, ...]
    rollback_targets: tuple[StageId, ...]
    prompt_version: str
    artifact_hash: str | None = None


S0_STAGE_CONTRACT = StageContract(
    stage_id=StageId.S0,
    objective="忠实保存用户原始表达，不抢先理论化。",
    required_inputs=("用户原始表达（名词、原句、草图、异常观察、附件）",),
    output_artifact_type="SeedRecord",
    required_fields=(
        "raw_input",
        "source_type",
        "user_intent_guess",
        "observation",
        "interpretation",
        "observation_interpretation_separated",
        "key_ambiguity",
        "user_corrections",
        "attachments",
    ),
    validators=("validate_seed_record",),
    tool_requirements=(),
    human_gate_policy="无强制确认；用户修改产生新版本。",
    pass_criteria=(
        "原文保留",
        "observation 与 interpretation 分栏",
        "最多一个关键歧义",
        "不静默改写用户立场",
    ),
    partial_criteria=("任一验证器 issue 存在",),
    blocked_criteria=("输出类型不是 SeedRecord",),
    allowed_next_stages=(StageId.S1,),
    rollback_targets=(),
    prompt_version="1.0.0",
)

S1_STAGE_CONTRACT = StageContract(
    stage_id=StageId.S1,
    objective="把用户原始表达转成结构化自然语言定义，且不偷换定义。",
    required_inputs=("SeedRecord",),
    output_artifact_type="NaturalLanguageSpec",
    required_fields=(
        "core_definition",
        "positive_examples",
        "non_examples",
        "boundary_conditions",
        "object_candidates",
        "ambiguous_terms",
        "explicit_non_goals",
        "expected_functions",
        "target_applications",
        "intended_users",
        "operational_constraints",
        "success_metrics",
        "assistant_proposed",
        "user_confirmed",
    ),
    validators=("validate_natural_language_spec",),
    tool_requirements=(),
    human_gate_policy="PASS 需要用户明确确认；模型不能代替用户确认。",
    pass_criteria=("至少一个正例", "至少一个非例", "至少一个边界", "用户明确确认"),
    partial_criteria=("验证器有 issue", "用户未确认"),
    blocked_criteria=("输出类型不是 NaturalLanguageSpec",),
    allowed_next_stages=(StageId.S2,),
    rollback_targets=(StageId.S0,),
    prompt_version="1.0.0",
)


def validate_seed_record(record: Any) -> tuple[str, ...]:
    """Return the business-rule issues of an S0 SeedRecord (empty = clean).

    Blueprint 03 S0: the raw input must be preserved, observation and
    interpretation must be separated, and the user's position must not be
    silently rewritten. An empty issues tuple means the validation rules pass;
    S0 has no mandatory confirmation gate.
    """
    issues: list[str] = []
    raw = getattr(record, "raw_input", None)
    if not isinstance(raw, str) or not raw.strip():
        issues.append("raw_input 必须保留非空原文")
    if not getattr(record, "observation_interpretation_separated", False):
        issues.append(
            "observation 与 interpretation 必须分栏（observation_interpretation_separated=True）"
        )
    observation = getattr(record, "observation", None)
    interpretation = getattr(record, "interpretation", None)
    if isinstance(observation, str) and observation and observation == interpretation:
        issues.append("observation 与 interpretation 不得混同")
    if not isinstance(observation, str) or not observation.strip():
        issues.append("observation 不能为空")
    if not isinstance(interpretation, str) or not interpretation.strip():
        issues.append("interpretation 不能为空")
    return tuple(issues)


def validate_natural_language_spec(spec: Any) -> tuple[str, ...]:
    """Return the business-rule issues of an S1 NaturalLanguageSpec.

    Blueprint 03 S1 PASS conditions: at least one positive example, at least
    one non-example, at least one boundary condition, plus explicit user
    confirmation (the confirmation itself is gate-level, not a validator).
    """
    issues: list[str] = []
    definition = getattr(spec, "core_definition", None)
    if not isinstance(definition, str) or not definition.strip():
        issues.append("core_definition 不能为空")
    for field, label in (
        ("positive_examples", "正例"),
        ("non_examples", "非例"),
        ("boundary_conditions", "边界"),
    ):
        values = getattr(spec, field, None)
        if not isinstance(values, (list, tuple)) or len(values) < 1:
            issues.append(f"至少一个{label}")
    return tuple(issues)
