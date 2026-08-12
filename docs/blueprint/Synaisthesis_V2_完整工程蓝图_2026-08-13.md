# Synaisthesis V2 完整工程蓝图

**中文名：联觉科研｜简称：联科｜英文名：Synaisthesis**

**当前工程根目录：`E:\Synaisthesis`**

本文件由分册蓝图合并生成；分册文件是便于逐阶段开发和按需加载的推荐使用方式。


---

<!-- SOURCE: 00_README.md -->

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


---

<!-- SOURCE: 00A_PROJECT_IDENTITY_AND_CURRENT_ENVIRONMENT.md -->

# 00A — 项目标识、冻结决策与当前开发环境

## 1. 正式名称

- 中文正式名：**联觉科研**
- 中文简称：**联科**
- 英文项目名：**Synaisthesis**
- GitHub / 包名建议：`synaisthesis`
- 历史工作名：ResearchLoop（仅作为早期蓝图历史名称，不再作为正式产品名）

`Synaisthesis` 取“联合感知 / 联觉”的词源意象：平台将人类语义、异构 LLM、文献、程序实验、SMT、Lean 与工程执行器的不同“感知通道”统一到一套可审计的研究控制平面中。

## 2. 当前工程根目录

Windows 本地开发根目录冻结为：

`E:\Synaisthesis`

所有项目级路径在文档、AGENTS.md、OpenCode 和 Git 中应优先使用相对路径；仅在安装、启动或本地环境文档中使用绝对路径。

## 3. 当前开发工具分工

### Synaisthesis 工程开发
- 主客户端：OpenCode
- 主工程模型：DeepSeek V4 Pro
- 工作目录：`E:\Synaisthesis`
- OpenCode 本体建议独立放在：`D:\AI\OpenCode`
- 第三方 Skill 源码缓存建议：`D:\AI\SkillSources`

### 现有理论验证
- Codex 继续用于当前已经在推进的理论验证工作。
- 不要求 Codex 接入 DeepSeek。
- 不允许 Synaisthesis 工程开发环境直接修改 Codex 正在工作的理论仓库。

## 4. 产品层面的 Codex 要求仍然保留

“开发时不用 Codex”不等于删除产品的 Codex 能力。

Synaisthesis V2 最终仍必须支持：

1. **Codex → Synaisthesis**：用户在 Codex 中通过 MCP / 插件调用平台，并保证原始操作意图忠实传递。
2. **Synaisthesis → Codex**：平台在配置允许时，将工程型任务委派给隔离 Codex Worker。
3. Codex 不是数学最终裁判；Lean/Z3/Python 的真实工具回执才可以形成对应验证证据。
4. Codex Instruction Fidelity Layer 仍为产品 P0 能力。

## 5. 当前实现优先级

在 DeepSeek + OpenCode 开发阶段，按以下顺序推进：

1. 工程骨架与不可变领域状态；
2. Instruction / Semantic Fidelity 领域模型；
3. Fake 双模型与 Fake Tool 的十轮 Loop；
4. ModelProvider 抽象，并首先实现 DeepSeek Provider；
5. Z3；
6. Python Sandbox；
7. Lean Compiler Mode；
8. Evidence Ledger、Regression 与 Revocation；
9. Synaisthesis MCP；
10. Codex 双向集成；
11. Web UI；
12. LeanDojo / 分支搜索等增强能力。

## 6. 关键冻结原则

- DeepSeek 是当前工程开发模型，不得硬编码成产品唯一模型。
- 产品仍以至少两个异构模型为正式科研模式。
- 默认自主 Loop 最大 10 轮，用户可修改。
- Proof Loop 不得静默修改 theorem statement。
- 核心语义变更必须触发 Human Gate。
- 模型输出不能自行生成 Lean/Z3/Python PASS。
- 所有修复必须建立新 Revision，失败证据不得删除。
- 所有已通过结论均允许因新证据被 REVOKED。


---

<!-- SOURCE: 01_WORKFLOW_AUDIT_AND_REUSE_MAP.md -->

# 01 — 现有工作流审计与复用映射

## 1. 审计结论

现有流程图不是“失败的插件设计”，而是一份已经相当成熟的科研治理规范。主要问题是**执行载体选择错误**：

- 适合写进 Skill 的：触发条件、用户交互方式、流程解释、MCP 工具调用策略；
- 不适合只写进 Skill 的：长期状态、角色隔离、工具回执、Loop 计数、权限、证据绑定、回归与撤回。

因此不应推倒重来，而应进行“协议迁移”。

## 2. 为什么 S0–S5 更容易有效

### S0 灵感捕获
只要求原样保存、分离观察与解释、识别一个关键歧义，LLM 擅长。

### S1 自然语言定义
依赖用户确认，偏差能快速纠正。

### S2 机制草图
主要是从叙述中提取输入、变化、输出、不变量和失败条件。

### S3 相关研究映射
开始依赖联网、来源真实性和检索覆盖，可靠性下降。

### S4 研究方向再规范
需要综合文献、对象域、非目标和证据要求，出现长程一致性问题。

### S5 最小范例
如果只写例子仍可工作；一旦要求真实执行与复现，就需要平台。

## 3. S6 以后低于预期的结构性原因

### 3.1 阶段标签不是状态
模型输出“S7 PASS”并不意味着：
- 必填字段齐全；
- 用户确认关键语义；
- 依赖阶段完成；
- 产物持久化；
- 旧版本可回退。

### 3.2 FrozenClaim 只是文本冻结
缺少：
- immutable hash；
- 版本号；
- 依赖快照；
- 允许修改范围；
- 工具版本；
- 预算、权限和数据政策快照。

### 3.3 角色隔离不真实
同一 Codex 会话或同一模型扮演三种角色会导致：
- 结论泄露；
- 锚定；
- 共享盲区；
- 同源错误；
- Independent 只是重述前两方。

### 3.4 ResearchPacket 过于宽泛
长文本无法可靠判断：
- 哪条主张对应哪条证据；
- 哪个反例针对哪个版本；
- 哪个结果真实运行；
- 哪个只是模型提案；
- 缺哪些必填字段。

### 3.5 Governor 过载
当前 Governor 同时承担汇总、分类、反例检查、停止条件、裁决和证据边界审查。如果 Governor 也是 LLM，容易把语言流畅度误当证据质量。

### 3.6 “十个有效轮次”没有客观计数
模型可以声称完成十轮，但没有：
- Round ID；
- 每轮输入快照；
- 新 Attack；
- 工具调用；
- Revision；
- 成本；
- 是否真实产生进展。

### 3.7 S8 与右侧研究议会重复
左侧 S8 已进行双重证伪，右侧议会又进行三轨对抗，造成：
- 成本加倍；
- 路由不清；
- 何时冻结不明确；
- 两套反例记录不一致。

### 3.8 外部动作旁路缺少真实执行器
ActionRequest 与 ExecutionReceipt 的设计正确，但必须由 ActionBroker 和 Tool Adapter 生成，而不是模型自行书写。

### 3.9 证据状态与研究结论混合
`PROVED`、`SUPPORTED`、`PASS` 容易混用。形式证明、有限验证、经验支持、语义对齐、原创性必须正交保存。

### 3.10 对话轮次承担过多职责
对话记录不能稳定充当数据库、事件日志、Artifact Store、版本控制、权限系统和作业队列。

## 4. 复用、修改、替换矩阵

| 现有组件 | 处理方式 | 平台新实现 |
|---|---|---|
| S0–S10 | 保留 | IncubatorStage 状态机 |
| MATURE_IDEA_READY | 保留并强化 | 由字段完整性与 Gate 计算 |
| 每次只推进一个方面 | 保留 | ProgressKind 与 StageAction |
| 每 5 轮 checkpoint | 保留 | ValidRound 计数后 Snapshot |
| 第 20 轮复核 | 保留 | Mandatory Maturity Gate |
| FrozenClaim | 保留并强化 | Immutable ClaimContract |
| Supporter | 保留 | SupportTrack 独立 Session |
| Opponent | 保留 | OpposeTrack 独立 Session |
| Independent | 保留并强化 | Blind Phase A + De-biased Phase B |
| ResearchPacket | 拆分 | SupportPacket / AttackPacket / IndependentPacket / ToolEvidencePacket |
| 外部动作旁路 | 保留并强化 | ActionBroker + ExecutionReceipt |
| Governor | 拆分 | PolicyGovernor + SynthesisAgent + HumanAdjudicator |
| 裁决状态 | 扩展 | 多轴状态模型 |
| A0–A3 | 保留 | DelegationPolicyProfile |
| Evidence 来源分类 | 保留并扩展 | ProvenanceType |
| 回退保留旧版本 | 保留并强化 | Event Store + immutable Revision |
| Skill | 缩小职责 | Codex Operator + MCP 工具调用 |
| 插件 | 保留 | 打包 Skills + MCP 连接 + 可选 Hooks |
| 同模型角色扮演 | 替换 | 异构模型 + 隔离 Session |
| 模型声明工具 PASS | 禁止 | 只有 Adapter 可写工具状态 |

## 5. S8 的重新定位

S8 不再承担完整十轮议会，而改为：

> **Pre-Freeze Readiness Attack：冻结前就绪攻击**

只运行一至两个轻量回合，检查：

- Claim 是否足够原子；
- 证伪见证是否清楚；
- 对象域与量词是否稳定；
- 是否存在显而易见的边界反例；
- 是否具备进入正式 Council 的条件。

完整十轮 Loop 只在 FrozenClaim 后运行。

## 6. Governor 的重新定位

### PolicyGovernor
纯规则与状态机：
- 检查字段；
- 验证权限；
- 验证轮次；
- 路由工具；
- 触发 Gate；
- 执行停止条件；
- 不做数学判断。

### SynthesisAgent
高能力模型：
- 汇总分歧；
- 生成候选修复；
- 生成公开理由；
- 没有最终提交权。

### HumanAdjudicator
决定：
- 是否接受 S2/S3/S4 语义变化；
- 是否改变研究目标；
- 是否继续超预算；
- 是否公开或接受结论。

## 7. 最值得保留的产品特色

1. 先孵化，后冻结，再对抗。
2. 支持者必须真正完成一条支持路线。
3. 反对者必须提出至少两类实质攻击。
4. 独立研究者先盲审，再去角色化复核。
5. 实验、方法、构造和证据都有 ID。
6. 示例、模拟、玩具模型和同模型复核不等于证明。
7. 任何回退都不删除失败历史。
8. 授权与隔离是研究流程的一部分。

这些应成为 GitHub README 的核心差异化。


---

<!-- SOURCE: 02_TARGET_ARCHITECTURE.md -->

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


---

<!-- SOURCE: 03_INCUBATOR_STAGE_CONTRACTS.md -->

# 03 — S0–S10 孵化阶段契约

## 1. 通用 StageContract

每个阶段必须定义：

- `stage_id`
- `objective`
- `required_inputs`
- `output_artifact_type`
- `required_fields`
- `validators`
- `tool_requirements`
- `human_gate_policy`
- `pass_criteria`
- `partial_criteria`
- `blocked_criteria`
- `allowed_next_stages`
- `rollback_targets`
- `prompt_version`
- `artifact_hash`

模型不能直接将 Stage 标为 PASS。`evaluate_stage_gate` 根据 Schema、验证器和用户确认计算状态。

---

## S0 — 灵感捕获

### 目标
忠实保存用户原始表达，不抢先理论化。

### 输入
名词、原句、草图、异常观察、附件。

### 输出：`SeedRecord`
- raw_input
- source_type
- user_intent_guess
- observation
- interpretation
- observation_interpretation_separated
- key_ambiguity
- user_corrections
- attachments

### 验证
- 原文保留；
- observation 与 interpretation 分栏；
- 最多提出一个关键歧义；
- 不静默改写用户立场。

