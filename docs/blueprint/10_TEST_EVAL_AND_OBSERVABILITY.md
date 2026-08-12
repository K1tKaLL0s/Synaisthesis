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
