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


S2_STAGE_CONTRACT = StageContract(
    stage_id=StageId.S2,
    objective="把 S1 的自然语言定义扩展为机制草图，不把相关性自动写成因果。",
    required_inputs=("NaturalLanguageSpec",),
    output_artifact_type="MechanismSketch",
    required_fields=(
        "inputs",
        "state_change",
        "outputs",
        "invariants",
        "failure_conditions",
        "causal_claims",
        "merely_descriptive_relations",
        "uncertainty_register",
    ),
    validators=("validate_mechanism_sketch",),
    tool_requirements=(),
    human_gate_policy="无强制确认；用户修改产生新版本。",
    pass_criteria=(
        "输入、变化、输出齐全",
        "至少一个不变量",
        "至少一个失败条件",
        "不把相关性自动写成因果",
    ),
    partial_criteria=("任一验证器 issue 存在",),
    blocked_criteria=("输出类型不是 MechanismSketch",),
    allowed_next_stages=(StageId.S3,),
    rollback_targets=(),
    prompt_version="1.0.0",
)

S3_STAGE_CONTRACT = StageContract(
    stage_id=StageId.S3,
    objective="把机制草图映射到可追溯的相关研究，学术与工程查询种子同时生成。",
    required_inputs=("MechanismSketch",),
    output_artifact_type="PriorWorkMap",
    required_fields=(
        "search_queries",
        "sources",
        "nearest_theories",
        "same_object_different_method",
        "same_method_different_object",
        "conflicts",
        "terminology_candidates",
        "retrieval_scope",
        "unsearched_areas",
        "literature_hits",
        "mature_engineering_projects",
        "engineering_maturity_evidence",
        "function_application_neighbors",
        "metadata_verified",
    ),
    validators=("validate_prior_work_map",),
    tool_requirements=(),
    human_gate_policy="无强制确认；检索状态由后续 RQ1 与 Gate 承接。",
    pass_criteria=(
        "查询和来源可追溯",
        "区分未发现与不存在",
        "至少给出最近邻类别",
        "文献元数据被外部源验证",
    ),
    partial_criteria=("任一验证器 issue 存在",),
    blocked_criteria=("输出类型不是 PriorWorkMap",),
    allowed_next_stages=(StageId.S4,),
    rollback_targets=(),
    prompt_version="1.0.0",
)

S4_STAGE_CONTRACT = StageContract(
    stage_id=StageId.S4,
    objective="在 S1–S3 基础上再规范研究方向，形成可冻结的 ResearchScopeSpec。",
    required_inputs=("PriorWorkMap",),
    output_artifact_type="ResearchScopeSpec",
    required_fields=(
        "main_question",
        "object_domain",
        "non_goals",
        "nearest_neighbor_difference",
        "central_claims",
        "evidence_requirements",
        "failure_learning_plan",
        "engineering_relevance",
        "stop_conditions",
        "user_confirmed_scope",
    ),
    validators=("validate_research_scope_spec",),
    tool_requirements=(),
    human_gate_policy=(
        "PASS 不要求用户确认；NATURAL_LANGUAGE_DESIGN_READY 要求用户确认且模型不能代替。"
    ),
    pass_criteria=(
        "主问题唯一",
        "对象域明确",
        "非目标明确",
        "每个中心主张有证据需求",
        "失败也有可学习输出",
    ),
    partial_criteria=("任一验证器 issue 存在",),
    blocked_criteria=("输出类型不是 ResearchScopeSpec",),
    allowed_next_stages=(),
    rollback_targets=(StageId.S1, StageId.S3),
    prompt_version="1.0.0",
)