### Gate
无强制确认，但用户修改产生新版本。

---

## S1 — 自然语言定义

### 输出：`NaturalLanguageSpec`
- core_definition
- positive_examples
- non_examples
- boundary_conditions
- object_candidates
- ambiguous_terms
- explicit_non_goals
- assistant_proposed
- user_confirmed

### PASS 条件
- 至少一个正例；
- 至少一个非例；
- 至少一个边界；
- 用户明确确认。

S1 是后续数学化工作的最高自然语言语义权威。

---

## S2 — 机制草图

### 输出：`MechanismSketch`
- inputs
- state_change
- outputs
- invariants
- failure_conditions
- causal_claims
- merely_descriptive_relations
- uncertainty_register

### PASS 条件
- 输入、变化、输出齐全；
- 至少一个不变量；
- 至少一个失败条件；
- 不把相关性自动写成因果。

### 默认停止点
用户可以在 S1 或 S2 后归档，不必继续科研化。

---

## S3 — 相关研究映射

### 输出：`PriorWorkMap`
- search_queries
- sources
- nearest_theories
- same_object_different_method
- same_method_different_object
- conflicts
- terminology_candidates
- retrieval_scope
- unsearched_areas
- literature_hits
- metadata_verified

### PASS 条件
- 查询和来源可追溯；
- 区分“未发现”与“不存在”；
- 至少给出最近邻类别；
- 文献元数据被外部源验证。

### 允许状态
- SEARCHED
- PARTIAL
- POSSIBLY_NOVEL
- OVERLAP_FOUND
- INCONCLUSIVE

禁止输出“绝对原创”。

---

## S4 — 研究方向再规范

### 输出：`ResearchScopeSpec`
- main_question
- object_domain
- non_goals
- nearest_neighbor_difference
- central_claims
- evidence_requirements
- failure_learning_plan
- engineering_relevance
- stop_conditions
- user_confirmed_scope

### PASS 条件
- 主问题唯一；
- 对象域明确；
- 非目标明确；
- 每个中心主张有证据需求；
- 失败也有可学习输出。

### 回退
重大文献冲突或对象域不稳定时回 S1/S3。

---

## S5 — 最小范例

### 输出：`MinimalCaseBundle`
- input
- control_or_baseline
- expected_output
- failure_condition
- reproduction_steps
- actually_executed
- execution_receipt_id
- toy_or_real
- limitations

### 状态
- PROPOSED
- DEMONSTRATED
- EXECUTED
- FAILED
- NOT_RUN

### 规则
`DEMONSTRATED ≠ PROVED`。没有真实运行时只能标 DEMONSTRATED 或 NOT_RUN。

---

## MATURE_IDEA_READY — 成熟灵感门

不允许模型直接输出，而由以下条件计算：

- S0–S4 PASS；
- S5 至少 DEMONSTRATED；
- S1 与 S4 有用户确认；
- 关键术语无未解决歧义；
- 存在可执行研究计划；
- 存在至少一个可构造 ClaimUnit；
- 无 Critical Blocker。

它只表示“可以交接”，不表示理论成立。

---

## S6 — 核心统一理论

### 输出：`TheoryKernel`
- candidate_mechanism
- competing_explanations
- examples
- counterexamples
- invariants
- boundaries
- predictions
- discarded_alternatives
- discard_reasons
- unresolved_conflicts

### PASS 条件
- 比较至少一个替代理论；
- 保留反例；
- 不以解释流畅度代替证据；
- 预测与解释分开。

### 回退
核心概念变化必须回 S1/S4，不在 S6 静默修补。

---

## S7 — 正式构造

### 输出：`FormalizationPlan`
- object_domain
- symbols
- definitions
- assumptions
- quantifiers
- claims
- dependency_graph
- proof_paths
- counterexample_paths
- intended_tools
- formalization_uncertainties
- proof_candidate_artifacts

### 规则
AI 产生的形式证明先标 `PROOF_CANDIDATE`。

### PASS 条件
- 每个 Claim 有对象域和量词；
- 每个 Claim 有证伪见证；
- 依赖关系无环，或明确递归；
- 已选验证工具或明确 NOT_APPLICABLE。

---

## S8 — 冻结前就绪攻击

### 新定位
不再执行完整十轮议会，只做一至两轮 readiness attack。

### 输出：`PreFreezeAttackReport`
- obvious_counterexamples
- boundary_failures
- definition_holes
- quantifier_risks
- tool_feasibility
- claim_atomicity
- recommended_split
- freeze_readiness

### PASS 条件
- 至少一次内部攻击；
- 至少一次独立外部攻击；
- Critical 问题已解决或明确阻断；
- Claim 足够原子。

### 回退
- 定义问题 → S1；
- 研究范围问题 → S4；
- 理论问题 → S6；
- 形式结构问题 → S7。

---

## S9 — 开放问题与猜想

### 输出：`OpenQuestionRegistry`
每条记录：
- question_id
- statement
- origin
- why_open
- known_failed_attempts
- falsification_path
- next_action
- dependency_claims
- status

### origin
- USER
- AI_GENERATED
- DERIVED
- LITERATURE
- TOOL_FAILURE

AI 生成问题必须保留 AI_GENERATED 标记。

---

## S10 — 研究交接

### 输出：`ResearchHandoffBundle`
- frozen_terms
- evidence_summary
- current_versions
- open_questions
- downstream_tasks
- verification_thresholds
- proof_track
- experiment_track
- engineering_track
- writing_track
- artifact_manifest
- unresolved_gates

### PASS 条件
- 不存在未归属证据；
- 每个下游任务有输入、输出和门槛；
- 可形成 FrozenClaim 候选。

---

## 2. 有效孵化轮次与 Checkpoint

### `IncubatorSubstantiveRound`
只有满足以下条件才计数：
- 选择一个 ProgressKind；
- 产生新 Artifact 或明确差异；
- 保存公开理由；
- 记录未解决项；
- 不是简单重述上一轮。

### ProgressKind
- DEFINITION
- BOUNDARY
- MECHANISM
- EVIDENCE
- TEST
- ASSUMPTION
- FORMALIZATION
- COUNTEREXAMPLE
- HANDOFF

### Checkpoint
- 每 5 个有效轮次生成 WIP_CHECKPOINT；
- 第 20 个有效轮次触发 Mandatory Maturity Gate；
- 未经用户确认不得自动扩大目标或对象域；
- Council 与 Incubator 轮次分开计数。

## 3. 阶段执行模板

每次 `execute_stage` 应按以下顺序：

1. 读取上游 Artifact 与当前权威语义；
2. 构造最小 visibility bundle；
3. 调模型或工具；
4. Schema 校验；
5. 业务验证；
6. 生成 StageDiff；
7. 计算 Gate；
8. 写 Artifact 与 DomainEvent；
9. 返回用户可读摘要；
10. 不自动删除旧产物。

## 4. 对话与平台的边界

Codex 或 Web 对话中只展示：
- 当前 Stage；
- 待确认差异；
- 新 Artifact 摘要；
- Blocker；
- 下一步工具动作。

完整状态保存在平台，不能依赖对话历史恢复。


---

<!-- SOURCE: 04_COUNCIL_AND_LOOP_PROTOCOL.md -->

# 04 — 冻结命题、对抗式研究议会与自主 Loop

## 1. Claim Compiler

宏观理论不能直接进入议会。先调用 `compile_claim_units` 拆为原子 ClaimUnit。

每个 ClaimUnit 必须包含：

- claim_id
- natural_language_statement
- formal_statement_candidate
- object_domain
- quantifiers
- assumptions
- conclusion
- claim_class
- baseline
- evidence_standard
- falsification_witness
- intended_verifiers
- dependencies
- engineering_relevance
- semantic_critical_fields

父级研究目标的状态由子 Claim 组合，不允许一个“总 PASS”掩盖局部失败。

## 2. FrozenClaim → ClaimContract

`ClaimContract` 是不可变对象。

字段：

- contract_id
- claim_revision_id
- natural_language_hash
- formal_statement_hash
- object_domain_snapshot
- assumption_snapshot
- conclusion_snapshot
- baseline_snapshot
- stop_conditions
- output_scope
- tool_plan
- network_policy
- data_policy
- budget_policy
- allowed_semantic_delta
- approval_policy
- artifact_manifest_hash
- model_role_assignments
- created_at
- user_confirmed

冻结后任何修改都生成新版本。

## 3. 三条隔离轨道

### SupportTrack

目标：
- 选择最强支持路线；
- 真正完成证明、构造、证据或实验；
- 无法完成时明确失败。

输出 `SupportPacket`：

- route
- assumptions_used
- constructed_artifacts
- tool_requests
- evidence_refs
- incomplete_steps
- failure_reason
- public_rationale

### OpposeTrack

目标：
- 至少两类实质不同攻击。

默认攻击家族：

- 逻辑反例；
- 边界反例；
- 量词攻击；
- 替代解释；
- 经验失效；
- 形式化偏差；
- 计算复杂度；
- 工程不可实现；
- 文献覆盖。

每条 `AttackPacket`：

- target_revision
- attack_family
- description
- witness
- severity
- validation_plan
- evidence_refs

### IndependentTrack

#### Phase A：盲审基线
只读取：
- FrozenClaim；
- 原始 ResearchSpec；
- 允许的公共文献。

不读取 Support/Oppose 输出。

目标：
- 独立重建问题；
- 独立给出结论；
- 独立提出工具计划。

#### Phase B：去角色化复核
读取双方的**结构化结论和证据引用**，不读取隐藏推理过程。

目标：
- 识别遗漏；
- 检查证据标准是否对称；
- 生成 IndependentPacket。

## 4. ResearchPacket 拆分

不保存巨型文本 Packet，而保存：

- ClaimHeader
- SupportPacket
- AttackPacket[]
- IndependentPacket
- ToolPlan
- ToolEvidencePacket[]
- RevisionProposal[]
- SemanticDiff
- RegressionReport
- RoundAssessment
- PublicRationale

所有 Packet 使用 Schema 验证。

## 5. Governor 拆分

### PolicyGovernor
确定性规则：
- 验证输入；
- 检查隔离；
- 路由工具；
- 处理预算；
- 触发 Gate；
- 检查停止条件；
- 计数有效轮次；
- 写状态。

### SynthesisAgent
模型：
- 汇总冲突；
- 生成候选修复；
- 对比修复；
- 生成公开裁决理由。

它不能：
- 写 LEAN_PASS；
- 批准 Human Gate；
- 修改 FrozenClaim；
- 宣称绝对原创。

### HumanAdjudicator
处理：
- S2/S3/S4 Semantic Delta；
- 高风险 Action；
- 超预算；
- 更改目标；
- 最终接受。

## 6. 默认十轮 Loop

### 默认参数
- `max_rounds = 10`
- `minimum_rounds_before_early_stop = 4`
- `stable_rounds_required = 2`
- `max_repairs_per_round = 3`
- `max_primary_calls_per_round = 3`
- `max_auditor_calls_per_round = 3`
- `max_codex_tasks_per_round = 2`
- `max_proof_attempts_per_round = 8`
- `checkpoint_interval = 5`
- 总成本与总时长上限。

用户可修改轮数。

建议限制：
- 1–20：直接允许；
- 21–100：显示成本预估并要求确认；
- 超过 100：高级配置，默认拒绝。

## 7. 有效 Council Round

一轮必须满足：

1. 有 RoundStartSnapshot；
2. Support 或 Primary 提交结构化结果；
3. Opponent 至少一个有效攻击；
4. Independent 或 Auditor 提交独立审查；
5. ToolPlan 已执行或明确 NOT_APPLICABLE；
6. Evidence 已保存；
7. 产生 Decision；
8. 产生 Revision、StabilityRecord 或 Blocker；
9. 成本与模型调用已记录；
10. RoundEndSnapshot 已保存。

