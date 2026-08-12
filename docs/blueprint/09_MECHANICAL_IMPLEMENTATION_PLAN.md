# 09 — 机械式、可碎片化实施方案

原则：每个阶段都能运行、测试和提交 Git。不要同时开发 UI、Lean、MCP 和多模型。

---

## Stage 0：仓库与质量底座

### 建立
- `src/` layout；
- pyproject；
- uv；
- pytest；
- Ruff；
- Pyright；
- GitHub Actions；
- README；
- LICENSE；
- SECURITY；
- CONTRIBUTING；
- ADR 目录。

### 函数
- `get_version`
- `load_settings`
- `validate_settings`

### 完成标准
- CLI 输出版本；
- 测试可运行；
- CI 通过；
- 没有 LLM 依赖。

---

## Stage 1：领域模型、Event Store、Artifact Store

### 实现
- Project；
- ResearchSpec；
- StageRun；
- ClaimUnit；
- Revision；
- Evidence；
- Gate；
- DomainEvent；
- Artifact。

### 函数
- `init_database`
- `append_domain_event`
- `save_artifact`
- `verify_artifact_hash`
- `create_project`
- `create_revision`
- `create_evidence`
- `revoke_evidence`

### 测试
- Revision 不可原地修改；
- Spec 确认后不能静默覆盖；
- hash 变化可检测；
- Event 顺序稳定；
- 撤回不删除。

### 完成标准
手工调用 CLI 即可记录完整研究状态。

---

## Stage 2：搬运当前有效的 S0–S5

### 任务
将当前 Skill 中表现良好的内容变成：
- StageContract；
- Pydantic Schema；
- Prompt Asset；
- Validation Rule。

### 函数
- `capture_seed`
- `execute_s0` 至 `execute_s5`
- `validate_stage_output`
- `evaluate_stage_gate`
- `advance_stage`

### 测试
把现有成功对话作为 golden cases。

### 完成标准
不依赖 Codex 会话历史，也能复现原本有效的灵感孵化。

---

## Stage 3：S6–S10 与 MATURE_IDEA_READY

### 实现
- TheoryKernel；
- FormalizationPlan；
- PreFreezeAttackReport；
- OpenQuestionRegistry；
- HandoffBundle；
- computed maturity gate。

### 特别处理
旧 S8 的十轮攻击改为一至两轮 readiness attack。

### 完成标准
项目能从 Seed 到 HandoffBundle，状态可恢复。

---

## Stage 4：Claim Compiler 与 FrozenClaim

### 实现
- 原子 Claim 拆分；
- ClaimClass；
- Evidence Standard；
- Falsification Witness；
- Dependency Graph；
- ClaimContract；
- hash 冻结。

### 测试
- 混合命题必须拆分；
- 不可验证命题被阻断；
- 冻结后修改生成新版本；
- 重大变更触发 Gate。

### 完成标准
平台能产生真实不可变 ClaimContract。

---

## Stage 5：ActionBroker、Gate、A0–A3

### 实现
- 风险分类；
- Approval；
- ExecutionReceipt；
- DelegationPolicy；
- Semantic Delta S0–S4。

### 测试
- 模型不能代用户批准；
- R4–R6 必须 Gate；
- S3 修改不能自动提交；
- Receipt 缺 hash 则失败。

### 完成标准
所有外部动作都有授权与回执。

---

## Stage 6：双模型 Provider 与真实隔离

### 依赖
- LiteLLM；
- httpx；
- tenacity。

### 实现
- `LLMProvider`
- `call_primary`
- `call_auditor`
- `validate_model_diversity`
- `create_role_session`
- `build_visibility_bundle`
- `validate_role_visibility`

### 测试
- 同模型警告；
- Phase A 看不到双方输出；
- 无效结构化输出被拒绝；
- 成本记录。

### 完成标准
同一 Claim 获得两份独立 Session 结果。

---

## Stage 7：Fake Council 十轮

### 先不用真实模型和工具
使用：
- FakePrimary；
- FakeAuditor；
- FakeLean；
- FakeZ3；
- FakeCodex。

### 实现
- Council state graph；
- valid round；
- checkpoint；
- pause/resume；
- early stop；
- max rounds；
- invalid round 不计数。

### 测试
- 默认最多十轮；
- 用户可配置；
- 第五轮 checkpoint；
- Gate 可暂停恢复；
- 第十轮停止；
- 重启后恢复。

### 完成标准
完全无付费调用也能稳定跑流程。

---

## Stage 8：Z3、Python Sandbox、Lean Compiler

### 顺序
1. Z3；
2. Python Sandbox；
3. Lean Compiler。

### Z3
实现 ConstraintSpec，不允许模型直接注入任意 Python。

### Python
Docker，无网络，无 secrets。

### Lean
固定命令模板，锁定 theorem statement hash。

### 完成标准
三类 Tool Evidence 能真实生成。

---

## Stage 9：真实 Council

将 Stage 6 的真实模型与 Stage 8 工具接入 Fake Council。