S6_STAGE_CONTRACT = StageContract(
    stage_id=StageId.S6,
    objective="形成核心统一理论 TheoryKernel，比较替代理论并保留反例。",
    required_inputs=("MinimalCaseBundle", "NaturalLanguageSpec"),
    output_artifact_type="TheoryKernel",
    required_fields=(
        "candidate_mechanism",
        "competing_explanations",
        "examples",
        "counterexamples",
        "invariants",
        "boundaries",
        "predictions",
        "discarded_alternatives",
        "discard_reasons",
        "unresolved_conflicts",
    ),
    validators=("validate_theory_kernel",),
    tool_requirements=(),
    human_gate_policy="S6 只产生 candidate，不产生验证状态。",
    pass_criteria=(
        "比较至少一个替代理论",
        "保留反例",
        "不以解释流畅度代替证据",
        "预测与解释分开",
    ),
    partial_criteria=("任一验证器 issue 存在",),
    blocked_criteria=("输出类型不是 TheoryKernel",),
    allowed_next_stages=(StageId.S7,),
    rollback_targets=(StageId.S1, StageId.S4),
    prompt_version="1.0.0",
)


S7_STAGE_CONTRACT = StageContract(
    stage_id=StageId.S7,
    objective="消费已批准早期公式，生成独立 FormalizationPlan（形式构造）。",
    required_inputs=("TheoryKernel", "EarlyFormalizationBundle"),
    output_artifact_type="FormalizationPlan",
    required_fields=(
        "object_domain",
        "symbols",
        "definitions",
        "assumptions",
        "quantifiers",
        "claims",
        "dependency_graph",
        "proof_paths",
        "counterexample_paths",
        "intended_tools",
        "formalization_uncertainties",
        "proof_candidate_artifacts",
    ),
    validators=("validate_formalization_plan",),
    tool_requirements=("intended_tools 或 NOT_APPLICABLE",),
    human_gate_policy="AI 产生的形式证明先标 PROOF_CANDIDATE，不得标 Tool-verified。",
    pass_criteria=(
        "每个 Claim 有对象域和量词",
        "每个 Claim 有证伪见证",
        "依赖关系无环或明确递归",
        "已选验证工具或明确 NOT_APPLICABLE",
    ),
    partial_criteria=("任一验证器 issue 存在",),
    blocked_criteria=("输出类型不是 FormalizationPlan",),
    allowed_next_stages=(StageId.S8,),
    rollback_targets=(StageId.S1, StageId.S4, StageId.S6),
    prompt_version="1.0.0",
)


S8_STAGE_CONTRACT = StageContract(
    stage_id=StageId.S8,
    objective="冻结前就绪攻击：一至两轮内部+独立外部攻击，不启动正式十轮 Council。",
    required_inputs=("FormalizationPlan",),
    output_artifact_type="PreFreezeAttackReport",
    required_fields=(
        "attack_rounds",
        "internal_attacks",
        "external_attacks",
        "obvious_counterexamples",
        "boundary_failures",
        "definition_holes",
        "quantifier_risks",
        "tool_feasibility",
        "claim_atomicity",
        "recommended_split",
        "freeze_readiness",
        "critical_issues_resolved",
        "critical_issues_blocked",
    ),
    validators=("validate_prefreeze_attack_report",),
    tool_requirements=(),
    human_gate_policy="S8 只做 1–2 轮 readiness attack；禁止启动正式十轮 Council。",
    pass_criteria=(
        "至少一次内部攻击",
        "至少一次独立外部攻击",
        "Critical 问题已解决或明确阻断",
        "Claim 足够原子",
    ),
    partial_criteria=("任一验证器 issue 存在",),
    blocked_criteria=("输出类型不是 PreFreezeAttackReport",),
    allowed_next_stages=(StageId.S9,),
    rollback_targets=(StageId.S1, StageId.S4, StageId.S6, StageId.S7),
    prompt_version="1.0.0",
)


