# 05 — Synaisthesis 与 Codex 的双向无缝集成

## 1. 两个方向

### 方向 A：Codex 调 Synaisthesis
用户在 Codex 中发出科研任务，Codex 通过 Synaisthesis MCP Server 操作平台。

### 方向 B：Synaisthesis 调 Codex
Synaisthesis 将工程型任务交给 Codex，例如：
- 修改 Lean 文件；
- 修复编译错误；
- 构建 Z3/Python harness；
- 分析研究仓库；
- 实现实验；
- 执行测试；
- 生成可审计 diff。

## 2. Codex → Synaisthesis

### 技术路径
- Synaisthesis 提供 MCP Server；
- Codex Plugin 打包 Operator Skill + MCP 配置；
- Codex 只做交互入口，不在会话中自行模拟研究状态。

### 推荐 MCP Tools
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

### 推荐 MCP Resources
- `research://projects/{project_id}/state`
- `research://projects/{project_id}/spec`
- `research://claims/{claim_id}`
- `research://runs/{run_id}/rounds`
- `research://runs/{run_id}/evidence`
- `research://runs/{run_id}/artifacts`
- `research://gates/{gate_id}`

### Codex Skill 的职责
- 识别什么时候应调用 Synaisthesis；
- 先查询状态再 mutation；
- 把 Gate 翻译给用户；
- 不替用户批准核心语义变化；
- 不把模型输出说成工具验证；
- 不在聊天中伪造十轮 Loop。

### 长任务
`research_start_council` 立即返回 run_id，Codex 轮询状态；不要保持一个超长 MCP 调用直到十轮结束。

## 3. Synaisthesis → Codex

### 3.1 首选：Codex Python SDK

Synaisthesis 核心使用 Python，因此首选稳定版 `openai-codex` 与 `AsyncCodex`。

建议模块：
`integrations/codex/sdk_adapter.py`

建议函数：

#### `start_codex_session`
输入：
- CodexTaskSpec；
- model；
- cwd；
- sandbox；
- worker_profile。

输出：
- CodexSessionRecord；
- thread_id。

#### `run_codex_task`
运行一个 turn。

#### `continue_codex_task`
使用 thread_id 继续。

#### `review_codex_result`
以 read-only sandbox 进行同线程自审；必须标记为同源检查，不算独立审查。

#### `collect_codex_execution_receipt`
收集：
- final response；
- thread id；
- start/end time；
- changed files；
- git diff；
- stdout/stderr；
- tests；
- artifact hashes；
- sandbox；
- approval policy；
- model；
- cwd。

#### `cancel_codex_session`
终止。

#### `validate_codex_receipt`
验证文件范围、hash 与测试结果。

### 3.2 兼容：Codex MCP Server

启动 `codex mcp-server`，Synaisthesis 作为 MCP Client 调用：

- `codex`
- `codex-reply`

适合：
- 把 Codex 当标准 MCP 专家；
- 未来切换编排器；
- 不希望 Core 紧耦合 SDK 对象。

建议模块：
`integrations/codex/mcp_adapter.py`

### 3.3 回退：codex exec

适合：
- CI；
- 单次无状态任务；
- 脚本化；
- SDK 不可用时。

建议模块：
`integrations/codex/exec_adapter.py`

### 3.4 App Server 的位置

Codex App Server 适合构建深度自定义客户端、审批 UI、历史与流事件。MVP 不直接依赖它，因为：

- SDK 已适合自动化；
- Synaisthesis 有自己的 UI 与状态；
- 远程 App Server 增加协议和安全复杂度。

后期若要在 Synaisthesis UI 中完整嵌入 Codex 对话，再增加 App Server Bridge。

## 4. CodexTaskSpec

字段：

- task_id
- root_run_id
- parent_round_id
- task_type
- objective
- repository_path
- worktree_path
- allowed_files
- read_context_artifacts
- expected_outputs
- expected_output_schema
- tests_to_run
- sandbox
- approval_policy
- network_policy
- secret_policy
- model
- max_turns
- timeout
- cost_budget
- origin_chain
- delegation_depth
- prompt_version

### task_type
- REPO_ANALYSIS
- LEAN_FILE_CONSTRUCTION
- LEAN_PROOF_REPAIR
- Z3_HARNESS_CONSTRUCTION
- PYTHON_EXPERIMENT_IMPLEMENTATION
- TEST_EXECUTION
- ARTIFACT_REFACTOR
- DIFF_REVIEW
- EXPORT_BUILD

## 5. Codex 的证据边界

Codex 的自然语言结论默认属于：
- ASSISTANT_PROPOSAL。

Codex 真实产生并被平台验证的文件、测试日志和 diff 可成为：
- EXECUTION_RESULT。

Lean Adapter 重新验证后才产生：
- LEAN_KERNEL_ACCEPTED。

Z3 Adapter 重新执行后才产生：
- SMT_MODEL 或 SMT_UNSAT_WITHIN_ENCODING。

因此：