否则标记 `INVALID_ROUND`，不计入十轮。

## 8. 每轮顺序

1. Freeze round input；
2. Support analysis；
3. Opponent attacks；
4. Independent Phase A；
5. Tool selection；
6. Lean/Z3/Python/Literature/Codex execution；
7. Merge evidence；
8. Detect failure；
9. Propose repairs；
10. Semantic audit；
11. Select revision；
12. Regression；
13. Proof Loop；
14. Independent Phase B；
15. Back-translation；
16. Round assessment；
17. Continue / Pause / Stop。

## 9. Proof Loop 与 Theory Repair Loop

### Proof Loop
允许：
- 修改 proof body；
- 增加局部 lemma；
- 调整 tactic；
- 修复 import。

禁止：
- 修改 theorem statement；
- 新增核心假设；
- 缩小对象域；
- 弱化结论。

statement hash 变化时立即退出 Proof Loop。

### Theory Repair Loop
允许提出：
- 新假设；
- 结论修改；
- 定义修改；
- 对象域修改。

但必须生成 Semantic Delta 并走 Gate。

## 10. Semantic Delta

- S0：只修改证明；
- S1：逻辑等价重写；
- S2：外围技术条件变化；
- S3：对象域、量词、核心假设或结论变化；
- S4：研究目标变化。

自动提交：
- S0；
- S1。

候选分支 + Gate：
- S2。

立即阻断：
- S3；
- S4。

## 11. 修复候选评分

维度：

- resolves_critical_attack
- semantic_distance
- added_assumption_penalty
- conclusion_weakening_penalty
- domain_shrinking_penalty
- verifier_strength
- regression_pass
- engineering_relevance
- complexity_penalty
- cost_penalty

MVP 使用固定规则选出第一名，再由 Auditor 复核；不把唯一选择交给自由 LLM Judge。

## 12. 停止状态

### CANDIDATE_STABLE
必须满足：
- 连续若干轮无新 Critical Attack；
- 未解决 High Attack 低于阈值；
- Regression PASS；
- Semantic Audit PASS；
- 必需工具验证通过或 NOT_APPLICABLE；
- 无未解决 Human Gate；
- Artifact 完整。

### 其他
- MAX_ROUNDS_REACHED
- BLOCKED_HUMAN
- BLOCKED_TOOL
- BUDGET_EXHAUSTED
- COUNTEREXAMPLE_CONFIRMED
- FORMAL_PROOF_COMPLETED
- USER_PAUSED
- USER_CANCELLED

## 13. 多轴裁决状态

### formal_status
- UNFORMALIZED
- FORMALIZED
- PROOF_CANDIDATE
- LEAN_PASS
- LEAN_FAIL
- COUNTEREXAMPLE_CONFIRMED
- UNDECIDED
- REVOKED

### empirical_status
- NOT_TESTED
- SUPPORTED_WITHIN_SCOPE
- NOT_SUPPORTED
- INSUFFICIENT_EVIDENCE
- REVOKED

### semantic_status
- CANDIDATE
- AI_AUDITED
- USER_CONFIRMED
- DRIFTED
- REVOKED

### novelty_status
- UNCHECKED
- SEARCHED
- POSSIBLY_ORIGINAL
- PARTIAL_OVERLAP
- STRONG_OVERLAP
- KNOWN_RESULT
- INCONCLUSIVE

只有 `formal_status=LEAN_PASS` 且 `semantic_status=USER_CONFIRMED` 时，UI 才显示：

> FORMALLY_PROVED_AS_STATED

## 14. 撤回

新反例、形式化错误、依赖撤回或语义偏差都可触发：

- EvidenceRevoked；
- ClaimRevoked；
- dependent Claims → NEEDS_REGRESSION；
- 导出报告追加撤回记录；
- 旧版本不删除。

## 15. 超过十轮

若用户配置超过十轮：

- 每五轮 checkpoint；
- 第 20 轮强制 Maturity Review；
- 每 20 轮重新确认目标与预算；
- 未经确认不自动延长；
- 旧 ClaimContract 继续保持不变，除非用户明确接受新版本。


---

<!-- SOURCE: 05_BIDIRECTIONAL_CODEX_INTEGRATION.md -->

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


---

<!-- SOURCE: 05A_CODEX_INSTRUCTION_FIDELITY_PROTOCOL.md -->

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


---

<!-- SOURCE: 06_DATA_MODEL_AND_STATE_MACHINE.md -->

# 06 — 数据模型、状态机与证据账本

## 1. 核心表

### `projects`
- id
- name
- description
- lifecycle_status
- active_spec_id
- active_claim_contract_id
- created_at
- updated_at

### `research_specs`
- id
- project_id
- version
- s1_natural_language_spec
- s4_scope_spec
- user_confirmed
- confirmed_at
- content_hash

### `incubation_stage_runs`
- id
- project_id
- stage_id
- input_artifact_ids
- output_artifact_id
- status
- prompt_version
- model_invocation_ids
- started_at
- ended_at

### `claim_units`
- id
- project_id
- parent_claim_id
- claim_key
- natural_language_statement
- claim_class
- importance
- status

### `claim_contracts`
- id
- claim_id
- revision_id
- version
- contract_hash
- policy_snapshot_id
- user_confirmed
- frozen_at

### `theory_revisions`
- id
- claim_id
- parent_revision_id
- round_id
- natural_language_statement
- formal_statement
- assumptions_snapshot
- semantic_delta_level
- created_by
- immutable_hash

### `council_runs`
- id
- claim_contract_id
- configured_rounds
- current_round
- status
- primary_model_profile_id
- auditor_model_profile_id
- delegation_policy_id
- budget_policy_id
- started_at
- ended_at

### `council_rounds`
- id
- run_id
- round_number
- valid
- start_revision_id
- end_revision_id
- outcome
- stability_score
- snapshot_artifact_id

### `role_sessions`
- id
- run_id
- round_id
- role
- model_profile_id
- visibility_policy_id
- isolated_context_hash
- session_status

### `model_invocations`
- id
- role_session_id
- provider
- model
- request_hash
- response_artifact_id
- input_tokens
- output_tokens
- cost
- latency_ms
- status

### `attacks`
- id
- target_revision_id
- round_id
- source_role
- attack_family
- description
- witness
- severity
- status
- validation_plan
- resolved_by_revision_id

### `evidence`
- id
- claim_id
- revision_id
- evidence_type
- provenance_type
- status
- scope
- strength
- artifact_id
- tool_invocation_id
- model_invocation_id
- created_at
- revoked_at

### `evidence_edges`
- id
- evidence_id
- target_claim_id
- relation
- notes

### `tool_invocations`
- id
- run_id
- round_id
- tool_name
- input_artifact_id
- output_artifact_id
- execution_receipt_id
- status
- duration_ms
- timeout

### `action_requests`
- id
- run_id
- round_id
- action_type
- risk_class
- requested_by
- parameters_artifact_id
- status
- required_approval

### `approval_decisions`
- id
- action_request_id
- actor
- decision
- reason
- decided_at

### `execution_receipts`
- id
- action_request_id
- executor
- parameters_hash
- result_hash
- stdout_artifact_id
- stderr_artifact_id
- diff_artifact_id
- started_at
- ended_at
- exit_status

### `human_gates`
- id
- project_id
- run_id
- gate_type
- reason
- semantic_diff_artifact_id
- status
- decision
- resolved_at

### `codex_sessions`
- id
- task_id
- transport
- thread_id
- profile
- cwd
- sandbox
- approval_policy
- origin_chain
- status

### `codex_tasks`
- id
- run_id
- round_id
- task_type
- task_spec_artifact_id
- session_id
- execution_receipt_id
- status

### `artifacts`
- id
- project_id
- relative_path
- media_type
- sha256
- immutable
- created_at

### `domain_events`
- id
- project_id
- aggregate_type
- aggregate_id
- event_type
- event_payload_artifact_id
- event_hash
- created_at

### `prompt_versions`
- id
- prompt_key
- version
- content_hash
- active
- evaluation_score

### `model_profiles`
- id
- provider
- model
- family
- reasoning_tier
- structured_output_support
- cost_profile
- privacy_profile
- enabled

### `visibility_policies`
- id
- name
- allowed_artifact_types
- denied_roles
- blind_phase
- notes

## 2. 项目生命周期

```text
SEED
→ INCUBATING
→ MATURE_IDEA_READY
→ THEORY_BUILDING
→ CLAIM_COMPILED
→ CLAIM_FROZEN
→ COUNCIL_RUNNING
→ BLOCKED_HUMAN / BLOCKED_TOOL
→ CANDIDATE_STABLE
→ USER_ACCEPTED
→ REVOKED
```

允许回退：

- THEORY_BUILDING → INCUBATING；
- CLAIM_COMPILED → THEORY_BUILDING；
- COUNCIL_RUNNING → CLAIM_COMPILED；
- CANDIDATE_STABLE → COUNCIL_RUNNING；
- USER_ACCEPTED → REVOKED。

回退只写事件，不删除历史。

## 3. ProvenanceType

- USER_INPUT
- USER_DECISION
- EXTERNAL_SOURCE
- ASSISTANT_PROPOSAL
- DERIVED
- TOOL_EXECUTION
- CODEX_EXECUTION
- HUMAN_VERIFIED

## 4. EvidenceType

- LITERATURE_METADATA
- LITERATURE_INTERPRETATION
- COUNTEREXAMPLE
- SMT_MODEL
- SMT_UNSAT_WITHIN_ENCODING
- PYTHON_EXPERIMENT
- LEAN_KERNEL_ACCEPTED
- LEAN_ERROR
- CODEX_EXECUTION_RECEIPT
- SEMANTIC_AUDIT
- REGRESSION_RESULT
- HUMAN_CONFIRMATION
- CONSTRUCTION_ARTIFACT

## 5. Evidence 强度

- E0：未经验证的模型提案；
- E1：可复述自然语言论证；
- E2：可复现计算或构造；
- E3：有限模型或范围验证；
- E4：形式证明器接受；
- E5：外部独立复核或多形式系统交叉验证。

强度不替代 scope：

- Z3 UNSAT 可以是 E3，但只在当前编码范围；
- Lean PASS 是 E4，但只针对形式 statement；
- 用户语义确认不是数学证据，但决定 semantic_status。

## 6. 独立性状态

- INDEPENDENT_VERIFIED
- INDEPENDENT_PARTIAL
- SAME_MODEL_FAMILY
- CONTEXT_LEAK_SUSPECTED
- ISOLATION_VIOLATION
- NOT_APPLICABLE

如果 Primary 与 Auditor 是同一模型或模型家族，系统可继续，但必须显示 `INDEPENDENCE_DEGRADED`，不能当成真正独立复核。

## 7. Artifact Store

```text
workspace/{project_id}/
  spec/
  stages/
  literature/
  theory/
  claims/
  formal/lean/
  formal/smt/
  experiments/
  codex/
  attacks/
  evidence/
  receipts/
  checkpoints/
  reports/
  exports/
```

规则：

- 内容不可变；
- SHA-256；
- 更新生成新文件；
- 数据库保存相对路径；
- 导出包含 manifest；
- 数据库状态引用具体 hash；
- 文件缺失时状态转 BLOCKED_ARTIFACT。

## 8. Public Rationale

平台保存：
- 结论摘要；
- 公开理由；
- 证据引用；
- 失败说明；
- 决策依据。

不要求保存模型隐藏推理过程。`public_rationale` 是可审计产物，不等于私有 chain-of-thought。

## 9. 状态派生

`overall_status` 不由模型输出，而由以下轴派生：

- stage_status
- formal_status
- empirical_status
- semantic_status
- novelty_status
- regression_status
- independence_status
- human_review_status
- tool_availability_status

