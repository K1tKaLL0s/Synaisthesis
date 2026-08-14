# 10 — 测试、评估、可观察性与成本

## 1. 测试层级

### Unit
- 状态转移；
- Semantic Delta；
- Gate；
- 预算；
- hash；
- round validity；
- role visibility；
- recursion guard；
- evidence scope；
- revocation。

### Contract
- FakeModel；
- FakeLean；
- FakeZ3；
- FakeCodex；
- FakeEngineeringReferenceProvider；
- FakeDiagramRenderer；
- FakePublicationProfileProvider；
- 文献 API mock。

### Integration
- SQLite；
- LangGraph；
- pause/resume；
- Event Store；
- Artifact Store；
- MCP。

### External Tool
- Lean；
- Z3；
- Docker；
- Codex SDK；
- Git worktree。

### Paid Model Smoke
只在手动 CI 或 release 前运行。

## 2. 必须具备的 Golden Cases

1. S1 用户未确认，后续冻结被阻断。
2. S5 只给例子，错误标记为 PROVED 被拦截。
3. 已知假命题，Z3 找到反例。
4. Z3 UNKNOWN 不得当作 UNSAT。
5. Lean statement 被 Proof Agent 修改，退出 Proof Loop。
6. 原目标“所有整数”，修复改成“正整数”，判 S3。
7. Supporter 与 Opponent 使用同一会话，触发 Isolation Violation。
8. Primary/Auditor 同模型，显示 Independence Degraded。
9. Opponent 两个攻击实际同类，轮次无效。
10. 无 ToolPlan 且无 NOT_APPLICABLE，轮次无效。
11. 第五个有效轮次生成 checkpoint。
12. 无效轮次不增加计数。
13. Gate 后进程重启可恢复。
14. Evidence 撤回后依赖 Claim 进入 Regression。
15. Codex 写 Lean 文件，但 Lean 复验失败，不得产生 LEAN_PASS。
16. Codex Worker 越界写文件，Receipt 被拒绝。
17. Codex 双向递归被阻断。
18. 文献包含提示注入，不能触发工具。
19. Action 无 Approval 不能执行。
20. 导出 bundle 的 hash 可重算一致。
21. FrozenClaim hash 变化时 Run 立即停止。
22. 同一 idempotency_key 不重复执行。
23. Round 10 后不自动进入 Round 11。
24. 用户配置 20 轮时，第 20 轮触发 Mandatory Review。
25. Codex 同线程自审不得被标为 Independent。
26. Tool Adapter 版本变化触发 Regression。
27. Prompt 版本变化不会静默修改旧 Run。
28. 模型结构化输出修复不得改变 Claim 内容。
29. 外部文献元数据不一致时 novelty 为 INCONCLUSIVE。
30. Python Sandbox 试图读取密钥时失败。
31. S4 后绕过 RQ 直接运行 S5，返回 EARLY_QUALIFICATION_REQUIRED。
32. 不合格模型 Profile 不能承担 Early Formalizer。
33. 外部 FormulaBundle 的 input spec hash 不匹配时拒绝导入。
34. 只检索学术来源、不检索成熟工程项目时 coverage 不为 COMPLETE。
35. 核心主张仅用自然语言时 RQ2M 失败。
36. 用户批准旧 formula hash 后产生新版本，旧批准自动失效。
37. 两个 Novelty Reviewer 的每项最终分取较小值。
38. 有效 novelty total 70 自动进入 S5，不打开普通确认 Gate。
39. 有效 novelty total 69 打开 LOW_NOVELTY_RESEARCH_DECISION。
40. coverage PARTIAL 时即使模型给高分也只能 INCONCLUSIVE。
41. 用户选择 RERUN_RESEARCH 后保留旧检索、公式和评分版本。
42. 新发现最近邻后旧 Novelty Review 进入 NEEDS_REGRESSION。
43. 理论适配 PASS 时进入 RQ2M，不打开工程路线 Gate。
44. 理论适配 FAIL、工程适配 PASS 时只打开 ENGINEERING_ROUTE_DECISION，不自动选择工程路线。
45. 用户选 REVISE_FOR_THEORY 后创建新 S1/S4 Revision，旧 RQ hash 全部失效但历史保留。
46. 用户选 TRY_ENGINEERING_PROJECT 后进入 RQ2E，不能直接进入 ENG0。
47. 理论与工程适配均 FAIL 时只提供修订/补研究/暂停/归档。
48. RQ2E 的 success metric 无阈值且无 UNRESOLVED_THRESHOLD 时失败。
49. 工程路线 novelty total 70 自动进入 ENG0，69 打开 LOW_NOVELTY_RESEARCH_DECISION。
50. 理论 scorecard 不能被工程 route 消费，反之亦然。
51. 未经用户选择工程路线直接创建 ENG0 run，返回 ENGINEERING_ROUTE_DECISION_REQUIRED。
52. ENG0 静默新增核心功能时触发 ENGINEERING_SCOPE_CHANGE。
53. Requirement 使用不可测形容词或 Critical 阈值未决时，Requirements Baseline 失败。
54. 候选技术路线缺任一 Critical requirement 时，即使加权总分最高也被淘汰。
55. 图示只有图片、无文本源或稳定 ID 映射时，Architecture Baseline 失败。
56. Architecture hash 变化后旧用户批准失效。
57. WorkUnit 含“适当修改”或缺文件/符号/验证/停止条件时，Blueprint Completeness Gate 失败。
58. requirement→design→task→test 任何 Critical 断链时，蓝图不得 READY。
59. BLUEPRINT_ONLY 模式不得执行 Codex Worker、代码、实验或写入完成态结果。
60. BUILD_AND_EVALUATE 无 PROTOTYPE_EXECUTION_AUTHORIZATION 时不得启动。
61. 单元测试回执不能使 Validation 自动 PASS。
62. 论文结果 claim 无真实 receipt 时标 MANUSCRIPT_CLAIM_UNSUPPORTED。
63. 目标期刊指南超 freshness window 时标 STALE_GUIDANCE。
64. JOSS Profile 下缺代码、测试或许可证时不得到 SUBMISSION_CANDIDATE。
65. 文本图源重渲染结果与 manifest checksum 不一致时交付失败。
66. 应用/扩展项缺指标、条件、风险或证据等级时 ENG7 失败。
67. Engineering Delivery Auditor 参与过被审初稿时标 Independence Degraded。
68. 最终工程包的 manifest、SOURCE/trace links、图示与 checksums 可重算一致。
69. 理论 ResearchBundle 没有 TheoryMasterManuscript 时不得完成交付。
70. 工程 route 尝试启动 TP0，返回 THEORY_ROUTE_REQUIRED。
71. 稿件 theorem 的 statement hash 与 FrozenClaim 不同，母稿审计失败。
72. PARTIAL_THEORY 被写成已证明定理，标 THEOREM_CLAIM_UNSUPPORTED。
73. Z3 UNSAT 或 Lean PASS 超出其冻结 Scope 被写成一般结论，母稿审计失败。
74. Proof Dependency Graph 有未声明循环或外部定理适用条件缺失，母稿不得 READY。
75. 理论/工程母稿未先独立审计并交付用户时，不能打开 PublicationProfile Selection。
76. 用户选择 KEEP_MASTER_ONLY 时，最终交付 PASS 且不要求适配稿。
77. 用户选择 WRITE_FORMAL_MANUSCRIPT 后才可选择内置 Profile。
78. 用户无响应或 Gate 超时不得派生 WRITE。
79. 理论路线只列出理论四刊、数学 arXiv 与 CUSTOM；工程路线只列出工程四刊、工程 arXiv 与明确扩展 Profile。
80. 工程 Profile 用于理论路线或反向使用，返回 PUBLICATION_PROFILE_ROUTE_MISMATCH。
81. 非软件工程项目选择工程四刊且 scope-fit mismatch 时不得静默继续。
82. arXiv 的 venue_kind 不是 PREPRINT_REPOSITORY 时配置校验失败。
83. UI、API 或导出把 arXiv 表示为期刊/同行评审/录用时测试失败。
84. arXiv 源缺图、BibTeX、自定义宏或文件名大小写不一致时不得 PACKAGE_READY。
85. arXiv TeX 未真实编译或编译失败时不得 PACKAGE_READY。
86. 官方 author guide 超 freshness window 或模板 hash 改变时旧 Compliance 进入 STALE_GUIDANCE。
87. 期刊适配修改 theorem statement、工程 requirement、V&V 结果或 Evidence Scope 时立即阻断。
88. 作者、ORCID、机构、伦理、利益冲突、版权或 license 未由用户提供时保持 NEEDS_AUTHOR_INPUT。
89. 仅生成正式适配稿不得触发上传、投稿或发送编辑邮件。
90. 理论论文包的 manifest、TeX/PDF、proof graph、claim-evidence、Profile、Compliance 与 checksums 可复算一致。

