# Synaisthesis V2：联觉科研半自动科研平台完整工程蓝图

## 项目定位


> **当前正式名称：联觉科研（联科） / Synaisthesis。**  
> **当前 Windows 工程根目录：`E:\Synaisthesis`。**  
> 本包整合了此前 V2 主蓝图与 Codex 指令忠实传递强化设计，作为当前 V2 的统一工程基线。历史工作名 ResearchLoop 已停止作为正式产品名使用。


Synaisthesis V2 是一个**人类治理、双模型异构审计、验证优先、可与 Codex 双向调用**的半自动科研平台。它不把科研理解为一次长 Prompt，也不把多 Agent 理解为同一模型在同一上下文中轮流扮演角色，而是把研究过程拆成可执行、可暂停、可回归、可撤回、可审计的状态机：

> 灵感孵化 → 研究规范化 → 原子命题编译 → 冻结命题 → 对抗式研究议会 → 工具验证 → 理论修正 → 语义回归 → 人类确认 → 研究交接与导出

第一优先适用领域：

- 数学与形式逻辑；
- 理论计算机科学；
- 需要数学形式化支撑的工程研究；
- 可通过有限模型、数值实验、程序构造或形式证明验证的问题。

## 对现有工作流的总判断

现有工作流最有价值的部分不是插件实现，而是已经形成的**研究治理协议**：

- S0–S10 灵感孵化阶段；
- MATURE_IDEA_READY 交接门；
- FrozenClaim 冻结命题；
- Supporter / Opponent / Independent 三轨隔离；
- ResearchPacket；
- ActionRequest → Approval → ExecutionReceipt；
- Governor；
- A0–A3 委托模式；
- Evidence / Method / Experiment / Construction ID；
- PASS / PARTIAL / BLOCKED / NOT_TESTED；
- 每 5 个有效轮次 checkpoint；
- 回退时保留历史版本、证据和失败记录。

这些设计应当保留，但要从“写在 Skill 里的流程要求”迁移为由平台强制执行的领域对象、状态转移、工具适配器和数据库约束。

## 为什么目前只有灵感孵化有效

S0–S5 主要依赖自然语言整理和用户即时纠正，不要求真实角色隔离、外部执行、长期状态或可复现实验。S6 以后开始要求：

- 文献检索覆盖；
- 数学对象稳定；
- 多模型独立分析；
- 角色上下文隔离；
- Lean/Z3/Python 真实执行；
- ExecutionReceipt；
- 多轮修正与回归；
- 证据与结论绑定；
- 跨会话持久化；
- 预算、权限和失败恢复。

这些能力不能只靠 Skill 或长 Prompt 稳定实现。v2 的核心变化因此是：

> **Skill 只负责让 Codex 正确调用平台；研究逻辑全部迁入 Synaisthesis Core。**

## 六个核心子系统

### 1. Incubator
把现有 S0–S10 变成可执行阶段状态机。

### 2. Claim Compiler
把宏观研究目标拆成可独立验证的 ClaimUnit，并为每个命题指定对象域、量词、证据标准、证伪见证与工具路径。

### 3. Adversarial Council
运行 Support、Oppose、Independent 三条隔离研究轨道，并执行默认最多 10 轮、用户可配置的验证—修正 Loop。

### 4. Verification Lab
统一调用 Lean、Z3、Python、文献源和 Codex 工程代理。

### 5. Governance Control Plane
管理状态、Evidence Ledger、Human Gate、ActionBroker、预算、隔离、回归和撤回。

### 6. Integration Plane
实现两个方向：
- **Codex → Synaisthesis**：Codex 通过 MCP/插件调用平台；
- **Synaisthesis → Codex**：平台通过 Codex Python SDK、Codex MCP Server 或 `codex exec` 调起 Codex。

## 推荐技术栈

