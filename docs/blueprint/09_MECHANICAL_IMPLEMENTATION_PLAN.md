# 09 — 机械式、可碎片化实施方案

原则：每个阶段都能运行、测试和提交 Git。不要同时开发 UI、Lean、MCP 和多模型。

本文件规定 Stage 目标；`19_MECHANICAL_EXECUTION_CONTRACT.md` 规定稳定 Task ID、允许文件、关键符号、前置条件、验证命令、通过/停止条件。没有完整 `WorkUnitContract` 时不得开始实现。

Stage 0.5 的编号表示安全优先级。实际硬依赖是 Stage 1 的领域/Event/Artifact 基础，其完成门位于 Stage 10 开放任何外部 Codex mutation 之前；它不阻断 Stage 1–9 的内部实现。

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

## Stage 2：搬运 S0–S4 并形成自然语言设计完成门

### 任务
将当前 Skill 中表现良好的内容变成：
- StageContract；
- Pydantic Schema；
- Prompt Asset；
- Validation Rule。

### 函数
- `capture_seed`
- `execute_s0` 至 `execute_s4`
- `validate_stage_output`
- `evaluate_stage_gate`
- `advance_stage`

### 测试
把现有成功对话作为 golden cases。

### 完成标准
不依赖 Codex 会话历史，也能从输入形成用户确认的 S1/S4 与 `NATURAL_LANGUAGE_DESIGN_READY`。

---

## Stage 2.5：RQ0–RQ4 早期形式化与新颖性资格

### 实现顺序
1. RQ Domain、状态、Gate、Event 与 migration；
2. Fake academic/engineering prior-art provider；
3. 高能力 Profile 检查与外部导入合同；
4. RQ2F 理论/工程适配谓词、双评估与保守聚合；
5. `ENGINEERING_ROUTE_DECISION` 和 `FORMALIZATION_FEASIBILITY_DECISION`；
6. RQ2M FormulaBundle Schema、符号/语义/失败公式验证；
7. RQ2E EngineeringConceptBundle、单位/阈值/I/O/状态/追踪验证；
8. 路线化用户审查 Gate；
9. 两个隔离 Reviewer 与理论 50 + 应用 50、工程 60 + 应用 40 的保守聚合；
10. route-aware 70/69 路由；
11. S5、ENG0 及后续成熟门的强制前置检查。

### 完成标准
- 无资格能力路线时阻断；
- 检索同时覆盖学术与成熟工程近邻；
- 理论不适配、工程适配时只打开用户 Gate，不自动转工程；
- 理论路线核心形式化全部为数学公式；工程路线概念以公式化 I/O、状态、要求、阈值和追踪关系表达；
- 用户批准绑定具体 hash；
- 理论路线有效总分 70 自动进入 S5，工程路线有效总分 70 自动进入 ENG0；
- 69、INCONCLUSIVE 或覆盖不足交还用户；
- Fake 路径在 CI 中可重复，真实 Provider 在 Stage 6/13 接入。

---

## Stage 2.6：ENG0–ENG10 工程转化、机械蓝图与论文交付

### 实现顺序
1. Engineering workflow Domain、Artifact、状态、事件、Gate 与 migration；
2. ENG0 mission charter 和 ENG1 ConOps；
3. ENG2 Requirement Schema、验收目录和双向追踪；
4. ENG3 Fake reference/trade study 与冻结权重策略；
5. ENG4 architecture/interface/data/state/security 机器对象、ADR 和文本图源渲染；
6. `ENGINEERING_ARCHITECTURE_REVIEW`；
7. ENG5 `MechanicalEngineeringBlueprint` 与原子 `EngineeringWorkUnitContract`；
8. Blueprint Completeness Gate；
9. ENG6 `BLUEPRINT_ONLY` 与需要独立授权的 `BUILD_AND_EVALUATE` 分流；
10. ENG7 应用/扩展 Portfolio；
11. ENG8 EngineeringMasterManuscript、ClaimEvidenceMatrix、独立母稿审计与母稿交付；
12. `FORMAL_MANUSCRIPT_DECISION`：KEEP_MASTER_ONLY 或用户选择 WRITE；
13. ENG9 双路线 Profile Registry、工程四刊/arXiv/扩展 Profile、freshness、Venue adapter、Compliance 与 ReproducibilityArtifact；
14. ENG10 独立 Auditor、manifest/checksum 和最终用户验收；
15. API/CLI/MCP/Fake E2E 纵向切片。

### 确定技术路线
- 系统工程主线采用 stakeholder/ConOps → requirements → logical decomposition/trade study → architecture → implementation tasks → verification/validation；
- 需求、设计、任务、测试与论文主张通过稳定 ID 双向追踪；
- 图示以机器对象为权威，使用 Mermaid/PlantUML/C4-PlantUML 等文本源生成 SVG；
- 软件质量按适用 ISO/IEC 25010 特性转成项目阈值，安全开发按 NIST SSDF 映射活动和证据；
- 论文先交付期刊中立母稿；只有用户选择 WRITE 后才按工程四刊、工程 arXiv 或扩展 Profile 生成适配稿 + 合规矩阵；
- 没有真实实现/实验时只允许 Design/Protocol Draft，禁止虚构结果。