> Codex 可以构造证明文件，但不能自行授予证明状态。

## 6. 双向调用的递归风险

危险循环：

```text
Codex Operator → Synaisthesis → Codex Worker → Synaisthesis → Codex Worker → ...
```

必须从架构上禁止。

### 6.1 双 Profile

#### `codex-operator`
- 面向用户；
- 安装 Synaisthesis Plugin；
- 可调用 Synaisthesis MCP；
- 不直接成为内部验证器。

#### `codex-worker`
- 平台调用；
- 使用独立 CODEX_HOME/Profile；
- 默认不加载 Synaisthesis MCP；
- 只接收最小任务快照；
- 无法回调平台 mutation tools。

### 6.2 调用链字段
每个 ActionRequest 保存：

- origin
- origin_chain
- root_run_id
- delegation_depth
- max_delegation_depth
- parent_action_id
- reentrancy_key

默认：
- `max_delegation_depth = 1`；
- 同一 root_run 内 Codex Worker 不得再次触发 Codex Worker；
- 相同 reentrancy_key 拒绝重复执行。

### 6.3 服务端防线

即使 worker 意外获得 MCP：
- worker token 只允许 read-only；
- mutation tool 检查 origin；
- origin=CODEX_WORKER 时拒绝启动新 CodexTask；
- 返回 `REENTRANCY_BLOCKED`。

## 7. 工作区隔离

每个 CodexTask 使用独立 Git worktree 或临时目录。

### read-only
用于仓库分析、diff review、文档检查。

### workspace-write
用于 Lean/Python/Z3 文件构造、测试修复、实验实现。

### full access
默认禁用。

任务结束：
- 保存 diff；
- 运行允许测试；
- 创建 ExecutionReceipt；
- 不自动合并主分支；
- 是否合并由 Policy 或 Human Gate 决定。

## 8. 认证与密钥

- Codex SDK 使用本地 Codex 登录或 API key；
- 凭据不写入 ResearchBundle；
- API key 不传入研究代码执行容器；
- Codex Worker 与 Python Sandbox 分离；
- 研究仓库脚本不能读取平台 LLM/Codex 密钥；
- 只在启动 Codex 进程时注入最小凭据环境。

## 9. Codex → 平台标准时序

1. 用户在 Codex 发出研究请求；
2. Operator Skill 调 `research_get_project_state`；
3. 调 `research_capture_seed` 或 `research_advance_stage`；
4. 平台返回 Stage 状态；
5. 需要 Gate 时 Codex 展示；
6. 用户明确批准；
7. Codex 调 `research_resolve_gate`；
8. 平台继续；
9. Codex 查询 run status；
10. 导出 bundle。

## 10. 平台 → Codex 标准时序

1. Council 生成 CodexTaskSpec；
2. ActionBroker 分类权限；
3. Policy 允许或触发 Gate；
4. CodexWorkerAdapter 建 worktree；
5. 启动 AsyncCodex；
6. Codex 执行；
7. 收集 ExecutionReceipt；
8. Tool Adapter 独立复验；
9. Evidence Ledger 写入；
10. Round 继续或进入修复。

## 11. 配置项

- `codex.enabled`
- `codex.transport = sdk | mcp | exec`
- `codex.model`
- `codex.worker_profile`
- `codex.default_sandbox`
- `codex.default_approval_policy`
- `codex.network_enabled`
- `codex.max_tasks_per_round`
- `codex.max_turns_per_task`
- `codex.timeout_seconds`
- `codex.max_delegation_depth`
- `codex.synaisthesis_mcp_enabled_for_worker = false`
- `codex.worktree_root`
- `codex.preserve_threads`
- `codex.preserve_rollouts`

## 12. Codex 任务路由

优先交给 Codex：
- 多文件工程；
- 仓库导航；
- Build/Test；
- Lean import 与语法修复；
- 实验 harness；
- 需要理解现有代码库的修改。

不优先交给 Codex：
- 原始自然语言语义裁决；
- 原创性最终判断；
- 用户价值选择；
- 形式证明最终 PASS；
- 同一 Claim 的独立数学审稿。

这些仍由 Primary/Auditor/Verifier/Human 分担。

## 13. v2.1 强制要求：Codex 指令忠实传递

Codex → Synaisthesis 不再只依赖 Operator Skill。完整模式必须启用 `05A_CODEX_INSTRUCTION_FIDELITY_PROTOCOL.md` 定义的 CIFL：

- UserPromptSubmit 捕获用户原文；
- Sidecar 保存 InstructionCapsule 并签发 token；
- PreToolUse 为 MCP mutation 注入传输凭据；
- 服务端比较原文、CommandProposal 与执行计划；
- 高风险命令两阶段提交；
- Stop Hook 检查最终回传。

原有推荐 MCP mutation 工具调整为通过统一 `research_prepare_command` / `research_commit_command` 对外暴露。若当前 Codex Surface 无法运行 Hook，平台只开放 read-only，不能声称达到 `FIDELITY_VERIFIED`。