例如：

```text
overall_status = CANDIDATE_STABLE
formal_status = LEAN_PASS
semantic_status = AI_AUDITED
human_review_status = PENDING
novelty_status = POSSIBLY_ORIGINAL
```

这表示形式命题已通过，但原始语义尚未由用户最终确认。

## 10. 依赖与回归

`dependency_edges` 表示：

- DEFINITION_USED_BY
- LEMMA_USED_BY
- EVIDENCE_SUPPORTS
- COUNTEREXAMPLE_REFUTES
- CLAIM_SPECIALIZES
- CLAIM_GENERALIZES
- ENGINEERING_DEPENDS_ON

Revision 或 Evidence 撤回后：

1. 查询下游依赖；
2. 标为 NEEDS_REGRESSION；
3. 生成 RegressionPlan；
4. 重跑；
5. 更新有效 Evidence；
6. 不删除旧记录。

## 11. 数据库迁移

使用 Alembic。每次 Schema 变更：

- 先写 migration；
- 更新 schema_version；
- 更新 export manifest；
- 为旧 bundle 提供 reader；
- 不允许应用启动时静默重建数据库。

## v2.1 新增数据模型：Codex 指令忠实传递

### `codex_session_bindings`
- id
- codex_session_id
- project_id
- claim_id
- mode
- active_state_version
- sequence_number
- bound_at
- expires_at
- status

### `user_instruction_events`
- id
- session_binding_id
- turn_id
- raw_user_text_artifact_id
- raw_user_text_hash
- sequence_number
- supersedes_instruction_id
- context_manifest_id
- privacy_class
- status

### `instruction_tokens`
- id
- instruction_id
- token_hash
- nonce
- allowed_operation_class
- state_version
- issued_at
- expires_at
- consumed_at
- signer_key_id

### `command_proposals`
- id
- instruction_id
- codex_interpretation_artifact_id
- platform_interpretation_artifact_id
- instruction_delta_level
- mismatch_fields
- status

### `prepared_commands`
- id
- command_proposal_id
- intended_state_diff_artifact_id
- preserved_constraints_artifact_id
- confirmation_nonce
- expected_state_version
- expires_at
- status

### `command_receipts`
- id
- instruction_id
- command_id
- starting_state_version
- ending_state_version
- executed_operation
- accepted_parameters_artifact_id
- rejected_parameters_artifact_id
- evidence_ids
- pending_gate_ids
- receipt_hash
- status

### `display_contracts`
- id
- command_receipt_id
- exact_summary_artifact_id
- mandatory_statuses
- mandatory_warnings
- prohibited_claims
- display_hash
- fulfilled_at
- status

### `context_manifests`
- id
- workspace_root
- git_revision
- file_refs
- line_ranges
- attached_artifacts
- research_spec_id
- claim_contract_id
- unresolved_refs
- manifest_hash

### 指令状态
- CAPTURED
- TOKEN_ISSUED
- INTERPRETED
- FIDELITY_MATCH
- FIDELITY_AMBIGUOUS
- FIDELITY_MISMATCH
- PREPARED
- COMMITTED
- EXECUTED
- SUPERSEDED
- EXPIRED
- REJECTED

### 指令忠实状态
- FIDELITY_UNCHECKED
- FIDELITY_VERIFIED
- FIDELITY_DEGRADED_READ_ONLY
- FIDELITY_UNAVAILABLE
- MISSING_CONTEXT
- STALE_STATE


---

<!-- SOURCE: 07_FUNCTION_API_AND_MCP_CONTRACTS.md -->

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


---

<!-- SOURCE: 08_SECURITY_AUTHORIZATION_ISOLATION.md -->

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


---

<!-- SOURCE: 09_MECHANICAL_IMPLEMENTATION_PLAN.md -->

# 09 — 机械式、可碎片化实施方案

原则：每个阶段都能运行、测试和提交 Git。不要同时开发 UI、Lean、MCP 和多模型。

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

## Stage 2：搬运当前有效的 S0–S5

### 任务
将当前 Skill 中表现良好的内容变成：
- StageContract；
- Pydantic Schema；
- Prompt Asset；
- Validation Rule。

### 函数
- `capture_seed`
- `execute_s0` 至 `execute_s5`
- `validate_stage_output`
- `evaluate_stage_gate`
- `advance_stage`

### 测试
把现有成功对话作为 golden cases。

### 完成标准
不依赖 Codex 会话历史，也能复现原本有效的灵感孵化。

---

## Stage 3：S6–S10 与 MATURE_IDEA_READY

### 实现
- TheoryKernel；
- FormalizationPlan；
- PreFreezeAttackReport；
- OpenQuestionRegistry；
- HandoffBundle；
- computed maturity gate。

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

## Stage 13：文献与原创性

### 数据源
- OpenAlex；
- Crossref；
- arXiv；
- 可选 Semantic Scholar。

### 实现
- 查询扩展；
- metadata 验证；
- 去重；
- 最近邻分类；
- novelty status；
- 外部内容隔离。

### 完成标准
已知经典结果被识别为重合；冷门结果只给 POSSIBLY_ORIGINAL。

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
- 未有 ActionBroker 就让 Codex 写主仓库；
- 未锁定 statement 就做 Proof Loop；
- 未有 Recursion Guard 就开启双向 Codex。

## 推荐首个垂直切片

为了尽快获得可用成果，建议优先完成：

1. S0–S5 持久化；
2. Synaisthesis MCP；
3. Codex Operator Skill；
4. ClaimContract；
5. Fake 十轮；
6. 双模型；
7. Z3；
8. Lean；
9. Codex Worker。

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


---

<!-- SOURCE: 10_TEST_EVAL_AND_OBSERVABILITY.md -->

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


---

<!-- SOURCE: 11_MIGRATION_FROM_CURRENT_SKILLS.md -->

# 11 — 从当前 Codex Skills / 插件迁移到平台

## 1. 迁移原则

不重新设计全部 Prompt。先把当前已有效的内容迁出 Codex 上下文，保留为版本化研究资产和评估语料。

## 2. 冻结现有工作流为 Baseline

保存：

- 当前流程图；
- 当前 Skills；
- 当前插件配置；
- 已成功对话；
- 已失败对话；
- 用户修正记录；
- 当前状态标签定义；
- 现有 ResearchPacket 模板。

形成：

- `legacy_workflow_v1`
- `legacy_prompt_corpus`
- `golden_cases`
- `failure_cases`
- `migration_mapping`

## 3. 拆分 Skill

当前大型 Skill 拆成三个小 Skill。

### `synaisthesis-incubator-operator`
只处理：
- 创建项目；
- S0–S10 操作；
- 用户确认；
- 查看状态。

### `synaisthesis-council-operator`
只处理：
- 冻结 Claim；
- 启动 Council；
- 查看 Round；
- 处理 Gate；
- 导出。

### `synaisthesis-admin`
只处理：
- doctor；
- 配置；
- 模型与工具状态；
- 预算；
- 安全诊断。

Skill 中不保存：
- 研究状态；
- 十轮执行逻辑；
- Tool PASS；
- 角色输出；
- Evidence Ledger。

## 4. Prompt 迁为版本化资产

目录：

- `prompts/incubator/s0/`
- `prompts/incubator/s1/`
- `prompts/council/support/`
- `prompts/council/oppose/`
- `prompts/council/independent/`
- `prompts/audit/semantic/`
- `prompts/literature/`
- `prompts/codex_task/`

每个 Prompt 保存：
- 版本；
- 输入 Schema；
- 输出 Schema；
- 禁止行为；
- golden tests；
- 变更理由。

## 5. 标签变成 Enum

- MATURE_IDEA_READY
- PROOF_CANDIDATE
- AI_GENERATED
- PROVED / REFUTED / UNDECIDED
- SUPPORTED / NOT_SUPPORTED / INSUFFICIENT_EVIDENCE
- PASS / PARTIAL / BLOCKED / NOT_TESTED
- A0–A3
- ISOLATION_VIOLATION

避免自由文本拼写漂移。

## 6. FrozenClaim 模板迁为 ClaimContract

旧插件中的冻结文本保留为初始化模板，但由平台：

- 自动 hash；
- 锁定；
- 版本化；
- 绑定 Policy；
- 绑定 Artifact；
- 绑定用户确认；
- 记录允许的 Semantic Delta。

## 7. 三角色迁为隔离 Session

旧角色 Prompt 保留，但：

- 每个角色独立模型调用；
- visibility bundle 不同；
- 独立 Session；
- model profile 记录；
- 不共享隐藏推理；
- Independent Phase A 盲审。

## 8. Governor 规则提取为 Policy

把旧 Governor Prompt 中可确定的内容写成规则：

- 什么算完整 Packet；
- 什么情况回 S1/S4/S6；
- 什么情况暂停；
- 什么情况 Tool Blocked；
- 什么情况允许结束；
- 什么情况必须撤回；
- 什么情况轮次无效。

只把需要综合的部分留给 SynthesisAgent。

## 9. ActionRequest/Receipt 实体化

旧文本模板迁为数据库对象和 Adapter 结果。

旧版：
- 模型写“已执行”。

新版：
- ActionBroker 生成 request；
- 用户或 Policy 决定；
- Executor 执行；
- Receipt 绑定真实结果。

## 10. Codex 插件降级为“遥控器”

最终 Codex Plugin 是：

- 用户界面；
- MCP 工具发现；
- Gate 翻译；
- 状态展示；
- 导出入口。

不是科研本体。

## 11. Legacy Chat Mode

迁移初期保留 `legacy_chat_mode`：

用途：
- 继续运行现有孵化 Skill；
- 将输出导入平台；
- 对比平台结果；
- 建立 eval。

必须标记：

- NOT_DURABLY_ORCHESTRATED
- ROLE_ISOLATION_UNVERIFIED
- TOOL_EVIDENCE_UNVERIFIED

## 12. 逐步切换

### Phase 1
旧 Skill 负责对话，平台只存状态。

### Phase 2
平台执行 S0–S5，Codex 只调用 MCP。

### Phase 3
平台执行 S6–S10，旧 Skill 只做兼容。

### Phase 4
平台执行 Council，旧对抗插件停用。

### Phase 5
平台调 Codex Worker，形成双向闭环。

## 13. 迁移验收

满足以下条件后停止旧工作流：

- S0–S5 平台输出不低于旧 Skill；
- S6–S10 状态可恢复；
- FrozenClaim 有 hash；
- Council 真实运行；
- Tool Evidence 可复现；
- Codex MCP 操作无明显摩擦；
- 平台可调起 Codex Worker；
- 旧案例可导入；
- 用户确认流程保留；
- 原流程图中的每个控制点有明确平台对象对应。

## 13. v2.1：把 Codex Operator 从 Prompt 客户端迁移为受控客户端

迁移顺序：

1. 保留现有灵感孵化 Skill 的自然语言交互能力。
2. 在插件中增加 UserPromptSubmit、PreToolUse、PostToolUse、Stop Hooks。
3. 增加本地 Sidecar 与 session binding。
4. Skill 不再把用户长指令压缩后直接传入 mutation tool。
5. Skill 只生成 CommandProposal；原始 prompt 由 Hook 直接注册。
6. 原 council operator 的 mutation 调用改成 prepare/commit。
7. Gate 的用户确认必须形成独立 confirmation event。
8. 原来的“最终总结”改为展示平台 CommandReceipt，并允许 Codex补充解释。
9. IDE Extension 路径不依赖 Plugin，单独安装 repo/user hooks 与 MCP 配置。
10. 旧 Skill-only 模式只保留 read-only compatibility，不再允许写平台状态。


---

<!-- SOURCE: 12_PROJECT_TREE_AND_CONFIG.md -->

