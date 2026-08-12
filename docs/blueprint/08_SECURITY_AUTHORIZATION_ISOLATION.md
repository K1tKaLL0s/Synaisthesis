# 08 — 授权、隔离、安全与失败边界

## 1. A0–A3 委托模式

### A0 USER_LED
- 用户决定每一步；
- AI 仅在明确请求时运行；
- 无自主 Loop。

### A1 AI_ASSISTED
- AI 生成候选；
- 每个 Stage Gate 需用户确认。

### A2 AI_DELEGATED
- 允许自动执行低风险步骤；
- 语义和外部动作仍需 Gate。

### A3 AI_AUTONOMOUS_BOUNDED
- 在 FrozenClaim、预算、工具和风险边界内运行；
- 自动执行默认十轮或用户指定轮数；
- S2/S3/S4、敏感外部动作、超预算必须暂停。

DelegationPolicy 必须冻结进 ClaimContract。

## 2. Action 风险类别

### R0 READ
- 读取项目文件；
- 查询数据库；
- 本地只读分析。

### R1 ISOLATED_WRITE
- 写临时 worktree；
- 写 Artifact；
- 无外部副作用。

### R2 NETWORK_READ
- 文献检索；
- 下载公开依赖。

### R3 COSTLY_COMPUTE
- 大量模型调用；
- 长时间实验；
- GPU。

### R4 EXTERNAL_WRITE
- 推送 Git；
- 写远程数据库；
- 发送邮件；
- 提交论文。

### R5 SECRET_OR_SENSITIVE
- 访问密钥；
- 私有数据；
- 用户身份信息。

### R6 DESTRUCTIVE
- 删除；
- 覆盖；
- 生产环境修改。

默认：
- R0 自动；
- R1 在 A2/A3 且 allowlist 内自动；
- R2 受域名 allowlist；
- R3 受预算；
- R4–R6 必须 Human Gate。

## 3. 隔离等级

### BEHAVIORAL
仅 Prompt 约束。只能作为辅助，不能作为强隔离证据。

### SESSION
独立模型会话与上下文。

### MODEL
不同模型或模型家族。

### WORKSPACE
独立目录/worktree。

### PROCESS
独立进程。

### CONTAINER
独立容器。

### CREDENTIAL
不同权限 token。

Support/Oppose/Independent 至少要求：
- SESSION；
- Primary 与 Auditor 尽量 MODEL；
- 工具执行 WORKSPACE/PROCESS；
- Python 使用 CONTAINER；
- Codex Worker 使用 WORKSPACE + 独立 PROFILE。

## 4. 外部内容隔离

文献、网页、PDF、仓库内容可能包含 Prompt Injection。

新增 `ExternalContentQuarantine`：

- 外部内容标记为 untrusted；
- 不允许其中指令获得工具权限；
- 文献 Agent 只提取内容与元数据；
- ActionBroker 忽略外部文本中的执行请求；
- 外部文本与系统指令分离；
- 引用保留来源；
- 可疑指令写 SECURITY_FINDING。

## 5. 密钥

- 密钥只进入 Provider/Codex 启动进程；
- 不写日志；
- 不写 Artifact；
- 不传给生成代码；
- 不挂载到 Python Sandbox；
- 不进入 Git worktree；
- `.env` 不进入导出包；
- 日志执行 redaction。

## 6. Codex 权限

默认：
- read-only 用于分析；
- workspace-write 用于受控构造；
- full access 禁用；
- network 默认关闭；
- 需要网络时 ActionBroker 单独批准。

出站 Codex Worker 使用独立 Profile，禁用 Synaisthesis MCP。

## 7. 同模型独立性

如果预算不足而不得不使用同一模型：

- 不宣称 Independent；
- 标记 `SAME_MODEL_FAMILY`；
- 强制独立会话；
- Phase A 不读取其他轨道；
- 工具证据仍可独立；
- 最终显示 INDEPENDENCE_DEGRADED。

## 8. Tool Evidence 防伪

