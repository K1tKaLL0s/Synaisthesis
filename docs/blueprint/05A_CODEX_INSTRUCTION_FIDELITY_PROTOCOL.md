# 05A — Codex 指令忠实传递协议（CIFL）

## 1. 目标与结论

用户主要在 Codex 中操作 Synaisthesis，因此 **Codex 不能只是一个“会自行理解并转述命令的聊天入口”**。它必须被改造成受审计的 Operator Client。

本协议命名为：

> **Codex Instruction Fidelity Layer，CIFL：Codex 指令忠实传递层。**

CIFL 的目标不是保证平台必然接受或执行每条命令，而是保证：

1. 用户在 Codex 中输入的原始指令被逐字保存，不依赖模型转述；
2. Codex 对该指令形成的结构化解释只能作为 `CommandProposal`，不能替代原文；
3. 平台在执行前能比较“原始指令—Codex 解释—实际执行计划”；
4. 高风险操作必须经过可验证的 prepare/commit 两阶段提交；
5. 平台结果、警告和 Gate 也必须被 Codex 忠实展示给用户；
6. 上下文压缩、会话切换、模型更换或 MCP 重试不能改变已接收指令；
7. 任何无法完成忠实校验的 mutation 默认失败关闭，而不是猜测执行。

仅依靠 Skill Prompt 无法实现上述保证。完整模式必须同时使用：

- `UserPromptSubmit` Hook；
- `PreToolUse` Hook；
- `PostToolUse` / `Stop` Hook；
- Synaisthesis MCP Server；
- 平台服务端签名、状态版本和幂等校验。

## 2. 为什么原来的 Skill-only 路径不够

Skill 可以要求 Codex“不要改变用户指令”，但模型仍可能：

- 将十轮改成“多轮”；
- 遗漏“不得改变核心语义”等否定约束；
- 把“仅研究”理解为“直接执行”；
- 把当前项目或 Claim 猜错；
- 在上下文压缩后只保留摘要；
- 误把一句讨论当作确认；
- 重试 MCP 时重复创建任务；
- 将平台的 `POSSIBLY_ORIGINAL` 转述为“已证明原创”。

因此，v2.1 将“忠实传递”从 Prompt 约束升级为协议和服务端验收条件。

## 3. 总体数据路径

```text
用户在 Codex 输入原始指令
        │
        ▼
UserPromptSubmit Hook
逐字捕获 prompt + session_id + turn_id + cwd
        │
        ▼
Codex Bridge Sidecar
保存不可变 InstructionCapsule，计算 hash，签发短期 InstructionToken
        │
        ▼
Codex 模型形成 CommandProposal
        │
        ▼
PreToolUse Hook
拦截 Synaisthesis MCP 调用，注入 token / instruction_id / state_version
        │
        ▼
Synaisthesis Command Gateway
比对原文、结构化解释、上下文清单、权限和当前状态
        │
        ├─ 不一致 / 上下文缺失 / 状态过期 → 阻断
        │
        └─ 一致 → prepare 或直接执行
        ▼
CommandReceipt + DisplayContract
        │
        ▼
PostToolUse / Stop Hook
验证 Codex 是否完整展示回执、警告和 Gate
        │
        ▼
用户
```

## 4. 本地 Codex Bridge Sidecar

新增本地组件：`synaisthesis-codex-bridge`。

它不是 LLM，也不做科研判断，只承担可靠传输：

- 接收 Hook 事件；
- 保存原始 prompt；
- 管理 Codex session 与 Synaisthesis project 的绑定；
- 生成 instruction_id、hash、nonce 和 sequence number；
- 向 Synaisthesis Command Gateway 注册指令；
- 为 PreToolUse Hook 提供签名 token；
- 缓存待展示的 DisplayContract；
- 在平台暂时不可达时保存本地 spool；
- 对重复 Hook 事件执行幂等去重。

推荐语言：Python 3.11，与 Synaisthesis Core 保持一致。

本地通信：

- Windows：localhost loopback 或命名管道；
- Linux / WSL2：Unix Domain Socket 优先，也可 localhost；
- 默认不监听非本机地址；
- 远程 Synaisthesis 由 Sidecar 转发，不让 Hook 直接持有远程长期凭据。

## 5. 三种 Codex 操作模式

### 5.1 STRICT_BOUND_SESSION — 默认推荐

Codex thread 与一个 Synaisthesis Project 绑定。

绑定后：