# 12 — 完整项目目录与配置设计

本文件给出可直接照着建立仓库的目录结构。目录名可以调整，但模块边界不应随意合并。

## 1. 推荐仓库结构

```text
synaisthesis/
├─ README.md
├─ README.zh-CN.md
├─ LICENSE
├─ SECURITY.md
├─ CONTRIBUTING.md
├─ CHANGELOG.md
├─ ROADMAP.md
├─ pyproject.toml
├─ uv.lock
├─ .env.example
├─ .gitignore
├─ docker-compose.yml
├─ Makefile                         # 可选；只包装常用命令
│
├─ configs/
│  ├─ default.yaml
│  ├─ development.yaml
│  ├─ test.yaml
│  ├─ profiles/
│  │  ├─ a1_assisted.yaml
│  │  ├─ a2_delegated.yaml
│  │  ├─ a3_autonomous_bounded.yaml
│  │  ├─ codex_worker_readonly.yaml
│  │  └─ codex_worker_workspace_write.yaml
│  └─ policies/
│     ├─ semantic_delta.yaml
│     ├─ evidence_status.yaml
│     ├─ action_authorization.yaml
│     └─ isolation.yaml
│
├─ src/synaisthesis/
│  ├─ __init__.py
│  ├─ version.py
│  ├─ config/
│  │  ├─ settings.py
│  │  ├─ loaders.py
│  │  └─ validation.py
│  │
│  ├─ domain/
│  │  ├─ enums.py
│  │  ├─ project.py
│  │  ├─ research_spec.py
│  │  ├─ stage.py
│  │  ├─ claim.py
│  │  ├─ claim_contract.py
│  │  ├─ revision.py
│  │  ├─ evidence.py
│  │  ├─ attack.py
│  │  ├─ gate.py
│  │  ├─ action.py
│  │  ├─ receipt.py
│  │  ├─ budget.py
│  │  ├─ isolation.py
│  │  ├─ event.py
│  │  ├─ policies.py
│  │  └─ errors.py
│  │
│  ├─ application/
│  │  ├─ incubation_service.py
│  │  ├─ claim_compiler_service.py
│  │  ├─ council_service.py
│  │  ├─ verification_service.py
│  │  ├─ semantic_audit_service.py
│  │  ├─ regression_service.py
│  │  ├─ gate_service.py
│  │  ├─ action_service.py
│  │  ├─ codex_delegation_service.py
│  │  ├─ export_service.py
│  │  └─ project_service.py
│  │
│  ├─ orchestration/
│  │  ├─ state.py
│  │  ├─ graph_builder.py
│  │  ├─ nodes/
│  │  │  ├─ incubator_nodes.py
│  │  │  ├─ council_nodes.py
│  │  │  ├─ verification_nodes.py
│  │  │  ├─ repair_nodes.py
│  │  │  ├─ semantic_nodes.py
│  │  │  ├─ regression_nodes.py
│  │  │  └─ codex_nodes.py
│  │  ├─ routes.py
│  │  ├─ checkpointing.py
│  │  ├─ run_worker.py
│  │  ├─ job_queue.py
│  │  └─ recovery.py
│  │
│  ├─ agents/
│  │  ├─ schemas.py
│  │  ├─ primary_researcher.py
│  │  ├─ auditor.py
│  │  ├─ supporter.py
│  │  ├─ opponent.py
│  │  ├─ independent_reviewer.py
│  │  ├─ formalizer.py
│  │  ├─ repairer.py
│  │  ├─ semantic_auditor.py
│  │  ├─ literature_reviewer.py
│  │  └─ synthesis_agent.py
│  │
│  ├─ providers/
│  │  ├─ llm/
│  │  │  ├─ base.py
│  │  │  ├─ litellm_provider.py
│  │  │  ├─ fake_provider.py
│  │  │  ├─ router.py
│  │  │  ├─ retry.py
│  │  │  ├─ usage.py
│  │  │  └─ structured_output.py
│  │  └─ literature/
│  │     ├─ base.py
│  │     ├─ openalex.py
│  │     ├─ crossref.py
│  │     ├─ arxiv.py
│  │     ├─ semantic_scholar.py
│  │     ├─ normalization.py
│  │     └─ deduplication.py
│  │
│  ├─ verifiers/
│  │  ├─ base.py
│  │  ├─ lean/
│  │  │  ├─ adapter.py
│  │  │  ├─ compiler.py
│  │  │  ├─ parser.py
│  │  │  ├─ statement_lock.py
│  │  │  └─ leandojo_adapter.py
│  │  ├─ z3/
│  │  │  ├─ adapter.py
│  │  │  ├─ constraint_spec.py
│  │  │  ├─ encoder.py
│  │  │  ├─ model_extractor.py
│  │  │  └─ witness_validator.py
│  │  ├─ python/
│  │  │  ├─ adapter.py
│  │  │  ├─ sandbox_job.py
│  │  │  ├─ docker_runner.py
│  │  │  └─ output_collector.py
│  │  └─ registry.py
│  │
│  ├─ integrations/
│  │  ├─ codex/
│  │  │  ├─ base.py
│  │  │  ├─ sdk_adapter.py
│  │  │  ├─ mcp_adapter.py
│  │  │  ├─ exec_adapter.py
│  │  │  ├─ app_server_bridge.py
│  │  │  ├─ task_spec.py
│  │  │  ├─ session.py
│  │  │  ├─ worktree.py
│  │  │  ├─ recursion_guard.py
│  │  │  ├─ receipt.py
│  │  │  └─ profile.py
│  │  ├─ git/
│  │  │  ├─ repository.py
│  │  │  ├─ worktree.py
│  │  │  └─ diff.py
│  │  └─ docker/
│  │     ├─ client.py
│  │     └─ policy.py
│  │
│  ├─ storage/
│  │  ├─ database.py
│  │  ├─ migrations/
│  │  ├─ repositories/
│  │  │  ├─ project_repository.py
│  │  │  ├─ claim_repository.py
│  │  │  ├─ event_repository.py
│  │  │  ├─ evidence_repository.py
│  │  │  └─ run_repository.py
│  │  ├─ artifact_store.py
│  │  ├─ hashing.py
│  │  ├─ snapshots.py
│  │  └─ export_bundle.py
│  │
│  ├─ security/
│  │  ├─ authorization.py
│  │  ├─ allowlist.py
│  │  ├─ secret_filter.py
│  │  ├─ prompt_injection.py
│  │  ├─ provenance.py
│  │  └─ audit.py
│  │
│  ├─ interfaces/
│  │  ├─ api/
│  │  │  ├─ main.py
│  │  │  ├─ dependencies.py
│  │  │  ├─ routes/
│  │  │  └─ schemas/
│  │  ├─ cli/
│  │  │  ├─ main.py
│  │  │  ├─ doctor.py
│  │  │  └─ commands/
│  │  └─ mcp/
│  │     ├─ server.py
│  │     ├─ tools.py
│  │     ├─ resources.py
│  │     ├─ auth.py
│  │     └─ annotations.py
│  │
│  ├─ prompts/
│  │  ├─ registry.py
│  │  ├─ incubator/
│  │  ├─ council/
│  │  ├─ formalization/
│  │  ├─ semantic_audit/
│  │  ├─ literature/
│  │  └─ codex_worker/
│  │
│  ├─ telemetry/
│  │  ├─ logging.py
│  │  ├─ metrics.py
│  │  ├─ tracing.py
│  │  └─ redaction.py
│  │
│  └─ evals/
│     ├─ runner.py
│     ├─ graders.py
│     ├─ datasets.py
│     └─ reports.py
│
├─ plugin/
│  ├─ .codex-plugin/
│  │  └─ plugin.json
│  ├─ .mcp.json
│  ├─ skills/
│  │  ├─ synaisthesis-incubator-operator/
│  │  │  └─ SKILL.md
│  │  ├─ synaisthesis-council-operator/
│  │  │  └─ SKILL.md
│  │  └─ synaisthesis-admin/
│  │     └─ SKILL.md
│  ├─ hooks/
│  │  └─ hooks.json
│  ├─ assets/
│  └─ README.md
│
├─ web/
│  ├─ package.json
│  ├─ vite.config.ts
│  ├─ src/
│  │  ├─ api/
│  │  ├─ components/
│  │  ├─ pages/
│  │  ├─ routes/
│  │  ├─ state/
│  │  └─ types/
│  └─ tests/
│
├─ examples/
│  ├─ simple_integer_counterexample/
│  ├─ lean_statement_drift/
│  ├─ finite_graph_claim/
│  └─ real_project_case_study/
│
├─ tests/
│  ├─ unit/
│  ├─ contract/
│  ├─ integration/
│  ├─ external/
│  ├─ security/
│  ├─ golden/
│  ├─ fixtures/
│  └─ fake_runtime/
│
├─ docs/
│  ├─ architecture/
│  ├─ protocols/
│  ├─ adr/
│  ├─ user-guide/
│  ├─ developer-guide/
│  └─ case-studies/
│
├─ scripts/
│  ├─ bootstrap_dev_environment.*
│  ├─ install_lean.*
│  ├─ install_codex_worker_profile.*
│  ├─ run_local_mcp.*
│  └─ export_demo_bundle.*
│
└─ .github/
   ├─ workflows/
   │  ├─ ci-core.yml
   │  ├─ ci-integration.yml
   │  ├─ ci-formal.yml
   │  ├─ ci-mcp.yml
   │  └─ release.yml
   ├─ ISSUE_TEMPLATE/
   └─ pull_request_template.md
```

## 2. 配置分组

### `platform`
- `workspace_root`
- `database_url`
- `artifact_root`
- `log_level`
- `environment`
- `event_sourcing_enabled`
- `api_host`
- `api_port`
- `mcp_transport`

### `loop`
- `default_rounds = 10`
- `max_rounds_allowed`
- `minimum_rounds_before_early_stop = 4`
- `stable_rounds_required = 2`
- `checkpoint_every_valid_rounds = 5`
- `maturity_review_round = 20`
- `max_repair_candidates = 3`
- `max_proof_attempts_per_round`
- `allow_early_stop`
- `allow_auto_extension = false`

这里必须明确：原工作流的“每 5 个实质轮次 checkpoint、20 轮成熟化复核”属于长期研究对话节律；Council 的默认 10 轮是单次自主验证预算。两套计数不可混用。

### `models`
- `primary`
- `auditor`
- `utility`
- `synthesis`
- `fallbacks`
- `require_model_diversity`
- `allow_same_family_with_warning`
- `structured_output_retries`
- `context_budget`

每个 ModelProfile：
- provider
- model
- endpoint
- credential_env
- timeout
- max_output_tokens
- reasoning_effort
- temperature 或等效参数
- cost metadata
- allowed_roles

### `budget`
- `max_total_model_calls`
- `max_input_tokens`
- `max_output_tokens`
- `max_reported_cost`
- `max_wall_time`
- `max_codex_tasks`
- `max_codex_turns_per_task`
- `max_tool_runtime`

### `lean`
- `enabled`
- `mode = compiler | interactive`
- `lean_bin`
- `lake_bin`
- `project_template`
- `mathlib_cache`
- `timeout`
- `proof_attempt_budget`
- `statement_hash_required = true`

### `z3`
- `enabled`
- `timeout_ms`
- `supported_sorts`
- `max_model_size`
- `independent_witness_validation = true`

### `python_sandbox`
- `enabled`
- `runtime = docker`
- `image`
- `network = none`
- `memory_limit`
- `cpu_limit`
- `pids_limit`
- `timeout`
- `allowed_output_size`