### 完成标准
- 只有已确认工程路线且通过 RQ4E 的项目可进入 ENG0；
- Critical requirements 100% 具有来源、验收、设计、任务和验证映射；
- 机械任务无未决产品/架构选择、无模糊动词，均有验证与停止条件；
- 所有图源可重渲染、稳定 ID 可回链；
- 未授权时不执行代码/实验，工作流仍能输出 `BLUEPRINT_ONLY` 交付候选；
- 每个论文结果 claim 都有真实 receipt，或被标为 planned/删除；
- 用户选择 KEEP_MASTER_ONLY 时不生成适配稿仍属于完整交付；arXiv 始终标为预印本平台；
- 最终工程包、manifest 和 checksum 可复算。

---

## Stage 3：S5–S10 与 MATURE_IDEA_READY

### 实现
- TheoryKernel；
- FormalizationPlan；
- PreFreezeAttackReport；
- OpenQuestionRegistry；
- HandoffBundle；
- computed maturity gate。
- S5 的 RQ 前置检查；

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

## Stage 9.5：纯数学理论论文母稿与正式发布适配

### 实现顺序
1. TP0 `TheoryPublicationEvidenceBaseline`，冻结 statement/proof/evidence/semantic/citation Scope；
2. TP1 `TheoryMasterManuscript`、`MathematicalManuscriptClaim[]`、Proof Dependency Graph 与 TeX/PDF 真实编译；
3. TP2 隔离 Theory Manuscript Auditor、母稿交付和 `FORMAL_MANUSCRIPT_DECISION`；
4. 用户选择 KEEP_MASTER_ONLY 时直接形成论文交付；
5. 用户选择 WRITE 时，TP3 从理论四刊、数学 arXiv 或 CUSTOM Profile 中选择；
6. TP4 Venue Adapter、ComplianceMatrix、作者输入登记和独立审计；
7. TP5 manifest/checksum、proof/reproducibility artifact 和导出；
8. API/CLI/MCP/Fake E2E。

### 内置 Profile
- Annals of Mathematics；
- Journal of the American Mathematical Society；
- Inventiones mathematicae；
- Acta Mathematica；
- arXiv Mathematics Preprint（不是期刊）；
- CUSTOM_VENUE。

工程方向同时内置 IEEE TSE、ACM TOSEM、Empirical Software Engineering、Journal of Systems and Software 与工程/计算 arXiv；JOSS/Nature Profile 保留为扩展。

### 完成标准
- 理论最终 ResearchBundle 必含独立审计通过的母稿；
- 定理 statement hash、对象域、量词、假设、proof status 和证据 100% 可追踪；
- conjecture/partial/solver-scope 结果不能升格为 theorem；
- 母稿先交付，用户明确 WRITE 后才生成正式适配稿；
- arXiv Profile 校验 TeX 源、图、BibTeX、metadata、license、category 与真实编译，且不产生同行评审状态；
- 指南过期、作者输入缺失或适配改变 statement 时不能 READY。

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

## Stage 13：生产级相邻工作检索与新颖性

### 数据源
- OpenAlex；
- Crossref；
- arXiv；
- 可选 Semantic Scholar。
- 工程来源按领域使用官方仓库、包注册表、官方项目/产品文档与标准资料；

### 实现
- 查询扩展；
- metadata 验证；
- 去重；
- 最近邻分类；
- novelty status；
- 工程成熟度证据；
- RQ1 真实检索回执；
- RQ4 两 Reviewer 生产评分；
- 外部内容隔离。

### 完成标准
已知经典结果被识别为重合；工程近邻按功能/应用排序；覆盖不足只能 INCONCLUSIVE；理论/工程可行性分流、用户工程路线决定和两种新颖性 policy 的 70/69 路由可复现；生产 Provider 可支撑 ENG3 的参考方案检索。

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
- 未通过 RQ0 能力门就生成早期形式化；
- 未批准当前 FormulaBundle hash 就启动新颖性审查；
- 新颖性总分低于 70 时自动重做研究或自动继续；
- 未有 ActionBroker 就让 Codex 写主仓库；
- 未锁定 statement 就做 Proof Loop；
- 未有 Recursion Guard 就开启双向 Codex。

## 推荐首个垂直切片

为了尽快获得可用成果，建议优先完成：

1. S0–S4 持久化；
2. RQ0–RQ4 Fake/外部导入与理论/工程分流纵向切片；
3. ENG0–ENG10 `BLUEPRINT_ONLY` Fake 纵向切片；
4. S5 持久化；
5. Synaisthesis MCP；
6. Codex Operator Skill；
7. ClaimContract；
8. Fake 十轮；
8. 双模型；
9. Z3；
10. Lean；
11. Codex Worker。

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