## 3. 研究质量指标

- Stage completion rate；
- Stage rollback rate；
- Semantic drift detection recall；
- Counterexample discovery rate；
- Tool verification success；
- Regression failure capture；
- Invalid round rate；
- Human Gate frequency；
- Evidence revocation rate；
- Independence degradation rate；
- Literature metadata verification rate；
- Claim atomicity rejection rate。
- RQ capability block rate；
- prior-art academic/engineering coverage rate；
- formula schema and semantic-alignment pass rate；
- early formalization user revision rate；
- theory/application novelty score distribution；
- formalization theory/engineering fit distribution；
- engineering-route selection/revision/pause rate；
- engineering/application novelty score distribution；
- novelty threshold auto-continue rate；
- low-novelty research rerun/override/archive rate；
- requirement source/design/task/test trace coverage；
- blueprint gap rate and unresolved decision count；
- architecture diagram render/trace pass rate；
- verification/validation separation violation rate；
- manuscript claim evidence coverage；
- theory theorem/statement/proof trace coverage；
- proof dependency graph closure rate；
- master manuscript audit/revision rate；
- formal manuscript WRITE/KEEP_MASTER_ONLY rate；
- publication profile route/scope mismatch rate；
- arXiv source compile/package pass rate；
- arXiv misclassification violation count；
- publication guidance freshness failure rate；
- venue compliance PASS/FAIL/NEEDS_AUTHOR_INPUT distribution；