- 每条用户 prompt 都生成 InstructionEvent；
- 所有 mutation 必须携带有效 InstructionToken；
- 高风险操作必须两阶段提交；
- 结果展示接受 Stop Hook 审计；
- 平台不可达时，研究 mutation 默认暂停。

这是用户主要在 Codex 中操作时的默认模式。

### 5.2 EXPLICIT_RESEARCHLOOP_COMMAND

只有明确提及 Synaisthesis Skill、指定前缀或专用命令的 prompt 被捕获。

适合在同一 Codex thread 中混合普通编程与科研平台操作。

### 5.3 RELAXED_READ_ONLY

不要求完整 Prompt Hook，但只允许：

- 查询状态；
- 读取 Evidence；
- 导出只读信息；
- 查看 pending Gate。

任何 mutation 都返回 `FIDELITY_CHANNEL_REQUIRED`。

## 6. Session 绑定

新增 `CodexSessionBinding`：

- binding_id
- codex_session_id
- project_id
- optional_claim_id
- mode
- bound_at
- bound_by_user_instruction_id
- active_state_version
- sequence_number
- expires_at
- status

绑定操作必须由用户指令触发，Codex 不能静默绑定其他项目。

绑定后，`SessionStart` 和 `PostCompact` Hook 只重新注入：

- 当前 project_id；
- active claim；
- authoritative spec hash；
- state_version；
- pending gate 数量；
- “mutation 必须使用 InstructionToken”的短规则。

不得依赖解析 `transcript_path` 恢复权威语义；聊天 transcript 只可作为辅助审计资料。

## 7. InstructionCapsule：原始指令的权威载体

每次 `UserPromptSubmit` 生成一个不可变 InstructionCapsule。

字段：

- instruction_id
- session_id
- turn_id
- project_binding_id
- actor_type = HUMAN_USER
- raw_user_text
- raw_user_text_hash
- submitted_at
- cwd
- active_model
- permission_mode
- sequence_number
- supersedes_instruction_id
- context_manifest_id
- capture_source
- hook_version
- plugin_version
- bridge_version
- privacy_class
- retention_policy
- status

原则：

> 平台执行时的最终语义来源是 InstructionCapsule，而不是 Codex 对用户话语的摘要。

原文默认作为 PRIVATE Artifact 保存；公开 ResearchBundle 默认只输出 hash、必要摘录和经用户允许的版本。

## 8. InstructionToken

Hook 捕获原始指令后，由 Sidecar 或平台签发短期 token。

Token 绑定：

- instruction_id；
- session_id；
- turn_id；
- project_id；
- raw_user_text_hash；
- allowed_operation_class；
- issued_at；
- expires_at；
- nonce；
- state_version；
- signer key id。

服务端 mutation 规则：

- 没有 token：拒绝；
- token 与 session/turn 不一致：拒绝；
- token 对应 prompt hash 不一致：拒绝；
- token 已过期：要求重新 prepare；
- token 已使用且请求非幂等重试：拒绝；
- token 绑定旧 state_version：返回 `STALE_STATE`。

Codex 无法通过自由生成参数伪造用户原始指令或用户确认。

## 9. 双通道指令表示

每次操作同时保存两条通道：

### 通道 A：Verbatim Channel

不可变原始文本：

- 用户原文；
- 原文 hash；
- 原始上下文引用；
- 原始否定约束；
- 用户纠正和确认。

### 通道 B：Structured Command Channel

Codex 或平台解析得到：

- operation
- target_project
- target_claim
- scope
- parameters
- constraints
- prohibitions
- acceptance_criteria
- required_artifacts
- requested_loop_rounds
- autonomy_level
- budget_limits
- requested_tools
- expected_outputs
- confirmation_policy
- unresolved_references

通道 B 只是解释候选。通道 A 永远保留，并用于审计和争议裁决。

## 10. CommandProposal 与 PlatformInterpretation

Codex MCP 调用传入 `CommandProposal`，但平台还要依据 InstructionCapsule独立生成 `PlatformInterpretation`。

需要比较的项目：

- 操作类型；
- 项目、Claim、Revision；
- 轮数；
- 时间/成本预算；
- 自治等级；
- 允许和禁止的工具；
- 对象域与适用范围；
- 是否允许修改理论；
- 是否允许外部动作；
- 交付物；
- 停止条件；
- 用户明确保留的原话约束。

若两者不一致，Codex 的解释不能覆盖原文。

## 11. Instruction Delta 分级

Instruction Delta 与理论的 Semantic Delta 是两个独立维度。