### `codex`
- `enabled`
- `preferred_transport = sdk`
- `fallback_transports = [mcp, exec]`
- `model`
- `operator_profile`
- `worker_profile`
- `worker_codex_home`
- `sandbox = read-only | workspace-write`
- `approval_policy`
- `network_policy`
- `use_git_worktree = true`
- `cleanup_worktree_on_success`
- `retain_failed_worktree`
- `max_delegation_depth = 1`
- `worker_synaisthesis_mcp_enabled = false`
- `max_turns`
- `timeout`
- `cost_budget`
- `allowed_task_types`

### `literature`
- providers
- request rate
- result count
- full-text policy
- metadata verification
- deduplication strategy
- query budget
- novelty wording policy

### `security`
- `manual_approval_default = true`
- `action_allowlist`
- `protected_paths`
- `secret_patterns`
- `prompt_injection_quarantine = true`
- `external_content_trust = untrusted`
- `evidence_hashing = true`
- `audit_log_immutable = true`

## 3. 推荐运行 Profile

### A1 — AI_ASSISTED
- 用户逐阶段决定下一步；
- 模型只产候选；
- 所有外部写操作人工批准；
- 不运行自主 Council。

### A2 — AI_DELEGATED
- 用户冻结任务后，平台可自主完成指定阶段；
- S2 以上 Semantic Delta 暂停；
- 工具写操作使用 allowlist；
- 默认不调 Codex Workspace Write。

### A3 — AI_AUTONOMOUS_BOUNDED
- 在 FrozenClaim、预算、工具权限和停止条件内运行；
- 默认最多 10 轮；
- S0/S1 自动提交；
- S2 进入 Gate；
- S3/S4 强制 Gate；
- 不允许自动延长预算；
- 不允许 Worker 递归调用。

### Codex Worker Readonly
- 只读仓库；
- 用于分析、计划、审查；
- 不加载 Synaisthesis MCP；
- 网络关闭；
- 不得写 Evidence PASS。

### Codex Worker Workspace Write
- 仅写独立 worktree；
- 只允许指定文件；
- 运行指定测试；
- diff 与日志进入 Receipt；
- 完成后由 Verification Adapter 重验。

## 4. 环境变量

`.env.example` 只列变量名，不提交真实值：
- Synaisthesis 数据库与 workspace；
- 各模型 provider credential；
- OpenAlex/Crossref 等可选 key；
- Codex Worker `CODEX_HOME`；
- 日志/追踪 endpoint；
- 可选 PostgreSQL/Redis。

任何 credential 都不得进入：
- Prompt Artifact；
- CodexTaskSpec；
- ResearchBundle；
- ExecutionReceipt；
- Git diff；
- 测试 fixture。

## 5. 版本化规则

配置文件也属于研究环境证据。每次 Run 保存：
- resolved config snapshot；
- config hash；
-模型 profile ID；
- Prompt version；
- Tool version；
- Codex transport/version；
- Lean/Z3/Python runtime version。

这样才能解释“为什么同一研究任务在不同日期得到不同结果”。

## v2.1 新增目录：Codex Fidelity

建议增加：

```text
app/
  fidelity/
    instruction_capsule.py
    instruction_token.py
    instruction_delta.py
    context_manifest.py
    command_gateway.py
    prepare_commit.py
    command_receipt.py
    display_contract.py
    session_binding.py

integrations/
  codex_bridge/
    sidecar.py
    local_spool.py
    hook_ingress.py
    token_client.py
    healthcheck.py

codex-plugin/
  hooks/
    hooks.json
    user_prompt_submit.py
    pre_synaisthesis_tool.py
    post_synaisthesis_tool.py
    stop_response_fidelity.py

configs/
  fidelity/
    strict_bound_session.yaml
    explicit_command.yaml
    degraded_read_only.yaml
```

新增配置：

- `fidelity.mode`
- `fidelity.fail_closed_for_mutations = true`
- `fidelity.capture_raw_prompt = true`
- `fidelity.raw_prompt_privacy = private`
- `fidelity.instruction_token_ttl_seconds`
- `fidelity.prepared_command_ttl_seconds`
- `fidelity.require_state_version = true`
- `fidelity.require_context_manifest_for_mutation = true`
- `fidelity.require_stop_display_audit = true`
- `fidelity.sidecar_transport`
- `fidelity.local_spool_path`
- `fidelity.spool_encryption`
- `fidelity.max_unresolved_references = 0`
- `fidelity.ide_extension_install_mode`
- `fidelity.plugin_hooks_required`


---

<!-- SOURCE: 13_ROADMAP_AND_PORTFOLIO.md -->

# 13 — 开发路线、开源发布与作品集设计

## 1. 总路线

整个项目按“先证明治理闭环，再增加自动化强度”推进。

### v0.1 — Durable Incubator
目标：把现有唯一有效的 S0–S5 从 Skill 迁入平台。

必须完成：
- Project / ResearchSpec / StageRecord；
- S0–S5 阶段契约；
- 用户确认与回退；
- Event Log；
- Artifact Store；
- CLI；
- Codex 通过最小 MCP 调用 Incubator；
- 旧 Skill 输出导入。

作品集价值：证明你能把 Prompt 流程转成耐久状态机。

### v0.2 — Claim Compiler and S6–S10
必须完成：
- Core Theory；
- Formal Construction；
- ClaimUnit；
- ClaimContract；
- MATURE_IDEA_READY；
- S6–S10；
- 研究交接包。

作品集价值：展示领域建模、类型化研究资产和状态边界。

### v0.3 — Dual-Model Council with Fake Tools
必须完成：
- Primary/Auditor；
- Support/Oppose/Independent visibility bundle；
- 默认 10 轮；
- Valid Round 判定；
- checkpoint；
- Human Gate；
- Fake Lean/Z3/Python；
- 成本预算。

作品集价值：展示多模型编排不是“角色扮演 Prompt”，而是隔离、状态与政策。

### v0.4 — Real Verification Lab
必须完成：
- Z3 Adapter；
- Docker Python Sandbox；
- Lean Compiler Mode；
- Statement Lock；
- ExecutionReceipt；
- Evidence Scope；
- Regression 与 Revocation。

作品集价值：展示确定性验证器与 LLM 的正确边界。

### v0.5 — Codex Inbound Integration
必须完成：
- Synaisthesis MCP；
- 三个窄 Skill；
- `.codex-plugin/plugin.json`；
- Codex Operator；
- 异步 run_id；
- Gate 翻译；
- MCP Inspector 测试。

作品集价值：展示标准协议集成和插件产品化。

### v0.6 — Codex Outbound Integration
必须完成：
- `openai-codex` SDK Adapter；
- CodexTaskSpec；
- 双 Profile；
- 独立 worktree；
- CodexExecutionReceipt；
- SDK → MCP → exec 回退；
- recursion guard；
- Codex 产物由 Lean/Z3/Python 重验。

作品集价值：这是项目最有辨识度的工程能力之一——同一系统既能被 Codex 调用，也能把 Codex 当受控工程代理调用。

### v0.7 — Literature and Evidence Graph
必须完成：
- OpenAlex/Crossref/arXiv；
- 最近邻分类；
- 文献元数据核验；
- Claim–Evidence Graph；
- `POSSIBLY_ORIGINAL` 语言边界；
- Bundle Export。

### v0.8 — Web UI and First Real Case Study
必须完成：
- Dashboard；
- Stage Timeline；
- Council Run；
- Evidence Ledger；
- Gate；
- Codex Task Diff；
- 真实案例；
- Demo GIF/视频。

### v0.9 — Interactive Lean and Branch Search
可选：
- LeanDojo-v2/Pantograph；
- proof state；
- sequential tactic；
- 有限修复分支搜索；
- branch scoring；
- branch pruning。

### v1.0 — Stable Local Research Workbench
条件：
- Schema 稳定；
- 跨版本迁移；
- Windows/WSL2 安装文档；
- 至少两个真实案例；
- 可靠 pause/resume；
- 安全审计；
- 完整插件发行流程；
- 清晰 limitation。

## 2. 第一公开版本应当小于最终愿景

公开 v0.1 不要宣称“自动科研平台已经完成”。更可信的定位：

> 一个把自然语言研究构想编译成版本化研究规范、原子命题和可审计验证任务的本地优先工作台。

等真实验证闭环跑通后，再升级描述。

## 3. 推荐第一个公开案例

选择一个同时具备以下条件的问题：
- 自然语言目标容易理解；
- 有一个明显但不一眼可见的有限反例；
- 修复时容易发生对象域或量词漂移；
- Z3 可以编码；
- 修复后有一个简单 Lean 定理；
- Python 可以枚举小规模实例；
- 与你的真实研究方法有关，但不暴露尚未公开的核心成果。

案例应展示：
1. Codex Operator 创建项目；
2. S0–S5；
3. Claim 编译；
4. Council Round 2 找到 Z3 反例；
5. Repair A 将对象域缩小，被判 S3；
6. 用户拒绝；
7. Repair B 保留原语义；
8. 平台调 Codex Worker 构造 Lean 文件；
9. Lean Adapter 独立验证；
10. Auditor 反译；
11. 用户确认；
12. 导出 Evidence Bundle。

这段演示比“多个 Agent 在终端里聊天”有说服力得多。

## 4. README 第一屏

建议一句话：

> Synaisthesis is a human-governed, dual-model research orchestration platform that turns natural-language research intent into versioned claims, adversarial verification loops, formal-tool evidence, and auditable human decisions—with bidirectional Codex integration.

随后展示：

```text
Idea / Spec
    ↓
Claim Compiler
    ↓
Frozen ClaimContract
    ↓
Support · Oppose · Independent
    ↓
Lean · Z3 · Python · Literature · Codex Worker
    ↓
Semantic Audit · Regression · Human Gate
    ↓
Versioned Research Bundle
```

## 5. Demo 不应该展示什么

不要把以下内容作为主要卖点：
- 10 个 Agent 名字；
- 终端中大量自然语言输出；
- 自动生成论文篇数；
- “AI 证明了新定理”；
- 无界自治；
- 模糊的通过率。

应该展示：
- 状态迁移；
- 反例；
- 语义差异；
- 工具回执；
- 撤回；
- 回归；
- 预算；
- Codex worktree diff；
- 可复现 artifact hash。

## 6. 项目指标

### 可靠性
- Invalid Round 比例；
- Tool Evidence 复现率；
- Statement Lock 违规捕获数；
- Semantic Gate 捕获数；
- Regression 捕获数；
- 撤回传播准确率；
- pause/resume 恢复率。

### 研究过程
- 每 Claim 平均攻击数；
- 每轮新增独立攻击数；
- 反例发现轮次；
- 修复候选被拒绝比例；
- 平均达到稳定轮数；
- Human Gate 次数。

### 成本
- 每轮模型调用；
- 每 Claim token；
- Codex Task 次数与耗时；
- 单次稳定结果成本；
- Fake/Eval 与真实模型调用比例。

### 集成
- Codex → Synaisthesis 成功率；
- Synaisthesis → Codex 成功率；
- Recursion Block 命中数；
- worktree 清理成功率；
- Receipt 完整率。

## 7. 简历描述

### 中文
设计并实现人类治理的双模型半自动科研编排平台，将自然语言研究构想编译为版本化命题与验证任务；通过可配置对抗式研究循环、语义变更预算、证据账本、SMT 反例搜索、Lean 形式验证、回归撤回及 Human Gate 构建可审计研究闭环，并通过 MCP/Codex 插件与 Codex Python SDK 实现双向调用和隔离式工程代理执行。

### 英文
Designed and implemented a human-governed dual-model research orchestration platform that compiles natural-language research intent into versioned claims and verification tasks. Built configurable adversarial loops, semantic-mutation controls, evidence provenance, SMT counterexample search, Lean verification, regression/revocation, human approval gates, and bidirectional Codex integration through MCP/plugins and the Codex SDK.

## 8. 面试时的核心讲法

不要说“我做了一个能自动科研的 AI”。

更准确的讲法：

