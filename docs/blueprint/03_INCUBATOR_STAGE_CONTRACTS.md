# 03 — S0–S10 孵化阶段契约

## 1. 通用 StageContract

每个阶段必须定义：

- `stage_id`
- `objective`
- `required_inputs`
- `output_artifact_type`
- `required_fields`
- `validators`
- `tool_requirements`
- `human_gate_policy`
- `pass_criteria`
- `partial_criteria`
- `blocked_criteria`
- `allowed_next_stages`
- `rollback_targets`
- `prompt_version`
- `artifact_hash`

模型不能直接将 Stage 标为 PASS。`evaluate_stage_gate` 根据 Schema、验证器和用户确认计算状态。

---

## S0 — 灵感捕获

### 目标
忠实保存用户原始表达，不抢先理论化。

### 输入
名词、原句、草图、异常观察、附件。

### 输出：`SeedRecord`
- raw_input
- source_type
- user_intent_guess
- observation
- interpretation
- observation_interpretation_separated
- key_ambiguity
- user_corrections
- attachments

### 验证
- 原文保留；
- observation 与 interpretation 分栏；
- 最多提出一个关键歧义；
- 不静默改写用户立场。

### Gate
无强制确认，但用户修改产生新版本。

---

## S1 — 自然语言定义

### 输出：`NaturalLanguageSpec`
- core_definition
- positive_examples
- non_examples
- boundary_conditions
- object_candidates
- ambiguous_terms
- explicit_non_goals
- assistant_proposed
- user_confirmed

### PASS 条件
- 至少一个正例；
- 至少一个非例；
- 至少一个边界；
- 用户明确确认。

S1 是后续数学化工作的最高自然语言语义权威。

---

## S2 — 机制草图

### 输出：`MechanismSketch`
- inputs
- state_change
- outputs
- invariants
- failure_conditions
- causal_claims
- merely_descriptive_relations
- uncertainty_register

### PASS 条件
- 输入、变化、输出齐全；
- 至少一个不变量；
- 至少一个失败条件；
- 不把相关性自动写成因果。

### 默认停止点
用户可以在 S1 或 S2 后归档，不必继续科研化。

---

## S3 — 相关研究映射

### 输出：`PriorWorkMap`
- search_queries
- sources
- nearest_theories
- same_object_different_method
- same_method_different_object
- conflicts
- terminology_candidates
- retrieval_scope
- unsearched_areas
- literature_hits
- metadata_verified

### PASS 条件
- 查询和来源可追溯；
- 区分“未发现”与“不存在”；
- 至少给出最近邻类别；
- 文献元数据被外部源验证。

### 允许状态
- SEARCHED
- PARTIAL
- POSSIBLY_NOVEL
- OVERLAP_FOUND
- INCONCLUSIVE

禁止输出“绝对原创”。

---

## S4 — 研究方向再规范

### 输出：`ResearchScopeSpec`
- main_question
- object_domain
- non_goals
- nearest_neighbor_difference
- central_claims
- evidence_requirements
- failure_learning_plan
- engineering_relevance
- stop_conditions
- user_confirmed_scope

### PASS 条件
- 主问题唯一；
- 对象域明确；
- 非目标明确；
- 每个中心主张有证据需求；
- 失败也有可学习输出。

### 回退
重大文献冲突或对象域不稳定时回 S1/S3。

---

## S5 — 最小范例

### 输出：`MinimalCaseBundle`
- input
- control_or_baseline
- expected_output
- failure_condition
- reproduction_steps
- actually_executed
- execution_receipt_id
- toy_or_real
- limitations

### 状态
- PROPOSED
- DEMONSTRATED
- EXECUTED
- FAILED
- NOT_RUN

### 规则
`DEMONSTRATED ≠ PROVED`。没有真实运行时只能标 DEMONSTRATED 或 NOT_RUN。

---

## MATURE_IDEA_READY — 成熟灵感门

不允许模型直接输出，而由以下条件计算：

- S0–S4 PASS；
- S5 至少 DEMONSTRATED；
- S1 与 S4 有用户确认；
- 关键术语无未解决歧义；
- 存在可执行研究计划；
- 存在至少一个可构造 ClaimUnit；
- 无 Critical Blocker。