### F0 — EXACT
结构化命令与用户原文完全一致。

### F1 — PRESENTATIONAL_ONLY
只有格式、标点、字段排序差异。

允许自动通过。

### F2 — INFERRED_DEFAULT
补充了非关键默认值，但没有改变范围、预算、权限或结论。

只读或可逆操作可继续；mutation 默认先显示 Preview。

### F3 — PARAMETER_DRIFT
轮数、目标对象、预算、工具、输出或停止条件发生变化。

阻断并要求用户确认。

### F4 — SEMANTIC_DRIFT
遗漏否定约束、改变对象域、把讨论改为执行、把候选改为冻结、把“可能”改为“已确认”等。

立即阻断。

### F5 — UNAUTHORIZED_ACTION
Codex 提议了用户未授权的删除、发布、外部通信、权限提升、预算提高或核心语义修改。

拒绝并生成 SecurityFinding。

## 12. 不允许静默规范化的字段

以下字段任何变化都不得被当作“普通摘要”：

- loop_rounds；
- max_cost；
- max_model_calls；
- target project / claim / revision；
- “只读”“不得修改”“不联网”“不发布”等 prohibition；
- A0–A3 autonomy level；
- 是否可修改 FrozenClaim；
- 是否可调用 Codex Worker；
- 是否允许网络；
- 是否允许执行代码；
- stop conditions；
- 用户要求的交付格式；
- 必须保留的失败证据；
- 用户明确的权威顺序。

## 13. ContextManifest：解决“这个文件”“上面那段”等引用

仅保存原始 prompt 还不够。任何上下文引用都必须解析到具体 Artifact。

ContextManifest 字段：

- context_manifest_id
- workspace_root
- git_commit_or_worktree
- selected_file_refs
- selected_line_ranges
- attached_artifact_refs
- active_research_spec_id
- active_claim_contract_id
- cited_instruction_ids
- artifact hashes
- unresolved_deictic_references

规则：

- 用户说“这个文件”但平台拿不到文件：`MISSING_CONTEXT`；
- 用户说“按上面的限制”但没有明确 instruction refs：先解析并展示；
- Codex 传入的文件路径必须由 Sidecar/Artifact Store 重算 hash；
- 高风险操作不允许仅凭 Codex 的文件摘要执行。

## 14. 指令优先级与纠正

新增顺序：

1. 当前用户明确纠正；
2. 当前用户明确确认；
3. USER_CONFIRMED ResearchSpec / ClaimContract；
4. 当前用户原始请求；
5. 平台 Policy；
6. Codex CommandProposal；
7. 模型推测和默认值。

用户说“上一条中的 X 改为 Y”时：

- 新建 InstructionEvent；
- 保存 `supersedes_instruction_id`；
- 不删除旧指令；
- 未执行的 PreparedCommand 自动失效；
- 已执行动作根据影响进入 rollback、reconciliation 或 Human Gate。

## 15. 状态版本与并发顺序

每个 mutation 必须携带：

- expected_state_version；
- instruction sequence_number；
- idempotency_key；
- command_id。

服务端采用 optimistic concurrency：

- state_version 一致才提交；
- 过期请求返回最新状态和 diff；
- 同一项目的 mutation 串行提交；
- Codex 队列消息或并行 thread 不得覆盖彼此；
- 相同 idempotency_key 返回同一 CommandReceipt，不重复执行。

## 16. 两阶段提交

### 16.1 可直接执行

- read-only 查询；
- 状态列表；
- Evidence 读取；
- 可撤销且无语义影响的低风险操作。

### 16.2 Prepare → Commit

以下操作必须两阶段：

- 确认 ResearchSpec；
- 冻结 ClaimContract；
- 接受 S2/S3/S4 修订；
- 启动高成本 Loop；
- 修改轮数或预算；
- 开启网络；
- 允许 workspace-write；
- 调用 Codex Worker；
- 合并 worktree；
- 删除、撤回、发布、对外发送；
- 修改授权策略。

`prepare_command` 返回：

- canonical action summary；
- preserved constraints；
- intended state diff；
- cost/permission impact；
- unresolved ambiguity；
- confirmation requirement；
- prepared_command_id；
- confirmation nonce；
- expires_at。

R3 以上操作要求用户明确输入或点击与 nonce 绑定的确认动作。Codex 不能自行提交。

## 17. 用户确认的防伪

高风险 commit 不接受 Codex 参数中的布尔值 `confirmed=true`。

确认必须产生独立 `UserConfirmationEvent`：