1. 我先在真实研究中设计了一套自然语言治理协议；
2. 发现 Skill 对早期灵感有效，但对长期状态、隔离和工具证据无效；
3. 因此把 Prompt 协议重构成状态机、领域对象和验证适配器；
4. 用两个异构模型降低单点认知错误；
5. 用 Lean/Z3/Python 把生成和验收分开；
6. 用 Semantic Gate 防止模型为了证明而改题；
7. 用双向 Codex 集成，把 Codex 既作为入口，又作为隔离工程执行器；
8. 所有结论都可撤回、回归和复现。

这比强调模型数量更能体现工程判断。

## 9. 开源策略

建议 Apache-2.0 或 MIT；若未来担心服务端商业封装，可再考虑更强限制，但第一版优先降低贡献门槛。

仓库初期公开：
- 核心 schema；
- FakeModel；
- FakeTool；
- 简单验证案例；
- 插件样例；
- 架构文档；
- Eval。

不要公开：
- 真实 API key；
- 用户私有研究材料；
- 未脱敏 Prompt corpus；
- 完整 Codex session；
- 含敏感路径的 Receipt；
- 尚未公开的理论成果。

## 10. 可控副项目节奏

为了不影响主项目，采用“每周一个可提交能力”的粒度：
- 一周只完成一个实体或 Adapter；
- 每个 PR 不跨多个架构层；
- 先 Fake，再真实服务；
- 每个里程碑都有可运行 Demo；
- UI 永远晚于 Core；
- LeanDojo 和树搜索永远晚于 Compiler Mode 和线性 Loop。

## v2.1 路线调整：Codex Fidelity 作为首个可演示能力

第一个公开 Demo 不必等待 Lean/Z3 完成，可以先展示：

1. 用户在 Codex 输入“对 Claim A 运行 10 轮，但不得修改核心语义”。
2. Hook 保存原文与 hash。
3. 故意让 FakeCodexProposal 传成 20 轮并遗漏 prohibition。
4. Command Gateway 返回 F3/F4 并拒绝。
5. 用户修正后 prepare。
6. 用户在 Codex 确认 nonce。
7. 平台执行 FakeRun。
8. Codex 故意遗漏 UNDECIDED 警告。
9. Stop Hook 要求其补全 CommandReceipt。

这个 Demo 能直接证明项目不是普通 Prompt 包，而是具备端到端指令完整性和授权治理的 Research Control Plane。


---

<!-- SOURCE: 14_REFERENCES.md -->

# 14 — 参考项目、官方文档与借鉴边界

本文件用于后续实现时快速定位官方资料。链接会随项目演进变化，正式开发时应再次核验版本。

## 1. OpenAI / Codex 官方资料

### Codex SDK
https://developers.openai.com/codex/codex-sdk

用途：
- Python `openai-codex`；
- `Codex` / `AsyncCodex`；
- thread start/resume；
- sandbox；
- 平台主动调起 Codex 的首选路径。

### Codex MCP Server
https://developers.openai.com/codex/mcp-server

用途：
- `codex mcp-server`；
- `codex()`；
- `codex-reply()`；
- 将 Codex 作为标准 MCP 专家接入编排器。

### Codex 使用 MCP
https://developers.openai.com/codex/mcp

用途：
- Codex Operator 连接 Synaisthesis MCP；
- 本地/远程 MCP 配置。

### Codex Non-interactive Mode
https://developers.openai.com/codex/non-interactive-mode

用途：
- `codex exec`；
- CI/脚本回退路径。

### Codex App Server
https://developers.openai.com/codex/app-server

用途：
- 深度自定义客户端；
- thread/history/approval/stream events；
- Synaisthesis 后期嵌入式 Codex UI。

### Codex Sandbox and Approvals
https://developers.openai.com/codex/sandboxing
https://developers.openai.com/codex/agent-approvals-security
https://developers.openai.com/codex/permissions

用途：
- read-only/workspace-write；
- approval policy；
- network/filesystem boundary；
- Worker Profile。

### Build Skills
https://developers.openai.com/plugins/build/skills

用途：
- Skill 应负责可重复工具流程与决策点；
- 不应替代服务端状态、鉴权与受控动作。

### Package Plugins
https://developers.openai.com/plugins/build/plugins

用途：
- `.codex-plugin/plugin.json`；
- `skills/`；
- `.mcp.json` / `.app.json`；
- hooks 与 assets。

### Build MCP Server for Plugins
https://developers.openai.com/plugins/build/mcp-server

用途：
- 给 ChatGPT/Codex 提供 server-backed controlled actions。

## 2. 自动科研项目

### AI Scientist v2
https://github.com/SakanaAI/AI-Scientist-v2

可借鉴：
- agentic tree search；
- experiment manager；
- 搜索预算；
- 分支评估。

不可直接照搬：
- 以机器学习实验和论文生成作为中心；
- 自动执行研究代码的风险边界；
- 缺少 Synaisthesis 所需的自然语言语义冻结、正交状态与撤回治理。

### Agent Laboratory
https://github.com/SamuelSchmidgall/AgentLaboratory

可借鉴：
- 文献、实验、报告分阶段；
- 专门 Agent；
- checkpoint。

Synaisthesis 差异：
- Claim-first；
- verification-first；
- 形式化工具和语义审计；
- 不以报告生成作为最终验收。

### AutoResearchClaw
应在正式开发前重新核验其仓库位置和当前维护状态。

可借鉴的概念：
- REFINE/PIVOT；
- artifact 版本化；
- multi-agent debate；
- sandbox。

Synaisthesis 必须额外施加：
- PIVOT 的 Semantic Delta；
- Human Gate；
- Tool Evidence；
- Revocation/Regression。

## 3. 工作流与 Agent 编排

### LangGraph
https://github.com/langchain-ai/langgraph
https://docs.langchain.com/oss/python/langgraph/overview

用途：
- 有状态图；
- conditional edge；
- checkpoint；
- pause/resume；
- human-in-the-loop。

边界：
- LangGraph 是执行器，不是领域状态权威；
- Claim 冻结、Evidence PASS、Gate 规则必须由 Domain Policy 决定。

### LiteLLM
https://github.com/BerriAI/litellm
https://docs.litellm.ai/

用途：
- 多 provider 统一调用；
- usage/cost；
- async；
- fallback。

边界：
- Synaisthesis 保留自己的 `LLMProvider` 接口；
- LiteLLM 只是 Adapter。

### Model Context Protocol
https://modelcontextprotocol.io/
https://github.com/modelcontextprotocol/python-sdk

用途：
- Codex/ChatGPT/其他客户端调用 Synaisthesis；
- tools/resources；
- stdio/streamable HTTP；
- Inspector。

## 4. 形式验证

### Lean
https://lean-lang.org/
https://leanprover-community.github.io/

用途：
- Lean 4；
- Lake；
- Mathlib；
- kernel-checked proof artifact。

### LeanDojo
https://github.com/lean-dojo/LeanDojo
https://leandojo.org/

用途：
- 程序化 Lean 交互；
- proof state；
- tactic/command interaction；
- 后期 Proof Loop。

MVP 边界：
- 先使用 Lean Compiler Mode；
- 等 statement lock、artifact、回归稳定后再接 LeanDojo。

### Z3
https://github.com/Z3Prover/z3
https://microsoft.github.io/z3guide/

用途：
- Solver；
- SAT/UNSAT/UNKNOWN；
- model；
- push/pop；
- timeout；
- 有限约束反例。

边界：
- `UNSAT` 只对当前编码成立；
- 编码正确性仍需审计；
- witness 必须独立重验。

## 5. 数据与文献

### OpenAlex
https://docs.openalex.org/

### Crossref
https://www.crossref.org/documentation/retrieve-metadata/rest-api/

### arXiv API
https://info.arxiv.org/help/api/

用途：
- 文献元数据；
- 最近邻研究；
- 原创性风险提示。

边界：
- 搜索结果不能逻辑证明原创；
- 只能给 `POSSIBLY_ORIGINAL`、`OVERLAP`、`INCONCLUSIVE` 等有限状态。

## 6. 采用原则

任何外部项目只能提供：
- 架构模式；
- Adapter 参考；
- 测试方式；
- 失败案例。

不得直接把外部项目宣称的“自治”“审稿”“证明”标签映射到 Synaisthesis 的状态。Synaisthesis 的状态必须经过自己的 ClaimContract、Evidence Scope、Tool Receipt、Semantic Audit 和 Human Gate。

## 15. Codex Hooks 与指令忠实传递

官方资料：

- Codex Hooks：`https://developers.openai.com/codex/hooks`
- Codex MCP：`https://developers.openai.com/codex/mcp`
- Codex Plugin Packaging：`https://developers.openai.com/plugins/build/plugins`
- Codex App Server：`https://developers.openai.com/codex/app-server`
- Codex SDK：`https://developers.openai.com/codex/codex-sdk`

v2.1 依赖的关键事件：

- UserPromptSubmit：获取即将发送的原始用户 prompt；
- PreToolUse：拦截和重写 MCP 工具参数；
- PostToolUse：读取 MCP 工具结果；
- Stop：检查最终 assistant message，必要时要求继续修正。

实现时必须锁定 Codex 版本，并使用对应版本的 schema 做 contract test。


---

<!-- SOURCE: 15_CHANGELOG_FROM_PREVIOUS_BLUEPRINT.md -->

# 15 — 相比上一版工程蓝图的实质性增强

## 1. 从通用设想转为基于真实工作流的迁移设计

上一版从“理想半自动科研平台”出发；v2 以现有 S0–S10 Skill、MATURE_IDEA_READY、FrozenClaim、三轨议会、Governor、ActionRequest/Receipt、A0–A3、checkpoint 与状态边界为权威输入。

因此 v2 不再建议重写整个流程，而是：
- 保留有效语义；
- 识别哪些环节目前只是 Prompt 假象；
- 为每个节点指定领域对象、输入、输出、Gate 和机器验收条件；
- 提供渐进迁移路线。

## 2. 明确解释“为什么只有灵感孵化有效”

新增工作流失败审计：
- S0–S5 属于短反馈、自然语言、用户高频纠正任务；
- S6 以后依赖持久状态、工具执行、角色隔离、证据绑定和回归；
- Skill 只能提供指令，不能自动提供这些系统能力。

这使项目目标从“继续强化 Prompt”转为“把治理协议外化成平台”。

## 3. S0–S10 全部变成 Stage Contract

每阶段新增：
- Entry Condition；
- Input Artifact；
- Output Artifact；
- AI 权限；
- User Gate；
- Machine Gate；
- Failure Route；
- Stage Event；
- 可回退目标。

`MATURE_IDEA_READY` 被改为可机器检查的复合 Gate，而不是模型自由输出标签。

## 4. 增加 Claim Compiler

现有流程从“统一理论”直接进入“正式构造”，容易把一个宏大目标当成一个可验证命题。

v2 新增：
- ClaimUnit；
- ClaimType；
- ClaimContract；
- Falsification Witness；
- Evidence Requirement；
- Tool Route；
- Dependency Graph。

这使 Lean、Z3、Python 和经验研究不再争夺同一个模糊 PASS。

## 5. 重构 S8 与对抗议会的关系

上一流程存在重复：
- S8 已经要求十轮双重反例；
- 右侧 Council 又运行完整对抗研究。

v2 将 S8 重定位为 **Pre-freeze Readiness Attack**：
- 默认 1–2 轮；
- 只检测命题是否足够清晰、是否存在立即致命反例；
- 不再承担完整十轮裁决。

完整默认 10 轮发生在 ClaimContract 冻结后的 Council 中。

## 6. Governor 被拆分

旧 Governor 同时读材料、判证据、决定工具、修复理论、停止 Loop 和导出结论，形成过载单点。