S9_STAGE_CONTRACT = StageContract(
    stage_id=StageId.S9,
    objective="登记开放问题与猜想，保留 AI_GENERATED 来源标记。",
    required_inputs=("PreFreezeAttackReport",),
    output_artifact_type="OpenQuestionRegistry",
    required_fields=(
        "registry_id",
        "entries",
    ),
    validators=("validate_open_question_registry",),
    tool_requirements=(),
    human_gate_policy="开放问题只登记不解决；来源标记不可改写。",
    pass_criteria=(
        "每条记录字段完整",
        "AI 生成问题保留 AI_GENERATED 标记",
        "失败尝试与证伪路径已记录",
    ),
    partial_criteria=("任一验证器 issue 存在",),
    blocked_criteria=("输出类型不是 OpenQuestionRegistry",),
    allowed_next_stages=(StageId.S10,),
    rollback_targets=(StageId.S1, StageId.S4, StageId.S6, StageId.S7),
    prompt_version="1.0.0",
)


S10_STAGE_CONTRACT = StageContract(
    stage_id=StageId.S10,
    objective="研究交接：无未归属证据、每个下游任务有输入/输出/门槛、可形成 FrozenClaim 候选。",
    required_inputs=("OpenQuestionRegistry", "MinimalCaseBundle"),
    output_artifact_type="ResearchHandoffBundle",
    required_fields=(
        "frozen_terms",
        "evidence_summary",
        "current_versions",
        "open_questions",
        "downstream_tasks",
        "verification_thresholds",
        "proof_track",
        "experiment_track",
        "engineering_track",
        "writing_track",
        "artifact_manifest",
        "unresolved_gates",
    ),
    validators=("validate_research_handoff_bundle",),
    tool_requirements=(),
    human_gate_policy="成熟门检查 RQ 状态：理论 route 必须已通过 RQ4M 或绑定 override。",
    pass_criteria=(
        "不存在未归属证据",
        "每个下游任务有输入、输出和门槛",
        "可形成 FrozenClaim 候选",
    ),
    partial_criteria=("任一验证器 issue 存在",),
    blocked_criteria=("输出类型不是 ResearchHandoffBundle",),
    allowed_next_stages=(),
    rollback_targets=(StageId.S1, StageId.S4, StageId.S6, StageId.S7),
    prompt_version="1.0.0",
)