- 由新的 UserPromptSubmit Hook 捕获；
- 与 prepared_command_id 和 nonce 对应；
- 保存用户确认原文与 hash；
- 由平台签发 confirmation_token；
- commit 时验证 token。

因此，Codex 不能把自己的判断冒充用户批准。

## 18. MCP 外部接口重构

### 18.1 Read-only tools

保持直接调用：

- `research_get_project_state`
- `research_get_run_status`
- `research_get_pending_gates`
- `research_get_command_receipt`
- `research_get_bound_session`
- `research_export_preview`

### 18.2 统一 mutation gateway

外部 Codex mutation 优先使用：

- `research_bind_codex_session`
- `research_register_context`
- `research_prepare_command`
- `research_commit_command`
- `research_cancel_prepared_command`
- `research_reconcile_instruction`

原有 `research_advance_stage`、`research_freeze_claim`、`research_start_council` 等可保留为内部业务服务，但 Codex 不应绕过 Command Gateway 直接调用。

### 18.3 必填字段

所有 mutation MCP 输入必须包含：

- instruction_token；
- instruction_id；
- command_proposal；
- expected_state_version；
- idempotency_key；
- context_manifest_id；
- client_capabilities；
- plugin/skill/hook versions。

PreToolUse Hook 可以对 Synaisthesis MCP 调用注入或重写这些传输字段。平台仍需服务端验证，不能只信 Hook。

## 19. Hook 组合

### UserPromptSubmit Hook

职责：

- 在模型处理之前捕获完整 prompt；
- 保存 session_id、turn_id、cwd、permission_mode；
- 注册 InstructionCapsule；
- 返回 instruction_id 和当前绑定摘要作为附加上下文；
- strict mode 下捕获失败时阻断 Synaisthesis mutation。

### PreToolUse Hook

只匹配 Synaisthesis MCP 工具：

- 检查当前 turn 是否存在 InstructionCapsule；
- 注入 token、instruction_id、state_version；
- 拒绝未绑定项目的 mutation；
- 对参数越权或缺失执行 fail closed；
- 不负责最终授权，服务端再校验一次。

### PostToolUse Hook

职责：

- 保存 CommandReceipt；
- 接收 DisplayContract；
- 标记本 turn 必须向用户展示的状态、警告和 Gate。

### Stop Hook

职责：

- 检查 Codex 最终消息是否包含必要 Receipt 标识；
- 检查是否遗漏关键警告、状态或用户下一步；
- 检查是否把有限证据夸大为全局结论；
- 不合格时要求 Codex 继续并修正输出。

Hooks 是重要防线，但不是唯一防线。MCP Server 必须独立验证 token、hash、权限和状态版本。

## 20. 平台结果的忠实回传

用户不只需要“命令忠实进入平台”，也需要“平台结果忠实返回 Codex”。

每次操作产生：

### CommandReceipt

- command_id
- instruction_id
- executed_operation
- target
- starting_state_version
- ending_state_version
- accepted_parameters
- rejected_parameters
- preserved_constraints
- side_effects
- evidence_ids
- pending_gate_ids
- cost_used
- status
- receipt_hash

### DisplayContract

- display_contract_id
- receipt_id
- exact_summary_block
- mandatory_statuses
- mandatory_warnings
- mandatory_next_action
- prohibited_claims
- allowed_paraphrase_fields
- display_hash

Codex 可以在 exact summary 前后增加解释，但不能修改或省略该块。

## 21. Codex Surface 支持矩阵

### Codex Desktop / CLI

完整支持：

- MCP；
- Skill / Plugin；
- Plugin-bundled Hooks；
- strict session binding；
- Stop output audit。

### Codex IDE Extension

由于 IDE Extension 不支持 Plugin，改用：

- 共享 MCP 配置；
- repo/user `.codex/hooks.json`；
- standalone Skill / AGENTS.md 指引；
- Sidecar。

只要 Hook 与 MCP 安装并通过 doctor，仍可达到完整忠实模式。

### 无 Hook 的宿主

只能使用 read-only 或显式 prepare/commit 降级模式，不标记为 `FIDELITY_VERIFIED`。

## 22. 健康检查与显式能力声明

新增 `research_codex_doctor`，必须检查：

- MCP 已连接；
- UserPromptSubmit Hook 已启用且受信任；
- PreToolUse Hook 能看到 Synaisthesis MCP 调用；
- Stop Hook 可运行；
- Sidecar 可写本地 spool；
- token 签名与验证正常；
- session binding 可创建；
- state_version 校验正常；
- plugin、skill、hook、server schema 版本兼容；
- 当前 surface 是否支持完整模式。

