# 02 — 目标系统架构

## 1. 总体结构

```text
                         Human Researcher
                                │
            ┌───────────────────┴───────────────────┐
            │                                       │
        Web / CLI                            Codex Operator
            │                                       │
            └───────────────────┬───────────────────┘
                                │
                         Synaisthesis MCP/API
                                │
                    ┌───────────▼────────────┐
                    │ Governance Control Plane│
                    │ State / Gate / Budget  │
                    │ Evidence / Action / ACL│
                    └───────────┬────────────┘
                                │
       ┌────────────────────────┼─────────────────────────┐
       │                        │                         │
   Incubator                Claim Compiler       Adversarial Council
   S0–S10                   Atomic ClaimUnit      bounded 10-round loop
       │                        │                         │
       └────────────────────────┴──────────────┬──────────┘
                                               │
                                      Verification Lab
                      ┌───────────┬──────────┬───────────┬─────────┐
                      │           │          │           │         │
                   Lean        Z3/cvc5     Python     Literature  Codex Worker
                      │           │          │           │         │
                      └───────────┴──────────┴───────────┴─────────┘
                                               │
                                      Artifact / Event Store
```

## 2. 运行进程

### `synaisthesisd`
本地常驻服务，负责：
- FastAPI；
- MCP Server；
- 本地作业队列；
- LangGraph Runner；
- 数据库；
- Artifact Store；
- Model Provider；
- Codex Worker Adapter。

MVP 可以单进程运行，但模块必须分离，避免以后无法拆成 worker/API/MCP 多进程。

### `synaisthesis` CLI
用于初始化、doctor、启停服务、项目管理、运行 Loop、处理 Gate、导出 Bundle。

### Web UI
后期加入，不阻塞核心能力。

### Codex Plugin
只包含：
- plugin manifest；
- MCP wiring；
- Operator Skills；
- 可选辅助 Hooks。

## 3. 软件分层

### Domain Layer
不依赖 FastAPI、MCP、LiteLLM、Codex SDK、Lean 子进程。

包含：
- Project；
- ResearchSpec；
- Stage；
- ClaimUnit；
- ClaimContract；
- Evidence；
- Revision；
- Attack；
- Gate；
- ActionRequest；
- ExecutionReceipt；
- Policy；
- DomainEvent。

### Application Layer
编排领域服务：
- IncubationService；
- ClaimCompilerService；
- CouncilService；
- VerificationService；
- GateService；
- ActionService；
- ExportService。

### Orchestration Layer
- LangGraph；
- RunWorker；
- checkpoint；
- pause/resume；
- retry；
- budget stop。

### Infrastructure Layer
- SQLite/PostgreSQL；
- Artifact filesystem；
- LLM Provider；
- Codex SDK；
- Lean；
- Z3；
- Docker；
- Literature APIs；
- Git worktree。

### Interface Layer
- CLI；
- HTTP；
- MCP；
- Web UI。

## 4. 权威顺序

1. 用户确认的 ResearchSpec；
2. 冻结 ClaimContract；
3. 不可变 Revision；
4. Tool Evidence；
5. Human Decision；
6. Model Proposal；
7. 临时对话文本。

LangGraph 只负责下一步运行哪个节点，不能直接决定：
- Claim 是否被冻结；
- 工具是否 PASS；
- Gate 是否可绕过；
- Revision 是否可以提交。

这些由 Domain Policy 决定。

## 5. Event Sourcing

所有关键变化写 DomainEvent：

- SpecCreated；
- SpecConfirmed；
- StageAdvanced；
- StageRolledBack；
- ClaimCompiled；
- ClaimFrozen；
- RoundStarted；
- AttackRecorded；
- ToolExecuted；
- EvidenceCreated；
- RevisionProposed；
- RevisionCommitted；
- GateOpened；
- GateResolved；
- EvidenceRevoked；
- ClaimRevoked；
- RunCompleted。

数据库保存当前状态 materialized view，但审计以事件日志为准。

## 6. 异步运行

十轮 Loop 不应占住一个 MCP Tool 调用。

标准模式：

1. `research_start_council` 创建 Run；
2. 立即返回 `run_id`；
3. RunWorker 后台执行；
4. Codex 或 UI 查询 `research_get_run_status`；
5. 触发 Gate 时状态为 `BLOCKED_HUMAN`；
6. 用户处理后恢复。

MVP 可使用 SQLite-backed 本地 JobQueue；后期再迁移 Redis/队列系统。

## 7. 模型角色

### Primary Model
负责：
- 研究综合；
- 形式化候选；
- 支持路线；
- 修复；
- 证明尝试。

### Auditor Model
负责：
- 独立解释；
- 反例；
- 语义差异；
- 证据边界；
- 回归审查。

### Utility Model
可选，负责：
- 查询扩展；
- 文档整理；
- 结构化抽取；
- 格式修复。

### Codex Worker
作为 `EngineeringAgentProvider`：
- 仓库分析；
- 文件修改；
- Lean/Z3/Python 工程；
- 测试与构建；
- 生成 diff 与执行回执。

Codex 不自动计入独立认知模型。只有模型身份、会话隔离和可见性满足要求时，才可将某次 Codex 审查标记为独立。

## 8. Claim 类型与工具路由

Claim Compiler 为每个 ClaimUnit 标记：

- FORMAL；
- FINITE_CONSTRAINT；
- COMPUTATIONAL；
- EMPIRICAL；
- ENGINEERING；
- LITERATURE_NOVELTY；
- MIXED。

ToolRouter 规则：

- FORMAL → Lean；
- FINITE_CONSTRAINT → Z3/cvc5；
- COMPUTATIONAL → Python/Sage；
- ENGINEERING → Codex + tests；
- LITERATURE_NOVELTY → literature adapters；
- MIXED → 必须先拆分，不允许直接给统一 PASS。

## 9. 本地优先部署

用户当前主要在 Windows/Codex 环境工作，推荐：

- WSL2 作为核心运行环境；
- Lean、Docker、Python、Git worktree 运行在 WSL2；
- Codex Operator 可在 Windows 或 WSL2；
- Synaisthesis MCP 使用 stdio 或 localhost；
- Artifact Store 位于 Linux 文件系统，避免跨文件系统权限和性能问题。

## 10. 设计边界

平台负责：
- 状态；
- 工具；
-证据；
-授权；
-回归；
-导出。

Codex 负责：
- 用户交互入口；
- 工程任务执行；
- 代码与形式文件操作。

LLM 负责：
- 候选生成；
-解释；
-攻击；
-修复提案。

Lean/Z3/Python 负责：
- 对应范围内的机器验证。

Human 负责：
- 语义；
-目标；
-价值判断；
-高风险授权；
-最终接受。

## v2.1 新增：Codex Instruction Fidelity Layer

在 Codex Operator 与 Synaisthesis MCP 之间新增强制传输层：

```text
Codex UI / CLI / IDE
  ├─ UserPromptSubmit Hook
  ├─ PreToolUse Hook
  ├─ PostToolUse / Stop Hook
  └─ Codex Bridge Sidecar
               │
               ▼
      Command Fidelity Gateway
  ├─ InstructionCapsule Store
  ├─ Token Verifier
  ├─ ContextManifest Resolver
  ├─ Instruction Delta Auditor
  ├─ Prepare / Commit Coordinator
  └─ CommandReceipt / DisplayContract
               │
               ▼
          Synaisthesis Core
```

所有外部 mutation 必须经过 Fidelity Gateway。原 MCP 业务工具可继续存在，但只作为内部 Service；Codex 不能绕过 Gateway 直接冻结 Claim、启动 Council 或批准 Gate。
