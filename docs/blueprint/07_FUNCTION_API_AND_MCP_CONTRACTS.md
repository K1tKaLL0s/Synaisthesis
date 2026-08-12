# 07 — 函数、服务、API 与 MCP 契约

本文不提供实现代码，只规定应实现的函数、输入输出和责任边界。

## 1. 配置与启动

### `load_settings`
读取配置文件和环境变量，输出 Settings。

### `validate_settings`
检查：
- 默认轮数大于零；
- Primary/Auditor 已配置；
- 工作目录存在；
- 工具 timeout 合法；
- Codex 双向配置无递归风险。

### `doctor`
检查数据库、Artifact Store、模型、Lean、Z3、Docker、Git、Codex SDK、Codex 登录、MCP 与 Recursion Guard。

## 2. Incubator

### `capture_seed`
创建 SeedRecord。

### `validate_seed_record`
检查原文保留与观察/解释分离。

### `create_stage_run`
建立 StageRun。

### `execute_stage`
调用对应 Agent/Tool。

### `validate_stage_output`
执行 Schema 与业务规则。

### `evaluate_stage_gate`
计算 PASS/PARTIAL/BLOCKED/NOT_TESTED。

### `advance_stage`
合法状态转移。

### `rollback_stage`
创建回退事件，保留旧 Artifact。

### `create_wip_checkpoint`
每五个有效轮次执行。

### `evaluate_mature_idea_ready`
计算成熟门。

## 3. Claim Compiler

### `extract_candidate_claims`
从 S6/S7 提取候选主张。

### `split_claim_into_atomic_units`
拆分混合命题。

### `classify_claim`
输出 ClaimClass。

### `define_falsification_witness`
定义反例结构。

### `build_claim_dependency_graph`
建立依赖。

### `validate_claim_atomicity`
检查能否独立验证。

### `build_claim_contract`
生成冻结候选。

### `freeze_claim_contract`
只有用户确认或策略允许时执行。

### `verify_claim_contract_hash`
每轮开始检查。

## 4. Role Isolation

### `create_role_session`
创建独立会话。

### `build_visibility_bundle`
根据 role/phase 生成最小上下文。

### `validate_role_visibility`
检查是否读取禁止内容。

### `record_isolation_violation`
保存违规并阻断。

### `run_support_track`
生成 SupportPacket。

### `run_oppose_track`
生成 AttackPacket。

### `run_independent_phase_a`
盲审。

### `run_independent_phase_b`
去角色复核。

## 5. Model Provider

### `call_model`
统一异步入口。

输入：
- model profile；
- role；
- prompt version；
- visibility bundle；
- response schema；
- budget；
- trace metadata。

输出：
- StructuredModelResult。

### `validate_model_diversity`
检查 provider、model、family 与 session isolation。

### `repair_structured_output`
只修复格式，不改变研究内容。

### `record_model_invocation`
保存 tokens、成本、延迟、hash。

### `enforce_budget_before_model_call`
调用前验证剩余预算。

## 6. Council

### `start_council_run`
创建 Run。

### `begin_round`
创建快照。

### `run_council_round`
执行单轮。

### `validate_round`
判断有效性。

### `select_tool_plan`
按 ClaimClass 路由。

### `merge_round_packets`
合并结构化 Packet。

### `detect_blocking_failures`
识别 Critical/High。

### `propose_revision_candidates`
最多 N 个。

### `score_revision_candidate`
固定评分。

### `audit_semantic_delta`
S0–S4。

### `commit_revision`
不可变写入。

### `run_regression`
重跑依赖。

### `assess_round`
计算稳定分。

### `should_continue_council`
继续、早停或阻断。

### `pause_run`
暂停。

### `resume_run`
从 checkpoint 恢复。

### `cancel_run`
终止但保留历史。

## 7. ActionBroker

### `create_action_request`
创建请求。

### `classify_action_risk`
READ / WRITE / NETWORK / COST / SECRET / DESTRUCTIVE。

### `evaluate_action_policy`
自动允许、Gate 或拒绝。

### `approve_action`
仅授权主体调用。

### `execute_authorized_action`
调用对应 Adapter。

### `create_execution_receipt`
绑定参数、结果、时间与 hash。

### `verify_execution_receipt`
检查完整性。

## 8. Lean

### `prepare_lean_workspace`
建立独立环境。

### `write_lean_candidate`
写入 Artifact。

### `freeze_lean_statement_hash`
锁定 theorem statement。

### `run_lean_check`
调用 Lean/Lake。

### `parse_lean_feedback`
错误分类。

### `verify_statement_unchanged`
Proof Loop 保护。

### `record_lean_evidence`
只有真实成功才写 LEAN_KERNEL_ACCEPTED。

### `request_codex_lean_repair`
将受控修复任务交给 Codex。

## 9. Z3

### `build_constraint_spec`
模型输出结构化约束，不能直接注入任意 Python。

### `compile_constraint_spec_to_z3`
构造 Z3 对象。

### `search_counterexample`
检查假设 + 否定结论。

### `extract_model_witness`
提取反例。

### `revalidate_model_witness`
独立 evaluator 再检查。

### `record_z3_evidence`
区分 SAT/UNSAT/UNKNOWN。

## 10. Python Sandbox

### `create_sandbox_job`
定义输入与资源。

### `validate_sandbox_job`
禁止 secrets、宿主路径和未授权网络。

### `run_sandbox_job`
Docker 执行。