- Tool Adapter 独占写入对应状态；
- 模型输出 `LEAN_PASS` 字样不能改变状态；
- 每个 Tool Evidence 绑定 invocation_id；
- 保存退出码、版本、命令模板、输入 hash；
- 结果被重新读取验证；
- Codex 生成日志不替代平台执行日志。

## 9. Recursion Guard

字段：
- root_run_id
- origin_chain
- delegation_depth
- reentrancy_key

规则：
- Codex Worker 不得启动 Synaisthesis mutation；
- 相同 reentrancy_key 只能执行一次；
- depth 超限立即拒绝；
- 子任务不能扩大权限；
- Worker Profile 不加载 Operator Plugin。

## 10. Failure Policy

### Fail Closed
以下情况不得自动继续：
- ClaimContract hash 不一致；
- 工具结果无法解析；
- Evidence 缺失；
- Isolation Violation；
- Human Gate 未解决；
- 预算未知；
- Codex diff 越过允许目录；
- Lean statement hash 变化；
- Z3 UNKNOWN 被误当 UNSAT；
- 文献元数据无法验证。

### Fail Open
只允许在低风险展示层：
- UI 加载失败；
- 非关键摘要生成失败；
- 次要格式化失败。

## 11. Public Rationale

导出：
- 证据；
- 公开推理摘要；
- 失败记录；
- 决策理由。

不导出：
- 密钥；
- 隐藏系统指令；
- 私有 chain-of-thought；
- 未授权敏感数据。

## 12. ActionRequest / ExecutionReceipt

### ActionRequest
必须包含：
- action type；
- risk class；
- requester；
- exact parameters；
- allowed paths；
- network intent；
- cost estimate；
- expected outputs；
- expiry；
- required approval。

### ExecutionReceipt
必须包含：
- request hash；
- executor；
- actual parameters；
- start/end；
- exit status；
- stdout/stderr；
- produced artifacts；
- diff；
- result hash；
- environment version；
- deviations from request。

没有 Receipt 的动作不能形成 Tool Evidence。

## 13. 供应链与依赖

- 锁定 Python dependencies；
- Lean project 固定 toolchain 与 Mathlib commit；
- Docker image 使用 digest；
- Codex SDK 记录版本；
- 模型 ID 与 provider 记录；
- 文献源记录访问时间；
- 导出 Bundle 包含 environment manifest。

## 14. 数据保留

配置：
- model transcript retention；
- Codex rollout retention；
- raw external content retention；
- artifact retention；
- revoked evidence retention。

默认：
- 研究状态与 Evidence 长期保存；
- 密钥永不保存；
- 临时 sandbox 可清理；
- 被撤回 Evidence 不删除。

## 15. Human Gate 类型

- SPEC_CONFIRMATION
- SCOPE_CHANGE
- SEMANTIC_DELTA_S2
- SEMANTIC_DELTA_S3
- GOAL_CHANGE_S4
- COST_OVERRUN
- NETWORK_ACCESS
- EXTERNAL_WRITE
- SECRET_ACCESS
- DESTRUCTIVE_ACTION
- CLAIM_ACCEPTANCE
- CONTINUE_AFTER_ROUND_20
- OVERRIDE_INDEPENDENCE_DEGRADATION

## 16. Codex 指令传输安全边界

- 用户原文必须在模型处理前被 Hook 捕获。
- mutation 必须携带服务端可验证的 InstructionToken。
- `confirmed=true`、Codex 自述“用户已经同意”均不构成授权。
- 高风险确认必须来自独立 UserConfirmationEvent。
- Hook 被禁用、未受信任或版本不兼容时，mutation fail closed。
- 原始 prompt 默认 PRIVATE，不进入公开 export。
- Sidecar 只监听本机；远程连接由 Sidecar 使用短期凭据转发。
- ContextManifest 中的文件必须重算 hash，不能只接受 Codex 摘要。
- state_version、sequence_number 与 idempotency_key 必须同时校验。
- Stop Hook 只能提高输出忠实度，最终状态仍由平台 CommandReceipt 决定。
- 服务端不得把 Hook 视作唯一防线；所有 token、权限、hash 和状态都要重新验证。