### 完成标准
完成第一个真实简单 Claim：
- 反例；
- 修复；
- 语义审计；
- Lean PASS；
- 用户确认。

---

## Stage 10：Codex 入站——让 Codex 调平台

### 实现
- MCP Server；
- Synaisthesis Operator Skill；
- plugin manifest；
- MCP resources；
- 状态轮询。

### 测试
使用 MCP Inspector 与 Codex：
- 创建项目；
- 查询状态；
- 启动 Run；
- 处理 Gate；
- 导出。

### 完成标准
用户不离开 Codex 即可完整操作平台。

---

## Stage 11：Codex 出站——让平台调 Codex

### 首选
安装 `openai-codex`，使用 AsyncCodex。

### 实现
- CodexTaskSpec；
- CodexSession；
- CodexExecutionReceipt；
- worktree；
- sandbox；
- thread resume；
- diff；
- test receipt。

### 第一个任务
让 Codex 在临时 worktree 修复一个故意制造的 Lean 语法错误，再由 Lean Adapter 独立复验。

### 完成标准
平台能在 Council 中调起 Codex，并保存可复现回执。

---

## Stage 12：双向递归防护

### 实现
- operator/worker profiles；
- origin chain；
- delegation depth；
- reentrancy key；
- worker 禁用 Synaisthesis MCP；
- token scope。

### 测试
构造：
- Codex Operator 启动平台；
- 平台调 Codex Worker；
- Worker 尝试再启动平台；
- 必须返回 REENTRANCY_BLOCKED。

### 完成标准
双向集成不能无限递归。

---

## Stage 13：文献与原创性

### 数据源
- OpenAlex；
- Crossref；
- arXiv；
- 可选 Semantic Scholar。

### 实现
- 查询扩展；
- metadata 验证；
- 去重；
- 最近邻分类；
- novelty status；
- 外部内容隔离。

### 完成标准
已知经典结果被识别为重合；冷门结果只给 POSSIBLY_ORIGINAL。

---

## Stage 14：Web UI

页面：
- Dashboard；
- Incubator；
- Claim；
- Council Run；
- Round；
- Evidence Ledger；
- Gate；
- Codex Task；
- Settings。

优先显示：
- 当前阶段；
- 当前轮次；
- 语义状态；
- 工具状态；
- 未解决 Attack；
- 成本；
- Gate；
- diff。

---

## Stage 15：评估与真实 Case Study

把用户现有数学研究中的一个小 Claim 作为首个真实案例。

要求：
- 完整事件日志；
- 至少一个失败；
- 至少一次修复；
- 至少一次 Gate；
- 至少一个工具验证；
- 可导出 bundle；
- Demo GIF。

---

## Stage 16：后期增强

按优先级：
1. LeanDojo-v2；
2. 多分支修复搜索；
3. PostgreSQL；
4. Remote MCP；
5. 多用户；
6. App Server 深度嵌入；
7. cvc5/SageMath；
8. 跨证明器交叉验证。

## 开发纪律

每次：
1. 实现一个函数；
2. 写单元测试；
3. 用 Fake Provider；
4. 再接真实外部系统；
5. 提交 Git；
6. 更新 ADR；
7. 更新 Changelog。

禁止：
- 未完成状态层就写 UI；
- 未有 FakeModel 就接付费模型；
- 未有 ActionBroker 就让 Codex 写主仓库；
- 未锁定 statement 就做 Proof Loop；
- 未有 Recursion Guard 就开启双向 Codex。

## 推荐首个垂直切片

为了尽快获得可用成果，建议优先完成：

1. S0–S5 持久化；
2. Synaisthesis MCP；
3. Codex Operator Skill；
4. ClaimContract；
5. Fake 十轮；
6. 双模型；
7. Z3；
8. Lean；
9. Codex Worker。

这比先做完整 Web UI 更快证明项目价值。

## Stage 0.5：先建立 Codex 指令忠实通道

由于用户主要在 Codex 操作，以下工作前移为 P0，并早于开放任何 mutation：

1. 建 `CodexSessionBinding`、`InstructionCapsule`、`InstructionToken`。
2. 建本地 `synaisthesis-codex-bridge`。
3. 安装 UserPromptSubmit Hook，验证能取得原始 prompt、session_id、turn_id。
4. 建 `research_bind_codex_session` 与只读状态查询。
5. 建 PreToolUse Hook，只允许带有效 token 的 Synaisthesis mutation。
6. 建 expected_state_version 与 idempotency。
7. 建 `research_prepare_command` / `research_commit_command`。
8. 建 CommandReceipt。
9. 建 PostToolUse / Stop 输出忠实检查。
10. `research_codex_doctor` 全部 PASS 后，才解锁原有 Stage 10 的完整 Codex 操作。

本阶段完成标准：

- Codex 不能改变 loop_rounds、目标 Claim 或否定约束而不被发现；
- 无 Hook/token 时 mutation 被服务端拒绝；
- 用户不离开 Codex 即可完成绑定、准备、确认、执行和查看回执；
- Codex 省略平台关键状态时 Stop Hook 会要求修正。