### 核心后端
- Python 3.11；
- `uv` + `pyproject.toml`；
- Pydantic v2；
- SQLModel 或 SQLAlchemy 2；
- SQLite 起步，后期 PostgreSQL；
- Alembic；
- FastAPI；
- Typer；
- LangGraph 作为工作流运行器；
- 自建领域状态机作为状态转移权威；
- pytest、pytest-asyncio；
- Ruff；
- Pyright 或 mypy；
- structlog；
- httpx；
- tenacity。

### 多模型层
- 自定义 `LLMProvider` 抽象；
- LiteLLM 作为首个统一 Provider 实现；
- 至少配置 Primary Model 和 Auditor Model；
- 默认要求二者模型身份或模型家族不同；
- 模型不可直接写入工具 PASS 状态。

### Codex 出站层
- 首选：稳定版 Python 包 `openai-codex`，使用 `AsyncCodex`；
- 兼容：将 `codex mcp-server` 作为子进程并由 MCP Client 调用；
- 回退：`codex exec` 非交互模式；
- MVP 不直接构建 Codex App Server 客户端。

### 验证层
- Lean 4 + Lake；
- Z3Py；
- Docker Python Sandbox；
- 后期 LeanDojo-v2；
- 可选 cvc5、SageMath。

### 前端
- MVP：CLI + Codex Plugin + MCP；
- 后期：React + TypeScript + Vite；
- SSE 或 WebSocket 显示 Loop 事件。

## 十条架构原则

1. 数据库与 Artifact Store 是研究状态真相源。
2. LangGraph 是执行器，不是状态权威。
3. 同一个模型换 Prompt 不等于独立研究者。
4. Codex 是工程执行代理，不是最终数学裁判。
5. Lean PASS 只证明已提交的形式命题。
6. Semantic Alignment 独立于 Formal Verification。
7. 模型输出只能生成 Proposal，工具执行才能生成 Tool Evidence。
8. 任何已通过结论都可以被撤回。
9. 每次修复产生新 Revision，不覆盖旧版本。
10. 机器可以自由探索，但没有无限修改用户语义的权力。

## MVP 验收场景

MVP 应完整跑通：

1. 用户在 Codex 中输入自然语言研究目标；
2. Codex 调 Synaisthesis MCP 创建项目并推进 S0–S5；
3. 用户确认 S1；
4. 平台完成 S6–S7，编译一个 ClaimUnit；
5. 冻结 ClaimContract；
6. 两个不同模型独立支持与攻击；
7. Z3 找到反例；
8. Primary 提出修复；
9. Auditor 发现某修复缩小对象域并判为 S3；
10. 平台暂停；
11. 用户拒绝；
12. 平台采用另一修复；
13. Lean 对冻结形式命题验证通过；
14. Auditor 反译 Lean statement；
15. 用户确认语义对齐；
16. 平台导出包含 Revision、Attack、Evidence、Receipt 和 Hash 的 ResearchBundle；
17. 其中一个工程步骤由平台调起隔离的 Codex Worker 完成，并保存 CodexExecutionReceipt。

## v2.1：Codex 指令忠实传递成为 P0

用户主要在 Codex 中操作，因此 v2.1 新增 `Codex Instruction Fidelity Layer (CIFL)`：

- UserPromptSubmit Hook 在模型处理前逐字捕获原始指令；
- 原文被保存为不可变 InstructionCapsule；
- PreToolUse Hook 给 Synaisthesis MCP mutation 注入签名 token；
- 服务端独立比较原文、Codex CommandProposal 与实际执行计划；
- 高风险操作使用 prepare/commit 两阶段提交；
- CommandReceipt 与 DisplayContract 约束 Codex 的结果展示；
- Stop Hook 检查 Codex 是否遗漏警告或夸大验证状态。

因此，Codex 不再是“凭 Prompt 自觉忠实”的入口，而是一个带原文捕获、签名、状态版本、幂等、回执和输出审计的第一等 Operator Client。

完整规范见 `05A_CODEX_INSTRUCTION_FIDELITY_PROTOCOL.md`。