v2 拆成：
- `PolicyGovernor`：确定性规则；
- `SynthesisAgent`：模型综合建议；
- `HumanAdjudicator`：语义和价值承诺；
- `ActionBroker`：外部执行；
- `EvidenceRegistry`：工具与来源边界。

不使用简单模型投票决定事实。

## 7. 增加 Event Sourcing 与不可变 Revision

上一版有 Evidence Ledger，但 v2 进一步规定：
- 所有关键动作写 DomainEvent；
- Revision 不可原地覆盖；
- 当前状态由 event materialization 得到；
- 所有 PASS 可被撤回；
- 依赖结论自动进入 Regression。

聊天记录不再承担数据库作用。

## 8. 增加强类型 ResearchPacket

旧 ResearchPacket 是宽泛文本包。

v2 将其拆成：
- ClaimPacket；
- MethodPacket；
- ExperimentPacket；
- ConstructionPacket；
- FailurePacket；
- UncertaintyPacket；
- ExecutionReceipt；
- ArtifactManifest。

每个 Packet 有 schema、来源、scope、hash 和完整性检查。

## 9. 增加“有效轮次”判定

默认 10 轮不再只是计数器。

一轮只有在以下内容满足时才计入 Valid Round：
- 输入 snapshot 固定；
- 至少一个独立攻击轨道完成；
- 选择的工具实际执行或明确 NOT_APPLICABLE；
- 新证据写入；
- 修复/不修复决定可追溯；
- Semantic Audit 完成；
- Round Receipt 完整。

失败重试、格式修复和空泛“再次思考”不计有效轮次。

## 10. 增加 Proof Loop / Theory Loop 分离

v2 强制：
- Proof Loop 只能修改 proof body；
- theorem statement 用 hash 锁定；
- 修改 statement 必须退出 Proof Loop；
- 进入 Theory Repair；
- 计算 Semantic Delta；
- S2–S4 按政策触发 Gate。

这是防止“为了 Lean 通过而偷偷改题”的核心防线。

## 11. 真正实现 Codex 双向集成

上一版只提出 MCP/Codex Plugin 入口。v2 增加完整出站架构。

### Codex → Synaisthesis
- MCP Server；
- Codex Plugin；
- Operator Skill；
- run_id 异步任务；
- Gate 翻译；
- 状态查询。

### Synaisthesis → Codex
- 首选 `openai-codex` Python SDK；
- 兼容 `codex mcp-server`；
- 回退 `codex exec`；
- 后期 App Server Bridge；
- CodexTaskSpec；
- SessionRecord；
- ExecutionReceipt；
- worktree；
- diff/test/hash；
- Tool Adapter 重验。

## 12. 增加双 Profile 与递归保护

为了防止：

`Codex Operator → Synaisthesis → Codex Worker → Synaisthesis → ...`

v2 新增：
- `codex-operator`；
- `codex-worker`；
- 独立 `CODEX_HOME`；
- Worker 默认不加载 Synaisthesis MCP；
- `origin_chain`；
- `delegation_depth`；
- `reentrancy_key`；
- `max_delegation_depth = 1`；
- 服务端 origin ACL。

## 13. 明确 Codex 的角色

Codex 被定位为：
- 仓库分析器；
- Lean/Z3/Python 工程执行器；
- 测试与 diff 生成器；
- 可审计工程代理。

Codex 不是：
- Lean kernel；
- 独立数学裁判；
- 用户语义确认者；
- 自动原创性认证者。

## 14. 增加安全威胁模型

v2 新增：
- 外部文献/仓库内容的 Prompt Injection 隔离；
- secret redaction；
- Codex Worker 最小上下文；
- Docker sandbox；
- network policy；
- protected path；
- Action allowlist；
- Receipt integrity；
- worker recursion；
- tool output spoofing 防线。

## 15. 增加完整迁移方案

不是一次性废弃现有 Skills，而是：
1. 冻结为 baseline；
2. 导入 golden/failure cases；
3. 平台先存状态；
4. 迁 S0–S5；
5. 迁 S6–S10；
6. 迁 Council；
7. 关闭旧插件执行逻辑；
8. 加平台调 Codex Worker。

## 16. 增加工程可实施性

v2 新增：
- 完整目录树；
- 配置分组；
- 进程拓扑；
- 函数/API/MCP 契约；
- 逐阶段机械实施；
- 测试矩阵；
- Eval 指标；
- 开源与作品集路线；
- 第一个真实 Demo 的选择标准。

## 17. 最终定位变化

上一版更像：
> 多模型 + Lean/Z3 的半自动科研 Agent 平台。

v2 更准确地定位为：
> 将研究语义、命题、攻击、工具证据、修复、授权、撤回和 Codex 工程执行统一到一个可审计状态机中的人类治理科研控制平面。

这个定位更加具体，也更适合作为可复用开源项目和工程作品集。

## 16. v2.1：Codex 指令忠实传递层

新增：

- Codex Bridge Sidecar；
- UserPromptSubmit 原文捕获；
- InstructionCapsule；
- InstructionToken；
- CodexSessionBinding；
- ContextManifest；
- CommandProposal / PlatformInterpretation 双解释；
- Instruction Delta F0–F5；
- mutation 统一 Command Gateway；
- prepare/commit；
- UserConfirmationEvent；
- CommandReceipt；
- DisplayContract；
- PostToolUse / Stop 输出忠实审计；
- Desktop/CLI 与 IDE Extension 双安装路径；
- `FIDELITY_VERIFIED` / degraded 状态；
- 18 项指令忠实性 E2E。

重大原则变化：

> Codex Skill 不再被视为忠实传递保证。只有 Hook 捕获、签名 token、服务端 diff、状态版本和回执审计共同通过，平台才标记 `FIDELITY_VERIFIED`。


---

<!-- SOURCE: 16_OPENCODE_DEEPSEEK_DEVELOPMENT_PROFILE.md -->

# 16 — OpenCode + DeepSeek 工程开发 Profile

## 1. 本文档定位

本文档只规定“使用 OpenCode + DeepSeek 开发 Synaisthesis 时的工程行为”，不替代产品架构规范，也不把 OpenCode 或 DeepSeek写入 Synaisthesis Core 的不可替换依赖。

## 2. 工作区

- 工程根目录：`E:\Synaisthesis`
- OpenCode 应从工程根目录启动。
- `AGENTS.md` 为工程行为规则入口。
- `docs/blueprint/` 保存本 V2 全套蓝图。
- `IMPLEMENTATION_STATUS.md` 保存真实当前实现状态。
- `TASKS.md` 保存待执行的机械任务。

## 3. 推荐 OpenCode 角色

### Architect
- 只读为主。
- 读取蓝图、拆任务、检查架构。
- 不直接实现大规模修改。

### Builder
- 实现当前已批准的单个 Task。
- 只能在该 Task 边界内修改文件。
- 必须执行对应测试并报告真实退出结果。

### Blind Reviewer
- 使用独立会话。
- 不依赖 Builder 的自我解释。
- 只根据蓝图、diff、代码与真实测试结果审查。

## 4. DeepSeek 使用原则

- 当前允许单一 DeepSeek 模型承担工程开发，但不同 Agent / 会话不等于产品中的“异构模型验证”。
- 产品设计中的 Primary / Auditor 必须继续保持 Provider 抽象。
- 所有模型调用必须经过结构化 schema 校验。
- 自动化测试使用 FakeModel，避免 CI 持续消耗真实 API。

## 5. 单 Task 开发循环

1. Architect 读取相关蓝图片段。
2. 输出任务边界、涉及文件、数据流、测试和风险。
3. 用户批准。
4. Builder 实现。
5. 运行 Ruff / 类型检查 / pytest 或任务指定验证。
6. 输出 git diff 摘要。
7. Blind Reviewer 在独立上下文审查。
8. 人工确认。
9. 小粒度 Git commit。

## 6. 禁止事项

- 不允许一句“按蓝图实现整个项目”触发全仓库重构。
- 不允许 DeepSeek 自行跨 Milestone。
- 不允许自动 `git push`。
- 不允许自动 `git reset --hard`、`git clean -fd` 等破坏性命令。
- 不允许把模型生成的工具结果文本当作真实工具回执。
- 不允许为了让测试通过而静默弱化核心规范。

## 7. Skills 策略

开发初期仅使用“软件工程纪律型” Skills，例如：

- spec-driven development
- task planning / decomposition
- incremental implementation
- test-driven development
- context engineering
- code review
- security hardening
- MCP builder（到 MCP 阶段再启用）

不要安装会重新定义科研方法论、自动研究议会或自治研究流程的第三方 Skill，以免污染 Synaisthesis 自身蓝图。


---

<!-- SOURCE: 17_AGENTS_MD_TEMPLATE.md -->

# 17 — AGENTS.md 模板

将本文件内容复制到仓库根目录 `AGENTS.md` 后再按实际实现阶段更新。

---

# Synaisthesis Engineering Rules

## Authority

Authoritative sources, highest first:

1. `docs/blueprint/`
2. `IMPLEMENTATION_STATUS.md`
3. `TASKS.md`
4. Current explicit user instruction
5. Existing implementation

When sources conflict, do not silently choose. Report the conflict and stop before changing authoritative semantics.

## Project identity

- Chinese name: 联觉科研
- Short Chinese name: 联科
- English name: Synaisthesis
- Repository root on this workstation: `E:\Synaisthesis`

## Development mode

Implement incrementally. Never implement the whole blueprint in one task.

Before modifying code:
1. identify the exact Task / Milestone;
2. read only the relevant blueprint sections;
3. list the files expected to change;
4. state acceptance tests;
5. state architectural risks.

After modifying code:
1. run the required real checks;
2. report commands and exit results;
3. show a diff summary;
4. update `IMPLEMENTATION_STATUS.md` when appropriate;
5. do not start the next Task automatically.

## Research verification boundaries

- LLM output is a proposal, not a deterministic tool result.
- Lean PASS can only be recorded after a real Lean invocation succeeds.
- Z3 SAT / UNSAT / UNKNOWN can only be recorded from the real solver adapter.
- Python experiment PASS can only be recorded from the sandbox execution receipt.
- Formal verification, semantic alignment, novelty and empirical validity are separate statuses.

## Semantic governance

- Do not silently change object domains, quantifiers, core assumptions, core conclusions or engineering goals.
- Core semantic changes require Human Gate.
- Proof Loop may modify proof content but not the frozen theorem statement.
- Every theory repair creates a new revision; never overwrite historical revisions.

## Git safety

Do not run without explicit user request:
- `git push`
- `git reset --hard`
- `git clean -fd`
- destructive rebase
- history rewriting
- automatic commit

## Provider architecture

DeepSeek is the current engineering model, but Synaisthesis Core must remain provider-agnostic.

Do not hard-code product logic to a single LLM vendor.


---

<!-- SOURCE: 18_IMPLEMENTATION_STATUS_TEMPLATE.md -->

# 18 — IMPLEMENTATION_STATUS.md 模板

# Synaisthesis Implementation Status

## Current milestone
`M0`

## Current task
`NOT_STARTED`

## Last verified commit
`NONE`

## Environment
- Project root: `E:\Synaisthesis`
- Primary engineering client: OpenCode
- Primary engineering model: DeepSeek V4 Pro
- Python: NOT_CHECKED
- uv: NOT_CHECKED
- Git: NOT_CHECKED
- Docker: NOT_CHECKED
- Z3: NOT_CHECKED
- Lean: NOT_CHECKED
- Node.js: NOT_CHECKED

## Implemented
- None.

## Verified
- None.

## Known failures
- None.

## Pending Human Gates
- None.

## Next allowed task
- Initialize repository skeleton according to the V2 blueprint.

## Notes
Only record work that actually exists in the repository. Do not infer completion from plans or model statements.
