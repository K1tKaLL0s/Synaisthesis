# 04 — 冻结命题、对抗式研究议会与自主 Loop

## 1. Claim Compiler

宏观理论不能直接进入议会。先调用 `compile_claim_units` 拆为原子 ClaimUnit。

每个 ClaimUnit 必须包含：

- claim_id
- natural_language_statement
- formal_statement_candidate
- object_domain
- quantifiers
- assumptions
- conclusion
- claim_class
- baseline
- evidence_standard
- falsification_witness
- intended_verifiers
- dependencies
- engineering_relevance
- semantic_critical_fields

父级研究目标的状态由子 Claim 组合，不允许一个“总 PASS”掩盖局部失败。

## 2. FrozenClaim → ClaimContract

`ClaimContract` 是不可变对象。

字段：

- contract_id
- claim_revision_id
- natural_language_hash
- formal_statement_hash
- object_domain_snapshot
- assumption_snapshot
- conclusion_snapshot
- baseline_snapshot
- stop_conditions
- output_scope
- tool_plan
- network_policy
- data_policy
- budget_policy
- allowed_semantic_delta
- approval_policy
- artifact_manifest_hash
- model_role_assignments
- created_at
- user_confirmed

冻结后任何修改都生成新版本。

## 3. 三条隔离轨道

### SupportTrack

目标：
- 选择最强支持路线；
- 真正完成证明、构造、证据或实验；
- 无法完成时明确失败。

输出 `SupportPacket`：

- route
- assumptions_used
- constructed_artifacts
- tool_requests
- evidence_refs
- incomplete_steps
- failure_reason
- public_rationale

### OpposeTrack

目标：
- 至少两类实质不同攻击。

默认攻击家族：

- 逻辑反例；
- 边界反例；
- 量词攻击；
- 替代解释；
- 经验失效；
- 形式化偏差；
- 计算复杂度；
- 工程不可实现；
- 文献覆盖。

每条 `AttackPacket`：

- target_revision
- attack_family
- description
- witness
- severity
- validation_plan
- evidence_refs

### IndependentTrack

#### Phase A：盲审基线
只读取：
- FrozenClaim；
- 原始 ResearchSpec；
- 允许的公共文献。

不读取 Support/Oppose 输出。

目标：
- 独立重建问题；
- 独立给出结论；
- 独立提出工具计划。

#### Phase B：去角色化复核
读取双方的**结构化结论和证据引用**，不读取隐藏推理过程。

目标：
- 识别遗漏；
- 检查证据标准是否对称；
- 生成 IndependentPacket。

## 4. ResearchPacket 拆分

不保存巨型文本 Packet，而保存：

- ClaimHeader
- SupportPacket
- AttackPacket[]
- IndependentPacket
- ToolPlan
- ToolEvidencePacket[]
- RevisionProposal[]
- SemanticDiff
- RegressionReport
- RoundAssessment
- PublicRationale

所有 Packet 使用 Schema 验证。

## 5. Governor 拆分

### PolicyGovernor
确定性规则：
- 验证输入；
- 检查隔离；
- 路由工具；
- 处理预算；
- 触发 Gate；
- 检查停止条件；
- 计数有效轮次；
- 写状态。

### SynthesisAgent
模型：
- 汇总冲突；
- 生成候选修复；
- 对比修复；
- 生成公开裁决理由。

它不能：
- 写 LEAN_PASS；
- 批准 Human Gate；
- 修改 FrozenClaim；
- 宣称绝对原创。

### HumanAdjudicator
处理：
- S2/S3/S4 Semantic Delta；
- 高风险 Action；
- 超预算；
- 更改目标；
- 最终接受。

## 6. 默认十轮 Loop

### 默认参数
- `max_rounds = 10`
- `minimum_rounds_before_early_stop = 4`
- `stable_rounds_required = 2`
- `max_repairs_per_round = 3`
- `max_primary_calls_per_round = 3`
- `max_auditor_calls_per_round = 3`
- `max_codex_tasks_per_round = 2`
- `max_proof_attempts_per_round = 8`
- `checkpoint_interval = 5`
- 总成本与总时长上限。

用户可修改轮数。

建议限制：
- 1–20：直接允许；
- 21–100：显示成本预估并要求确认；
- 超过 100：高级配置，默认拒绝。

## 7. 有效 Council Round

一轮必须满足：

1. 有 RoundStartSnapshot；
2. Support 或 Primary 提交结构化结果；
3. Opponent 至少一个有效攻击；
4. Independent 或 Auditor 提交独立审查；
5. ToolPlan 已执行或明确 NOT_APPLICABLE；
6. Evidence 已保存；
7. 产生 Decision；
8. 产生 Revision、StabilityRecord 或 Blocker；
9. 成本与模型调用已记录；
10. RoundEndSnapshot 已保存。

否则标记 `INVALID_ROUND`，不计入十轮。

## 8. 每轮顺序

