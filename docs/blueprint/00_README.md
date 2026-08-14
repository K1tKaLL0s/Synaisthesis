# Synaisthesis V2：联觉科研半自动科研平台完整工程蓝图

## 项目定位


> **当前正式名称：联觉科研（联科） / Synaisthesis。**  
> **当前 Windows 工程根目录：`E:\Synaisthesis`。**  
> 本包整合了此前 V2 主蓝图与 Codex 指令忠实传递强化设计，作为当前 V2 的统一工程基线。历史工作名 ResearchLoop 已停止作为正式产品名使用。


Synaisthesis V2 是一个**人类治理、双模型异构审计、验证优先、可与 Codex 双向调用**的半自动科研平台。它不把科研理解为一次长 Prompt，也不把多 Agent 理解为同一模型在同一上下文中轮流扮演角色，而是把研究过程拆成可执行、可暂停、可回归、可撤回、可审计的状态机：

> 灵感孵化 → 自然语言设计冻结 → 相邻研究/成熟工程检索 → 形式化可行性分流 →〔数学早期形式化 → 理论/应用新颖性 → 原子命题研究 → 理论论文母稿〕或〔用户确认工程路线 → 工程概念形式化 → 工程/应用新颖性 → 机械工程蓝图、验证与工程论文母稿〕→ 用户决定是否按内置四刊/arXiv Profile 生成正式适配稿 → 研究交接与导出

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

## 八个核心子系统

### 1. Incubator
把现有 S0–S10 变成可执行阶段状态机。

### 2. Early Research Qualification
在 S4 后执行 RQ0–RQ4：选择高能力形式化路线、检索学术和成熟工程近邻，先以确定性谓词审查纯数学理论与工程构造的适配性。纯理论不适配但工程可尝试时，必须由用户选择修改设计或转工程路线；理论路线采用理论 50 + 应用 50，工程路线采用工程 60 + 应用 40，新颖性有效总分达到 70 自动进入各自后续流程。完整合同见 `03A_EARLY_FORMALIZATION_AND_NOVELTY_GATE.md`。

### 3. Engineering Translation & Publication
把通过工程新颖性门的概念转化为利益相关者/ConOps、可追踪要求、方案权衡、架构与接口、可机械执行 WorkUnit、源文件与渲染图、验证—确认计划、应用/扩展路线和期刊中立母稿。母稿先交付用户；用户选择后才按工程四刊、工程 arXiv 或扩展 Profile 生成正式适配稿、合规矩阵和可复现工件。完整合同见 `03B_ENGINEERING_TRANSLATION_AND_PUBLICATION_WORKFLOW.md`。

### 4. Claim Compiler
把宏观研究目标拆成可独立验证的 ClaimUnit，并为每个命题指定对象域、量词、证据标准、证伪见证与工具路径。

### 5. Adversarial Council
运行 Support、Oppose、Independent 三条隔离研究轨道，并执行默认最多 10 轮、用户可配置的验证—修正 Loop。

### 6. Verification Lab
统一调用 Lean、Z3、Python、文献源和 Codex 工程代理。

### 7. Governance Control Plane
管理状态、Evidence Ledger、Human Gate、ActionBroker、预算、隔离、回归和撤回。

### 8. Integration Plane
实现两个方向：
- **Codex → Synaisthesis**：Codex 通过 MCP/插件调用平台；
- **Synaisthesis → Codex**：平台通过 Codex Python SDK、Codex MCP Server 或 `codex exec` 调起 Codex。

理论路线完成研究交付时同样必须生成 `TheoryMasterManuscript`。理论母稿先交付用户，用户选择后才按 Annals of Mathematics、JAMS、Inventiones mathematicae、Acta Mathematica、数学 arXiv 或自定义 Profile 生成正式适配稿。双路线 PublicationProfile 合同见 `03C_THEORY_PUBLICATION_AND_DUAL_TRACK_VENUE_PROFILES.md`。

## 推荐技术栈

### 核心后端
- Python 3.11；
- `uv` + `pyproject.toml`；
- Pydantic v2；
- SQLAlchemy 2（不使用 SQLModel 作为领域模型层）；
- SQLite 起步，后期 PostgreSQL；
- Alembic；
- FastAPI；
- Typer；
- LangGraph 作为工作流运行器；
- 自建领域状态机作为状态转移权威；
- pytest、pytest-asyncio；
- Ruff；
- basedpyright（Pyright 兼容类型检查器，与当前 M0 CI 一致）；
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
2. Codex 调 Synaisthesis MCP 创建项目并推进 S0–S4；
3. 用户确认 S1 与 S4，项目进入 `NATURAL_LANGUAGE_DESIGN_READY`；
4. 平台执行 RQ0–RQ2F，检索相邻研究与成熟工程项目并完成理论/工程适配分析；本主场景得到 `PURE_THEORY_FIT`；
5. 平台执行 RQ2M，生成数学公式化早期形式化；
6. 用户审查并批准当前 EarlyFormalizationBundle；
7. 两个隔离 Reviewer 完成理论/应用新颖性评分，保守总分达到 70 后自动进入 S5；
8. 平台完成 S5–S7，编译一个 ClaimUnit；
9. 冻结 ClaimContract；
10. 两个不同模型独立支持与攻击；
11. Z3 找到反例；
12. Primary 提出修复；
13. Auditor 发现某修复缩小对象域并判为 S3；
14. 平台暂停；
15. 用户拒绝；
16. 平台采用另一修复；
17. Lean 对冻结形式命题验证通过；
18. Auditor 反译 Lean statement；
19. 用户确认语义对齐；
20. 平台生成、独立审计并交付 TheoryMasterManuscript；
21. 用户选择保留母稿，或选择理论四刊/arXiv Profile 生成正式适配稿；
22. 平台导出包含 RQ Artifact、Revision、Attack、Evidence、Receipt、论文与 Hash 的 ResearchBundle；
23. 其中一个工程步骤由平台调起隔离的 Codex Worker 完成，并保存 CodexExecutionReceipt。

工程分支另有强制 MVP 场景：RQ2F 判断 `ENGINEERING_PROJECT_CANDIDATE` 后只打开用户 Gate；用户选择 `TRY_ENGINEERING_PROJECT`，RQ2E/RQ3E/RQ4E 通过并达到 70 后自动进入 ENG0；平台至少以 `BLUEPRINT_ONLY` 模式导出可机械执行蓝图、图示源及渲染件、应用/扩展路线和 Design/Protocol 母稿。母稿交付后，用户选择是否按工程四刊/arXiv Profile 生成正式适配稿；任何路径均不得虚构实现或实验结果。

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