### `collect_sandbox_receipt`
收集日志和结果。

### `terminate_sandbox_job`
超时停止。

## 11. Codex Worker

### `route_task_to_codex`
判断是否工程型。

### `build_codex_task_spec`
生成最小任务。

### `start_codex_session`
使用 SDK/MCP/exec。

### `run_codex_task`
执行。

### `continue_codex_session`
继续 thread。

### `collect_codex_execution_receipt`
收集 diff、测试与 hash。

### `verify_codex_output`
由确定性工具复验。

### `detect_codex_reentrancy`
阻止循环调用。

### `close_codex_session`
结束。

## 12. Evidence

### `create_evidence`
保存 Evidence。

### `bind_evidence_to_claim`
建立关系。

### `calculate_evidence_scope`
确定范围。

### `revoke_evidence`
撤回。

### `cascade_revalidation`
触发依赖回归。

### `build_claim_evidence_view`
形成账本视图。

## 13. Human Gate

### `open_gate`
创建。

### `resolve_gate`
保存用户决定。

### `validate_gate_actor`
防止模型代替用户。

### `resume_after_gate`
继续。

## 14. FastAPI 端点

- POST `/projects`
- GET `/projects`
- GET `/projects/{id}`
- POST `/projects/{id}/seed`
- POST `/projects/{id}/stages/{stage_id}/run`
- POST `/specs/{id}/confirm`
- POST `/projects/{id}/claims/compile`
- POST `/claims/{id}/freeze`
- POST `/claims/{id}/council-runs`
- GET `/runs/{id}`
- GET `/runs/{id}/rounds`
- POST `/runs/{id}/pause`
- POST `/runs/{id}/resume`
- POST `/runs/{id}/cancel`
- GET `/gates`
- POST `/gates/{id}/resolve`
- GET `/claims/{id}/evidence`
- GET `/artifacts/{id}`
- POST `/projects/{id}/export`
- GET `/events`

## 15. CLI 命令

- `synaisthesis init`
- `synaisthesis serve`
- `synaisthesis doctor`
- `synaisthesis project create`
- `synaisthesis seed import`
- `synaisthesis stage run`
- `synaisthesis spec confirm`
- `synaisthesis claim compile`
- `synaisthesis claim freeze`
- `synaisthesis council start`
- `synaisthesis run status`
- `synaisthesis run pause`
- `synaisthesis run resume`
- `synaisthesis gate list`
- `synaisthesis gate resolve`
- `synaisthesis export`

## 16. MCP Tools

保持粗粒度。禁止暴露：
- 直接写数据库；
- 直接赋予 PASS；
- 直接调用 Lean/Z3；
- 直接修改 FrozenClaim。

推荐：

- `research_create_project`
- `research_capture_seed`
- `research_get_project_state`
- `research_advance_stage`
- `research_confirm_spec`
- `research_compile_claims`
- `research_freeze_claim`
- `research_start_council`
- `research_get_run_status`
- `research_get_pending_gates`
- `research_resolve_gate`
- `research_pause_run`
- `research_resume_run`
- `research_cancel_run`
- `research_export_bundle`

## 17. 幂等性

所有 mutation 接口接受：
- `idempotency_key`
- `trace_id`
- `expected_version`

若 expected_version 不匹配：
- 返回 CONFLICT；
- 不自动覆盖；
- 要求重新读取状态。

## 18. 错误对象

统一错误：

- error_code
- message
- recoverable
- retry_after
- blocker_type
- required_user_action
- artifact_refs
- trace_id

不得只返回自然语言“失败了”。

## 17. Codex Instruction Fidelity Layer

### Sidecar / Hook 函数

- `capture_codex_user_prompt`：接收 UserPromptSubmit 事件并保存原始指令。
- `bind_codex_session`：绑定 Codex session 与 Synaisthesis project。
- `persist_instruction_capsule`：创建不可变原文 Artifact 和 hash。
- `issue_instruction_token`：签发短期、turn-scoped token。
- `load_current_instruction_for_tool_call`：为 PreToolUse 取得当前指令。
- `inject_instruction_transport_fields`：重写 Synaisthesis MCP 参数，加入 token、instruction_id、state_version。
- `record_tool_display_contract`：保存 PostToolUse 返回的展示要求。
- `validate_codex_final_response`：Stop 阶段检查是否忠实展示。

### Command Gateway 函数

- `validate_instruction_token`
- `resolve_instruction_capsule`
- `resolve_context_manifest`
- `build_platform_interpretation`
- `compare_command_proposal_to_instruction`
- `classify_instruction_delta`
- `enforce_expected_state_version`
- `enforce_instruction_sequence`
- `prepare_command`
- `issue_confirmation_challenge`
- `capture_user_confirmation`
- `commit_prepared_command`
- `invalidate_superseded_commands`
- `create_command_receipt`
- `create_display_contract`
- `reconcile_instruction_change`

### 对外 MCP Tools

只读：
- `research_get_project_state`
- `research_get_run_status`
- `research_get_pending_gates`
- `research_get_bound_session`
- `research_get_command_receipt`
- `research_codex_doctor`

会话与上下文：
- `research_bind_codex_session`
- `research_unbind_codex_session`
- `research_register_context`

统一 mutation：
- `research_prepare_command`
- `research_commit_command`
- `research_cancel_prepared_command`
- `research_reconcile_instruction`

所有 mutation 的业务处理最终仍调用原 Core Service，但外部 Codex 不再直接调用底层 mutation tools。