Codex 每个会话开始时显示之一：

- `FIDELITY_VERIFIED`
- `FIDELITY_DEGRADED_READ_ONLY`
- `FIDELITY_UNAVAILABLE`

不得在未验证 Hook 时声称“指令已被忠实传递”。

## 23. 隐私与保留

原始 prompt 可能包含未公开研究内容。

要求：

- local spool 文件权限最小化；
- raw_user_text 默认 PRIVATE；
- ResearchBundle 默认不公开原文；
- 可配置保留周期；
- 删除操作采用 tombstone + secure local purge policy；
- 远程部署时 TLS + 用户级加密；
- Hook 输出不得回显密钥；
- transcript_path 不作为稳定数据源，也不默认上传。

## 24. 失败处理

### 平台暂时不可达

- raw prompt 先写本地 spool；
- strict bound session 的 mutation 暂停；
- read-only 可使用最后缓存状态，但明确标记 stale；
- 恢复后按 sequence_number 同步；
- 不自动执行过期的高风险 prepared command。

### Hook 未受信任或被禁用

- doctor 返回 fail；
- mutation MCP 服务端拒绝无 token 请求；
- Codex 提示用户修复安装，不降级为“模型自觉遵守”。

### Codex 参数与原文冲突

- 返回 `INSTRUCTION_MISMATCH`；
- 展示逐字段 diff；
- 不执行；
- 用户可重新表达或明确批准修改后的 PreparedCommand。

## 25. 必须通过的验收场景

1. 用户说“运行 10 轮”，Codex 传成 20：阻断。
2. 用户说“不得修改核心语义”，Codex 参数遗漏：阻断。
3. 用户只询问状态，Codex试图启动 Council：阻断。
4. 用户目标是 Claim A，Codex传 Claim B：阻断。
5. 同一 MCP 请求因重试发送两次：只执行一次。
6. 项目状态在准备与提交之间变化：返回 STALE_STATE。
7. 用户纠正上一条指令：旧 PreparedCommand 自动失效。
8. 用户说“这个文件”，但文件未注册：MISSING_CONTEXT。
9. Hook 关闭后发起 mutation：FIDELITY_CHANNEL_REQUIRED。
10. Codex省略平台的 UNDECIDED 警告：Stop Hook要求修正。
11. Codex把 `NO_COUNTEREXAMPLE_WITHIN_SCOPE`说成“已证明”：Stop Hook要求修正。
12. 会话发生 compact：权威指令与 contract hash 不丢失。
13. 多个 Codex thread并行修改同一 Claim：一个提交成功，其余 STALE_STATE。
14. Codex试图用 `confirmed=true`冒充用户：拒绝。
15. 用户确认 nonce 对应其他 PreparedCommand：拒绝。
16. Sidecar重启后从本地 spool恢复，sequence顺序不变。
17. 附件 hash 在执行前变化：阻断并要求重新确认。
18. Codex Worker回调 mutation tool：继续由 Recursion Guard 拒绝。

## 26. 实施优先级

CIFL 是 P0，不是后期增强。

建议顺序：

1. InstructionCapsule + SessionBinding；
2. 本地 Sidecar + UserPromptSubmit Hook；
3. mutation MCP 的 token 强制校验；
4. PreToolUse 注入；
5. state version + idempotency；
6. prepare/commit；
7. CommandReceipt；
8. DisplayContract + Stop Hook；
9. ContextManifest；
10. 之后才开放 Codex 内完整十轮 Council 操作。

在上述第 1–6 步未完成前，Codex 入口只开放 read-only 查询。

## 27. 官方能力依据

当前 Codex 官方文档支持本协议所依赖的关键能力：

- MCP Server instructions、STDIO 与 Streamable HTTP；
- ChatGPT Desktop、Codex CLI 和 IDE Extension 共享 MCP 配置；
- Plugin 可打包 Skill、MCP 和 lifecycle hooks；
- `UserPromptSubmit` Hook 可收到即将发送的原始 prompt；
- `PreToolUse` 可拦截并重写 MCP tool arguments；
- `PostToolUse` 和 `Stop` 可对工具结果及最终回复施加检查；
- App Server / SDK 可提供 Codex thread、turn 和事件级集成。

实现时必须锁定 Codex 版本，并使用该版本生成的 Hook/App Server schema 进行契约测试。