def _non_empty_str(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _non_empty_str_list(value: Any) -> bool:
    return (
        isinstance(value, (list, tuple))
        and len(value) >= 1
        and all(_non_empty_str(item) for item in value)
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


def validate_mechanism_sketch(sketch: Any) -> tuple[str, ...]:
    """Return the business-rule issues of an S2 MechanismSketch.

    Blueprint 03 S2 PASS conditions: inputs/state change/outputs all present,
    at least one invariant, at least one failure condition, and a relation
    must not be listed as both causal and merely descriptive.
    """
    issues: list[str] = []
    if not _non_empty_str_list(getattr(sketch, "inputs", None)):
        issues.append("inputs 至少包含一个输入")
    if not _non_empty_str(getattr(sketch, "state_change", None)):
        issues.append("state_change 不能为空")
    if not _non_empty_str_list(getattr(sketch, "outputs", None)):
        issues.append("outputs 至少包含一个输出")
    if not _non_empty_str_list(getattr(sketch, "invariants", None)):
        issues.append("至少一个不变量")
    if not _non_empty_str_list(getattr(sketch, "failure_conditions", None)):
        issues.append("至少一个失败条件")
    causal = {item.strip() for item in getattr(sketch, "causal_claims", ()) if _non_empty_str(item)}
    descriptive = {
        item.strip()
        for item in getattr(sketch, "merely_descriptive_relations", ())
        if _non_empty_str(item)
    }
    if causal & descriptive:
        issues.append("同一关系不得同时列为 causal_claims 与 merely_descriptive_relations")
    return tuple(issues)


def validate_prior_work_map(prior_work: Any) -> tuple[str, ...]:
    """Return the business-rule issues of an S3 PriorWorkMap.

    Blueprint 03 S3 PASS conditions plus the M2.2 acceptance clause: queries
    and sources must be traceable, academic and engineering query seeds must
    both exist, "not found" must be separated from "does not exist", at least
    one nearest-neighbor category must be given, and literature metadata must
    be externally verified.
    """
    issues: list[str] = []
    queries = getattr(prior_work, "search_queries", None)
    academic = queries.get("academic", ()) if isinstance(queries, dict) else ()
    engineering = queries.get("engineering", ()) if isinstance(queries, dict) else ()
    if not _non_empty_str_list(academic):
        issues.append("search_queries.academic 至少包含一个学术查询种子")
    if not _non_empty_str_list(engineering):
        issues.append("search_queries.engineering 至少包含一个工程查询种子")
    if not _non_empty_str_list(getattr(prior_work, "sources", None)):
        issues.append("sources 至少包含一个可追溯来源")
    if not _non_empty_str(getattr(prior_work, "retrieval_scope", None)):
        issues.append("retrieval_scope 不能为空")
    neighbor_fields = (
        "nearest_theories",
        "same_object_different_method",
        "same_method_different_object",
        "function_application_neighbors",
    )
    if not any(_non_empty_str_list(getattr(prior_work, field, None)) for field in neighbor_fields):
        issues.append("至少给出一个最近邻类别")
    if not getattr(prior_work, "metadata_verified", False):
        issues.append("metadata_verified 必须为 true（文献元数据须由外部源验证）")
    literature_hits = getattr(prior_work, "literature_hits", None)
    unsearched_areas = getattr(prior_work, "unsearched_areas", None)
    if not _non_empty_str_list(literature_hits) and not _non_empty_str_list(unsearched_areas):
        issues.append("literature_hits 为空时必须列出 unsearched_areas，以区分未发现与不存在")
    return tuple(issues)


def validate_research_scope_spec(scope: Any) -> tuple[str, ...]:
    """Return the business-rule issues of an S4 ResearchScopeSpec.

    Blueprint 03 S4 PASS conditions: a single main question, an explicit
    object domain and non-goals, one evidence requirement per central claim,
    and a learnable output even on failure. Confirmation of the scope is
    gate-level (NATURAL_LANGUAGE_DESIGN_READY), not a validator.
    """
    issues: list[str] = []
    for field, label in (
        ("main_question", "main_question"),
        ("object_domain", "object_domain"),
        ("nearest_neighbor_difference", "nearest_neighbor_difference"),
        ("failure_learning_plan", "failure_learning_plan"),
        ("engineering_relevance", "engineering_relevance"),
    ):
        if not _non_empty_str(getattr(scope, field, None)):
            issues.append(f"{label} 不能为空")
    if not _non_empty_str_list(getattr(scope, "non_goals", None)):
        issues.append("non_goals 至少包含一个明确非目标")
    central_claims = getattr(scope, "central_claims", None)
    evidence_requirements = getattr(scope, "evidence_requirements", None)
    if not _non_empty_str_list(central_claims):
        issues.append("central_claims 至少包含一个中心主张")
    if not _non_empty_str_list(evidence_requirements):
        issues.append("evidence_requirements 至少包含一条证据需求")
    if (
        isinstance(central_claims, (list, tuple))
        and isinstance(evidence_requirements, (list, tuple))
        and len(central_claims) != len(evidence_requirements)
    ):
        issues.append("每个中心主张必须有对应证据需求（数量一致）")
    if not _non_empty_str_list(getattr(scope, "stop_conditions", None)):
        issues.append("stop_conditions 至少包含一个停止条件")
    return tuple(issues)


def validate_theory_kernel(kernel: Any) -> tuple[str, ...]:
    """Return the business-rule issues of an S6 TheoryKernel (03, S6).

    PASS conditions: at least one competing explanation is compared,
    counterexamples are preserved (never silently dropped), explanation
    fluency is not evidence (predictions and explanations stay separate
    fields), and predictions are separated from explanations.
    """
    issues: list[str] = []
    if not _non_empty_str(getattr(kernel, "candidate_mechanism", None)):
        issues.append("candidate_mechanism 不能为空")
    if not _non_empty_str_list(getattr(kernel, "competing_explanations", None)):
        issues.append("必须比较至少一个替代理论（competing_explanations）")
    if not _non_empty_str_list(getattr(kernel, "counterexamples", None)):
        issues.append("反例必须保留（counterexamples 至少一个，或显式 NONE_FOUND）")
    if not _non_empty_str_list(getattr(kernel, "invariants", None)):
        issues.append("invariants 至少包含一个不变量")
    if not _non_empty_str_list(getattr(kernel, "boundaries", None)):
        issues.append("boundaries 至少包含一个边界")
    discarded = getattr(kernel, "discarded_alternatives", None)
    reasons = getattr(kernel, "discard_reasons", None)
    if (
        isinstance(discarded, (list, tuple))
        and isinstance(reasons, (list, tuple))
        and len(discarded) != len(reasons)
    ):
        issues.append("每个被放弃的替代理论必须有放弃理由（数量一致）")
    return tuple(issues)


def _dependency_graph_acyclic_or_explicitly_recursive(graph: Any) -> bool:
    if not isinstance(graph, dict):
        return False
    if not graph:
        return True
    visited: set[str] = set()
    active: set[str] = set()

    def visit(node: str) -> bool:
        if node in active:
            return True  # cycle found
        if node in visited:
            return False
        active.add(node)
        deps = graph.get(node, ())
        if not isinstance(deps, (list, tuple)):
            active.discard(node)
            return False
        for dependency in deps:
            if dependency == node:
                continue  # explicit self-recursion is allowed and declared
            if dependency in graph and visit(dependency):
                return True
        active.discard(node)
        visited.add(node)
        return False

    return all(not visit(node) for node in graph)


def validate_formalization_plan(plan: Any) -> tuple[str, ...]:
    """Return the business-rule issues of an S7 FormalizationPlan (03, S7).

    PASS conditions: every claim carries an object domain, quantifiers and a
    falsification witness; the dependency graph is acyclic or explicitly
    recursive; verification tools are chosen or NOT_APPLICABLE is declared.
    """
    issues: list[str] = []
    if not _non_empty_str(getattr(plan, "object_domain", None)):
        issues.append("object_domain 不能为空")
    if not _non_empty_str_list(getattr(plan, "symbols", None)):
        issues.append("symbols 至少包含一个符号")
    claims = getattr(plan, "claims", None)
    if not isinstance(claims, (list, tuple)) or not claims:
        issues.append("claims 至少包含一个 Claim")
    else:
        for claim in claims:
            claim_id = getattr(claim, "claim_id", "?")
            if not _non_empty_str(getattr(claim, "object_domain", None)):
                issues.append(f"claim {claim_id} 缺少对象域")
            if not _non_empty_str_list(getattr(claim, "quantifiers", None)):
                issues.append(f"claim {claim_id} 缺少量词")
            if not _non_empty_str(getattr(claim, "falsification_witness", None)):
                issues.append(f"claim {claim_id} 缺少证伪见证")
    if not _dependency_graph_acyclic_or_explicitly_recursive(
        getattr(plan, "dependency_graph", None)
    ):
        issues.append("依赖图必须无环或显式声明递归")
    intended_tools = getattr(plan, "intended_tools", None)
    if not _non_empty_str_list(intended_tools) and "NOT_APPLICABLE" not in (intended_tools or ()):
        issues.append("必须选择验证工具或显式声明 NOT_APPLICABLE")
    return tuple(issues)


def validate_prefreeze_attack_report(report: Any) -> tuple[str, ...]:
    """Return the business-rule issues of an S8 PreFreezeAttackReport (03, S8).

    Only 1-2 attack rounds are allowed; the ten-round Council is never started
    here.  freeze_readiness requires every critical issue to be resolved or
    explicitly blocked.
    """
    issues: list[str] = []
    rounds = getattr(report, "attack_rounds", None)
    if not isinstance(rounds, int) or rounds < 1 or rounds > 2:
        issues.append("S8 只允许 1–2 轮 readiness attack，不得启动正式十轮 Council")
    if not _non_empty_str_list(getattr(report, "internal_attacks", None)):
        issues.append("至少一次内部攻击（internal_attacks）")
    if not _non_empty_str_list(getattr(report, "external_attacks", None)):
        issues.append("至少一次独立外部攻击（external_attacks）")
    resolved = bool(getattr(report, "critical_issues_resolved", False))
    blocked = bool(getattr(report, "critical_issues_blocked", False))
    if not resolved and not blocked:
        issues.append("Critical 问题必须已解决或明确阻断")
    if bool(getattr(report, "freeze_readiness", False)) and not resolved:
        issues.append("freeze_readiness 要求 Critical 问题已解决")
    if not _non_empty_str_list(getattr(report, "claim_atomicity", None)):
        issues.append("claim_atomicity 至少包含一条原子性检查")
    return tuple(issues)


OPEN_QUESTION_ORIGINS = frozenset({"USER", "AI_GENERATED", "DERIVED", "LITERATURE", "TOOL_FAILURE"})


def validate_open_question_registry(registry: Any) -> tuple[str, ...]:
    """Return the business-rule issues of an S9 OpenQuestionRegistry (03, S9)."""
    issues: list[str] = []
    entries = getattr(registry, "entries", None)
    if not isinstance(entries, (list, tuple)) or not entries:
        issues.append("至少登记一条开放问题")
        return tuple(issues)
    for entry in entries:
        entry_id = getattr(entry, "question_id", "?")
        origin = getattr(entry, "origin", None)
        if origin not in OPEN_QUESTION_ORIGINS:
            issues.append(f"question {entry_id} 的来源 {origin!r} 非法")
        for field, label in (
            ("statement", "statement"),
            ("why_open", "why_open"),
            ("falsification_path", "falsification_path"),
            ("next_action", "next_action"),
        ):
            if not _non_empty_str(getattr(entry, field, None)):
                issues.append(f"question {entry_id} 缺少 {label}")
        if not _non_empty_str_list(getattr(entry, "known_failed_attempts", None)):
            issues.append(f"question {entry_id} 缺少已知失败尝试")
        if not _non_empty_str(getattr(entry, "status", None)):
            issues.append(f"question {entry_id} 缺少 status")
    return tuple(issues)


def validate_research_handoff_bundle(bundle: Any) -> tuple[str, ...]:
    """Return the business-rule issues of an S10 ResearchHandoffBundle (03, S10).

    PASS: no unattributed evidence, every downstream task carries
    input/output/threshold, and FrozenClaim candidates are formable.
    """
    issues: list[str] = []
    if not _non_empty_str_list(getattr(bundle, "frozen_terms", None)):
        issues.append("frozen_terms 至少包含一个冻结术语")
    evidence = getattr(bundle, "evidence_summary", None)
    if not isinstance(evidence, (list, tuple)) or not evidence:
        issues.append("evidence_summary 至少包含一条证据")
    else:
        for item in evidence:
            if not isinstance(item, str) or "@" not in item:
                issues.append(f"证据未归属：{item!r}（必须标注 @来源）")
    tasks = getattr(bundle, "downstream_tasks", None)
    if not isinstance(tasks, (list, tuple)) or not tasks:
        issues.append("downstream_tasks 至少包含一个下游任务")
    else:
        for task in tasks:
            task_id = getattr(task, "task_id", "?")
            for field in ("input", "output", "threshold"):
                if not _non_empty_str(getattr(task, field, None)):
                    issues.append(f"任务 {task_id} 缺少 {field}")
    if not _non_empty_str_list(getattr(bundle, "verification_thresholds", None)):
        issues.append("verification_thresholds 至少包含一个验证门槛")
    if not _non_empty_str_list(getattr(bundle, "artifact_manifest", None)):
        issues.append("artifact_manifest 至少包含一个工件")
    return tuple(issues)