1. Freeze round input；
2. Support analysis；
3. Opponent attacks；
4. Independent Phase A；
5. Tool selection；
6. Lean/Z3/Python/Literature/Codex execution；
7. Merge evidence；
8. Detect failure；
9. Propose repairs；
10. Semantic audit；
11. Select revision；
12. Regression；
13. Proof Loop；
14. Independent Phase B；
15. Back-translation；
16. Round assessment；
17. Continue / Pause / Stop。

## 9. Proof Loop 与 Theory Repair Loop

### Proof Loop
允许：
- 修改 proof body；
- 增加局部 lemma；
- 调整 tactic；
- 修复 import。

禁止：
- 修改 theorem statement；
- 新增核心假设；
- 缩小对象域；
- 弱化结论。

statement hash 变化时立即退出 Proof Loop。

### Theory Repair Loop
允许提出：
- 新假设；
- 结论修改；
- 定义修改；
- 对象域修改。

但必须生成 Semantic Delta 并走 Gate。

## 10. Semantic Delta

- S0：只修改证明；
- S1：逻辑等价重写；
- S2：外围技术条件变化；
- S3：对象域、量词、核心假设或结论变化；
- S4：研究目标变化。

自动提交：
- S0；
- S1。

候选分支 + Gate：
- S2。

立即阻断：
- S3；
- S4。

## 11. 修复候选评分

维度：

- resolves_critical_attack
- semantic_distance
- added_assumption_penalty
- conclusion_weakening_penalty
- domain_shrinking_penalty
- verifier_strength
- regression_pass
- engineering_relevance
- complexity_penalty
- cost_penalty

MVP 使用固定规则选出第一名，再由 Auditor 复核；不把唯一选择交给自由 LLM Judge。

## 12. 停止状态

### CANDIDATE_STABLE
必须满足：
- 连续若干轮无新 Critical Attack；
- 未解决 High Attack 低于阈值；
- Regression PASS；
- Semantic Audit PASS；
- 必需工具验证通过或 NOT_APPLICABLE；
- 无未解决 Human Gate；
- Artifact 完整。
- 早期新颖性资格为理论 route 的 `NOVELTY_QUALIFIED`，或存在绑定理论 route 的可审计用户低分继续决定。`ENGINEERING_NOVELTY_QUALIFIED` 只允许进入 03B 的 ENG0，不得直接进入本 Council。

`CANDIDATE_STABLE` 是研究状态，不是最终交付完成状态。理论 route 的最终 ResearchBundle 必须继续执行 `03C` TP0–TP2，至少交付经独立审计的 `TheoryMasterManuscript`。用户选择 `KEEP_MASTER_ONLY` 即可完成论文交付；只有用户选择 `WRITE_FORMAL_MANUSCRIPT` 才执行 TP3–TP5 的期刊/arXiv 适配。

### 其他
- MAX_ROUNDS_REACHED
- BLOCKED_HUMAN
- BLOCKED_TOOL
- BUDGET_EXHAUSTED
- COUNTEREXAMPLE_CONFIRMED
- FORMAL_PROOF_COMPLETED
- USER_PAUSED
- USER_CANCELLED

## 13. 多轴裁决状态

### formal_status
- UNFORMALIZED
- FORMALIZED
- PROOF_CANDIDATE
- LEAN_PASS
- LEAN_FAIL
- COUNTEREXAMPLE_CONFIRMED
- UNDECIDED
- REVOKED

### empirical_status
- NOT_TESTED
- SUPPORTED_WITHIN_SCOPE
- NOT_SUPPORTED
- INSUFFICIENT_EVIDENCE
- REVOKED

### semantic_status
- CANDIDATE
- AI_AUDITED
- USER_CONFIRMED
- DRIFTED
- REVOKED

### novelty_status
- UNCHECKED
- QUALIFICATION_PENDING
- NOVELTY_QUALIFIED
- NOVELTY_RESEARCH_REQUIRED
- USER_OVERRIDDEN_BELOW_THRESHOLD
- SEARCHED
- POSSIBLY_ORIGINAL
- PARTIAL_OVERLAP
- STRONG_OVERLAP
- KNOWN_RESULT
- INCONCLUSIVE

早期资格使用 `03A` 的 100 分制：理论最高 50、应用最高 50，两个隔离 Reviewer 逐项取较小值；有效总分达到 70 自动继续，低于 70 或 INCONCLUSIVE 打开用户研究决定 Gate。后期 Council/文献回归可以更新或撤回该状态，但不得把分数表述为“绝对原创”。

只有 `formal_status=LEAN_PASS` 且 `semantic_status=USER_CONFIRMED` 时，UI 才显示：

> FORMALLY_PROVED_AS_STATED

## 14. 撤回

新反例、形式化错误、依赖撤回或语义偏差都可触发：

- EvidenceRevoked；
- ClaimRevoked；
- dependent Claims → NEEDS_REGRESSION；
- 导出报告追加撤回记录；
- 旧版本不删除。

## 15. 超过十轮

若用户配置超过十轮：

- 每五轮 checkpoint；
- 第 20 轮强制 Maturity Review；
- 每 20 轮重新确认目标与预算；
- 未经确认不自动延长；
- 旧 ClaimContract 继续保持不变，除非用户明确接受新版本。