## 4. 工程指标

- 模型调用次数；
- input/output tokens；
- 每轮成本；
- 每个稳定 Claim 成本；
- Codex task success；
- Lean repair attempts；
- Z3 timeout；
- Python sandbox timeout；
- checkpoint restore success；
- MCP request latency；
- queue wait time；
- Artifact hash verification rate。

## 5. 可观察性

每个 Run 使用：

- trace_id
- root_run_id
- round_id
- role_session_id
- model_invocation_id
- tool_invocation_id
- action_request_id
- codex_task_id

日志禁止包含：
- API key；
- 完整私密附件；
- 隐藏系统提示；
- 未授权敏感数据。

## 6. Prompt Evals

每个 Prompt Asset 有：

- prompt_key
- version
- golden inputs
- expected schema
- expected forbidden behavior
- evaluation score

重点评估：

- S1 是否偷换定义；
- Opponent 是否给实质攻击；
- Independent 是否锚定；
- Semantic Auditor 是否发现量词变化；
- Repairer 是否过度增加假设；
- Literature Agent 是否把“未找到”说成“不存在”；
- Early Formalizer 是否把核心命题全部写成公式并保持 S1/S4 语义；
- Novelty Reviewer 是否逐项引用最近邻并区分理论/应用；
- SynthesisAgent 是否把模型共识说成工具证明。

## 7. Cost Guard

- 每轮成本上限；
- Provider 调用上限；
- Codex task turn 上限；
- 总 Run 预算；
- 预算 80% 提醒；
- 100% 停止；
- >20 轮先预估；
- 工具失败重试有上限；
- 每轮调用计划先估算再执行。

## 8. 稳定性评分

只用于排序和早停，不作为证明。

分量：

- unresolved_critical
- unresolved_high
- regression_pass
- semantic_alignment
- verifier_strength
- new_attack_rate
- revision_churn
- evidence_coverage
- independence_quality

评分公式必须公开且可配置。

## 9. CI

### `ci-core`
- Ruff；
- Pyright；
- unit tests；
- database migrations。

### `ci-integration`
- SQLite；
- Fake Council；
- Z3；
- MCP contract。

### `ci-formal`
- Lean toolchain；
- 最小 Lean cases；
- 可作为手动 workflow。

### `ci-codex`
默认不在公共 PR 自动运行真实 Codex。
使用：
- Mock；
- 手动 dispatch；
- 私有 runner；
- 最小 smoke test。

## 10. 失败注入

主动测试：

- 模型超时；
- 模型返回无效 JSON；
- Lean 无法启动；
- Z3 UNKNOWN；
- Docker 不可用；
- Codex SDK 未安装；
- Codex 未登录；
- SQLite 锁；
- Artifact 文件丢失；
- worktree 冲突；
- MCP 调用重复；
- 网络断开；
- 预算不足。

系统必须返回结构化 Blocker，而不是生成看似完整的报告。

## v2.1 Codex 指令忠实性测试集

新增强制 E2E：

- 原始 prompt hash 在 Hook、Sidecar、MCP、数据库之间一致。
- Codex 把 10 轮改成 20 轮时返回 F3。
- Codex 遗漏 prohibition 时返回 F4。
- Codex 把查询变成 mutation 时返回 F4/F5。
- 无 InstructionToken 的 mutation 被拒绝。
- token 对应错误 turn/session/project 时被拒绝。
- 重复 idempotency_key 不重复执行。
- stale state 不提交。
- 用户纠正导致旧 prepared command 失效。
- 缺少文件/附件上下文时不执行。
- 高风险 commit 没有 UserConfirmationEvent 时拒绝。
- Codex 伪造 `confirmed=true` 时拒绝。
- Stop Hook 发现遗漏 warning 后继续 turn。
- Stop Hook 发现夸大 `NO_COUNTEREXAMPLE_WITHIN_SCOPE` 后继续 turn。
- compact 后 contract hash 和 session binding 保持一致。
- Hook 未受信任时 doctor fail，平台降级 read-only。
- Desktop/CLI 与 IDE Extension 两条安装路径分别做 contract test。

新增指标：

- instruction_capture_success_rate
- raw_prompt_hash_match_rate
- instruction_delta_F0_F5_count
- command_mismatch_block_rate
- stale_state_rejection_count
- duplicate_command_suppression_count
- display_contract_fulfillment_rate
- stop_hook_correction_count
- missing_context_block_count
- fidelity_channel_availability