它只表示“可以交接”，不表示理论成立。

---

## S6 — 核心统一理论

### 输出：`TheoryKernel`
- candidate_mechanism
- competing_explanations
- examples
- counterexamples
- invariants
- boundaries
- predictions
- discarded_alternatives
- discard_reasons
- unresolved_conflicts

### PASS 条件
- 比较至少一个替代理论；
- 保留反例；
- 不以解释流畅度代替证据；
- 预测与解释分开。

### 回退
核心概念变化必须回 S1/S4，不在 S6 静默修补。

---

## S7 — 正式构造

### 输出：`FormalizationPlan`
- object_domain
- symbols
- definitions
- assumptions
- quantifiers
- claims
- dependency_graph
- proof_paths
- counterexample_paths
- intended_tools
- formalization_uncertainties
- proof_candidate_artifacts

### 规则
AI 产生的形式证明先标 `PROOF_CANDIDATE`。

### PASS 条件
- 每个 Claim 有对象域和量词；
- 每个 Claim 有证伪见证；
- 依赖关系无环，或明确递归；
- 已选验证工具或明确 NOT_APPLICABLE。

---

## S8 — 冻结前就绪攻击

### 新定位
不再执行完整十轮议会，只做一至两轮 readiness attack。

### 输出：`PreFreezeAttackReport`
- obvious_counterexamples
- boundary_failures
- definition_holes
- quantifier_risks
- tool_feasibility
- claim_atomicity
- recommended_split
- freeze_readiness

### PASS 条件
- 至少一次内部攻击；
- 至少一次独立外部攻击；
- Critical 问题已解决或明确阻断；
- Claim 足够原子。

### 回退
- 定义问题 → S1；
- 研究范围问题 → S4；
- 理论问题 → S6；
- 形式结构问题 → S7。

---

## S9 — 开放问题与猜想

### 输出：`OpenQuestionRegistry`
每条记录：
- question_id
- statement
- origin
- why_open
- known_failed_attempts
- falsification_path
- next_action
- dependency_claims
- status

### origin
- USER
- AI_GENERATED
- DERIVED
- LITERATURE
- TOOL_FAILURE

AI 生成问题必须保留 AI_GENERATED 标记。

---

## S10 — 研究交接

### 输出：`ResearchHandoffBundle`
- frozen_terms
- evidence_summary
- current_versions
- open_questions
- downstream_tasks
- verification_thresholds
- proof_track
- experiment_track
- engineering_track
- writing_track
- artifact_manifest
- unresolved_gates

### PASS 条件
- 不存在未归属证据；
- 每个下游任务有输入、输出和门槛；
- 可形成 FrozenClaim 候选。

---

## 2. 有效孵化轮次与 Checkpoint

### `IncubatorSubstantiveRound`
只有满足以下条件才计数：
- 选择一个 ProgressKind；
- 产生新 Artifact 或明确差异；
- 保存公开理由；
- 记录未解决项；
- 不是简单重述上一轮。

### ProgressKind
- DEFINITION
- BOUNDARY
- MECHANISM
- EVIDENCE
- TEST
- ASSUMPTION
- FORMALIZATION
- COUNTEREXAMPLE
- HANDOFF

### Checkpoint
- 每 5 个有效轮次生成 WIP_CHECKPOINT；
- 第 20 个有效轮次触发 Mandatory Maturity Gate；
- 未经用户确认不得自动扩大目标或对象域；
- Council 与 Incubator 轮次分开计数。

## 3. 阶段执行模板

每次 `execute_stage` 应按以下顺序：

1. 读取上游 Artifact 与当前权威语义；
2. 构造最小 visibility bundle；
3. 调模型或工具；
4. Schema 校验；
5. 业务验证；
6. 生成 StageDiff；
7. 计算 Gate；
8. 写 Artifact 与 DomainEvent；
9. 返回用户可读摘要；
10. 不自动删除旧产物。

## 4. 对话与平台的边界

Codex 或 Web 对话中只展示：
- 当前 Stage；
- 待确认差异；
- 新 Artifact 摘要；
- Blocker；
- 下一步工具动作。

完整状态保存在平台，不能依赖对话历史恢复。
