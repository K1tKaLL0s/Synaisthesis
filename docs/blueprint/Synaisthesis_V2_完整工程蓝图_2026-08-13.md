# Synaisthesis V2.4 完整工程蓝图

**中文名：联觉科研｜简称：联科｜英文名：Synaisthesis**

**当前工程根目录：E:\Synaisthesis**

本文件由分册蓝图按 manifest.authoritative_order 机械合并生成；分册文件是唯一编辑源。V2.4 已冻结形式化分流、工程转化以及双路线论文母稿/正式稿决策与发布 Profile 规范；文档基线不表示相应产品功能已经实现。

---

<!-- SOURCE: 00_README.md -->

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
- 工程客户端：OpenCode 或 DeepSeek 官方 DSH；两者均从工程根目录启动并遵守同一套 `AGENTS.md`、WorkUnitContract、Human Gate 与验证规则
- 主工程模型：DeepSeek V4 Pro
- 工作目录：`E:\Synaisthesis`
- OpenCode 本体建议独立放在：`D:\AI\OpenCode`
- DeepSeek 官方 DSH 本机安装位置：`E:\CodexData\apps\deepseek-harness`
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

在 DeepSeek + OpenCode / 官方 DSH 开发阶段，按以下顺序推进：

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

<!-- SOURCE: CURRENT_DECISIONS.md -->

# CURRENT_DECISIONS

- 正式中文名：联觉科研
- 简称：联科
- 英文名：Synaisthesis
- Windows 项目根目录：`E:\Synaisthesis`
- 当前工程客户端：OpenCode 或 DeepSeek 官方 DSH；两者共享同一工程规则与任务边界
- 当前工程模型：DeepSeek V4 Pro
- Codex：继续独立推进现有理论验证；产品最终仍需双向 Codex 集成
- 默认自主 Loop：最多 10 轮，用户可配置
- 产品正式科研模式：至少两个异构模型
- 核心验证工具：Lean + Z3 + Python Sandbox
- 核心治理：Semantic Delta、Human Gate、Evidence Ledger、Regression、Revocation
- 开发策略：小 Task、小 commit、FakeModel/FakeTool 先行、UI 后置
- 持久化 ORM：SQLAlchemy 2 + Alembic；不采用 SQLModel 作为领域模型层
- 类型检查：basedpyright（与当前 M0 CI 一致）
- 自然语言设计完成门：S0–S4 PASS 且 S1/S4 用户确认后进入 `NATURAL_LANGUAGE_DESIGN_READY`
- 强制早期资格：S4 后必须执行带 RQ2F 可行性分流的 RQ0–RQ4，不得绕过
- 早期形式化能力：平台 ADVANCED Formalizer 或标准化外部高能力模型导入
- 形式化可行性：理论 TFO–TFP、工程 EFS–EFF 双评估保守聚合；纯理论不适配但工程适配时必须由用户选择修改设计或尝试工程项目
- 理论早期形式化：核心内容必须是数学公式，用户审查 formula/spec hash 与简明解释
- 工程概念形式化：以 I/O、状态、要求谓词、质量阈值、架构图候选和追踪关系表达，不伪装成纯数学理论
- 新颖性：理论路线为理论 50 + 应用 50；工程路线为工程 60 + 应用 40；两个隔离 Reviewer 逐项取较小值
- 自动门槛：有效总分 >=70 时理论路线自动进入 S5、工程路线自动进入 ENG0；<70 或 INCONCLUSIVE 交还用户决定是否重新研究
- 工程交付：ENG0–ENG10 输出可机械执行蓝图、文本图源及渲染图、应用/扩展路线和证据约束 EngineeringMasterManuscript
- 理论论文交付：纯数学路线最终交付必须包含 TheoryMasterManuscript、证明依赖图和 theorem/claim→statement/proof/evidence/citation 追踪矩阵
- 论文顺序：两条路线都先生成并独立审计母稿、先交给用户，再打开 `FORMAL_MANUSCRIPT_DECISION`；无响应不得默认为正式稿
- 正式稿选择：只有用户选择 WRITE_FORMAL_MANUSCRIPT 才打开 PublicationProfile Selection，并生成 VenueAdapter 稿与 ComplianceMatrix；KEEP_MASTER_ONLY 也是完整交付
- 理论内置 Profile：Annals of Mathematics、JAMS、Inventiones mathematicae、Acta Mathematica，加 `MATH_ARXIV_PREPRINT`
- 工程内置 Profile：IEEE TSE、ACM TOSEM、Empirical Software Engineering、Journal of Systems and Software，加 `ENG_ARXIV_PREPRINT`；非软件工程使用 CUSTOM_VENUE
- arXiv 身份：arXiv 是 `PREPRINT_REPOSITORY`，不是期刊、同行评审或录用状态
- 论文适配：不承诺一篇稿件天然满足所有期刊；采用 MasterManuscript + PublicationProfile + VenueAdapter + ComplianceMatrix，且适配不得改变研究语义或证据
- 工程执行边界：默认 BLUEPRINT_ONLY；代码、实验、采购、生产发布与投稿均需各自授权，论文不得虚构结果
- 机械实施：任何代码 Task 必须满足 `19_MECHANICAL_EXECUTION_CONTRACT.md`

V2.3 工程分流与 ENG0–ENG10 已于 2026-08-14 被用户整体采纳；连同双路线论文交付补丁统一冻结为 `V2.4` 正式文档基线。文档冻结不表示相应产品功能已经实现。


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
       ┌────────────────┬───────────────────────┼─────────────────────────┐
       │                │                       │                         │
 Incubator + RQ   Engineering Translation   Claim Compiler       Adversarial Council
 S0–S4→RQ0–RQ4   ENG0–ENG10 Blueprint       Atomic ClaimUnit      bounded 10-round loop
       │                │                       │                         │
       └────────────────┴───────────────────────┴──────────────┬──────────┘
                                               │
                                      Verification Lab
                      ┌───────────┬──────────┬───────────┬─────────┐
                      │           │          │           │         │
                   Lean        Z3/cvc5     Python     Literature  Codex Worker
                      │           │          │           │         │
                      └───────────┴──────────┴───────────┴─────────┘
                                               │
                             Dual-track Publication Pipeline
                       Theory/Engineering Master → User Decision
                       → 4 Journals or arXiv Venue Adapter
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
- FormalizationFeasibilityAssessment；
- EngineeringConceptBundle；
- EngineeringMissionCharter；
- EngineeringRequirement / ArchitectureBaseline / EngineeringWorkUnitContract；
- PublicationProfile / ManuscriptClaim / VenueComplianceItem；
- TheoryPublicationEvidenceBaseline / TheoryMasterManuscript；
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
- QualificationService；
- NoveltyService；
- EngineeringDesignService；
- EngineeringTraceabilityService；
- PublicationService；
- TheoryPublicationService；
- EngineeringDeliveryAuditService；
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

### Early Formalizer
负责：
- 基于 S1/S4 与最近邻证据集参与理论适配分析并生成数学公式化候选；
- 输出符号、公式依赖、语义映射与不确定性；
- 只能使用通过 RQ0 能力门的 Profile；
- 不得写入证明、新颖性或工具 PASS。

### Engineering Feasibility Assessor
负责：
- 在隔离 Session 中评估 system boundary、I/O、可分解架构、验收指标与约束可调查性；
- 与 Early Formalizer 的谓词矩阵保守聚合；
- 只能产生 `ENGINEERING_PROJECT_CANDIDATE`，不能替用户选择工程路线；
- 不得把缺少理论对象自动等同于工程可行。

### Novelty Reviewers
负责：
- 按 route 分别对理论 50 + 应用 50，或工程 60 + 应用 40 给出证据化评分；
- 正式科研 Profile 使用两个异构、隔离 Session；
- 平台逐项取较小评分并确定 70 分路由；
- 不得宣称绝对原创、论文可录用或可授予专利。

### Engineering Delivery Auditor
负责：
- 独立检查 requirement → design → task → test → manuscript 双向追踪；
- 检查机械蓝图是否仍把产品或架构决策留给实施者；
- 检查图示、接口、状态、单位、真实回执和论文主张一致性；
- 不得参与被审版本的初稿生成。

### Theory Manuscript Auditor
负责：
- 检查稿件定义、假设、对象域、量词、定理 statement hash 与 FrozenClaim 一致；
- 检查 Proof Dependency Graph、形式/计算 Scope、引用、反例和未解决义务；
- 检查模型没有把 conjecture、partial proof 或 solver 范围结果升格成 theorem；
- 不得参与被审母稿或适配稿的初稿生成。

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
- 早期形式化审查；
- 纯理论不适配时选择修改设计、尝试工程路线、暂停或归档；
- 工程概念、重大架构、原型执行、目标期刊和工程交付验收；
- 理论/工程母稿交付后是否生成正式论文、选择哪个期刊/arXiv Profile，以及所有作者责任和投稿动作；
- 低于 70 分或检索不确定时是否重新研究；
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
- expected_functions
- target_applications
- intended_users
- operational_constraints
- success_metrics
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
- mature_engineering_projects
- engineering_maturity_evidence
- function_application_neighbors
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

## NATURAL_LANGUAGE_DESIGN_READY — 自然语言设计完成门

由 S0–S4 PASS、S1/S4 用户确认、预期功能/应用/用户/约束/指标齐全且无 Critical 歧义计算。一次性导入的完整设计也必须规范化为 S0–S4 Artifact。

该状态的唯一下一步是 RQ0，不允许直接进入 S5 或 ENG0。RQ0–RQ4 的输入输出、可行性分流、公式要求、用户审查、路线化新颖性百分制与路由见 `03A_EARLY_FORMALIZATION_AND_NOVELTY_GATE.md`；工程路线通过后进入 `03B`，不计算本文件的理论型 `MATURE_IDEA_READY`。

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
- 当前 S1/S4 hash 已完成 RQ0–RQ4；
- novelty status 为 `NOVELTY_QUALIFIED`，或用户以 `CONTINUE_WITH_RECORDED_OVERRIDE` 明确继续；
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

S4 之后的 `execute_stage` 必须先检查 `NATURAL_LANGUAGE_DESIGN_READY` 和 RQ 前置；S5 只接受理论 route 的有效 RQ4M，ENG0 只接受用户已选择的工程 route 与有效 RQ4E。检查失败统一返回 `EARLY_QUALIFICATION_REQUIRED`，不得隐式补跑或绕过。

## 4. 对话与平台的边界

Codex 或 Web 对话中只展示：
- 当前 Stage；
- 待确认差异；
- 新 Artifact 摘要；
- Blocker；
- 下一步工具动作。

完整状态保存在平台，不能依赖对话历史恢复。


---

<!-- SOURCE: 03A_EARLY_FORMALIZATION_AND_NOVELTY_GATE.md -->

# 03A — 早期形式化、可行性分流、相邻工作检索与新颖性资格门

本文是 S0–S10 孵化流程的强制子协议。它解决四个固定问题：自然语言设计成形后，系统应先判断其是否适合构建纯数学理论；如果适合，则生成可审查的数学早期形式化；如果不适合纯数学理论但可构建为工程项目，则必须由用户决定是否改设计或转工程路线；两条路线都必须在进入后续主流程前完成相邻工作检索、用户审查和与路线匹配的新颖性审验。

不得先进入最小范例、核心理论、工程蓝图、Claim 冻结或 Council，再补做本协议。

## 1. 适用位置、路线和唯一合法主路径

自然语言设计的完成状态定义为 `NATURAL_LANGUAGE_DESIGN_READY`，计算条件是：

- S0–S4 均为 PASS；
- S1 `NaturalLanguageSpec` 与 S4 `ResearchScopeSpec` 均已由用户确认；
- `expected_functions`、`target_applications`、`intended_users`、`operational_constraints`、`success_metrics` 均存在；
- 不存在未解决的 Critical 歧义。

用户一次性提交完整自然语言设计时，平台仍须将其规范化为 S0–S4 Artifact 并取得 S1、S4 确认。不得因为输入看似完整而跳过语义冻结。

唯一合法主路径：

```text
S0 → S1 → S2 → S3 → S4
                     ↓
        NATURAL_LANGUAGE_DESIGN_READY
                     ↓
RQ0 能力与执行路线确认
                     ↓
RQ1 相邻研究与成熟工程项目检索
                     ↓
RQ2F 形式化可行性分析
        ├─ THEORY_OR_HYBRID_FIT
        │       ↓
        │  RQ2M 数学公式化早期形式化
        │       ↓
        │  RQ3M 用户审查数学形式化
        │       ↓ APPROVE
        │  RQ4M 理论 50 + 应用 50 新颖性审查
        │       ├─ score >= 70 → NOVELTY_QUALIFIED → S5
        │       └─ score < 70 / INCONCLUSIVE → BLOCKED_NOVELTY_USER
        │
        ├─ ENGINEERING_PROJECT_CANDIDATE
        │       ↓
        │  ENGINEERING_ROUTE_DECISION（强制 Human Gate）
        │       ├─ REVISE_FOR_THEORY → 新 S1/S4 Revision → RQ1
        │       ├─ TRY_ENGINEERING_PROJECT
        │       │       ↓
        │       │  RQ2E 工程概念形式化
        │       │       ↓
        │       │  RQ3E 用户审查工程概念
        │       │       ↓ APPROVE
        │       │  RQ4E 工程 60 + 应用 40 新颖性审验
        │       │       ├─ score >= 70 → ENGINEERING_NOVELTY_QUALIFIED → ENG0
        │       │       └─ score < 70 / INCONCLUSIVE → BLOCKED_NOVELTY_USER
        │       └─ PAUSE / ARCHIVE
        │
        └─ NEITHER_FIT / INCONCLUSIVE
                ↓
          FORMALIZATION_FEASIBILITY_DECISION（强制 Human Gate）
                ├─ REVISE_DESIGN → 新 S1/S4 Revision → RQ1
                ├─ RESEARCH_MORE → RQ1
                └─ PAUSE / ARCHIVE
```

`RQ2` 是阶段族名称；`RQ2F`、`RQ2M`、`RQ2E` 是互斥或前后相接的稳定子阶段。V2.2 Artifact 中未带后缀的 `RQ2`、`RQ3`、`RQ4` 分别按 `RQ2M`、`RQ3M`、`RQ4M` 读取，不得把旧 Artifact 猜测为工程路线。

理论路线的 RQ3M 未批准时禁止启动 RQ4M。工程路线的 `ENGINEERING_ROUTE_DECISION` 未选择 `TRY_ENGINEERING_PROJECT`、RQ3E 未批准时，禁止启动 RQ4E。任何 RQ4 未形成有效结论时，均禁止自动进入后续主流程。

工程路线的后续唯一入口是 `03B_ENGINEERING_TRANSLATION_WORKFLOW.md` 的 ENG0；不得进入 S5、S6–S10 或纯理论 Claim Compiler，除非用户之后建立新的理论型 S1/S4 Revision 并重新通过本协议。

## 2. RQ0 — 能力与执行路线确认

### 2.1 目标

确保早期形式化和可行性分流不是由只适合整理文本的低能力配置完成。产品不得把具体供应商或模型名称硬编码为“更智能”；使用可验证的能力 Profile。

### 2.2 两条允许路线

#### `PLATFORM_ADVANCED_FORMALIZER`

平台选择具有 `EARLY_FORMALIZER` 角色资格的 `ModelProfile`。全部满足才可用：

- `capability_tier >= ADVANCED`；
- `formalization_eval_score >= 80/100`；
- `math_schema_valid_rate >= 0.95`；
- 支持来源引用和结构化输出；
- 上下文预算可容纳 S1/S4、检索证据集和输出 Schema；
- 能力评估记录未过期，默认有效期 90 天；
- 当前调用预算与隐私策略允许。

若自然语言设计所用模型不满足上述要求，平台必须选择更高能力 Profile。若原模型已经满足，平台可以继续使用，但必须建立新的隔离 `EARLY_FORMALIZER` Session。

RQ2F 的工程适配判定还必须有 `ENGINEERING_FEASIBILITY_ASSESSOR` 角色。该角色可以与 Early Formalizer 使用同一模型 Profile，但必须使用隔离 Session、不同 Prompt Asset 和独立初始输出；正式科研 Profile 优先使用不同模型家族。

#### `EXTERNAL_ADVANCED_MODEL_IMPORT`

用户可在外部高能力模型中完成可行性分析或早期形式化并导入。导入包必须包含：

- `source_model_identity`；
- `source_provider` 或 `USER_REDACTED`；
- `created_at`；
- `input_spec_hash`；
- `neighbor_evidence_set_id`；
- `route_assessment`；
- `formula_bundle` 或 `engineering_concept_bundle`；
- `public_rationale`；
- `provenance = EXTERNAL_MODEL_IMPORT`。

外部导入不自动获得可信状态。平台仍要执行 Schema、公式覆盖、引用、语义对齐、分流规则和 hash 校验。

### 2.3 输出：`FormalizationCapabilityDecision`

- `decision_id`
- `project_id`
- `research_spec_id`
- `route`
- `model_profile_id`（外部导入可为空）
- `capability_evidence_refs`
- `input_spec_hash`
- `budget_snapshot_id`
- `privacy_policy_snapshot_id`
- `status`
- `blocker`

### 2.4 状态

- `CAPABILITY_READY`
- `CAPABILITY_UNAVAILABLE`
- `EXTERNAL_IMPORT_PENDING`
- `BLOCKED_BUDGET`
- `BLOCKED_PRIVACY`

没有 `CAPABILITY_READY` 时不得进入 RQ1/RQ2；外部导入等待期间不得以普通模型静默代替。

## 3. RQ1 — 相邻研究与成熟工程项目检索

### 3.1 目标

在生成形式化前建立最近邻证据集，覆盖：

1. 理论、方法、对象域或预期结论接近的研究；
2. 在预期功能、使用场景、系统边界或应用目标上接近的成熟工程项目；
3. 适用领域的标准、参考架构或公开工程规范；
4. 适用领域中的专利或公开技术方案（可选，只有策略要求时启用）。

S3 `PriorWorkMap` 是查询种子，不直接等于 RQ1 结果。RQ1 必须产生与当前 S1/S4 hash 绑定的新检索快照。

### 3.2 查询生成

查询必须从以下字段分别派生，不允许只使用项目标题：

- 核心对象与术语；
- 候选机制；
- 预期输入/输出；
- 预期功能；
- 目标用户或应用场景；
- 失败条件与约束；
- 系统边界、质量属性和部署约束；
- 已知近邻及其同义词。

每个查询保存原文、生成来源、Provider、时间范围、过滤条件、页数/结果数和执行时间。

### 3.3 最低覆盖门

默认配置：

- 至少 3 类独立学术来源，首选 OpenAlex、Crossref、arXiv；
- 至少 2 类工程来源，按领域从官方仓库、包注册表、官方产品/项目文档、标准组织资料中选择；
- 去重后至少保留 5 个学术最近邻与 3 个成熟工程最近邻；
- 若客观不足，保存完整查询与不足原因，状态只能为 `PARTIAL` 或 `INCONCLUSIVE`；
- 每个入选项必须有可稳定解析的标识符或 URL、元数据核验状态和访问时间；
- 外部内容一律按不可信输入隔离，不得触发工具或修改状态。

“成熟工程项目”至少满足以下四项中的两项，并保存证据：

- 有稳定版本、发布记录或明确部署版本；
- 有持续维护记录；
- 有公开用户、部署、引用或采用证据；
- 有足以复现主要功能的官方文档或测试。

不足最低数量不等于不存在近邻，也不得据此给高新颖性分。

### 3.4 近邻相似度记录

每个近邻由两组 0–4 离散特征描述，分值必须附证据引用：

```text
theory_proximity =
  0.35*object_domain +
  0.30*mechanism +
  0.20*assumptions +
  0.15*conclusion

application_proximity =
  0.25*expected_function +
  0.20*use_context +
  0.20*input_output +
  0.15*system_architecture +
  0.10*operational_constraints +
  0.10*maturity
```

其中每个分量范围为 `[0, 4]`。公式只用于排序，不构成新颖性结论。学术最近邻按 `theory_proximity` 排序；工程最近邻按 `application_proximity` 排序。

### 3.5 输出：`NeighborEvidenceSet`

- `search_id`
- `research_spec_id`
- `input_spec_hash`
- `query_records[]`
- `academic_neighbors[]`
- `engineering_neighbors[]`
- `standards_and_reference_architectures[]`
- `patent_neighbors[]`
- `metadata_verification_receipts[]`
- `inclusion_exclusion_log`
- `unsearched_areas[]`
- `coverage_status`
- `coverage_blockers[]`
- `artifact_hash`

允许状态：

- `COMPLETE`
- `PARTIAL`
- `INCONCLUSIVE`
- `FAILED_PROVIDER`
- `BLOCKED_NETWORK`

只有 `COMPLETE` 可以进入自动新颖性判定。`PARTIAL` 可以继续生成候选供用户审查，但 RQ4 最终只能给 `INCONCLUSIVE`。

## 4. RQ2F — 形式化可行性分析与强制分流

### 4.1 目标与禁止行为

RQ2F 判断当前冻结设计是否具备纯数学理论构造所需的语义材料，以及是否具备工程项目构造所需的可实施材料。它不判断设计“好坏”，也不得为了得到某条路线而改写 S1/S4。

系统不得把“目前缺少数学对象”自动解释为“工程项目”，也不得把工程需求包装成虚构定理。只有 `theory_fit = false` 且 `engineering_fit = true` 时才能产生 `ENGINEERING_PROJECT_CANDIDATE`，并且必须由用户明确选择 `TRY_ENGINEERING_PROJECT`。

### 4.2 理论适配的确定性谓词

每个谓词必须是 `PASS | FAIL | UNKNOWN` 并附 S1/S4 字段或 RQ1 证据引用：

- `TFO`：存在稳定的对象域、类型或集合；
- `TFR`：核心关系、运算、约束或动力学可定义；
- `TFC`：至少存在一个非平凡、可证明或可证伪的核心主张；
- `TFW`：可表达证明义务、反例或失败见证；
- `TFP`：数学抽象不删除预期功能、目标应用或关键边界。

```text
theory_fit = TFO ∧ TFR ∧ TFC ∧ TFW ∧ TFP
```

任何谓词为 `UNKNOWN` 时，`theory_fit` 不得为 true。

### 4.3 工程适配的确定性谓词

- `EFS`：存在明确的利益相关者、用户问题或应用场景；
- `EFI`：存在可定义的输入、输出、接口或操作行为；
- `EFA`：可以分解出系统边界、组件或责任；
- `EFM`：至少一个成功指标可转成带阈值的验收条件；
- `EFF`：在已知时间、预算、数据、依赖、安全与合规约束下存在可调查的实现路线。

```text
engineering_fit = EFS ∧ EFI ∧ EFA ∧ EFM ∧ EFF
```

`EFF` 只表示“值得进入工程设计”，不表示已证明项目能成功、已获预算或可直接生产部署。

### 4.4 双评估与保守聚合

Early Formalizer 和 Engineering Feasibility Assessor 分别输出自己的谓词矩阵。聚合器对每个谓词采用 `FAIL > UNKNOWN > PASS` 的保守顺序；任一评估器给 `FAIL`，聚合结果为 `FAIL`，任一评估器给 `UNKNOWN` 且无人给 `FAIL`，结果为 `UNKNOWN`。

固定分类：

| theory_fit | engineering_fit | `route_classification` | 路由 |
|---|---|---|---|
| true | true | `HYBRID_FIT` | 默认 RQ2M；保留工程映射 |
| true | false | `PURE_THEORY_FIT` | RQ2M |
| false | true | `ENGINEERING_PROJECT_CANDIDATE` | 强制 `ENGINEERING_ROUTE_DECISION` |
| false | false | `NEITHER_CURRENTLY_FIT` | 强制 `FORMALIZATION_FEASIBILITY_DECISION` |
| 任一 UNKNOWN | 任意 | `INCONCLUSIVE` | 强制 `FORMALIZATION_FEASIBILITY_DECISION` |

### 4.5 输出：`FormalizationFeasibilityAssessment`

- `assessment_id`
- `version`
- `research_spec_id`
- `input_spec_hash`
- `neighbor_evidence_set_id`
- `assessor_session_ids[]`
- `theory_predicates[]`
- `engineering_predicates[]`
- `disagreements[]`
- `missing_information[]`
- `route_classification`
- `recommended_route`
- `public_explanation`
- `artifact_hash`
- `status`

`public_explanation` 最多 12 条，必须解释为什么不适合纯数学理论、为什么可能适合工程项目以及判断的不确定性；禁止使用贬低性语言。

### 4.6 Human Gate

`ENGINEERING_ROUTE_DECISION` 必须展示当前 S1/S4 hash、失败的理论谓词、通过的工程谓词、最近工程近邻、风险和两个可行动选项。合法决定：

- `REVISE_FOR_THEORY`：创建新的 S1/S4 Revision 草案；必须再次由用户冻结后从 RQ1 开始；
- `TRY_ENGINEERING_PROJECT`：创建 `EngineeringRouteSelection`，进入 RQ2E；
- `PAUSE`；
- `ARCHIVE`。

`FORMALIZATION_FEASIBILITY_DECISION` 的合法决定：

- `REVISE_DESIGN`：创建新的 S1/S4 Revision 草案；
- `RESEARCH_MORE`：返回 RQ1；
- `PAUSE`；
- `ARCHIVE`。

用户决定绑定 `assessment_id + version + artifact_hash + input_spec_hash`。任何绑定字段变化都会使旧决定失效。模型、工作流或管理员不得代替用户选择工程路线。

## 5. RQ2M — 数学公式化早期形式化

### 5.1 目标与边界

RQ2M 将理论或混合型自然语言设计翻译为可审查的数学候选，不声称已证明、已验证或已达到 Lean/Z3 可执行性。S7 仍负责后续正式构造，Verification Lab 仍负责真实工具结果。

核心形式化内容必须写成数学公式。自然语言只能用于符号释义、来源说明、不确定性和面向用户的简短解释；不得把核心命题只留在叙述中。

### 5.2 输出：`EarlyFormalizationBundle`

- `formalization_id`
- `version`
- `research_spec_id`
- `input_spec_hash`
- `feasibility_assessment_id`
- `neighbor_evidence_set_id`
- `formalizer_profile_or_import_id`
- `notation_table[]`
- `formula_items[]`
- `formula_dependency_graph`
- `semantic_alignment_matrix[]`
- `neighbor_difference_matrix[]`
- `uncertainty_register[]`
- `plain_language_explanation`
- `validator_results[]`
- `artifact_hash`
- `status`

### 5.3 `FormulaItem`

每个公式项必须包含：

- `formula_id`
- `formula_type`
- `latex`
- `normalized_math_ast`（若当前解析器支持）
- `symbols_used[]`
- `source_spec_fields[]`
- `assumption_formula_ids[]`
- `neighbor_refs[]`
- `origin = USER | DERIVED | PRIOR_WORK | MODEL_PROPOSAL`
- `confidence`
- `known_ambiguities[]`
- `falsification_or_failure_formula_id`

### 5.4 必须覆盖的公式类型

适用时必须包含：

- 对象域：例如 `x \in \mathcal{X}`；
- 输入/输出映射：例如 `f: \mathcal{X} \to \mathcal{Y}`；
- 状态与转移：例如 `s_{t+1}=T(s_t,u_t;\theta)`；
- 假设集合：例如 `A(x,\theta)=\bigwedge_i A_i(x,\theta)`；
- 不变量：例如 `\forall t,\ I(s_t)=1`；
- 核心主张：例如 `\forall x\in D,\ A(x)\Rightarrow C(x)`；
- 目标或评价函数：例如 `\theta^*=\arg\min_\theta L(\theta)`；
- 失败/证伪见证：例如 `\exists x\in D,\ A(x)\land\neg C(x)`；
- 理论到工程应用映射：例如 `\Phi:\mathcal{M}\to\mathcal{A}`；
- 后续验证义务：例如 `O=\{O_1,\ldots,O_n\}`。

确实不适用的类型记录 `NOT_APPLICABLE` 和理由。对象域、假设、至少一个核心主张、至少一个失败/证伪公式以及应用映射不得标记为不适用。

### 5.5 确定性验证

RQ2M 通过前必须满足：

- 所有使用的符号均在 `notation_table` 定义；
- 公式依赖不存在未声明环；
- 每个 S1/S4 核心语义字段至少映射到一个公式或明确的非目标；
- 每个核心公式至少引用一个源语义字段；
- 每个核心贡献都有最近邻差异记录；
- 每个核心主张都有失败/证伪公式；
- formula bundle 的 hash 可重算；
- 未出现 `PROVED`、`VERIFIED`、`NOVEL` 等越权状态。

允许状态：

- `EARLY_FORMALIZATION_CANDIDATE`
- `SCHEMA_INVALID`
- `SEMANTIC_GAP`
- `FORMULA_COVERAGE_INCOMPLETE`
- `READY_FOR_USER_REVIEW`
- `SUPERSEDED`

## 6. RQ2E — 工程概念形式化

### 6.1 目标与边界

RQ2E 不是把工程构想伪装成纯数学理论，而是用数学关系、可判定约束和机器可读 Schema 固定工程意图，使后续工程蓝图可以机械生成和验收。它不等于详细架构，不授权写代码、采购、部署或生产变更。

### 6.2 核心形式化

至少包含：

```text
system_boundary = (Actors, ExternalSystems, TrustZones)

F: X × C → Y

s_{t+1} = T(s_t, u_t, e_t)

R_i(z) ∈ {true, false}

Q_j(z) comparator_j threshold_j

G_arch = (V_components, E_interfaces, type)

Trace ⊆ Requirement × DesignElement × VerificationObligation

Risk_k = likelihood_k × impact_k
```

其中：

- `X`、`Y`、`C` 分别是输入、输出和运行约束；
- `R_i` 是功能、接口、安全或合规要求谓词；
- `Q_j` 是性能、可靠性、可维护性、可用性或领域特定质量指标；
- 每个阈值必须带单位、测量方法和允许误差；
- `Trace` 中每个 requirement 至少映射一个设计义务和一个验证义务；
- 未知阈值用 `UNRESOLVED_THRESHOLD`，不得由模型虚构数字。

### 6.3 输出：`EngineeringConceptBundle`

- `concept_id`
- `version`
- `research_spec_id`
- `input_spec_hash`
- `route_selection_id`
- `feasibility_assessment_id`
- `neighbor_evidence_set_id`
- `notation_table[]`
- `system_boundary_model`
- `actors_and_use_cases[]`
- `input_output_contracts[]`
- `state_transition_formulas[]`
- `requirement_predicates[]`
- `quality_metric_formulas[]`
- `architecture_graph_candidate`
- `traceability_relation`
- `verification_obligations[]`
- `neighbor_difference_matrix[]`
- `assumptions_and_constraints[]`
- `unresolved_thresholds[]`
- `plain_language_explanation`
- `artifact_hash`
- `status`

### 6.4 确定性验证

- 所有对象和单位均已定义；
- 每个 expected function 有 I/O 或状态转移表达；
- 每个 success metric 有公式、比较符、阈值或显式 unresolved 标记；
- 每个安全、隐私、伦理或监管约束都有验证义务；
- 设计元素不得超出 S1/S4，模型建议必须标为 `MODEL_PROPOSAL`；
- 至少一个失败状态和恢复义务被表达；
- Bundle hash 可重算；
- 未出现 `IMPLEMENTED`、`VALIDATED`、`PRODUCTION_READY` 或 `NOVEL`。

允许状态：

- `ENGINEERING_CONCEPT_CANDIDATE`
- `SCHEMA_INVALID`
- `SEMANTIC_GAP`
- `REQUIREMENT_COVERAGE_INCOMPLETE`
- `UNRESOLVED_THRESHOLD`
- `READY_FOR_USER_REVIEW`
- `SUPERSEDED`

## 7. RQ3M / RQ3E — 用户审查

### 7.1 理论路线 RQ3M

平台必须向用户同时展示：

1. formula bundle 的版本与 hash；
2. 符号表和核心公式；
3. 自然语言设计字段到公式的映射；
4. 与最近邻的主要差异；
5. 不确定性与未覆盖项；
6. 不超过 12 条的简明自然语言解释。

Gate 为 `EARLY_FORMALIZATION_REVIEW`。合法决定：

- `APPROVE`：记录 `UserFormalizationApproval`，进入 RQ4M；
- `REQUEST_REVISION`：生成新版本，返回 RQ2M；
- `RESEARCH_MORE`：返回 RQ1；
- `REVISE_DESIGN`：创建新 S1/S4 Revision；
- `REJECT`：状态 `BLOCKED_FORMALIZATION_USER`；
- `PAUSE`。

### 7.2 工程路线 RQ3E

平台必须展示系统边界、行为/I/O 公式、要求谓词、质量阈值、验证义务、近邻差异、未解决阈值和不超过 12 条的简明解释。

Gate 为 `EARLY_ENGINEERING_CONCEPT_REVIEW`。合法决定：

- `APPROVE`：记录 `UserEngineeringConceptApproval`，进入 RQ4E；
- `REQUEST_REVISION`：返回 RQ2E；
- `RESEARCH_MORE`：返回 RQ1；
- `RETURN_TO_ROUTE_DECISION`：重新打开 `ENGINEERING_ROUTE_DECISION`；
- `REJECT`；
- `PAUSE`。

两种用户确认都绑定 `artifact_id + version + artifact_hash + input_spec_hash + route`。任何绑定字段变化都会使旧确认失效。

## 8. RQ4M / RQ4E — 路线化新颖性审验

### 8.1 共同前置条件

- RQ3M 或 RQ3E 对当前 hash 为 `APPROVE`；
- RQ1 `coverage_status = COMPLETE`；
- 至少两个隔离 Novelty Reviewer 完成评分；
- 正式科研 Profile 下两个 Reviewer 必须属于不同模型家族；
- 每个评分项都引用 RQ1 近邻或明确引用“未检索区域”；
- 不允许 Reviewer 读取对方评分后再生成自己的初始评分。

任一条件不满足时结果为 `INCONCLUSIVE`，不得生成自动通行分数。

每个 Reviewer 对每个项目给出 `r_i ∈ {0,1,2,3,4,5}`。固定锚点：

- 0：与最近邻实质相同，或无证据支持差异；
- 1：仅表述、界面或参数级差异；
- 2：增量变化或常规组合；
- 3：有清楚、可引用的中等新贡献；
- 4：强且非显然的贡献；
- 5：在已检索范围内具有异常强、可能改变研究或实践方式的贡献。

每项采用保守聚合：

```text
q_i = min(r_i_primary, r_i_auditor)
```

### 8.2 RQ4M：理论 50 + 应用 50

理论新颖度最高 50 分：

| ID | 项目 | 权重 | 最高分 |
|---|---|---:|---:|
| T1 | 与最近理论在对象、定义或问题设定上的实质区别 | 3 | 15 |
| T2 | 机制、定理、推导或解释是否非显然 | 3 | 15 |
| T3 | 是否扩展知识、解释范围或产生新的可证伪预测 | 2 | 10 |
| T4 | 最近邻比较和差异主张的来源覆盖是否充分 | 2 | 10 |

应用新颖度最高 50 分：

| ID | 项目 | 权重 | 最高分 |
|---|---|---:|---:|
| A1 | 相对成熟工程项目的预期功能差异 | 3 | 15 |
| A2 | 目标用户、应用场景或任务设定的新颖性 | 2 | 10 |
| A3 | 系统机制、工作流或人机协作方式的新颖性 | 2 | 10 |
| A4 | 跨域迁移或组件组合是否具有非显然性 | 2 | 10 |
| A5 | 是否提出可测量、具有实践价值的新能力或收益 | 1 | 5 |

```text
theory_score = 3q_T1 + 3q_T2 + 2q_T3 + 2q_T4

application_score = 3q_A1 + 2q_A2 + 2q_A3 + 2q_A4 + q_A5

novelty_total = theory_score + application_score
```

### 8.3 RQ4E：工程 60 + 应用 40

工程新颖度最高 60 分：

| ID | 项目 | 权重 | 最高分 |
|---|---|---:|---:|
| E1 | 功能边界或系统能力相对成熟工程近邻的实质区别 | 3 | 15 |
| E2 | 核心技术机制、架构或算法是否非显然 | 3 | 15 |
| E3 | 组件集成、接口、数据流或人机工作流的新颖性 | 2 | 10 |
| E4 | 是否提出可测量且非微小的质量属性改进 | 2 | 10 |
| E5 | 工程近邻、标准和差异主张的证据覆盖是否充分 | 2 | 10 |

应用新颖度最高 40 分：

| ID | 项目 | 权重 | 最高分 |
|---|---|---:|---:|
| EA1 | 用户、场景或任务设定的新增价值 | 2 | 10 |
| EA2 | 部署、使用或运维方式的实践新颖性 | 2 | 10 |
| EA3 | 可验证的效益、可采用性或运营优势 | 2 | 10 |
| EA4 | 跨域迁移、平台化或未来扩展潜力 | 2 | 10 |

```text
engineering_score = 3q_E1 + 3q_E2 + 2q_E3 + 2q_E4 + 2q_E5

engineering_application_score = 2q_EA1 + 2q_EA2 + 2q_EA3 + 2q_EA4

novelty_total = engineering_score + engineering_application_score
```

两套 `novelty_total` 范围均为 `[0,100]`，但 policy 不可互换。评分是研究资格信号，不是论文录用、专利有效性、商业成功预测或法律意见。

### 8.4 固定路由

```text
if review_valid and novelty_total >= 70 and route == THEORY:
    status = NOVELTY_QUALIFIED
    open_gate = false
    next = S5
elif review_valid and novelty_total >= 70 and route == ENGINEERING:
    status = ENGINEERING_NOVELTY_QUALIFIED
    open_gate = false
    next = ENG0
elif review_valid and novelty_total < 70:
    status = NOVELTY_RESEARCH_REQUIRED
    open_gate = LOW_NOVELTY_RESEARCH_DECISION
else:
    status = INCONCLUSIVE
    open_gate = LOW_NOVELTY_RESEARCH_DECISION
```

分数达到 70 分及以上时必须按已由用户确认的路线自动进入后续流程，不得额外要求普通确认。分数低于 70 或结果不确定时，必须交还用户，不得自动重做研究。

`LOW_NOVELTY_RESEARCH_DECISION` 的合法决定：

- `RERUN_RESEARCH`：保留旧版本，返回 RQ1；
- `REVISE_DESIGN`：生成新的 S1/S4 Revision，旧可行性分析、形式化和评分失效；
- `CONTINUE_WITH_RECORDED_OVERRIDE`：按当前已确认路线继续，但保持 `novelty_status = USER_OVERRIDDEN_BELOW_THRESHOLD`；
- `RETURN_TO_ROUTE_DECISION`：仅工程路线可用；返回 `ENGINEERING_ROUTE_DECISION`；
- `ARCHIVE`；
- `PAUSE`。

### 8.5 输出：`NoveltyReview`

- `review_id`
- `route`
- `policy_version`
- `subject_artifact_id`
- `subject_artifact_hash`
- `neighbor_evidence_set_id`
- `reviewer_session_ids[]`
- `reviewer_scorecards[]`
- `conservative_item_scores`
- `theory_score`（理论路线）
- `application_score`（理论路线）
- `engineering_score`（工程路线）
- `engineering_application_score`（工程路线）
- `novelty_total`
- `coverage_status`
- `status`
- `nearest_overlap_refs[]`
- `strongest_difference_refs[]`
- `limitations[]`
- `artifact_hash`

## 9. 状态、事件与回退不变量

必须写入以下事件：

- `NaturalLanguageDesignReady`
- `FormalizationCapabilitySelected`
- `NeighborSearchCompleted`
- `FormalizationFeasibilityAssessed`
- `EngineeringRouteDecisionOpened`
- `EngineeringRouteSelected`
- `EarlyFormalizationCreated`
- `EngineeringConceptCreated`
- `EarlyFormalizationReviewOpened`
- `EarlyEngineeringConceptReviewOpened`
- `EarlyFormalizationApproved`
- `EarlyEngineeringConceptApproved`
- `NoveltyReviewStarted`
- `NoveltyReviewScored`
- `NoveltyThresholdPassed`
- `EngineeringNoveltyThresholdPassed`
- `NoveltyResearchDecisionOpened`
- `NoveltyResearchRequested`
- `NoveltyOverrideAccepted`

不变量：

1. 所有搜索、可行性分析、形式化、评分和用户决定均不可变；修订创建新版本。
2. S1/S4 hash 变化使下游 RQ Artifact 进入 `NEEDS_REQUALIFICATION`。
3. 邻近工作被新增、撤回或元数据纠正时，Novelty Review 进入 `NEEDS_REGRESSION`。
4. 外部模型输出只属于 Proposal；用户批准只确认语义，不证明理论成立或工程可行。
5. 用户选择工程路线会创建派生 `EngineeringRouteSelection`，不会覆盖原 NaturalLanguageSpec。
6. `NOVELTY_QUALIFIED` 或 `ENGINEERING_NOVELTY_QUALIFIED` 只表示在记录的检索范围和评分政策下达到 70 分。
7. 理论路线不得消费工程评分，工程路线不得消费理论评分。
8. 不得输出“绝对原创”“已获学术认可”“可授予专利”“生产就绪”。

## 10. 失败与阻断

| 条件 | 状态 | 可恢复动作 |
|---|---|---|
| 无合格高能力模型且无外部导入 | `BLOCKED_CAPABILITY` | 用户配置模型或选择外部导入 |
| 学术或工程来源不可用 | `BLOCKED_RETRIEVAL` | 重试、切换 Provider、用户提供来源 |
| 检索覆盖不足 | `INCONCLUSIVE` | 用户决定是否 RQ1 继续研究 |
| 可行性谓词缺少证据 | `FEASIBILITY_INCONCLUSIVE` | 补研究、修订设计或暂停 |
| 纯理论不适配但工程适配 | `ENGINEERING_ROUTE_DECISION_REQUIRED` | 用户修订或选择工程路线 |
| 理论与工程均不适配 | `FORMALIZATION_FEASIBILITY_USER_DECISION_REQUIRED` | 用户修订、补研究、暂停或归档 |
| 公式 Schema 或符号不闭合 | `FORMULA_COVERAGE_INCOMPLETE` | 返回 RQ2M |
| 工程要求或阈值覆盖不足 | `REQUIREMENT_COVERAGE_INCOMPLETE` | 返回 RQ2E 或 S1/S4 |
| Artifact 与 S1/S4 语义不一致 | `SEMANTIC_GAP` | 返回对应 RQ2 或 S1/S4 |
| 用户不批准 | `BLOCKED_FORMALIZATION_USER` | 修订、补检索、暂停或拒绝 |
| Novelty Reviewer 不独立 | `INDEPENDENCE_DEGRADED` | 建立异构隔离 Reviewer；否则仅人工判定 |
| 分数低于 70 | `NOVELTY_RESEARCH_REQUIRED` | 打开用户研究决定 Gate |

## 11. 非目标

- RQ2M 不替代 S7 的正式构造。
- RQ2E 不替代 03B 的需求基线、详细架构、实现蓝图或验证执行。
- RQ4 不替代同行评审、系统综述、查新机构或专利检索意见。
- 新颖性分数不参与 Lean/Z3/Python 的真值判定。
- 用户批准形式化不自动确认后续 ClaimContract 或工程架构。
- 工程项目成熟度只用于选择可信近邻，不直接增加新颖性分。
- 选择工程路线不授权自动实现、付费采购、外部发布、生产部署或论文投稿。

## 12. 最小验收场景

1. S4 通过后直接运行 S5 或 ENG0，返回 `EARLY_QUALIFICATION_REQUIRED`。
2. 普通整理模型未达到能力门，RQ2F 被阻断。
3. 外部包的 `input_spec_hash` 不匹配，导入失败。
4. 只搜索学术文献、不搜索成熟工程项目，RQ1 不得 COMPLETE。
5. 理论谓词全部 PASS，工程谓词任意时按 RQ2M 继续。
6. 理论谓词 FAIL、工程谓词 PASS 时只打开 `ENGINEERING_ROUTE_DECISION`，不得自动转工程。
7. 用户选 `REVISE_FOR_THEORY` 后创建新 Revision，旧 RQ Artifact 保留并失效。
8. 用户选 `TRY_ENGINEERING_PROJECT` 后进入 RQ2E，而不是 RQ2M 或 ENG0。
9. 理论和工程均 FAIL 时不展示“尝试工程项目”的自动继续动作。
10. 核心理论主张只用自然语言时 RQ2M 失败。
11. 工程 success metric 没有阈值也没有 unresolved 标记时 RQ2E 失败。
12. 用户未批准当前 Artifact hash，RQ4 不得启动。
13. 两个 Reviewer 每项评分不同，最终使用逐项较小值。
14. 理论有效总分 70 自动进入 S5。
15. 工程有效总分 70 自动进入 ENG0。
16. 任一路线有效总分 69 打开 `LOW_NOVELTY_RESEARCH_DECISION`。
17. coverage PARTIAL 时即使模型给高分也只能 INCONCLUSIVE。
18. 用户选择重新研究后产生新检索/评分版本，旧记录不删除。
19. 用户低分继续时保留 `USER_OVERRIDDEN_BELOW_THRESHOLD` 和 route。
20. 新发现最近邻后，原 Novelty Review 自动进入 `NEEDS_REGRESSION`。


---

<!-- SOURCE: 03B_ENGINEERING_TRANSLATION_AND_PUBLICATION_WORKFLOW.md -->

# 03B — 工程转化、机械蓝图、验证与论文交付工作流

本文定义由 `03A` 的工程路线进入后，如何把已经通过用户审查和工程新颖性审验的 `EngineeringConceptBundle` 转化为可机械执行的工程蓝图、项目图示、应用/扩展路线及一篇证据约束的行业规范论文。

本工作流借鉴系统工程的“利益相关者期望 → 技术要求 → 逻辑分解 → 设计解 → 验证/确认”、规格驱动开发的“Spec → Plan → Tasks → Implement”、软件质量模型、安全开发框架、可复现科研工件和目标期刊模板适配思想。外部经验只提供方法，不构成对具体设计、结果或期刊录用的背书。

## 1. 入口、出口与授权边界

### 1.1 唯一入口

进入 ENG0 必须全部满足：

- 当前 S1/S4 hash 未变化；
- `EngineeringRouteSelection.decision = TRY_ENGINEERING_PROJECT`；
- RQ3E 已批准当前 `EngineeringConceptBundle` hash；
- RQ4E `status = ENGINEERING_NOVELTY_QUALIFIED` 且总分 `>= 70`，或存在绑定当前 route/artifact 的显式低分用户 override；
- 没有未解决的隐私、伦理、监管、付费或安全 Gate。

任何条件不满足都返回结构化 Blocker；不得凭自然语言备注绕过。

### 1.2 最终出口

ENG10 只允许产生：

- `ENGINEERING_DELIVERY_CANDIDATE`：蓝图完整，但真实实现或论文证据尚未达到相应等级；
- `ENGINEERING_DELIVERY_READY`：蓝图、图示、路线和稿件均通过确定性检查及独立审计；
- `BLOCKED_ENGINEERING_DELIVERY`：存在未解决的 Critical 缺口；
- `SUPERSEDED`：输入语义或架构基线已被新版本取代。

`ENGINEERING_DELIVERY_READY` 不表示工程已生产部署、论文已投稿、已录用、已获专利或商业上可行。

### 1.3 不自动授权的动作

本工作流的通过不授权：

- 新增或修改生产代码；
- 购买服务、设备、数据或算力；
- 连接真实用户、敏感数据或生产系统；
- 生产发布、数据迁移、破坏性操作；
- 对外公开仓库、上传工件或投稿论文；
- 代表用户接受许可证、作者责任或利益冲突声明。

这些动作必须进入其各自的 WorkUnit、ActionBroker 和 Human Gate。

## 2. 总流程

```text
ENGINEERING_NOVELTY_QUALIFIED / bound user override
                         ↓
ENG0 工程任务章程与基线导入
                         ↓
ENG1 利益相关者、场景与 ConOps
                         ↓
ENG2 可追踪技术要求与验收基线
                         ↓
ENG3 参考方案、技术路线与权衡研究
                         ↓
ENG4 架构、接口、数据、状态与安全设计
                         ↓
        ENGINEERING_ARCHITECTURE_REVIEW
                         ↓ APPROVE
ENG5 可机械执行实施蓝图与项目图示
                         ↓
ENG6 原型/实现选择与验证—确认闭环
        ├─ BLUEPRINT_ONLY → 只验证蓝图，不虚构结果
        └─ BUILD_AND_EVALUATE
                ↓ PROTOTYPE_EXECUTION_AUTHORIZATION
           独立代码 WorkUnit / 实验 / V&V
                         ↓
ENG7 预期应用与未来扩展路线
                         ↓
ENG8 期刊中立母稿、独立审计与用户交付
                         ↓ FORMAL_MANUSCRIPT_DECISION
        ├─ KEEP_MASTER_ONLY → ENG10
        └─ WRITE_FORMAL_MANUSCRIPT
                         ↓ PUBLICATION_PROFILE_SELECTION
ENG9 内置期刊/arXiv 适配稿、合规矩阵与可复现工件
                         ↓
ENG10 独立交付审计、打包与用户验收
                         ↓
           ENGINEERING_DELIVERY_READY
```

阶段不得合并写入一个不透明 Artifact。每个阶段必须保存输入 hash、输出 hash、来源、决定、错误和回退目标。

## 3. ENG0 — 工程任务章程与基线导入

### 3.1 输入

- 冻结的 S1 `NaturalLanguageSpec`；
- 冻结的 S4 `ResearchScopeSpec`；
- `FormalizationFeasibilityAssessment`；
- `EngineeringRouteSelection`；
- 已批准的 `EngineeringConceptBundle`；
- RQ1 `NeighborEvidenceSet`；
- RQ4E `NoveltyReview`。

### 3.2 输出：`EngineeringMissionCharter`

- `charter_id`, `version`, `project_id`；
- `source_artifact_hashes[]`；
- `problem_statement`；
- `stakeholders[]`；
- `intended_users[]`；
- `operational_context`；
- `system_of_interest_boundary`；
- `objectives[]` 与 `non_goals[]`；
- `success_metrics[]`；
- `constraints[]`；
- `assumptions[]`；
- `regulatory_security_ethics_flags[]`；
- `delivery_mode = BLUEPRINT_ONLY | BUILD_AND_EVALUATE_UNDECIDED`；
- `artifact_hash`, `status`。

### 3.3 不变量

- 章程只导入已经冻结或经用户批准的内容；
- 模型新增内容必须进入 `proposed_additions[]`，不能混入基线；
- 出现对象域、用户、核心功能、数据分类或工程目标变化时，必须打开 `ENGINEERING_SCOPE_CHANGE`，不得继续 ENG1。

## 4. ENG1 — 利益相关者、场景与 ConOps

### 4.1 输出

`OperationalConceptBundle` 至少包含：

- stakeholder map 与责任边界；
- 主要、替代、失败、恢复和退役场景；
- system context；
- 外部系统、数据源、信任边界和人工参与点；
- 运行环境、规模、频率、延迟、可用性与约束假设；
- 可用性、无障碍、伦理、隐私、安全和监管需求；
- 每个场景的 precondition、trigger、main flow、alternate flow、postcondition；
- 未解决问题和决策所有者。

### 4.2 通过标准

- 每个 expected function 至少有一个场景；
- 每个 intended user 至少映射一个角色或明确标为非操作者；
- 每个外部依赖有 owner、failure mode 和 fallback；
- 所有敏感数据和外部动作已标注 trust zone；
- 用户意图与 ConOps 的双向追踪覆盖率为 100%。

## 5. ENG2 — 可追踪技术要求与验收基线

### 5.1 Requirement Schema

每个 `EngineeringRequirement` 必须包含：

- 稳定 `requirement_id`；
- `type = FUNCTIONAL | INTERFACE | DATA | QUALITY | SAFETY | SECURITY | PRIVACY | COMPLIANCE | OPERATIONS | CONSTRAINT`；
- 单一、明确、可测试的 statement；
- `source_refs[]`；
- priority 与 rationale；
- precondition、input、expected behavior/output；
- measurement method、unit、threshold、tolerance；
- `verification_method = TEST | ANALYSIS | INSPECTION | DEMONSTRATION`；
- acceptance criterion；
- owner；
- dependency/conflict refs；
- status 与 artifact hash。

禁止使用“尽量”“适当”“快速”“友好”“高性能”等无阈值形容词。无法确定阈值时必须标记 `UNRESOLVED_THRESHOLD` 并阻断 Architecture Baseline。

### 5.2 质量与安全框架

- 质量属性从适用的 ISO/IEC 25010 产品质量特性选择，并转成项目阈值；不得声称“符合 ISO”而没有逐项证据；
- 安全开发活动按 NIST SSDF 的 Prepare、Protect、Produce、Respond 四类映射到责任、工件和验证；
- 涉及 AI 的工程还必须记录数据来源、模型/Provider 边界、已知失效、人工监督、漂移和滥用场景；
- 涉及科研结论时，实验有效性、工程验证、语义对齐和新颖性保持独立状态。

### 5.3 输出

- `RequirementsBaseline`；
- `RequirementsTraceabilityMatrix`；
- `AcceptanceCriteriaCatalog`；
- `QualityAttributeScenarioSet`；
- `SecurityPrivacyComplianceObligationSet`；
- `UnresolvedDecisionRegister`。

### 5.4 通过标准

```text
source_coverage = 100%
requirement_with_verification_method = 100%
critical_requirement_with_numeric_or_boolean_acceptance = 100%
unresolved_critical_conflicts = 0
unresolved_critical_thresholds = 0
```

## 6. ENG3 — 参考方案、技术路线与权衡研究

### 6.1 研究范围

复用 RQ1，但必须针对已冻结 Requirements Baseline 追加工程深检索：

- 同方向 GitHub/GitLab 官方仓库及其 release、architecture、test、issue 证据；
- 官方产品/项目文档与参考实现；
- 标准组织、政府或行业指南；
- 论文、技术报告、基准和可复现实验；
- 包注册表、依赖健康度、许可证与供应链信息。

星标、下载量、宣传文案或单一 benchmark 不得单独构成成熟度或路线优越性证据。

### 6.2 候选路线与权衡

至少生成一个基线方案和一个有意义的替代方案；客观上只有一条可行路线时，保存排除记录而不得虚构候选。

每个方案必须记录：

- 对 Requirements 的覆盖；
- 关键组件、依赖、接口和数据路径；
- 性能、可靠性、安全、可维护性和可扩展性预测；
- 实现复杂度、人员、时间、成本和基础设施；
- 许可证、供应链、锁定和弃用风险；
- 原型/风险刺探建议；
- 未知项和证据置信度。

固定权衡公式：

```text
weighted_score(option) = Σ_j w_j × normalized_score(option, criterion_j)

Σ_j w_j = 1
```

权重由 Requirements Baseline 派生并向用户展示；模型不得为了使推荐方案胜出而事后改权重。Critical requirement 未覆盖的方案直接淘汰，不参与加权补偿。

### 6.3 输出

- `EngineeringReferenceSet`；
- `OptionTradeStudy`；
- `TechnologySelectionRecord`；
- `RejectedOptionLog`；
- 初始 ADR 集。

## 7. ENG4 — 架构、接口、数据、状态与安全设计

### 7.1 必须产出的设计视图

- 系统上下文；
- 容器/子系统；
- 组件及责任；
- 运行时序列和关键流程；
- 数据模型、数据生命周期和数据流；
- 状态机、错误恢复、幂等与并发边界；
- 接口与版本策略；
- 部署拓扑、环境和运维边界；
- 信任边界、威胁模型和安全控制；
- 可观测性、审计、备份、恢复和退役；
- 硬件项目适用时的物理、连接、电源、热、机械与制造视图。

### 7.2 设计工件

- `ArchitectureBaseline`；
- C4 或等价层级的 architecture model；
- `InterfaceContractSet`（OpenAPI/AsyncAPI/Proto/JSON Schema 或领域等价物）；
- `DataContractSet`；
- `StateAndFailureModel`；
- `ThreatModel`；
- `DeploymentAndOperationsDesign`；
- `ArchitectureDecisionRecord[]`；
- 更新后的 Traceability Matrix。

### 7.3 图示规则

每张图必须同时保存：

- 可版本控制的源文件（优先 Mermaid、PlantUML/C4-PlantUML、Graphviz 或领域标准文本格式）；
- 渲染后的 SVG；必要时附 PNG/PDF；
- `diagram_id`、标题、版本、输入 hash、图例、节点/边语义；
- 图中元素到 requirement、component、interface 或 state 的稳定 ID 映射；
- 自动渲染回执和断链检查结果。

图片不得成为唯一事实来源；机器可读设计对象是权威，图片是投影视图。

### 7.4 `ENGINEERING_ARCHITECTURE_REVIEW`

必须向用户展示推荐路线、重大权衡、不可逆选择、公开接口、数据边界、安全边界、成本区间和未解决风险。合法决定：

- `APPROVE_BASELINE`；
- `REQUEST_REVISION`；
- `RETURN_TO_TRADE_STUDY`；
- `REVISE_REQUIREMENTS`；
- `PAUSE`；
- `ARCHIVE`。

确认绑定 Requirements、Trade Study 和 Architecture 三者 hash。任一变化使旧确认失效。

## 8. ENG5 — 可机械执行实施蓝图与项目图示

### 8.1 `MechanicalEngineeringBlueprint`

蓝图必须足以让大多数合格开发者和主流代码执行模型在不补产品决策的前提下逐项实施。至少包含：

- 规范项目树及每个目录责任；
- 文件级新增/修改/禁止清单；
- 模块、组件、服务、接口、Schema 和关键符号；
- 依赖与版本锁定策略；
- 配置、密钥引用、环境和 feature flag 策略；
- 数据创建、迁移、回滚、备份和兼容策略；
- 每个运行流程的状态、事件、错误码和恢复动作；
- 性能、安全、隐私、可观测性和运维要求；
- 构建、测试、部署、验证与回滚命令模板；
- 从 requirement 到 design、task、test 的双向追踪；
- 风险登记表、停止条件和升级条件；
- 应生成但尚未生成的源码、配置、IaC、测试和文档清单。

### 8.2 `EngineeringWorkUnitContract`

每个机械任务必须包含：

1. 稳定 Task ID 和唯一目标；
2. 权威输入文档及精确章节；
3. 前置 Task、Gate 和环境；
4. allowed files/modules/symbols；
5. forbidden files/actions；
6. 输入、输出、接口、Schema、状态和事件；
7. 必须保持的不变量；
8. 逐步修改动作；
9. 错误、边界、兼容和回滚；
10. focused tests；
11. full checks；
12. 每项验收标准；
13. 失败时停止/升级条件；
14. 交付 diff、命令、回执和未验证事项格式。

任务粒度必须满足：一次只实现一个可独立核验的行为；不得用“适当修改”“完善相关代码”“视情况测试”等措辞。

### 8.3 Blueprint Completeness Gate

```text
requirements_traced_to_design = 100%
requirements_traced_to_task = 100%
critical_requirements_traced_to_test = 100%
public_interfaces_with_schema = 100%
tasks_with_stop_condition = 100%
unresolved_product_decisions = 0
unresolved_architecture_decisions = 0
broken_diagram_references = 0
```

未满足时状态为 `BLUEPRINT_GAP`，禁止 ENG6 的 Build 路线。

## 9. ENG6 — 原型/实现选择与验证—确认闭环

### 9.1 两种合法交付模式

#### `BLUEPRINT_ONLY`

只完成静态可执行性审计、Schema 检查、图示渲染、追踪覆盖和必要的设计模拟。论文只能是：

- `DESIGN_ARTICLE_DRAFT`；或
- `PROTOCOL_MANUSCRIPT_DRAFT`。

不得出现假造的实现、性能、用户实验或比较结果。

#### `BUILD_AND_EVALUATE`

必须先通过 `PROTOTYPE_EXECUTION_AUTHORIZATION`，再按独立代码/实验 WorkUnit 实施。该 Gate 展示范围、环境、预算、数据、安全风险、外部动作和停止条件。

代码任务必须遵守 `19_MECHANICAL_EXECUTION_CONTRACT.md`；本文件不能替代代码任务固定的规划—实施交接或用户授权。

### 9.2 Verification 与 Validation

- Verification 回答“是否按要求构建”，每条 requirement 使用预定的 test/analysis/inspection/demonstration；
- Validation 回答“是否在预期环境解决用户问题”，必须基于 ConOps、代表性用户/场景和预注册成功指标；
- 两者状态独立，不得用单元测试 PASS 代替应用有效性，不得用用户满意代替安全/接口要求通过。

### 9.3 输出

- `VerificationPlan` 与 `ValidationPlan`；
- `ExperimentProtocol` 与预注册指标（适用时）；
- real tool receipts、版本、环境和随机种子；
- `VerificationReport`；
- `ValidationReport`；
- discrepancy、corrective action 与 residual risk；
- `ClaimEvidenceMatrix`。

任何论文结果主张必须在 `ClaimEvidenceMatrix` 中绑定真实回执；缺证据时只能标 `PLANNED` 或从稿件删除。

## 10. ENG7 — 预期应用与未来扩展路线

### 10.1 `ApplicationDirectionPortfolio`

每个应用方向包含：

- 用户/利益相关者；
- 问题和使用场景；
- 所需能力与当前覆盖；
- 数据、接口、部署和合规条件；
- 可测量价值指标；
- 采用障碍和失败模式；
- 证据等级；
- `NOW | NEXT | LATER | RESEARCH_ONLY` 时间层级。

### 10.2 `ExtensionRoadmap`

每个未来扩展包含：

- 扩展目标与非目标；
- 触发条件；
- 被影响的 requirements/components/interfaces；
- 兼容与迁移策略；
- 依赖的新研究、数据、基础设施或监管条件；
- 风险、成本级别和可逆性；
- 独立 ADR/Task 建议；
- 不得提前耦合到当前版本的理由。

“可扩展”必须落到稳定 extension point、接口或迁移路径；宣传性愿景不能算路线项。

## 11. ENG8 — 工程论文母稿与母稿后用户决策

### 11.1 证据决定论文类型

| 证据状态 | 允许 `paper_type` | 禁止主张 |
|---|---|---|
| 仅蓝图 | `DESIGN_ARTICLE`, `PROTOCOL_ARTICLE` | 已实现、优于基线、用户有效、生产可用 |
| 原型 + 工程验证 | `SYSTEMS_ARTICLE`, `METHODS_ARTICLE` | 未执行的长期/真实场景效果 |
| 原型 + Verification + Validation | `FULL_ENGINEERING_RESEARCH_ARTICLE` | 超出样本、场景和统计功效的推广 |
| 成熟开源软件 + 文档/测试/许可证 | `RESEARCH_SOFTWARE_ARTICLE` | 未满足目标期刊软件门槛的合规声明 |

### 11.2 `EngineeringMasterManuscript`

期刊中立母稿至少包含：

1. title、abstract、keywords；
2. problem、stakeholders、statement of need；
3. related work 与最近学术/工程近邻；
4. requirements、ConOps 和设计目标；
5. method、architecture、interfaces 与实现；
6. verification/validation/experiment methods；
7. results（只有真实证据时）；
8. 与基线的定量/定性比较；
9. threats to validity、limitations、failure modes；
10. 应用方向与扩展方向；
11. security、privacy、ethics 和 sustainability；
12. data/code/materials availability；
13. reproducibility instructions；
14. conclusion；
15. references；
16. author contributions、AI-use disclosure、funding、conflicts 和 acknowledgements；未由用户提供的字段必须是结构化 `NEEDS_AUTHOR_INPUT`，不得生成虚构占位文本。

每个实质主张必须分配 `claim_id` 并绑定：source requirement、design element、evidence receipt、figure/table 和 citation。无证据主张不得使用完成时或确定性语言。

### 11.3 母稿审计与交付

未参与母稿生成的 `ENGINEERING_MANUSCRIPT_AUDITOR` 必须检查 claim-evidence、V&V Scope、近邻引用、结果/时态、限制、AI 使用、作者输入状态和真实编译。通过后状态为 `ENGINEERING_MASTER_MANUSCRIPT_READY`，平台先向用户交付母稿、evidence tier、主要主张、未解决义务、审计结果和工程四刊/arXiv 的 scope-fit 候选。

### 11.4 `FORMAL_MANUSCRIPT_DECISION`

母稿交付后打开 Gate，绑定 `master_manuscript_id + version + master_hash + engineering_delivery_hash`。合法决定：

- `KEEP_MASTER_ONLY`：母稿即正式交付物，不生成期刊/arXiv 适配稿；
- `WRITE_FORMAL_MANUSCRIPT`：进入 ENG9 的 `PUBLICATION_PROFILE_SELECTION`；
- `REVISE_MASTER`：生成新母稿 revision 并重新审计；
- `PAUSE`。

模型不得在用户无响应时默认选择正式论文。

## 12. ENG9 — Profile 选择、正式适配与可复现工件

### 12.1 内置 Profile

工程路线内置：

- `ENG_IEEE_TSE`；
- `ENG_ACM_TOSEM`；
- `ENG_EMSE`；
- `ENG_JSS`；
- `ENG_ARXIV_PREPRINT`（`venue_kind = PREPRINT_REPOSITORY`）；
- 扩展 `JOSS_RESEARCH_SOFTWARE`、`NATURE_PORTFOLIO_METHODS_OR_SOFTWARE` 与 `CUSTOM_VENUE`。

完整字段、官方指南 freshness、模板 checksum、arXiv 边界和两路线 Registry 见 `03C_THEORY_PUBLICATION_AND_DUAL_TRACK_VENUE_PROFILES.md`。

### 12.2 `PUBLICATION_PROFILE_SELECTION`

只有 `FORMAL_MANUSCRIPT_DECISION = WRITE_FORMAL_MANUSCRIPT` 才可打开。系统根据领域、论文证据类型和篇幅给出 scope-fit 推荐；用户选择期刊、arXiv 或自定义 Profile。模型不得代表用户确认作者顺序、投稿声明、伦理审批或版权/许可证。选择只授权生成适配稿，不授权投稿。

### 12.3 期刊/arXiv 适配

`VenueAdaptedManuscript` 必须由 Master + PublicationProfile 机械派生，保存转换记录而不得覆盖母稿。`VenueComplianceMatrix` 对每条要求给出：

- `PASS`：有具体稿件位置或工件证据；
- `FAIL`：不满足且阻断 submission candidate；
- `NEEDS_AUTHOR_INPUT`：作者、伦理、利益冲突、版权等必须由用户提供；
- `NOT_APPLICABLE`：有明确理由；
- `STALE_GUIDANCE`：官方指南超过配置的 freshness window，必须重新检索。

arXiv 必须显示为预印本平台，适配包使用 `ARXIV_PACKAGE_READY`，不得产生 `PEER_REVIEWED`、`JOURNAL_ACCEPTED` 或同义状态。

### 12.4 可复现工件

`ReproducibilityArtifact` 至少包含：

- README：目的、系统要求、安装、运行、测试、复现实验和预期输出；
- immutable version/tag/commit 和 checksum；
- 环境/依赖锁定；
- 数据清单、来源、许可证、隐私与获取方式；
- 一键或分步 reproduction commands；
- claim-to-artifact mapping；
- 时间/算力/存储要求；
- 已知差异、随机性和容差；
- LICENSE、CITATION、贡献者与 AI 使用说明；
- 失败排查与支持边界。

软件论文 Profile 只有在软件实际存在、可安装、文档和自动化测试通过且许可证兼容时，才能到 `SUBMISSION_CANDIDATE`。

## 13. ENG10 — 独立交付审计、打包与用户验收

### 13.1 独立审计

至少一个未参与 ENG3–ENG9 初稿生成的 `ENGINEERING_DELIVERY_AUDITOR` 检查：

- S1/S4 → concept → requirement → design → task → test → paper 的双向追踪；
- 蓝图是否仍有需要实施者自行做出的产品/架构选择；
- 图、接口、状态、错误、单位和 Schema 是否一致；
- V&V 与论文主张是否有真实回执；
- 最近邻、引用、许可证和合规 Profile 是否可追溯；
- 论文是否含夸大、虚构结果或过时指南；
- 敏感信息、密钥、隐私数据和不安全执行说明是否泄露。

### 13.2 最终交付目录

```text
engineering_delivery/
├── 00_manifest.yaml
├── 01_executive_summary.md
├── 02_mission_and_conops/
├── 03_requirements/
│   ├── requirements.yaml
│   ├── acceptance_criteria.yaml
│   └── traceability_matrix.csv
├── 04_reference_and_trade_study/
├── 05_architecture/
│   ├── architecture_baseline.yaml
│   ├── adr/
│   ├── interfaces/
│   ├── data/
│   ├── states/
│   ├── security/
│   └── deployment/
├── 06_diagrams/
│   ├── source/
│   └── rendered/
├── 07_implementation_blueprint/
│   ├── project_tree.md
│   ├── module_and_file_plan.yaml
│   ├── work_units/
│   ├── build_test_deploy.md
│   └── rollback_and_migration.md
├── 08_verification_and_validation/
├── 09_applications_and_extensions/
├── 10_risk_register/
├── 11_publication/
│   ├── master_manuscript.*
│   ├── master_audit.yaml
│   ├── formal_manuscript_decision.yaml
│   ├── venue_profile.yaml              # 用户选择正式适配时存在
│   ├── venue_adapted_manuscript.*      # 用户选择正式适配时存在
│   └── compliance_matrix.yaml          # 用户选择正式适配时存在
├── 12_reproducibility_artifact/
├── 13_audit/
└── 14_checksums.sha256
```

`00_manifest.yaml` 必须记录每个文件的 role、source artifact、version、byte size、checksum、generation method 和验证状态。

### 13.3 最终通过条件

全部满足才可 `ENGINEERING_DELIVERY_READY`：

- ENG0–ENG9 当前版本均非 BLOCKED/SUPERSEDED；
- Blueprint Completeness Gate 全通过；
- 所有图可从源文件重渲染且无断链；
- 关键要求的 Verification 计划完整；已有实现时，声称 PASS 的项有真实回执；
- 应用与扩展路线含条件、指标、风险和证据等级；
- MasterManuscript 完整；
- MasterManuscript 已独立审计并先交付用户；
- `KEEP_MASTER_ONLY` 时 manifest 明确 `formal_manuscript_requested = false`；
- `WRITE_FORMAL_MANUSCRIPT` 时，选择的 Profile 当前有效且 Compliance Matrix 无 FAIL/STALE_GUIDANCE；
- 不存在虚构结果、伪造引用或未披露 AI 辅助；
- 独立审计无 Critical/Major finding；
- 用户通过 `ENGINEERING_DELIVERY_ACCEPTANCE` 接受当前 manifest hash。

用户验收只确认交付范围与语义，不替代工程测试、同行评审、伦理审查或期刊编辑决定。

## 14. 回归、修订与撤回

以下变化必须产生新 revision，并按影响范围回退：

| 变化 | 最早回退点 |
|---|---|
| S1/S4 核心语义变化 | RQ1 / RQ2F |
| 新近邻改变新颖性判断 | RQ4E |
| stakeholder / ConOps 变化 | ENG1 |
| requirement 或阈值变化 | ENG2 |
| 技术路线或重大依赖变化 | ENG3 |
| 公开接口、数据或安全边界变化 | ENG4 |
| 机械任务发现蓝图缺口 | ENG4 或 ENG5 |
| 实现证伪架构假设 | ENG3 或 ENG4 |
| 新实验结果改变论文主张 | ENG6 / ENG8 |
| 母稿主张变化 | ENG8 |
| 期刊/arXiv 指南更新 | ENG9 |
| 证据撤回或许可证不兼容 | ENG6 / ENG8 / ENG9 / ENG10 |

历史 Artifact、评分、决定、稿件和回执不可覆盖；只能标 `SUPERSEDED`、`RETRACTED` 或 `NEEDS_REGRESSION`。

## 15. 失败与停止条件

| 条件 | 状态 | 停止/恢复 |
|---|---|---|
| 工程路线未由用户选择 | `ENGINEERING_ROUTE_DECISION_REQUIRED` | 返回 03A Gate |
| 新颖性未达门且无 override | `ENGINEERING_NOVELTY_REQUIRED` | 返回 RQ4E |
| Critical requirement 无阈值 | `REQUIREMENTS_BASELINE_BLOCKED` | 返回 ENG2 |
| 无可行技术路线 | `TRADE_STUDY_BLOCKED` | 修订要求或用户暂停 |
| 重大架构选择未确认 | `ENGINEERING_ARCHITECTURE_REVIEW_REQUIRED` | 打开 Gate |
| 蓝图仍要求实施者补产品决策 | `BLUEPRINT_GAP` | 返回 ENG2–ENG5 |
| 用户未授权实现 | `BLUEPRINT_ONLY` | 不运行代码/实验 |
| 实验/验证环境不可用 | `EVIDENCE_BLOCKED` | 稿件降级或记录 Blocker |
| 结果主张无真实回执 | `MANUSCRIPT_CLAIM_UNSUPPORTED` | 删除/降级主张或补执行 |
| 目标期刊指南过期 | `STALE_GUIDANCE` | 重新读取官方指南 |
| 软件论文不满足代码/测试/许可证要求 | `SOFTWARE_ARTICLE_INELIGIBLE` | 换 paper type 或补工件 |
| 独立审计有 Critical/Major | `BLOCKED_ENGINEERING_DELIVERY` | 一轮定向返工后重审 |

## 16. 最小验收场景

1. 未选择工程路线时直接 ENG0，必须失败。
2. RQ4E 总分 70 自动进入 ENG0；69 返回用户 Gate。
3. ENG0 尝试静默新增核心功能，触发 `ENGINEERING_SCOPE_CHANGE`。
4. requirement 写“响应要快”但无指标，ENG2 不得通过。
5. Critical requirement 未被候选方案覆盖时，该方案即使总分最高也必须淘汰。
6. 架构图节点没有稳定 component ID，ENG4 不得通过。
7. 用户未批准 Architecture hash，ENG5 不得冻结。
8. WorkUnit 使用“适当修改相关文件”，Blueprint Completeness Gate 失败。
9. BLUEPRINT_ONLY 模式的母稿写入虚构 benchmark，ENG8/ENG10 阻断。
10. BUILD_AND_EVALUATE 未通过授权 Gate，不得执行代码或实验。
11. 单元测试通过但未做预期场景 Validation，不得标应用有效。
12. 新实现结果与原假设冲突，必须回退 ENG3/ENG4，而不是修改论文掩盖。
13. 母稿未先交付用户就打开 Profile Selection，工作流阻断。
14. 用户选择 `KEEP_MASTER_ONLY`，工程交付仍可 READY 且不生成适配稿。
15. 用户选择 `WRITE_FORMAL_MANUSCRIPT` 后才允许选择工程四刊、工程 arXiv 或扩展 Profile。
16. 目标期刊官方指南超出 freshness window，Compliance Matrix 标 `STALE_GUIDANCE`。
17. arXiv 被标成期刊或同行评审，测试失败。
18. JOSS Profile 下软件无开源许可证或自动化测试，不得到 SUBMISSION_CANDIDATE。
19. 图示源和 SVG hash 对不上，最终包不得 READY。
20. 论文每个结果 claim 都能追踪到真实 receipt 和图表。
21. 应用方向只有宣传文本、没有指标/风险/证据等级，ENG7 失败。
22. 独立审计发现实施者仍需选择数据库或公开接口，返回 BLUEPRINT_GAP。
23. 用户接受新 manifest 后修改任一权威文件，旧验收自动失效。
24. 完整包重建后，manifest、checksums、图示、追踪和稿件合规检查全部可复算。


---

<!-- SOURCE: 03C_THEORY_PUBLICATION_AND_DUAL_TRACK_VENUE_PROFILES.md -->

# 03C — 纯数学理论论文交付与双路线内置发布 Profile

本文定义纯数学理论路线的论文交付工作流，并统一规定理论路线、工程路线各自的四种内置主要期刊 Profile 与共享的 arXiv 预印本 Profile。

`arXiv` 是开放预印本平台，不是同行评审期刊。领域模型必须用 `venue_kind = PREPRINT_REPOSITORY` 区分；UI、论文和导出包不得把 arXiv 称为期刊、同行评审或录用状态。

## 1. 适用范围与总原则

### 1.1 理论路线最终交付物

理论路线在完成研究交付时必须追加：

- 一篇期刊中立的 `TheoryMasterManuscript`；
- theorem/claim → statement hash → proof/evidence → citation 的追踪矩阵；
- 符号、定义、引理、定理和证明依赖图；
- 形式证明、计算、代码、数据或反例附件（适用时）；
- 局限性、未解决义务和开放问题；
- AI 使用、作者责任、资助、利益冲突和可用性字段的结构化状态；
- 一份 Master Manuscript 独立审计报告。

母稿是固定交付物。期刊/预印本正式适配稿不是默认自动生成；母稿交付后必须询问用户是否需要按内置 Profile 编写正式论文。

### 1.2 两条路线共享的发布顺序

理论与工程路线都必须采用：

```text
evidence / design delivery ready
              ↓
build route-neutral MasterManuscript
              ↓
independent MasterManuscript audit
              ↓
deliver MasterManuscript to user
              ↓
FORMAL_MANUSCRIPT_DECISION
     ├─ KEEP_MASTER_ONLY → 保存母稿并完成交付
     ├─ WRITE_FORMAL_MANUSCRIPT → 选择内置/自定义 Profile
     ├─ REVISE_MASTER → 新母稿 revision → 重新审计
     └─ PAUSE
              ↓ WRITE
PUBLICATION_PROFILE_SELECTION
              ↓
refresh official author guide
              ↓
generate VenueAdaptedManuscript + ComplianceMatrix
              ↓
independent venue audit
              ↓
FORMAL_MANUSCRIPT_READY / BLOCKED
```

禁止在母稿生成前要求用户选择期刊后再反向塑造研究结论。期刊 Profile 只调整篇幅、结构、元数据、格式、声明、工件和投稿材料，不得改变 theorem statement、工程结果、证据范围或失败记录。

### 1.3 不自动授权的动作

生成母稿或正式适配稿不授权：

- 代表用户确定作者、作者顺序或通讯作者；
- 代表用户接受版权、许可、独家投稿或利益冲突声明；
- 代表用户确认伦理审批、机构批准或资助信息；
- 创建 arXiv/期刊账户、上传文件、正式投稿或发送编辑邮件；
- 把模型列为作者；
- 把预印本写成已同行评审成果。

上述字段状态必须是 `USER_CONFIRMED | NEEDS_AUTHOR_INPUT | NOT_APPLICABLE`；外部动作必须通过独立 Human Gate 和 ActionBroker。

## 2. 双路线内置 Profile Registry

### 2.1 纯数学理论方向四种主要期刊

| Profile ID | 期刊 | venue_kind | 主要适用范围 |
|---|---|---|---|
| `MATH_ANNALS_OF_MATHEMATICS` | Annals of Mathematics | `PEER_REVIEWED_JOURNAL` | 具有广泛数学重要性的重大原创理论结果 |
| `MATH_JAMS` | Journal of the American Mathematical Society | `PEER_REVIEWED_JOURNAL` | 数学各领域高质量、广泛兴趣的研究文章 |
| `MATH_INVENTIONES` | Inventiones mathematicae | `PEER_REVIEWED_JOURNAL` | 具有显著新颖性和深度的纯数学研究 |
| `MATH_ACTA_MATHEMATICA` | Acta Mathematica | `PEER_REVIEWED_JOURNAL` | 重要、完整且具有长期价值的数学研究 |

这些 Profile 是格式与合规适配器，不是“达到该期刊学术门槛”的自动判定器。平台可以给 `SCOPE_FIT_CANDIDATE | SCOPE_FIT_UNCERTAIN | SCOPE_MISMATCH`，不得输出录用概率或“符合顶刊水平”的保证。

### 2.2 工程/软件系统方向四种主要期刊

Synaisthesis 的工程分支主要交付可实施的软件、科研工具和系统工程蓝图，因此默认内置以下四种覆盖软件工程理论、方法、实证和系统实现的期刊：

| Profile ID | 期刊 | venue_kind | 主要适用范围 |
|---|---|---|---|
| `ENG_IEEE_TSE` | IEEE Transactions on Software Engineering | `PEER_REVIEWED_JOURNAL` | 软件工程方法、理论、工具与有证据的系统研究 |
| `ENG_ACM_TOSEM` | ACM Transactions on Software Engineering and Methodology | `PEER_REVIEWED_JOURNAL` | 重要、可复现的软件工程方法与系统成果 |
| `ENG_EMSE` | Empirical Software Engineering | `PEER_REVIEWED_JOURNAL` | 实证研究、研究设计、数据与可复现评价 |
| `ENG_JSS` | Journal of Systems and Software | `PEER_REVIEWED_JOURNAL` | 软件系统、架构、要求、V&V、维护及系统证据 |

工程项目不属于软件/计算系统时，系统必须给 `SCOPE_MISMATCH`，并允许选择 `CUSTOM_VENUE`；不得因为内置 Profile 存在而强迫硬件、生物、化学或其他工程项目套用软件工程期刊。

`JOSS_RESEARCH_SOFTWARE` 和 `NATURE_PORTFOLIO_METHODS_OR_SOFTWARE` 保留为可选扩展 Profile，但不计入本节固定的工程四刊。JOSS 只有在真实研究软件、可浏览源码、许可证、文档和测试均满足其门槛时可用。

### 2.3 两条路线共享的 arXiv Profile

| Profile ID | 显示名称 | venue_kind | 类别范围 |
|---|---|---|---|
| `MATH_ARXIV_PREPRINT` | arXiv Mathematics Preprint | `PREPRINT_REPOSITORY` | `math.*`，按实际主题选择主分类/交叉分类 |
| `ENG_ARXIV_PREPRINT` | arXiv Engineering/Computing Preprint | `PREPRINT_REPOSITORY` | `cs.*`、`eess.*` 或实际适用分类 |

arXiv Profile 必须验证：

- 内容是 topical、refereeable 的科学贡献；
- submitter/author 注册、endorsement、license 和 moderation 状态需要用户处理；
- 优先交付可编译 TeX/LaTeX、AMS-LaTeX 或 PDFLaTeX 源；
- 所有源文件、图、`.bib`/`.bbl`、宏和 ancillary files 完整；
- 文件名只使用 arXiv 允许字符，大小写引用完全一致；
- 在隔离环境使用目标 TeX 版本执行真实编译并保存日志；
- title、abstract、authors、category、comments、license 等 metadata 均有结构化检查；
- 上传前由用户检查 PDF、元数据、许可证和投稿类别；
- 状态只允许 `ARXIV_PACKAGE_READY`，不能写 `PEER_REVIEWED`、`ACCEPTED` 或 `PUBLISHED_IN_JOURNAL`。

## 3. PublicationProfile 的机械合同

每个内置 Profile 必须是版本化、可刷新、可审计的数据包，至少包含：

- `profile_id`, `profile_version`, `route`, `venue_kind`；
- `venue_name`, `publisher_or_operator`；
- `scope_summary` 与 `scope_fit_rules[]`；
- `official_author_guide_urls[]`；
- `official_policy_urls[]`；
- `accessed_at`, `last_modified_if_available`；
- `freshness_days`，默认 30 天；
- `template_files[]`、来源 URL、byte size、SHA-256 和许可证；
- `article_types[]`；
- `submission_format` 与可接受源文件；
- title/abstract/keywords/MSC/section/length/figure/reference 要求；
- anonymity/review model；
- preprint/concurrent-submission/overlap policy；
- author/ORCID/corresponding-author 要求；
- AI/LLM disclosure 规则；
- ethics/conflict/funding/copyright/license 要求；
- data/code/proof/artifact availability 规则；
- supplementary material 规则；
- machine checks、human-only checks 和 blocking checks；
- `profile_hash`。

Profile 的官方 author guide 超过 freshness window、官方页面不可访问或模板 hash 改变时，状态必须是 `STALE_GUIDANCE`，禁止生成 `FORMAL_MANUSCRIPT_READY`。允许生成带明确过时警告的 `VENUE_ADAPTATION_DRAFT`。

## 4. TP0 — 理论证据与语义基线冻结

### 4.1 入口

理论论文流程可以在以下任一状态启动：

- `CANDIDATE_STABLE`；
- `USER_ACCEPTED`；
- 用户明确要求形成研究札记、反例论文、未完成理论报告或开放问题稿件。

RQ4M 必须已通过或有绑定理论 route 的显式用户 override。工程 route 不得进入 TP0。

### 4.2 输出：`TheoryPublicationEvidenceBaseline`

- `baseline_id`, `version`, `project_id`；
- `research_spec_hash`；
- `formalization_hash`；
- `frozen_claim_contract_ids[]`；
- `claim_statement_hashes[]`；
- `theory_revision_ids[]`；
- `proof_artifact_ids[]`；
- `tool_receipt_ids[]`；
- `counterexample_ids[]`；
- `semantic_audit_ids[]`；
- `human_decision_ids[]`；
- `citation_evidence_set_id`；
- `unresolved_obligations[]`；
- `retracted_or_superseded_evidence[]`；
- `evidence_tier`；
- `artifact_hash`, `status`。

### 4.3 证据等级与允许论文类型

| evidence_tier | 允许类型 | 禁止主张 |
|---|---|---|
| `PROVED_AND_SEMANTICALLY_ACCEPTED` | `FULL_THEORY_ARTICLE` | 超出冻结 statement、对象域或假设的推广 |
| `FORMALLY_VERIFIED` | `FORMALIZED_THEORY_ARTICLE` | Lean/Z3 Scope 之外的绝对真值 |
| `COMPUTER_ASSISTED_PROOF` | `COMPUTER_ASSISTED_THEORY_ARTICLE` | 不披露代码、算法、误差与独立检查 |
| `COUNTEREXAMPLE_OR_NEGATIVE_RESULT` | `NEGATIVE_RESULT_ARTICLE` | 把有限反例推广为未证明的一般结论 |
| `PARTIAL_THEORY` | `RESEARCH_NOTE`, `CONJECTURE_OR_OPEN_PROBLEM_ARTICLE` | 把未完成命题写成 theorem/proved |
| `DESIGN_ONLY` | `THEORY_PROTOCOL_OR_PROGRAMME_DRAFT` | 已完成证明、实验或验证 |

Evidence tier 由确定性规则计算，不允许模型自由选择更高等级。

## 5. TP1 — TheoryMasterManuscript

### 5.1 母稿结构

母稿至少包含：

1. title、running title（适用时）；
2. self-contained abstract；
3. Mathematics Subject Classification、keywords；
4. introduction：问题、背景、意义和贡献边界；
5. related work 与最近邻差异；
6. notation and preliminaries；
7. definitions and assumptions；
8. main results；
9. proof architecture 与依赖顺序；
10. complete proofs，或对未完成部分的明确状态；
11. examples、counterexamples、boundary cases；
12. formal/computational verification methods 与 Scope；
13. limitations、threats to correctness、unresolved obligations；
14. implications、applications 和 open problems；
15. proof/code/data/materials availability；
16. acknowledgements、funding、conflicts、author contributions、AI-use disclosure 的结构化状态；
17. complete references。

### 5.2 `MathematicalManuscriptClaim`

每个定理性表述必须包含：

- `manuscript_claim_id`；
- `kind = DEFINITION | ASSUMPTION | LEMMA | PROPOSITION | THEOREM | COROLLARY | CONJECTURE | COUNTEREXAMPLE | APPLICATION_CLAIM`；
- `display_statement`；
- `normalized_statement_hash`；
- `source_claim_contract_id`；
- `object_domain`、`quantifiers`、`assumptions[]`、`conclusion`；
- `proof_status`；
- `proof_artifact_ids[]`；
- `tool_receipt_ids[]`；
- `semantic_status`；
- `citation_refs[]`；
- `limitations[]`；
- `manuscript_locations[]`。

`THEOREM | LEMMA | PROPOSITION | COROLLARY` 只有在对应 Evidence tier 允许且 proof status 非 `INCOMPLETE` 时才能出现。否则必须改成 `CONJECTURE`、`OPEN_PROBLEM` 或明确的 conditional statement，不能只在脚注中弱化。

### 5.3 Proof Dependency Graph

```text
G_proof = (V, E)

V = Definitions ∪ Assumptions ∪ Lemmas ∪ Theorems ∪ Corollaries

E = {(u, v) | proof(v) directly depends on u}
```

图必须无未声明循环；每个主定理的全部上游定义、假设、引理和外部定理可追踪。引用外部结果时必须记录精确版本、定理编号/位置和适用条件。

### 5.4 母稿源文件

至少交付：

- `master.tex`；
- `references.bib`；
- `macros.tex`；
- `sections/*.tex`；
- `figures/source/*` 与渲染图；
- `proof_dependency_graph.*`；
- `claim_evidence_matrix.yaml`；
- `compile_environment.yaml`；
- 编译命令与真实 log；
- PDF；
- checksums。

## 6. TP2 — 母稿审计与用户决策

### 6.1 独立母稿审计

未参与初稿生成的 `THEORY_MANUSCRIPT_AUDITOR` 必须检查：

- 题目、摘要、引言、定理与结论是否忠于冻结 ResearchSpec；
- object domain、quantifier、assumption、conclusion 与 statement hash 一致；
- 定理、引理和引用的 proof/evidence 状态没有越权；
- Proof Dependency Graph 闭合且外部定理适用条件完整；
- 反例、失败尝试、限制和 Scope 没有被隐藏；
- citation 可解析且没有捏造；
- TeX/PDF 在锁定环境真实编译；
- 作者责任字段没有被模型虚构。

Critical/Major finding 必须完成一次定向返工后重审；仍失败则状态 `BLOCKED_THEORY_MASTER_MANUSCRIPT`。

### 6.2 母稿交付

审计通过后状态为 `THEORY_MASTER_MANUSCRIPT_READY`。平台必须先向用户交付：

- Master PDF 与 TeX source；
- evidence tier；
- 核心 theorem/claim 列表；
- 未解决义务；
- 独立审计结论；
- 四种理论期刊和 arXiv Profile 的 scope-fit 候选结果；
- “正式适配不会改变数学结论”的说明。

### 6.3 `FORMAL_MANUSCRIPT_DECISION`

Gate 必须绑定 `master_manuscript_id + version + master_hash + evidence_baseline_hash`。合法决定：

- `KEEP_MASTER_ONLY`：母稿即论文交付物，不生成正式适配稿；
- `WRITE_FORMAL_MANUSCRIPT`：进入 `PUBLICATION_PROFILE_SELECTION`；
- `REVISE_MASTER`：生成新 revision 并返回 TP1；
- `PAUSE`。

禁止把无响应解释为同意编写正式论文。

## 7. TP3 — Profile 选择与正式适配

### 7.1 `PUBLICATION_PROFILE_SELECTION`

理论路线合法 Profile：

- `MATH_ANNALS_OF_MATHEMATICS`；
- `MATH_JAMS`；
- `MATH_INVENTIONES`；
- `MATH_ACTA_MATHEMATICA`；
- `MATH_ARXIV_PREPRINT`；
- `CUSTOM_VENUE`。

选择界面必须展示：venue kind、scope-fit、官方指南更新时间、模板、篇幅/结构关键差异、预印本/重复投稿政策、开放/版权要求和需要用户补充的字段。

用户选择期刊/平台只授权生成适配稿，不授权投稿。

### 7.2 适配动作

允许：

- 套用官方或允许的 LaTeX class/template；
- 调整 title page、abstract length、MSC、keywords、heading、references、figure placement 和 supplementary files；
- 生成 cover-letter draft、suggested editor/referee 字段或 submission checklist；
- 依据 Profile 生成 AI/LLM、code/data/proof availability 等声明草案；
- 为 arXiv 生成分类和 metadata 候选、source archive 和编译检查。

禁止：

- 删除或弱化关键假设以满足篇幅；
- 将 conjecture 升格为 theorem；
- 修改 statement hash；
- 隐藏负结果、限制或计算依赖；
- 虚构作者、机构、ORCID、编辑、审稿人、许可或声明；
- 为迎合期刊范围捏造应用。

## 8. TP4 — VenueComplianceMatrix 与正式论文审计

每条 Profile 要求输出：

- `requirement_id`；
- `source_url`、`accessed_at`；
- `check_type = MACHINE | HUMAN`；
- `status = PASS | FAIL | NEEDS_AUTHOR_INPUT | NOT_APPLICABLE | STALE_GUIDANCE`；
- `manuscript_location`；
- `evidence_artifact_id`；
- `blocking`；
- `rationale`。

正式论文只有在以下条件全部满足时为 `FORMAL_MANUSCRIPT_READY` 或 `ARXIV_PACKAGE_READY`：

- 母稿 hash 与适配输入一致；
- 指南未过期；
- 所有 machine blocking checks 为 PASS；
- human-only blocking 项已由用户确认，或保持 `NEEDS_AUTHOR_INPUT` 并将整体状态降为 `FORMAL_MANUSCRIPT_DRAFT`；
- statement/evidence/citation 追踪 100%；
- TeX 与 PDF 真实编译；
- 独立 Auditor 无 Critical/Major；
- 没有 unsupported theorem/result claim。

## 9. TP5 — 理论论文交付包

```text
theory_publication_delivery/
├── 00_manifest.yaml
├── 01_evidence_baseline/
├── 02_master_manuscript/
│   ├── master.tex
│   ├── master.pdf
│   ├── sections/
│   ├── macros.tex
│   ├── references.bib
│   ├── figures/
│   ├── proof_dependency_graph.*
│   └── claim_evidence_matrix.yaml
├── 03_master_audit/
├── 04_formal_manuscript_decision.yaml
├── 05_publication_profile/             # 用户选择正式适配时存在
├── 06_venue_adapted_manuscript/        # 用户选择正式适配时存在
├── 07_compliance_matrix/                # 用户选择正式适配时存在
├── 08_proof_and_reproducibility_artifact/
├── 09_author_input_register/
└── 10_checksums.sha256
```

`KEEP_MASTER_ONLY` 时 05–07 不存在是合法状态；manifest 必须明确 `formal_manuscript_requested = false`，不能把缺失误报为不完整。

## 10. 与工程论文流程的统一约束

工程路线的 03B 必须遵守本文件第 1–3 节：

- ENG8 先生成并审计 `EngineeringMasterManuscript`；
- 母稿交付后打开同名 `FORMAL_MANUSCRIPT_DECISION`；
- 用户选择 `WRITE_FORMAL_MANUSCRIPT` 后才允许选择工程四刊、工程 arXiv 或扩展 Profile；
- `KEEP_MASTER_ONLY` 是完整合法交付；
- 期刊/预印本适配不得改变 Requirement、Architecture、V&V 或 Evidence；
- arXiv 始终是 `PREPRINT_REPOSITORY`。

## 11. 回归与撤回

| 变化 | 回退点 |
|---|---|
| ResearchSpec、对象域、量词或核心假设变化 | RQ / TP0 |
| FrozenClaim statement hash 变化 | TP0 |
| Proof/Evidence 撤回或工具版本使结果失效 | TP0 / TP1 |
| 新最近邻改变引用或新颖性边界 | RQ1 / TP1 |
| 母稿内容变化 | TP2 独立审计 |
| 用户改 Profile | TP3，新适配稿 revision |
| 官方指南或模板更新 | TP3 / TP4 |
| 作者、机构、许可或声明变化 | TP4 |
| arXiv 新版本 | 新 package revision，保留旧版本 |

所有母稿、适配稿、Profile snapshot、审计和用户决定不可覆盖；只能新建 revision 并标记旧版本 `SUPERSEDED`、`RETRACTED` 或 `NEEDS_REGRESSION`。

## 12. 最小验收场景

1. 理论路线完成交付但没有论文母稿，最终 Bundle 不得 READY。
2. 工程 route 尝试进入 TP0，返回 `THEORY_ROUTE_REQUIRED`。
3. 未完成证明被写成 theorem，母稿审计失败。
4. Lean PASS 的 statement hash 与稿件定理不同，阻断母稿。
5. Z3 UNSAT 被写成无 Scope 的一般定理，阻断母稿。
6. 负结果论文隐藏反例范围或失败记录，阻断母稿。
7. 母稿未先交付用户就直接选择期刊，阻断正式适配。
8. 用户选择 KEEP_MASTER_ONLY，论文交付完整且不生成期刊稿。
9. 用户选择 WRITE_FORMAL_MANUSCRIPT 后才打开 Profile Selection。
10. 用户无响应不能被当作 WRITE。
11. Profile 选择 Annals，系统按官方指南快照检查摘要、完整参考文献、LaTeX/图源和 AI 责任字段。
12. Profile 选择 JAMS，系统检查 MSC、投稿独占性、author package 和用户责任字段。
13. Inventiones 或 Acta 官方指南超过 freshness window，状态为 STALE_GUIDANCE。
14. arXiv 被 UI 或导出称为期刊，测试失败。
15. arXiv TeX 在锁定环境不能编译，不得 ARXIV_PACKAGE_READY。
16. arXiv 源缺图、`.bib/.bbl` 或自定义宏，不得 READY。
17. 用户选择工程四刊中的不适用 Profile 时显示 SCOPE_MISMATCH，并要求确认 custom venue，而不是静默套用。
18. 期刊适配改变 theorem statement hash，立即阻断并撤销旧合规状态。
19. `NEEDS_AUTHOR_INPUT` 未解决时可生成 Draft，但不得 Ready 或投稿。
20. manifest、TeX/PDF、Profile、矩阵、proof graph 和 checksums 可重算一致。


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
- 早期新颖性资格为理论 route 的 `NOVELTY_QUALIFIED`，或存在绑定理论 route 的可审计用户低分继续决定。`ENGINEERING_NOVELTY_QUALIFIED` 只允许进入 03B 的 ENG0，不得直接进入本 Council。

`CANDIDATE_STABLE` 是研究状态，不是最终交付完成状态。理论 route 的最终 ResearchBundle 必须继续执行 `03C` TP0–TP2，至少交付经独立审计的 `TheoryMasterManuscript`。用户选择 `KEEP_MASTER_ONLY` 即可完成论文交付；只有用户选择 `WRITE_FORMAL_MANUSCRIPT` 才执行 TP3–TP5 的期刊/arXiv 适配。

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
- QUALIFICATION_PENDING
- NOVELTY_QUALIFIED
- NOVELTY_RESEARCH_REQUIRED
- USER_OVERRIDDEN_BELOW_THRESHOLD
- SEARCHED
- POSSIBLY_ORIGINAL
- PARTIAL_OVERLAP
- STRONG_OVERLAP
- KNOWN_RESULT
- INCONCLUSIVE

早期资格使用 `03A` 的 100 分制：理论最高 50、应用最高 50，两个隔离 Reviewer 逐项取较小值；有效总分达到 70 自动继续，低于 70 或 INCONCLUSIVE 打开用户研究决定 Gate。后期 Council/文献回归可以更新或撤回该状态，但不得把分数表述为“绝对原创”。

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

### `formalization_capability_decisions`
- id
- project_id
- research_spec_id
- route
- model_profile_id
- capability_evidence_artifact_id
- input_spec_hash
- budget_snapshot_id
- privacy_policy_snapshot_id
- status
- blocker

### `prior_art_searches`
- id
- project_id
- research_spec_id
- input_spec_hash
- query_records_artifact_id
- academic_neighbor_count
- engineering_neighbor_count
- patent_neighbor_count
- coverage_status
- coverage_blockers_artifact_id
- artifact_hash
- created_at

### `prior_art_neighbors`
- id
- search_id
- neighbor_type
- stable_identifier
- canonical_url
- metadata_artifact_id
- metadata_verified
- maturity_evidence_artifact_id
- theory_proximity
- application_proximity
- similarity_evidence_artifact_id
- rank

### `early_formalizations`
- id
- project_id
- research_spec_id
- prior_art_search_id
- capability_decision_id
- version
- input_spec_hash
- formula_bundle_artifact_id
- formula_bundle_hash
- status
- supersedes_id
- created_at

### `formalization_feasibility_assessments`
- id
- project_id
- research_spec_id
- prior_art_search_id
- version
- input_spec_hash
- assessor_session_ids_artifact_id
- theory_predicates_artifact_id
- engineering_predicates_artifact_id
- route_classification
- recommended_route
- missing_information_artifact_id
- artifact_hash
- status
- supersedes_id

### `engineering_route_selections`
- id
- project_id
- feasibility_assessment_id
- decision
- user_actor_id
- decision_event_id
- bound_assessment_hash
- input_spec_hash
- created_at

### `engineering_concepts`
- id
- project_id
- research_spec_id
- feasibility_assessment_id
- route_selection_id
- prior_art_search_id
- version
- input_spec_hash
- concept_bundle_artifact_id
- concept_bundle_hash
- status
- supersedes_id
- created_at

### `novelty_reviews`
- id
- project_id
- route
- subject_artifact_type
- subject_artifact_id
- prior_art_search_id
- policy_version
- coverage_status
- theory_score
- application_score
- engineering_score
- engineering_application_score
- novelty_total
- status
- scorecard_artifact_id
- artifact_hash
- created_at

### `engineering_workflow_runs`
- id
- project_id
- engineering_concept_id
- stage_id
- input_artifact_ids
- output_artifact_id
- output_hash
- status
- gate_id
- started_at
- ended_at

### `engineering_requirements`
- id
- project_id
- baseline_version
- requirement_key
- requirement_type
- statement
- source_refs_artifact_id
- priority
- measurement_method
- unit
- threshold
- tolerance
- verification_method
- acceptance_criterion
- owner
- status
- content_hash

### `engineering_trace_edges`
- id
- project_id
- from_type
- from_id
- relation
- to_type
- to_id
- baseline_version
- evidence_artifact_id

### `publication_profiles`
- id
- profile_id
- profile_version
- route
- venue_kind
- venue_name
- publisher_or_operator
- article_type
- official_author_guide_urls_artifact_id
- official_policy_urls_artifact_id
- guide_accessed_at
- guide_last_modified_at
- freshness_days
- template_identifier
- template_checksum
- scope_fit_rules_artifact_id
- rules_artifact_id
- freshness_status
- content_hash

### `engineering_manuscripts`
- id
- project_id
- manuscript_type
- evidence_tier
- master_artifact_id
- master_version
- master_hash
- claim_evidence_matrix_artifact_id
- status
- content_hash
- supersedes_id

### `theory_publication_evidence_baselines`
- id
- project_id
- version
- research_spec_hash
- formalization_hash
- claim_contract_ids_artifact_id
- claim_statement_hashes_artifact_id
- proof_evidence_refs_artifact_id
- citation_evidence_set_id
- unresolved_obligations_artifact_id
- evidence_tier
- content_hash
- status
- supersedes_id

### `theory_manuscripts`
- id
- project_id
- manuscript_type
- evidence_baseline_id
- evidence_tier
- master_artifact_id
- master_hash
- proof_dependency_graph_artifact_id
- claim_evidence_matrix_artifact_id
- adapted_artifact_id
- publication_profile_id
- compliance_matrix_artifact_id
- status
- content_hash
- supersedes_id

### `manuscript_audits`
- id
- project_id
- route
- master_manuscript_type
- master_manuscript_id
- master_version
- master_hash
- producer_session_id
- auditor_session_id
- audit_profile_version
- findings_artifact_id
- compile_receipt_artifact_id
- status
- content_hash
- supersedes_id

### `formal_manuscript_decisions`
- id
- project_id
- route
- master_manuscript_type
- master_manuscript_id
- master_version
- master_hash
- bound_delivery_or_evidence_hash
- decision
- user_actor_id
- decision_event_id
- created_at
- content_hash
- supersedes_id

### `publication_profile_selections`
- id
- project_id
- route
- formal_manuscript_decision_id
- master_manuscript_type
- master_manuscript_id
- master_hash
- publication_profile_id
- publication_profile_version
- scope_fit_status
- selected_by_actor_id
- selection_event_id
- created_at
- content_hash

### `venue_manuscript_adaptations`
- id
- project_id
- route
- master_manuscript_type
- master_manuscript_id
- master_hash
- publication_profile_selection_id
- publication_profile_id
- publication_profile_version
- adapted_artifact_id
- compliance_matrix_artifact_id
- adaptation_trace_artifact_id
- compile_receipt_artifact_id
- status
- content_hash
- supersedes_id

### `novelty_score_items`
- id
- novelty_review_id
- reviewer_session_id
- criterion_id
- rating
- weight
- evidence_refs_artifact_id
- rationale_artifact_id

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
→ NATURAL_LANGUAGE_DESIGN_READY
→ EARLY_RESEARCH_QUALIFYING
→ FORMALIZATION_FEASIBILITY_REVIEWING
   ├─ THEORY_OR_HYBRID_ROUTE
   │  → FORMALIZATION_CANDIDATE → FORMALIZATION_USER_REVIEW
   │  → NOVELTY_REVIEWING
   │  → NOVELTY_QUALIFIED / BLOCKED_NOVELTY_USER
   │  → MATURE_IDEA_READY → THEORY_BUILDING → CLAIM_COMPILED
   │  → CLAIM_FROZEN → COUNCIL_RUNNING → CANDIDATE_STABLE
   │  → THEORY_MASTER_MANUSCRIPT_BUILDING
   │  → THEORY_MASTER_MANUSCRIPT_AUDITING
   │  → THEORY_MASTER_MANUSCRIPT_READY
   │  → FORMAL_MANUSCRIPT_DECISION_REQUIRED
   │  → MASTER_ONLY_DELIVERED / MASTER_REVISION_REQUIRED / FORMAL_MANUSCRIPT_PAUSED
   │  → PUBLICATION_PROFILE_REQUIRED → FORMAL_MANUSCRIPT_READY / ARXIV_PACKAGE_READY
   │
   ├─ ENGINEERING_ROUTE_USER_DECISION
   │  → ENGINEERING_CONCEPT_CANDIDATE → ENGINEERING_CONCEPT_USER_REVIEW
   │  → ENGINEERING_NOVELTY_REVIEWING
   │  → ENGINEERING_NOVELTY_QUALIFIED / BLOCKED_NOVELTY_USER
   │  → ENGINEERING_DESIGNING → ENGINEERING_ARCHITECTURE_REVIEW
   │  → ENGINEERING_BLUEPRINTING → ENGINEERING_VALIDATING
   │  → ENGINEERING_PUBLISHING → ENGINEERING_DELIVERY_READY
   │
   └─ FORMALIZATION_FEASIBILITY_USER_DECISION

任一路线 → BLOCKED_HUMAN / BLOCKED_TOOL
任一路线 → USER_ACCEPTED / REVOKED
```

允许回退：

- THEORY_BUILDING → INCUBATING；
- ENGINEERING_DESIGNING → EARLY_RESEARCH_QUALIFYING；
- ENGINEERING_BLUEPRINTING → ENGINEERING_DESIGNING；
- ENGINEERING_VALIDATING → ENGINEERING_DESIGNING；
- ENGINEERING_PUBLISHING → ENGINEERING_VALIDATING；
- CLAIM_COMPILED → THEORY_BUILDING；
- COUNCIL_RUNNING → CLAIM_COMPILED；
- CANDIDATE_STABLE → COUNCIL_RUNNING；
- USER_ACCEPTED → REVOKED。

回退只写事件，不删除历史。

## 3. ProvenanceType

- USER_INPUT
- USER_DECISION
- EXTERNAL_MODEL_IMPORT
- EXTERNAL_SOURCE
- ASSISTANT_PROPOSAL
- DERIVED
- TOOL_EXECUTION
- CODEX_EXECUTION
- HUMAN_VERIFIED

## 4. EvidenceType

- LITERATURE_METADATA
- LITERATURE_INTERPRETATION
- PRIOR_ART_METADATA_VERIFIED
- ENGINEERING_MATURITY_EVIDENCE
- FORMALIZATION_FEASIBILITY_ASSESSMENT
- EARLY_FORMALIZATION_ALIGNMENT
- ENGINEERING_CONCEPT_ALIGNMENT
- NOVELTY_SCORECARD
- REQUIREMENTS_BASELINE
- ARCHITECTURE_BASELINE
- ENGINEERING_TRACEABILITY
- VERIFICATION_REPORT
- VALIDATION_REPORT
- MANUSCRIPT_CLAIM_EVIDENCE
- VENUE_COMPLIANCE_MATRIX
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
  prior_art/academic/
  prior_art/engineering/
  formalization/early/
  novelty/
  theory/
  publication/theory/master/
  publication/theory/adapted/
  publication/engineering/master/
  publication/engineering/adapted/
  publication/profiles/
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
- early_qualification_status
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
early_qualification_status = NOVELTY_QUALIFIED
formal_status = LEAN_PASS
semantic_status = AI_AUDITED
human_review_status = PENDING
novelty_status = POSSIBLY_ORIGINAL
```

这表示形式命题已通过，但原始语义尚未由用户最终确认。

`early_qualification_status` 的允许值：

- NOT_STARTED
- CAPABILITY_PENDING
- RETRIEVAL_RUNNING
- FEASIBILITY_REVIEWING
- ENGINEERING_ROUTE_USER_DECISION
- FORMALIZATION_FEASIBILITY_USER_DECISION
- FORMALIZATION_CANDIDATE
- FORMALIZATION_USER_REVIEW
- ENGINEERING_CONCEPT_CANDIDATE
- ENGINEERING_CONCEPT_USER_REVIEW
- NOVELTY_REVIEWING
- NOVELTY_QUALIFIED
- ENGINEERING_NOVELTY_QUALIFIED
- NOVELTY_RESEARCH_REQUIRED
- USER_OVERRIDDEN_BELOW_THRESHOLD
- INCONCLUSIVE
- NEEDS_REQUALIFICATION

任何 S1/S4 hash 变化都把已有 RQ 产物派生为 `NEEDS_REQUALIFICATION`；不得沿用旧用户确认或新颖性分数。

`engineering_delivery_status` 的允许值：

- NOT_STARTED
- MISSION_BASELINING
- CONOPS_DEFINING
- REQUIREMENTS_BASELINING
- TRADE_STUDY_RUNNING
- ARCHITECTURE_DESIGNING
- ARCHITECTURE_USER_REVIEW
- BLUEPRINT_BUILDING
- BLUEPRINT_GAP
- BLUEPRINT_ONLY
- BUILD_AUTHORIZATION_REQUIRED
- VERIFYING
- VALIDATING
- APPLICATION_ROADMAP_BUILDING
- MASTER_MANUSCRIPT_BUILDING
- ENGINEERING_MASTER_MANUSCRIPT_AUDITING
- ENGINEERING_MASTER_MANUSCRIPT_READY
- FORMAL_MANUSCRIPT_DECISION_REQUIRED
- MASTER_ONLY_DELIVERED
- MASTER_REVISION_REQUIRED
- FORMAL_MANUSCRIPT_PAUSED
- PUBLICATION_PROFILE_REQUIRED
- VENUE_MANUSCRIPT_BUILDING
- FORMAL_MANUSCRIPT_DRAFT
- FORMAL_MANUSCRIPT_READY
- ARXIV_PACKAGE_READY
- DELIVERY_AUDITING
- ENGINEERING_DELIVERY_CANDIDATE
- ENGINEERING_DELIVERY_READY
- BLOCKED_ENGINEERING_DELIVERY
- NEEDS_REGRESSION
- SUPERSEDED

`theory_publication_status` 的允许值：

- NOT_STARTED
- EVIDENCE_BASELINING
- THEORY_MASTER_MANUSCRIPT_BUILDING
- THEORY_MASTER_MANUSCRIPT_AUDITING
- THEORY_MASTER_MANUSCRIPT_READY
- FORMAL_MANUSCRIPT_DECISION_REQUIRED
- MASTER_ONLY_DELIVERED
- MASTER_REVISION_REQUIRED
- FORMAL_MANUSCRIPT_PAUSED
- PUBLICATION_PROFILE_REQUIRED
- VENUE_MANUSCRIPT_BUILDING
- FORMAL_MANUSCRIPT_DRAFT
- FORMAL_MANUSCRIPT_READY
- ARXIV_PACKAGE_READY
- BLOCKED_THEORY_MASTER_MANUSCRIPT
- BLOCKED_FORMAL_MANUSCRIPT
- NEEDS_AUTHOR_INPUT
- STALE_GUIDANCE
- NEEDS_REGRESSION
- SUPERSEDED

`venue_kind` 的允许值：

- `PEER_REVIEWED_JOURNAL`
- `PREPRINT_REPOSITORY`
- `CUSTOM_PUBLICATION_VENUE`

`formal_manuscript_decisions.decision` 的允许值：

- `KEEP_MASTER_ONLY`
- `WRITE_FORMAL_MANUSCRIPT`
- `REVISE_MASTER`
- `PAUSE`

该字段不得为自由文本，也没有默认值；缺少绑定当前 master hash 的真实用户决定时，状态保持 `FORMAL_MANUSCRIPT_DECISION_REQUIRED`。

`publication_profiles.route`、`formal_manuscript_decisions.route`、`publication_profile_selections.route` 与 `venue_manuscript_adaptations.route` 的允许值统一为：

- `THEORY`
- `ENGINEERING`

四者必须相等；跨 route 选择返回 `PUBLICATION_PROFILE_ROUTE_MISMATCH`，不得自动转换。

arXiv Profile 只能使用 `PREPRINT_REPOSITORY`。状态机禁止从 `ARXIV_PACKAGE_READY` 派生 `PEER_REVIEWED`、`JOURNAL_ACCEPTED` 或同义状态。

## 10. 依赖与回归

`dependency_edges` 表示：

- DEFINITION_USED_BY
- LEMMA_USED_BY
- EVIDENCE_SUPPORTS
- COUNTEREXAMPLE_REFUTES
- CLAIM_SPECIALIZES
- CLAIM_GENERALIZES
- ENGINEERING_DEPENDS_ON
- MANUSCRIPT_CLAIM_DERIVED_FROM
- PROOF_SUPPORTS_MANUSCRIPT_CLAIM
- REQUIREMENT_SUPPORTS_MANUSCRIPT_CLAIM
- PROFILE_ADAPTS_MASTER

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

## 3. Early Research Qualification

### `evaluate_formalizer_capability`
按能力 Profile 计算 RQ0，不接受供应商名称作为能力证明。

### `select_early_formalization_route`
选择 `PLATFORM_ADVANCED_FORMALIZER` 或 `EXTERNAL_ADVANCED_MODEL_IMPORT`。

### `run_prior_art_search`
执行学术与成熟工程项目检索，返回 `NeighborEvidenceSet`。

### `validate_prior_art_coverage`
检查来源类别、数量、元数据、成熟度证据、未检索区域和外部内容隔离。

### `import_external_formalization`
验证外部模型身份、输入 spec hash、检索集引用、可行性矩阵、FormulaBundle/EngineeringConceptBundle Schema 与来源。

### `assess_formalization_feasibility`
建立隔离的理论与工程评估 Session，逐项计算 `03A` 的 TFO–TFP 与 EFS–EFF，保守聚合为 route classification。

### `open_formalization_feasibility_gate`
仅对 `ENGINEERING_PROJECT_CANDIDATE` 或 `NEITHER_CURRENTLY_FIT/INCONCLUSIVE` 打开对应 Gate，绑定 assessment/spec hash。

### `resolve_engineering_route_decision`
只接受 `REVISE_FOR_THEORY | TRY_ENGINEERING_PROJECT | PAUSE | ARCHIVE`；必须验证真实用户 actor。

### `build_early_formula_bundle`
生成符号表、数学公式、依赖、语义映射、近邻差异与简明解释。

### `validate_early_formula_bundle`
检查符号闭合、公式覆盖、语义对齐、失败公式、引用与 hash。

### `open_early_formalization_review`
打开 `EARLY_FORMALIZATION_REVIEW`，绑定 formula/spec hash。

### `resolve_early_formalization_review`
只接受 APPROVE / REQUEST_REVISION / RESEARCH_MORE / REVISE_DESIGN / REJECT / PAUSE。

### `build_engineering_concept_bundle`
在用户明确选择工程路线后生成 I/O、状态转移、要求谓词、质量阈值、架构图候选和追踪关系。

### `validate_engineering_concept_bundle`
检查符号/单位、功能覆盖、阈值、失败与恢复、安全义务、来源和 hash；禁止写入 implemented/validated/novel。

### `open_early_engineering_concept_review`
打开 `EARLY_ENGINEERING_CONCEPT_REVIEW`，绑定 concept/spec/route hash。

### `start_novelty_review`
在用户批准且检索 COMPLETE 后建立两个隔离 Reviewer Session。

### `calculate_conservative_novelty_score`
按 route 和 `03A` policy 逐项取较小评分：理论路线计算理论 50 + 应用 50，工程路线计算工程 60 + 应用 40。

### `route_novelty_decision`
有效总分 `>=70` 时理论路线自动转 S5、工程路线自动转 ENG0；`<70` 或 INCONCLUSIVE 打开用户 Gate。

## 3A. Engineering Translation & Publication

### `initialize_engineering_workflow`
验证 route selection、concept approval、novelty status/override 和输入 hash，创建 ENG0 run。

### `build_engineering_mission_charter`
只从冻结 Artifact 导入 problem、stakeholder、boundary、objectives、constraints 和 success metrics；新增建议进入 proposed additions。

### `build_operational_concept`
生成 stakeholder map、主要/替代/失败/恢复场景、外部系统、信任边界和运行约束。

### `baseline_engineering_requirements`
创建稳定 Requirement ID、测量阈值、verification method、acceptance criterion 与 100% source trace。

### `run_engineering_trade_study`
检索公开工程证据，验证候选路线对 Critical requirements 的硬门并使用冻结权重计算方案分数。

### `build_architecture_baseline`
生成 context/container/component/runtime/data/state/deployment/security 机器对象、ADR 和接口/数据 Schema。

### `render_engineering_diagrams`
从机器对象生成版本化文本图源和 SVG/PNG/PDF，保存渲染回执及稳定 ID 映射。

### `open_engineering_architecture_review`
绑定 requirements/trade-study/architecture hashes，展示重大影响和不可逆决策。

### `build_mechanical_engineering_blueprint`
生成项目树、文件/模块/符号计划、依赖/迁移/错误/测试/回滚合同及原子 `EngineeringWorkUnitContract[]`。

### `validate_blueprint_completeness`
计算 requirement→design→task→test 覆盖、Schema、停止条件、断链和未决产品/架构决策；失败返回 `BLUEPRINT_GAP`。

### `select_engineering_delivery_mode`
选择 `BLUEPRINT_ONLY` 或请求 `BUILD_AND_EVALUATE`；后者只打开授权 Gate，不直接执行。

### `record_engineering_verification`
只接受真实 test/analysis/inspection/demonstration receipt；验证与确认分别存储。

### `build_application_and_extension_roadmaps`
为每个应用/扩展记录条件、指标、证据等级、影响、风险和时间层级。

### `build_engineering_master_manuscript`
按 evidence tier 生成期刊中立母稿和 claim-evidence matrix；无回执结果只能标 planned 或删除。

### `audit_master_manuscript`
由未参与初稿的 route-specific Auditor 检查语义、证据、引用、Scope、作者输入和真实编译；只有通过后才能交付母稿。

### `open_formal_manuscript_decision`
母稿交付后打开 `FORMAL_MANUSCRIPT_DECISION`，绑定 master/delivery-or-evidence hash。

### `resolve_formal_manuscript_decision`
只接受 `KEEP_MASTER_ONLY | WRITE_FORMAL_MANUSCRIPT | REVISE_MASTER | PAUSE`；无响应不得默认 WRITE。

### `select_publication_profile`
只有 decision 为 WRITE 时创建或选择 Profile；验证 route、`venue_kind`、官方指南时间、模板 checksum 和 scope-fit。作者责任字段只允许用户确认。

### `refresh_publication_profile`
从官方 author guide/policy/template URL 更新内置 Profile snapshot；超过 freshness window 或 hash 改变时使旧 Compliance 失效。

### `adapt_manuscript_to_venue`
从 Master + PublicationProfile 机械派生适配稿与 `VenueComplianceMatrix`，不得覆盖母稿。

### `audit_engineering_delivery`
由未参与初稿生成的 Auditor 检查追踪、机械性、图示、回执、引用、许可证、论文与敏感信息。

### `export_engineering_delivery`
按 `03B` 固定目录生成 manifest、checksums 和全部工件；只有最终条件满足才标 READY。

## 3B. Theory Publication

### `baseline_theory_publication_evidence`
验证理论 route，冻结 ResearchSpec、Formalization、FrozenClaim statement hash、Proof/Evidence、Semantic Audit、Citation 和未解决义务，确定 evidence tier。

### `build_theory_master_manuscript`
按 `03C` 生成期刊中立 TeX 母稿、`MathematicalManuscriptClaim[]`、Proof Dependency Graph 和 claim-evidence matrix。

### `validate_mathematical_manuscript_claims`
逐项检查对象域、量词、假设、结论、statement hash、proof/evidence status 与稿件类型；禁止把 conjecture/partial/solver-scope 结果升格为 theorem。

### `audit_theory_master_manuscript`
由隔离 Theory Manuscript Auditor 检查语义、证明依赖、引用、失败/限制、AI/作者字段和真实 TeX 编译。

### `deliver_theory_master_manuscript`
交付母稿、evidence tier、主 theorem/claim、未解决义务、审计报告和四刊/arXiv scope-fit；随后打开 `FORMAL_MANUSCRIPT_DECISION`。

### `export_theory_publication_delivery`
按 `03C` 固定目录导出母稿、proof/reproducibility artifact、决定、可选适配稿、Compliance 和 checksums。

## 4. Claim Compiler

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

## 5. Role Isolation

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

## 6. Model Provider

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

## 7. Council

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

## 8. ActionBroker

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

## 9. Lean

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

## 10. Z3

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

## 11. Python Sandbox

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

## 12. Codex Worker

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

## 13. Evidence

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

## 14. Human Gate

### `open_gate`
创建。

### `resolve_gate`
保存用户决定。

### `validate_gate_actor`
防止模型代替用户。

### `resume_after_gate`
继续。

## 15. FastAPI 端点

- POST `/projects`
- GET `/projects`
- GET `/projects/{id}`
- POST `/projects/{id}/seed`
- POST `/projects/{id}/stages/{stage_id}/run`
- POST `/specs/{id}/confirm`
- POST `/projects/{id}/qualification/capability`
- POST `/projects/{id}/qualification/prior-art-searches`
- POST `/projects/{id}/qualification/feasibility-assessments`
- GET `/feasibility-assessments/{id}`
- POST `/feasibility-assessments/{id}/route-decision`
- POST `/projects/{id}/qualification/formalizations/generate`
- POST `/projects/{id}/qualification/formalizations/import`
- GET `/formalizations/{id}`
- POST `/formalizations/{id}/review`
- POST `/projects/{id}/qualification/engineering-concepts/generate`
- GET `/engineering-concepts/{id}`
- POST `/engineering-concepts/{id}/review`
- POST `/qualification-subjects/{type}/{id}/novelty-reviews`
- GET `/novelty-reviews/{id}`
- POST `/projects/{id}/engineering-workflows`
- POST `/engineering-workflows/{id}/stages/{stage_id}/run`
- GET `/engineering-workflows/{id}`
- POST `/engineering-workflows/{id}/architecture-review`
- POST `/engineering-workflows/{id}/delivery-mode`
- POST `/engineering-workflows/{id}/master-manuscript`
- POST `/manuscripts/{type}/{id}/audit`
- POST `/manuscripts/{type}/{id}/formal-manuscript-decision`
- POST `/manuscripts/{type}/{id}/publication-profile`
- POST `/manuscripts/{type}/{id}/adapt`
- GET `/engineering-workflows/{id}/traceability`
- POST `/engineering-workflows/{id}/audit`
- POST `/engineering-workflows/{id}/export`
- POST `/projects/{id}/theory-publications`
- POST `/theory-publications/{id}/evidence-baseline`
- POST `/theory-publications/{id}/master-manuscript`
- GET `/theory-publications/{id}`
- POST `/theory-publications/{id}/export`
- GET `/publication-profiles`
- POST `/publication-profiles/{profile_id}/refresh`
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

## 16. CLI 命令

- `synaisthesis init`
- `synaisthesis serve`
- `synaisthesis doctor`
- `synaisthesis project create`
- `synaisthesis seed import`
- `synaisthesis stage run`
- `synaisthesis spec confirm`
- `synaisthesis qualification capability`
- `synaisthesis qualification search`
- `synaisthesis qualification feasibility`
- `synaisthesis qualification route-decision`
- `synaisthesis formalization generate`
- `synaisthesis formalization import`
- `synaisthesis formalization review`
- `synaisthesis engineering concept generate`
- `synaisthesis engineering concept review`
- `synaisthesis engineering workflow start`
- `synaisthesis engineering stage run`
- `synaisthesis engineering trace show`
- `synaisthesis engineering blueprint validate`
- `synaisthesis engineering manuscript master`
- `synaisthesis manuscript audit`
- `synaisthesis manuscript formal-decision`
- `synaisthesis engineering publication select`
- `synaisthesis manuscript adapt`
- `synaisthesis engineering audit`
- `synaisthesis engineering export`
- `synaisthesis theory publication start`
- `synaisthesis theory manuscript master`
- `synaisthesis theory publication export`
- `synaisthesis publication profiles list`
- `synaisthesis publication profile refresh`
- `synaisthesis novelty start`
- `synaisthesis novelty show`
- `synaisthesis claim compile`
- `synaisthesis claim freeze`
- `synaisthesis council start`
- `synaisthesis run status`
- `synaisthesis run pause`
- `synaisthesis run resume`
- `synaisthesis gate list`
- `synaisthesis gate resolve`
- `synaisthesis export`

## 17. MCP Tools

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
- `research_prepare_early_formalization`
- `research_get_formalization_feasibility`
- `research_submit_engineering_route_decision`
- `research_get_early_formalization`
- `research_submit_early_formalization_review`
- `research_prepare_engineering_concept`
- `research_get_engineering_concept`
- `research_submit_engineering_concept_review`
- `research_start_novelty_review`
- `research_get_novelty_review`
- `research_resolve_novelty_gate`
- `research_start_engineering_workflow`
- `research_advance_engineering_stage`
- `research_get_engineering_traceability`
- `research_validate_engineering_blueprint`
- `research_build_engineering_master_manuscript`
- `research_get_master_manuscript`
- `research_submit_formal_manuscript_decision`
- `research_select_publication_profile`
- `research_adapt_manuscript_to_profile`
- `research_get_engineering_delivery_status`
- `research_export_engineering_delivery`
- `research_start_theory_publication`
- `research_build_theory_master_manuscript`
- `research_get_theory_publication_status`
- `research_export_theory_publication_delivery`
- `research_list_publication_profiles`
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

外部 Codex 使用时，上述 mutation 名称只表示 `research_prepare_command` 支持的业务意图，不得绕过 Fidelity Gateway 暴露为直接 mutation。

## 18. 幂等性

所有 mutation 接口接受：
- `idempotency_key`
- `trace_id`
- `expected_version`

若 expected_version 不匹配：
- 返回 CONFLICT；
- 不自动覆盖；
- 要求重新读取状态。

## 19. 错误对象

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

早期资格固定错误码：

- `EARLY_QUALIFICATION_REQUIRED`
- `FORMALIZER_CAPABILITY_UNAVAILABLE`
- `PRIOR_ART_COVERAGE_INCOMPLETE`
- `FORMALIZATION_FEASIBILITY_INCONCLUSIVE`
- `ENGINEERING_ROUTE_DECISION_REQUIRED`
- `FORMALIZATION_FEASIBILITY_USER_DECISION_REQUIRED`
- `FORMULA_BUNDLE_INVALID`
- `ENGINEERING_CONCEPT_BUNDLE_INVALID`
- `FORMALIZATION_USER_APPROVAL_REQUIRED`
- `ENGINEERING_CONCEPT_USER_APPROVAL_REQUIRED`
- `NOVELTY_REVIEW_INCONCLUSIVE`
- `LOW_NOVELTY_USER_DECISION_REQUIRED`
- `ENGINEERING_NOVELTY_REQUIRED`
- `REQUIREMENTS_BASELINE_BLOCKED`
- `ENGINEERING_ARCHITECTURE_REVIEW_REQUIRED`
- `ENGINEERING_BLUEPRINT_GAP`
- `PROTOTYPE_EXECUTION_AUTHORIZATION_REQUIRED`
- `PUBLICATION_PROFILE_REQUIRED`
- `MASTER_MANUSCRIPT_REQUIRED`
- `MASTER_MANUSCRIPT_AUDIT_FAILED`
- `FORMAL_MANUSCRIPT_DECISION_REQUIRED`
- `THEORY_ROUTE_REQUIRED`
- `THEOREM_CLAIM_UNSUPPORTED`
- `PUBLICATION_PROFILE_ROUTE_MISMATCH`
- `VENUE_SCOPE_MISMATCH`
- `ARXIV_PACKAGE_INVALID`
- `MANUSCRIPT_CLAIM_UNSUPPORTED`
- `STALE_PUBLICATION_GUIDANCE`
- `BLOCKED_ENGINEERING_DELIVERY`

## 20. Codex Instruction Fidelity Layer

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
- ENGINEERING_ROUTE_DECISION
- FORMALIZATION_FEASIBILITY_DECISION
- EARLY_FORMALIZATION_REVIEW
- EARLY_ENGINEERING_CONCEPT_REVIEW
- LOW_NOVELTY_RESEARCH_DECISION
- ENGINEERING_SCOPE_CHANGE
- ENGINEERING_ARCHITECTURE_REVIEW
- PROTOTYPE_EXECUTION_AUTHORIZATION
- FORMAL_MANUSCRIPT_DECISION
- PUBLICATION_PROFILE_SELECTION
- ENGINEERING_DELIVERY_ACCEPTANCE
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

`ENGINEERING_ROUTE_DECISION` 必须绑定 `assessment_id + version + assessment_hash + input_spec_hash`，展示失败的理论谓词、通过的工程谓词、最近工程近邻、风险和所有合法决定。只有真实用户 actor 可以选择 `TRY_ENGINEERING_PROJECT`；模型、工作流、管理员或默认超时动作不得代选。

`EARLY_FORMALIZATION_REVIEW` 必须绑定 `formalization_id + version + formula_hash + input_spec_hash`；`EARLY_ENGINEERING_CONCEPT_REVIEW` 必须绑定 `concept_id + version + concept_hash + route_selection_id + input_spec_hash`。

`LOW_NOVELTY_RESEARCH_DECISION` 必须按 route 展示理论/应用分或工程/应用分、总分、最近重合项、检索限制和所有可选决定；模型不得替用户选择重新研究或低分继续。

`ENGINEERING_ARCHITECTURE_REVIEW` 必须绑定 requirements、trade study 与 architecture 三个 hash。`PROTOTYPE_EXECUTION_AUTHORIZATION` 必须展示代码/实验范围、环境、预算、数据、安全、外部动作和停止条件；拒绝或未解决时工作流保持 `BLUEPRINT_ONLY`。

`FORMAL_MANUSCRIPT_DECISION` 只能在理论或工程母稿完成独立审计并先交付用户后打开，必须绑定 `route + master_manuscript_id + version + master_hash + evidence_or_delivery_hash`。合法决定只有 `KEEP_MASTER_ONLY | WRITE_FORMAL_MANUSCRIPT | REVISE_MASTER | PAUSE`；模型、管理员、默认值或超时动作不得代选 WRITE。

`PUBLICATION_PROFILE_SELECTION` 只有当前绑定的 `FORMAL_MANUSCRIPT_DECISION = WRITE_FORMAL_MANUSCRIPT` 才可打开。必须展示 venue kind、scope-fit、官方指南 freshness、模板 checksum、主要合规差异、预印本/独家投稿政策和作者输入项；不得由模型确认作者、作者顺序、机构、ORCID、伦理、利益冲突、资助、许可证、版权或投稿。arXiv 必须显示为 `PREPRINT_REPOSITORY`，不得暗示同行评审。

`ENGINEERING_DELIVERY_ACCEPTANCE` 绑定最终 manifest hash，任何文件或 checksum 变化都会使旧验收失效。

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

本文件规定 Stage 目标；`19_MECHANICAL_EXECUTION_CONTRACT.md` 规定稳定 Task ID、允许文件、关键符号、前置条件、验证命令、通过/停止条件。没有完整 `WorkUnitContract` 时不得开始实现。

Stage 0.5 的编号表示安全优先级。实际硬依赖是 Stage 1 的领域/Event/Artifact 基础，其完成门位于 Stage 10 开放任何外部 Codex mutation 之前；它不阻断 Stage 1–9 的内部实现。

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

## Stage 2：搬运 S0–S4 并形成自然语言设计完成门

### 任务
将当前 Skill 中表现良好的内容变成：
- StageContract；
- Pydantic Schema；
- Prompt Asset；
- Validation Rule。

### 函数
- `capture_seed`
- `execute_s0` 至 `execute_s4`
- `validate_stage_output`
- `evaluate_stage_gate`
- `advance_stage`

### 测试
把现有成功对话作为 golden cases。

### 完成标准
不依赖 Codex 会话历史，也能从输入形成用户确认的 S1/S4 与 `NATURAL_LANGUAGE_DESIGN_READY`。

---

## Stage 2.5：RQ0–RQ4 早期形式化与新颖性资格

### 实现顺序
1. RQ Domain、状态、Gate、Event 与 migration；
2. Fake academic/engineering prior-art provider；
3. 高能力 Profile 检查与外部导入合同；
4. RQ2F 理论/工程适配谓词、双评估与保守聚合；
5. `ENGINEERING_ROUTE_DECISION` 和 `FORMALIZATION_FEASIBILITY_DECISION`；
6. RQ2M FormulaBundle Schema、符号/语义/失败公式验证；
7. RQ2E EngineeringConceptBundle、单位/阈值/I/O/状态/追踪验证；
8. 路线化用户审查 Gate；
9. 两个隔离 Reviewer 与理论 50 + 应用 50、工程 60 + 应用 40 的保守聚合；
10. route-aware 70/69 路由；
11. S5、ENG0 及后续成熟门的强制前置检查。

### 完成标准
- 无资格能力路线时阻断；
- 检索同时覆盖学术与成熟工程近邻；
- 理论不适配、工程适配时只打开用户 Gate，不自动转工程；
- 理论路线核心形式化全部为数学公式；工程路线概念以公式化 I/O、状态、要求、阈值和追踪关系表达；
- 用户批准绑定具体 hash；
- 理论路线有效总分 70 自动进入 S5，工程路线有效总分 70 自动进入 ENG0；
- 69、INCONCLUSIVE 或覆盖不足交还用户；
- Fake 路径在 CI 中可重复，真实 Provider 在 Stage 6/13 接入。

---

## Stage 2.6：ENG0–ENG10 工程转化、机械蓝图与论文交付

### 实现顺序
1. Engineering workflow Domain、Artifact、状态、事件、Gate 与 migration；
2. ENG0 mission charter 和 ENG1 ConOps；
3. ENG2 Requirement Schema、验收目录和双向追踪；
4. ENG3 Fake reference/trade study 与冻结权重策略；
5. ENG4 architecture/interface/data/state/security 机器对象、ADR 和文本图源渲染；
6. `ENGINEERING_ARCHITECTURE_REVIEW`；
7. ENG5 `MechanicalEngineeringBlueprint` 与原子 `EngineeringWorkUnitContract`；
8. Blueprint Completeness Gate；
9. ENG6 `BLUEPRINT_ONLY` 与需要独立授权的 `BUILD_AND_EVALUATE` 分流；
10. ENG7 应用/扩展 Portfolio；
11. ENG8 EngineeringMasterManuscript、ClaimEvidenceMatrix、独立母稿审计与母稿交付；
12. `FORMAL_MANUSCRIPT_DECISION`：KEEP_MASTER_ONLY 或用户选择 WRITE；
13. ENG9 双路线 Profile Registry、工程四刊/arXiv/扩展 Profile、freshness、Venue adapter、Compliance 与 ReproducibilityArtifact；
14. ENG10 独立 Auditor、manifest/checksum 和最终用户验收；
15. API/CLI/MCP/Fake E2E 纵向切片。

### 确定技术路线
- 系统工程主线采用 stakeholder/ConOps → requirements → logical decomposition/trade study → architecture → implementation tasks → verification/validation；
- 需求、设计、任务、测试与论文主张通过稳定 ID 双向追踪；
- 图示以机器对象为权威，使用 Mermaid/PlantUML/C4-PlantUML 等文本源生成 SVG；
- 软件质量按适用 ISO/IEC 25010 特性转成项目阈值，安全开发按 NIST SSDF 映射活动和证据；
- 论文先交付期刊中立母稿；只有用户选择 WRITE 后才按工程四刊、工程 arXiv 或扩展 Profile 生成适配稿 + 合规矩阵；
- 没有真实实现/实验时只允许 Design/Protocol Draft，禁止虚构结果。

### 完成标准
- 只有已确认工程路线且通过 RQ4E 的项目可进入 ENG0；
- Critical requirements 100% 具有来源、验收、设计、任务和验证映射；
- 机械任务无未决产品/架构选择、无模糊动词，均有验证与停止条件；
- 所有图源可重渲染、稳定 ID 可回链；
- 未授权时不执行代码/实验，工作流仍能输出 `BLUEPRINT_ONLY` 交付候选；
- 每个论文结果 claim 都有真实 receipt，或被标为 planned/删除；
- 用户选择 KEEP_MASTER_ONLY 时不生成适配稿仍属于完整交付；arXiv 始终标为预印本平台；
- 最终工程包、manifest 和 checksum 可复算。

---

## Stage 3：S5–S10 与 MATURE_IDEA_READY

### 实现
- TheoryKernel；
- FormalizationPlan；
- PreFreezeAttackReport；
- OpenQuestionRegistry；
- HandoffBundle；
- computed maturity gate。
- S5 的 RQ 前置检查；

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

## Stage 9.5：纯数学理论论文母稿与正式发布适配

### 实现顺序
1. TP0 `TheoryPublicationEvidenceBaseline`，冻结 statement/proof/evidence/semantic/citation Scope；
2. TP1 `TheoryMasterManuscript`、`MathematicalManuscriptClaim[]`、Proof Dependency Graph 与 TeX/PDF 真实编译；
3. TP2 隔离 Theory Manuscript Auditor、母稿交付和 `FORMAL_MANUSCRIPT_DECISION`；
4. 用户选择 KEEP_MASTER_ONLY 时直接形成论文交付；
5. 用户选择 WRITE 时，TP3 从理论四刊、数学 arXiv 或 CUSTOM Profile 中选择；
6. TP4 Venue Adapter、ComplianceMatrix、作者输入登记和独立审计；
7. TP5 manifest/checksum、proof/reproducibility artifact 和导出；
8. API/CLI/MCP/Fake E2E。

### 内置 Profile
- Annals of Mathematics；
- Journal of the American Mathematical Society；
- Inventiones mathematicae；
- Acta Mathematica；
- arXiv Mathematics Preprint（不是期刊）；
- CUSTOM_VENUE。

工程方向同时内置 IEEE TSE、ACM TOSEM、Empirical Software Engineering、Journal of Systems and Software 与工程/计算 arXiv；JOSS/Nature Profile 保留为扩展。

### 完成标准
- 理论最终 ResearchBundle 必含独立审计通过的母稿；
- 定理 statement hash、对象域、量词、假设、proof status 和证据 100% 可追踪；
- conjecture/partial/solver-scope 结果不能升格为 theorem；
- 母稿先交付，用户明确 WRITE 后才生成正式适配稿；
- arXiv Profile 校验 TeX 源、图、BibTeX、metadata、license、category 与真实编译，且不产生同行评审状态；
- 指南过期、作者输入缺失或适配改变 statement 时不能 READY。

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

## Stage 13：生产级相邻工作检索与新颖性

### 数据源
- OpenAlex；
- Crossref；
- arXiv；
- 可选 Semantic Scholar。
- 工程来源按领域使用官方仓库、包注册表、官方项目/产品文档与标准资料；

### 实现
- 查询扩展；
- metadata 验证；
- 去重；
- 最近邻分类；
- novelty status；
- 工程成熟度证据；
- RQ1 真实检索回执；
- RQ4 两 Reviewer 生产评分；
- 外部内容隔离。

### 完成标准
已知经典结果被识别为重合；工程近邻按功能/应用排序；覆盖不足只能 INCONCLUSIVE；理论/工程可行性分流、用户工程路线决定和两种新颖性 policy 的 70/69 路由可复现；生产 Provider 可支撑 ENG3 的参考方案检索。

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
- 未通过 RQ0 能力门就生成早期形式化；
- 未批准当前 FormulaBundle hash 就启动新颖性审查；
- 新颖性总分低于 70 时自动重做研究或自动继续；
- 未有 ActionBroker 就让 Codex 写主仓库；
- 未锁定 statement 就做 Proof Loop；
- 未有 Recursion Guard 就开启双向 Codex。

## 推荐首个垂直切片

为了尽快获得可用成果，建议优先完成：

1. S0–S4 持久化；
2. RQ0–RQ4 Fake/外部导入与理论/工程分流纵向切片；
3. ENG0–ENG10 `BLUEPRINT_ONLY` Fake 纵向切片；
4. S5 持久化；
5. Synaisthesis MCP；
6. Codex Operator Skill；
7. ClaimContract；
8. Fake 十轮；
8. 双模型；
9. Z3；
10. Lean；
11. Codex Worker。

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
平台执行 S0–S4、带理论/工程可行性分流的 RQ0–RQ4、S5 与 ENG0–ENG10 BLUEPRINT_ONLY 纵向切片，Codex 只调用 MCP；RQ、双路线论文母稿审计和发布 Profile 首先使用 Fake Provider、冻结官方指南 fixture 或标准化外部导入，真实检索/模型随后接入。Profile 选择必须晚于母稿交付和 `FORMAL_MANUSCRIPT_DECISION`。

### Phase 3
平台执行 S6–S10，旧 Skill 只做兼容。

### Phase 4
平台执行 Council，旧对抗插件停用。

### Phase 5
平台调 Codex Worker，形成双向闭环。

## 13. 迁移验收

满足以下条件后停止旧工作流：

- S0–S4、S5 与 ENG0–ENG10 BLUEPRINT_ONLY 平台输出不低于旧 Skill/文档合同；
- RQ0–RQ4 的能力、检索、可行性分流、理论/工程概念、用户审查与 route-aware 70 分路由可恢复且不可绕过；
- 工程路线只有真实用户可选择，Mechanical Blueprint 无未决产品/架构决策；
- 理论路线交付 `TheoryMasterManuscript`，工程路线交付 `EngineeringMasterManuscript`；两者均先独立审计并交给用户，再由用户决定是否生成期刊/arXiv 正式适配稿；
- 无实现/实验时工程论文保持 Design/Protocol Master 且无虚构结果；
- S6–S10 状态可恢复；
- FrozenClaim 有 hash；
- Council 真实运行；
- Tool Evidence 可复现；
- Codex MCP 操作无明显摩擦；
- 平台可调起 Codex Worker；
- 旧案例可导入；
- 用户确认流程保留；
- 原流程图中的每个控制点有明确平台对象对应。

## 14. v2.1：把 Codex Operator 从 Prompt 客户端迁移为受控客户端

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

本文件给出可直接照着建立仓库的目录结构。v0.1–v1.0 默认按此路径实现；目录改名或模块移动必须先写 ADR，并在同一文档任务中更新 `07`、`09`、`19` 与 manifest，代码执行者不得临场自行调整。

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
│     ├─ research_qualification.yaml
│     ├─ novelty_scoring_v1.yaml
│     ├─ engineering_novelty_scoring_v1.yaml
│     ├─ engineering_workflow.yaml
│     ├─ blueprint_completeness.yaml
│     ├─ publication.yaml
│     ├─ action_authorization.yaml
│     └─ isolation.yaml
│
├─ configs/publication_profiles/
│  ├─ theory/
│  │  ├─ annals_of_mathematics.yaml
│  │  ├─ jams.yaml
│  │  ├─ inventiones_mathematicae.yaml
│  │  └─ acta_mathematica.yaml
│  ├─ engineering/
│  │  ├─ ieee_tse.yaml
│  │  ├─ acm_tosem.yaml
│  │  ├─ empirical_software_engineering.yaml
│  │  └─ journal_of_systems_and_software.yaml
│  └─ shared/
│     ├─ math_arxiv_preprint.yaml
│     └─ engineering_arxiv_preprint.yaml
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
│  │  ├─ qualification.py
│  │  ├─ novelty.py
│  │  ├─ engineering.py
│  │  ├─ requirements.py
│  │  ├─ architecture.py
│  │  ├─ traceability.py
│  │  ├─ publication.py
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
│  │  ├─ qualification_service.py
│  │  ├─ novelty_service.py
│  │  ├─ engineering_design_service.py
│  │  ├─ engineering_traceability_service.py
│  │  ├─ publication_service.py
│  │  ├─ theory_publication_service.py
│  │  ├─ engineering_delivery_audit_service.py
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
│  │  │  ├─ qualification_nodes.py
│  │  │  ├─ engineering_nodes.py
│  │  │  ├─ publication_nodes.py
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
│  │  ├─ early_formalizer.py
│  │  ├─ engineering_feasibility_assessor.py
│  │  ├─ novelty_reviewer.py
│  │  ├─ theory_manuscript_auditor.py
│  │  ├─ engineering_manuscript_auditor.py
│  │  ├─ engineering_delivery_auditor.py
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
│  │  └─ prior_art/
│  │     ├─ base.py
│  │     ├─ fake.py
│  │     ├─ openalex.py
│  │     ├─ crossref.py
│  │     ├─ arxiv.py
│  │     ├─ semantic_scholar.py
│  │     ├─ engineering_base.py
│  │     ├─ repository_registry.py
│  │     ├─ package_registry.py
│  │     ├─ official_docs.py
│  │     ├─ standards.py
│  │     ├─ maturity.py
│  │     ├─ normalization.py
│  │     └─ deduplication.py
│  ├─ renderers/
│  │  ├─ base.py
│  │  ├─ mermaid.py
│  │  ├─ plantuml.py
│  │  ├─ c4_plantuml.py
│  │  └─ fake.py
│  ├─ publication/
│  │  ├─ profile_registry.py
│  │  ├─ profile_provider.py
│  │  ├─ official_guide_fetcher.py
│  │  ├─ theory_master_manuscript.py
│  │  ├─ engineering_master_manuscript.py
│  │  ├─ venue_adapter.py
│  │  ├─ arxiv_adapter.py
│  │  ├─ tex_compiler.py
│  │  ├─ compliance.py
│  │  └─ fake.py
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
│  │  │  ├─ engineering_repository.py
│  │  │  ├─ traceability_repository.py
│  │  │  ├─ publication_repository.py
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
│  │  ├─ novelty/
│  │  ├─ engineering/
│  │  ├─ publication/
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
│  │  ├─ synaisthesis-engineering-operator/
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
- `early_formalizer`
- `engineering_feasibility_assessor`
- `novelty_primary`
- `novelty_auditor`
- `theory_manuscript_auditor`
- `engineering_manuscript_auditor`
- `engineering_delivery_auditor`
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
- capability_tier
- formalization_eval_score
- math_schema_valid_rate
- capability_evaluated_at
- capability_valid_days

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

### `prior_art`
- `academic_providers`
- `engineering_providers`
- `patent_providers`
- `standards_providers`
- `request_rate`
- `result_count`
- `full_text_policy`
- `metadata_verification`
- `deduplication_strategy`
- `query_budget`
- `min_academic_source_types = 3`
- `min_engineering_source_types = 2`
- `min_academic_neighbors = 5`
- `min_engineering_neighbors = 3`
- `external_content_trust = untrusted`

### `research_qualification`
- `required_after_stage = S4`
- `block_s5_until_complete = true`
- `block_eng0_until_complete = true`
- `allowed_routes = [platform_advanced_formalizer, external_advanced_model_import]`
- `minimum_capability_tier = advanced`
- `minimum_formalization_eval_score = 80`
- `minimum_math_schema_valid_rate = 0.95`
- `capability_valid_days = 90`
- `require_formula_core = true`
- `require_user_formula_hash_approval = true`
- `feasibility_policy_version = formalization_feasibility_v1`
- `require_independent_theory_and_engineering_assessments = true`
- `engineering_route_requires_human_decision = true`
- `require_engineering_concept_hash_approval = true`

### `novelty`
- `policy_version = novelty_scoring_v1`
- `engineering_policy_version = engineering_novelty_scoring_v1`
- `require_two_isolated_reviewers = true`
- `require_model_diversity_in_research_profile = true`
- `aggregation = per_item_min`
- `theory_max = 50`
- `application_max = 50`
- `engineering_max = 60`
- `engineering_application_max = 40`
- `auto_continue_threshold = 70`
- `below_threshold_action = human_gate`
- `inconclusive_action = human_gate`
- `allow_user_override_with_audit = true`

### `engineering_workflow`
- `entry_status = engineering_novelty_qualified`
- `stages = [ENG0, ENG1, ENG2, ENG3, ENG4, ENG5, ENG6, ENG7, ENG8, ENG9, ENG10]`
- `default_delivery_mode = blueprint_only`
- `build_requires_human_gate = true`
- `architecture_review_required = true`
- `require_bidirectional_traceability = true`
- `require_text_diagram_sources = true`
- `diagram_render_formats = [svg, png]`
- `require_independent_delivery_auditor = true`
- `max_directed_rework_rounds = 1`

### `blueprint_completeness`
- `requirement_to_design_coverage = 1.0`
- `requirement_to_task_coverage = 1.0`
- `critical_requirement_to_test_coverage = 1.0`
- `public_interface_schema_coverage = 1.0`
- `task_stop_condition_coverage = 1.0`
- `max_unresolved_product_decisions = 0`
- `max_unresolved_architecture_decisions = 0`
- `max_broken_diagram_references = 0`
- `forbidden_ambiguous_phrases = [适当修改, 酌情优化, 根据情况处理, 完善相关代码, 视情况测试]`

### `publication`
- `theory_builtin_profiles = [MATH_ANNALS_OF_MATHEMATICS, MATH_JAMS, MATH_INVENTIONES, MATH_ACTA_MATHEMATICA]`
- `engineering_builtin_profiles = [ENG_IEEE_TSE, ENG_ACM_TOSEM, ENG_EMSE, ENG_JSS]`
- `preprint_profiles = [MATH_ARXIV_PREPRINT, ENG_ARXIV_PREPRINT]`
- `optional_extension_profiles = [ENG_JOSS, ENG_NATURE_PORTFOLIO_METHODS_OR_SOFTWARE]`
- `custom_venue_allowed = true`
- `guide_freshness_days = 30`
- `master_manuscript_required = true`
- `master_audit_required = true`
- `master_delivery_before_profile_selection = true`
- `formal_manuscript_decision_required = true`
- `formal_manuscript_default_decision = null`
- `venue_adapter_required_when_selected = true`
- `venue_kind_required = true`
- `arxiv_venue_kind = PREPRINT_REPOSITORY`
- `reject_arxiv_as_journal = true`
- `reject_route_profile_mismatch = true`
- `reject_scope_mismatch = true`
- `claim_evidence_mapping_required = true`
- `forbid_unsupported_results = true`
- `ai_use_disclosure_required = true`
- `author_responsibility_fields_require_human = true`
- `reproducibility_artifact_required = true`

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

在主项目树中增加以下固定路径：

```text
src/synaisthesis/
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

plugin/
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

### v0.1 — Durable Incubator and Early Research Qualification
目标：把 S0–S4、自然语言设计完成门、带形式化可行性分流的 RQ0–RQ4 与 S5/ENG0 入口迁入平台；第一阶段使用 Fake Provider 和标准化外部高能力模型导入。

必须完成：
- Project / ResearchSpec / StageRecord；
- S0–S4、S5 与 ENG0 入口契约；
- RQ0 能力/导入路线；
- Fake 学术/工程近邻检索；
- 理论/工程适配谓词、双评估和强制用户工程路线决定；
- 数学公式化 EarlyFormalizationBundle；
- 工程公式化 EngineeringConceptBundle；
- 用户 Artifact hash 审查；
- 理论 50 + 应用 50、工程 60 + 应用 40 的 route-aware 70 分确定性路由；
- 用户确认与回退；
- Event Log；
- Artifact Store；
- CLI；
- Codex 通过最小 MCP 调用 Incubator；
- 旧 Skill 输出导入。

作品集价值：证明你能把 Prompt 流程转成耐久状态机。

### v0.1.1 — Engineering Translation and Publication Blueprint
必须完成：
- ENG0–ENG10 Durable Workflow；
- mission/ConOps、Requirement Schema、Acceptance Catalog 与双向 Traceability；
- Fake 工程参考方案与冻结权重 Trade Study；
- architecture/interface/data/state/security/deployment 机器对象和 ADR；
- 文本图源 → SVG 的可复算渲染；
- MechanicalEngineeringBlueprint 与原子 WorkUnitContract；
- `BLUEPRINT_ONLY` 与授权后 `BUILD_AND_EVALUATE` 的隔离；
- Verification/Validation 分离；
- 应用方向与未来扩展 Portfolio；
- EngineeringMasterManuscript → 独立审计 → 用户正式稿决策 → PublicationProfile/Venue Adapter/Compliance Matrix；
- 四种软件/系统工程主要期刊 Profile 与工程 arXiv 预印本 Profile；非软件工程使用 CUSTOM_VENUE，不强行套用；
- ClaimEvidenceMatrix、ReproducibilityArtifact、manifest/checksums；
- Independent Engineering Delivery Audit。

作品集价值：证明系统不仅能孵化理论命题，也能在不让模型补产品决策、不虚构实验结果的前提下交付可机械执行的工程设计与证据约束论文。

### v0.2 — Claim Compiler and S6–S10
必须完成：
- Core Theory；
- Formal Construction；
- ClaimUnit；
- ClaimContract；
- MATURE_IDEA_READY；
- S6–S10；
- 研究交接包。
- TheoryMasterManuscript、theorem/proof/evidence/citation 追踪矩阵与证明依赖图；
- 理论母稿独立审计、母稿交付和 `FORMAL_MANUSCRIPT_DECISION`；
- Annals、JAMS、Inventiones、Acta 四种数学期刊 Profile 与数学 arXiv 预印本 Profile；
- 只有用户选择 `WRITE_FORMAL_MANUSCRIPT` 才生成目标 Profile 的正式适配稿与合规矩阵。

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
- 成熟工程项目官方仓库、包注册表和官方文档 Provider；
- 最近邻分类；
- 文献元数据核验；
- Claim–Evidence Graph；
- `POSSIBLY_ORIGINAL` 语言边界；
- Bundle Export；
- RQ0–RQ4 生产 Provider 端到端验证。
- ENG3 生产级工程参考/标准检索与 PublicationProfile 官方指南刷新。

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
2. S0–S4 与自然语言设计确认；
3. RQ1 检索学术与成熟工程近邻；
4. RQ2F 判定理论路线适配，RQ2M 生成数学公式化候选，用户在 RQ3M 批准；
5. RQ4M 有效总分达到 70 后自动进入 S5；
6. Claim 编译；
7. Council Round 2 找到 Z3 反例；
8. Repair A 将对象域缩小，被判 S3；
9. 用户拒绝；
10. Repair B 保留原语义；
11. 平台调 Codex Worker 构造 Lean 文件；
12. Lean Adapter 独立验证；
13. Auditor 反译；
14. 用户确认；
15. 导出 Evidence Bundle。

这段演示比“多个 Agent 在终端里聊天”有说服力得多。

另设一个工程分流案例，必须展示：
1. RQ2F 的理论谓词 FAIL、工程谓词 PASS；
2. 平台只打开 `ENGINEERING_ROUTE_DECISION`，用户明确选择 `TRY_ENGINEERING_PROJECT`；
3. RQ2E/RQ3E 固定 I/O、状态、要求、阈值和追踪；
4. RQ4E 有效总分达到 70 后自动进入 ENG0；
5. ENG1–ENG4 从 ConOps、Requirements 和 Trade Study 形成用户批准的 Architecture Baseline；
6. ENG5 输出无未决产品/架构选择的机械 WorkUnit；
7. 项目保持 BLUEPRINT_ONLY，未授权任何代码或实验；
8. ENG7 输出有指标/风险/条件的应用和扩展路线；
9. ENG8 输出经独立审计的 Design/Protocol EngineeringMasterManuscript 并先交给用户；只有用户选择 WRITE_FORMAL_MANUSCRIPT，ENG9 才输出目标期刊或 arXiv 适配稿与合规矩阵，结果章节不含虚构数据；
10. ENG10 重算图、追踪、manifest 和 checksums，用户验收当前交付 hash。

## 4. README 第一屏

建议一句话：

> Synaisthesis is a human-governed, dual-model research orchestration platform that turns natural-language research intent into versioned claims, adversarial verification loops, formal-tool evidence, and auditable human decisions—with bidirectional Codex integration.

随后展示：

```text
Idea / Spec
    ↓
Neighbor Search · Formula-First Early Formalization
    ↓
User Review · Theory/Application Novelty >= 70
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
- 早期形式化用户修订次数；
- 理论/应用新颖性分布；
- 理论/工程适配判定与用户分流选择分布；
- 工程/应用新颖性分布；
- 70 分自动继续与低分研究回流比例；
- Requirement→Design→Task→Test 追踪覆盖率；
- Blueprint Gap 数与未决决策数；
- 双路线论文 Claim Evidence 覆盖率、母稿审计状态、正式稿决策分布与 Venue Compliance 状态；

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

## 6. 新颖性与研究价值评审依据

### Nature editorial criteria and reviewer guidance
https://www.nature.com/nature/for-authors/editorial-criteria-and-processes
https://www.nature.com/nature/for-referees/policies-and-processes

借鉴：
- 原创研究、科学重要性与对领域理解的推进是不同维度；
- 新颖性主张必须与会削弱新颖性的最近论文直接比较；
- 技术可靠性和证据充分性不能被新颖性分替代。

### NSF Merit Review
https://www.nsf.gov/funding/merit-review

借鉴：
- 区分知识推进（intellectual merit）与社会/实践影响（broader impacts）；
- 创造性、原创性、潜在变革性和有依据的执行计划需要分别说明。

### WIPO patentability overview and PCT inventive-step guidance
https://www.wipo.int/en/web/patents/protection
https://www.wipo.int/en/web/pct-system/texts/ispe/13_01_02

借鉴：
- “不同”不等于“非显然”；
- 最近技术、非显然性与实际可用性应分开审查；
- Synaisthesis 的应用新颖性评分不是专利性或法律意见。

这些来源只用于校准 `03A` 的评分维度。平台必须使用自己的检索证据、双 Reviewer、保守聚合和 Human Gate，不能把期刊、基金或专利机构标准直接映射为录用/授权结论。

## 7. 采用原则

任何外部项目只能提供：
- 架构模式；
- Adapter 参考；
- 测试方式；
- 失败案例。

不得直接把外部项目宣称的“自治”“审稿”“证明”标签映射到 Synaisthesis 的状态。Synaisthesis 的状态必须经过自己的 ClaimContract、Evidence Scope、Tool Receipt、Semantic Audit 和 Human Gate。

## 8. Codex Hooks 与指令忠实传递

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

## 9. 工程转化与机械蓝图依据

### NASA Systems Engineering Handbook and process guidance

- https://www.nasa.gov/wp-content/uploads/2018/09/nasa_systems_engineering_handbook_0.pdf
- https://www.nasa.gov/reference/4-0-system-design-processes/
- https://www.nasa.gov/reference/4-1-stakeholder-expectations-definition/
- https://www.nasa.gov/reference/4-3-logical-decomposition/
- https://www.nasa.gov/reference/5-4-product-validation/
- https://www.nasa.gov/reference/6-2-requirements-management/

借鉴：
- stakeholder expectations / ConOps → technical requirements → logical decomposition → design solution；
- Verification 与 Validation 分离；
- 期望、要求、设计元素、验证活动和变更之间的双向追踪；
- 验证/确认报告记录版本、环境、方法、通过/失败、偏差和纠正动作。

边界：
- Synaisthesis 不宣称执行 NASA 认证流程；
- 只采用可迁移的方法结构，领域项目仍须使用其自己的法规和标准。

### GitHub Spec Kit

- https://github.com/github/spec-kit
- https://github.com/github/spec-kit/blob/main/spec-driven.md
- https://github.github.com/spec-kit/

借鉴：
- specification 是 source of truth；
- Spec → Plan → Tasks → Implement；
- 要求、计划、任务和验收标准之间的 traceability 与 consistency；
- 实施任务必须足够明确，不能把产品决策推给代码模型。

### ISO/IEC 25010 product quality model

- https://www.iso.org/standard/78176.html

借鉴：
- 从适用的产品质量特性派生质量要求、目标和验收指标；
- 质量模型用于需求与评估框架，而不是无证据的“符合 ISO”宣传。

### NIST Secure Software Development Framework (SSDF)

- https://csrc.nist.gov/projects/ssdf

借鉴：
- Prepare the Organization、Protect the Software、Produce Well-Secured Software、Respond to Vulnerabilities；
- 安全活动按结果和风险映射到责任、开发工件、供应链与验证证据。

### C4-PlantUML

- https://github.com/plantuml-stdlib/C4-PlantUML
- https://github.com/plantuml-stdlib/C4-PlantUML/blob/master/samples/C4CoreDiagrams.md

借鉴：
- context/container/component/dynamic/deployment 层级；
- 使用可版本控制的文本图源生成渲染图；
- 图示是机器架构对象的投影，不作为唯一事实来源。

## 10. 同方向自动化项目与论文/工件规范

### AI Scientist v2

- https://github.com/sakanaai/ai-scientist-v2

借鉴：idea → experiments → paper 的阶段划分、实验管理和显式安全警告。边界：不采用其自治声明作为 Synaisthesis 的证据，不允许生成代码或实验结果绕过 Sandbox、WorkUnit 和真实回执。

### Agent Laboratory

- https://github.com/SamuelSchmidgall/AgentLaboratory

借鉴：literature review、experimentation、report writing 三段式研究工件组织。边界：Agent 输出仍是 Proposal，论文主张必须绑定 Synaisthesis Evidence。

### Nature reporting and formatting guidance

- https://www.nature.com/npjclimatsci/for-authors-and-referees/about/editorial-policies/reporting-standards
- https://www.nature.com/nature/for-authors/formatting-guide

借鉴：可复现性、data/code/materials availability、方法与报告完整性、目标期刊格式要求。具体期刊规则必须在用户选择 Profile 后重新读取官方页面，不能把当前快照永久硬编码。

### IEEE Computer Society author resources

- https://www.computer.org/publications/author-resources

借鉴：模板、style、publication-specific instructions、研究工件和可复现实践。每个具体期刊仍使用独立 PublicationProfile。

### ACM authoring and artifact evaluation

- https://authors.acm.org/binaries/content/assets/publications/taps/acm_layout_submission_template.pdf
- https://github.com/acmsigsoft/artifact-evaluation

借鉴：统一母稿/模板、可访问性、目标 publication 指令，以及工件 README、安装、运行、claim-to-artifact、许可证、自包含和不可变归档要求。

### Journal of Open Source Software author/reviewer guidance

- https://joss.readthedocs.io/en/latest/submitting.html
- https://joss.readthedocs.io/en/latest/paper.html
- https://joss.readthedocs.io/en/latest/review_checklist.html

借鉴：软件论文必须有真实研究软件、可浏览源码、许可证、文档、测试、明确 research application 和与软件同仓库的稿件。没有实际软件时，Synaisthesis 禁止选择 JOSS Profile 的 submission-candidate 状态。

### 纯数学理论内置期刊官方规范

- Annals of Mathematics — https://annals.math.princeton.edu/submission-guidelines
- Journal of the American Mathematical Society — https://www.ams.org/publications/journals/journalsframework/jamssubmit
- Inventiones mathematicae — https://link.springer.com/journal/222/submission-guidelines
- Acta Mathematica — https://www.mittag-leffler.se/publications/acta-mathematica/submission-of-manuscripts/

借鉴：初稿格式、LaTeX/图源、摘要与分类信息、并行投稿限制、作者责任及具体投稿材料。期刊声望与范围说明只用于 `scope_fit` 提示，不能由系统推导录用概率或“顶刊水平”。

### 软件/系统工程内置期刊官方规范

- IEEE Transactions on Software Engineering / IEEE Computer Society author resources — https://www.computer.org/publications/author-resources
- ACM Transactions on Software Engineering and Methodology / ACM authoring template — https://authors.acm.org/binaries/content/assets/publications/taps/acm_layout_submission_template.pdf
- Empirical Software Engineering — https://link.springer.com/journal/10664/submission-guidelines
- Journal of Systems and Software — https://www.sciencedirect.com/journal/journal-of-systems-and-software/publish/guide-for-authors

借鉴：目标 publication 模板与声明、实证设计和可复现材料、结果证据、软件/数据引用、作者与 AI 使用责任。四个内置工程期刊面向软件/计算系统；其他工程领域必须返回 `SCOPE_MISMATCH` 并使用 `CUSTOM_VENUE`，不能硬套。

### arXiv 预印本规范

- Submission Guidelines — https://info.arxiv.org/help/submit/index.html
- TeX Submission Guidelines — https://info.arxiv.org/help/submit_tex.html

arXiv 是经 moderation 的预印本仓储平台，不是同行评审期刊。Profile 必须使用 `venue_kind = PREPRINT_REPOSITORY`，并检查分类、endorsement、许可、元数据、TeX 源闭包、图件、文件名和可编译性；平台不能把 `ARXIV_PACKAGE_READY` 表述为期刊投稿、同行评审或录用。

以上官方页面在 2026-08-14 用于建立初始 Registry。它们共同支持 `03B` 与 `03C` 的方法结构，但不可能形成“一篇稿件同时满足所有期刊”的静态保证。权威规则始终是用户选择时刷新后的目标期刊/平台官方 author guide；平台必须保存访问时间、模板 checksum、逐项合规矩阵和需要作者亲自确认的字段。


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
4. 迁 S0–S4；
5. 加 RQ0–RQ4 后迁 S5；
6. 迁 S6–S10；
7. 迁 Council；
8. 关闭旧插件执行逻辑；
9. 加平台调 Codex Worker。

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

## 18. v2.1：Codex 指令忠实传递层

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

## 19. v2.2：早期形式化、新颖性资格与机械执行合同

新增：

- S4 后、S5 前的强制 RQ0–RQ4 子流程；
- 高能力 Early Formalizer Profile 或标准化外部模型导入；
- 学术研究与成熟工程项目的双类最近邻检索；
- 以数学公式为核心的 EarlyFormalizationBundle；
- 绑定具体 formula/spec hash 的用户审查；
- 理论 50 + 应用 50 的百分制新颖性规则；
- 两个隔离 Reviewer 逐项取较小值；
- 有效总分 70 自动继续，69 及以下或 INCONCLUSIVE 交还用户；
- `19_MECHANICAL_EXECUTION_CONTRACT.md` 的稳定 Task ID、文件/符号/命令/停止条件；
- 分册、汇编版与 manifest 的同步和完整性规则；
- 修正重复章节编号与 manifest 自引用 hash 缺陷。

## 20. v2.3-draft：形式化可行性分流与工程转化/论文工作流

新增：

- RQ2F 理论/工程适配的确定性谓词、双评估和保守聚合；
- 纯数学理论不适配但工程可尝试时的强制 `ENGINEERING_ROUTE_DECISION`；
- 用户选择工程路线后，以 I/O、状态、要求、质量阈值、架构图和追踪关系为核心的 `EngineeringConceptBundle`；
- 理论 50 + 应用 50 与工程 60 + 应用 40 两套不可混用的新颖性 policy；
- 工程新颖性达到 70 后自动进入 ENG0，而不是进入理论型 S5；
- ENG0–ENG10：Mission/ConOps、Requirements、Trade Study、Architecture、Mechanical Blueprint、V&V、应用/扩展路线、PublicationProfile、MasterManuscript、独立审计与工程交付包；
- 文本图源 + 渲染图 + 稳定 ID 回链；
- `BLUEPRINT_ONLY` 与需显式授权的 `BUILD_AND_EVALUATE` 分流；
- “期刊中立母稿 + 目标期刊官方 Profile + 适配稿 + 合规矩阵”，替代不可能验证的“单稿天然符合所有期刊”；
- 每个论文主张到真实 Evidence Receipt 的追踪，禁止虚构实现与实验结果；
- 与上述对象对应的数据、API/CLI/MCP、Gate、配置、测试、路线和机械 Task 合同。

该设计已由用户于 2026-08-14 明确整体采纳，并由 v2.4 的双路线论文交付补丁一并冻结。它仍只代表蓝图语义，不代表任何 ENG 功能已经实现。

## 21. v2.4：双路线论文母稿、正式稿决策与内置 Profile

在已采纳的 v2.3 基础上新增并冻结：

- 纯数学理论路线的固定最终交付物 `TheoryMasterManuscript`、证明依赖图及 theorem/claim→statement/proof/evidence/citation 追踪矩阵；
- 工程与理论路线统一采用“母稿生成 → 独立审计 → 先交付用户 → `FORMAL_MANUSCRIPT_DECISION`”顺序；
- 用户可选择 `KEEP_MASTER_ONLY`、`WRITE_FORMAL_MANUSCRIPT`、`REVISE_MASTER` 或 `PAUSE`，且无响应不得默认为编写正式稿；
- 只有选择 WRITE 后才开放 `PUBLICATION_PROFILE_SELECTION`，期刊适配不得反向改变理论陈述、工程要求、证据范围或失败记录；
- 理论路线内置 Annals of Mathematics、JAMS、Inventiones mathematicae、Acta Mathematica 四种期刊 Profile；
- 软件/系统工程路线内置 IEEE TSE、ACM TOSEM、Empirical Software Engineering、Journal of Systems and Software 四种期刊 Profile；
- 数学与工程各有独立 arXiv Profile，并将 arXiv 明确定义为 `PREPRINT_REPOSITORY` 而非期刊；
- 非软件工程项目与四种工程 Profile 不匹配时返回 `SCOPE_MISMATCH`，改用 `CUSTOM_VENUE`；
- 官方指南、模板 hash、访问时间、freshness、机器检查与作者确认字段被纳入可刷新 `PublicationProfile`；
- 投稿、上传、版权、作者排序和对外通信仍需独立 Human Gate，不因生成正式稿而自动授权。

v2.4 是 2026-08-14 起的正式文档基线；它不表示这些产品能力已经实现。


---

<!-- SOURCE: 16_OPENCODE_DEEPSEEK_DEVELOPMENT_PROFILE.md -->

# 16 — OpenCode / 官方 DSH + DeepSeek 工程开发 Profile

## 1. 本文档定位

本文档只规定“使用 OpenCode 或 DeepSeek 官方 DSH，并以 DeepSeek 作为主要工程模型开发 Synaisthesis 时的工程行为”，不替代产品架构规范，也不把 OpenCode、DSH 或 DeepSeek 写入 Synaisthesis Core 的不可替换依赖。

## 2. 工作区

- 工程根目录：`E:\Synaisthesis`
- OpenCode 与 DeepSeek 官方 DSH 均应从工程根目录启动；一次 WorkUnit 只由一个主客户端持有写权限，避免两个客户端并发修改同一工作树。
- `AGENTS.md` 为工程行为规则入口。
- `docs/blueprint/` 保存本 V2 全套蓝图。
- `IMPLEMENTATION_STATUS.md` 保存真实当前实现状态。
- `TASKS.md` 保存待执行的机械任务。

## 3. 推荐工程客户端角色

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
1. identify the exact stable Task ID / Milestone from `docs/blueprint/19_MECHANICAL_EXECUTION_CONTRACT.md`;
2. read only the authoritative sections listed for that Task;
3. write a complete `WorkUnitContract` including allowed/forbidden files, symbols, I/O, state/events, invariants, errors, commands, acceptance and stop conditions;
4. confirm all Task preconditions and Human Gates;
5. state architectural risks.

If the Task has no complete contract, sources conflict, or a required field is undefined, report `BLUEPRINT_GAP` or `BLUEPRINT_CONFLICT` and stop before code changes.

After modifying code:
1. run the required real checks;
2. report commands and exit results;
3. show a diff summary;
4. update `IMPLEMENTATION_STATUS.md` when appropriate;
5. do not start the next Task automatically.

The modular files in `docs/blueprint/` are authoritative. The consolidated blueprint is generated and must not be edited independently. Any blueprint change must follow the synchronization and integrity checks in document 19.

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

## Blueprint baseline
`<manifest.version>` / manifest verification timestamp（候选基线必须显式标记 pending；只有完成所需 Human Gate 后才能标记 frozen）

## Active work unit
- Stable Task ID: `NOT_STARTED`
- WorkUnitContract: `NONE`

## Environment
- Project root: `E:\Synaisthesis`
- Primary engineering client: OpenCode or official DeepSeek DSH
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
- When blueprint files change: verify manifest size/hash and consolidated SOURCE order.

## Known failures
- None.

## Pending Human Gates
- None.

## Next allowed task
- Initialize repository skeleton according to the V2 blueprint.

## Notes
Only record work that actually exists in the repository. Do not infer completion from plans or model statements.


---

<!-- SOURCE: 19_MECHANICAL_EXECUTION_CONTRACT.md -->

# 19 — 蓝图机械执行合同与审计结论

## 1. 审计结论

审计日期：2026-08-13。

审计对象：`docs/blueprint/`、根目录 `README.md`、`AGENTS.md`、`IMPLEMENTATION_STATUS.md`、`TASKS.md`，以及当前 M0 源码、配置、测试和 CI。

修补前结论：**架构可实现，但不足以让多数开发者或主流 AI 无歧义地机械完成。** 已确认的缺口：

1. 自然语言设计之后没有强制的早期形式化与新颖性资格状态机；
2. `novelty_status` 有枚举但没有固定评分、证据门和自动/人工路由；
3. `09` 给出 Stage，但没有统一规定每个 Task 的文件、符号、前置条件、命令、通过标准和停止条件；
4. 分册、汇编版和 manifest 的权威关系及同步方法不够明确；
5. manifest 记录自身 hash，形成无法稳定满足的自引用完整性条件；
6. 个别章节编号重复，Stage 0.5 的依赖含义不清。

本轮修补后的目标结论：**蓝图足以让执行者按一个有界 Task 一次一项地机械实现；仍禁止用一条任务实现整个蓝图。** 机械可执行不表示环境、外部凭据、产品价值或科学结论已经验证。

## 2. 权威源与读取顺序

### 2.1 权威分册

分册是规范源。执行一个 Task 时按以下顺序读取：

1. `00A_PROJECT_IDENTITY_AND_CURRENT_ENVIRONMENT.md`；
2. `CURRENT_DECISIONS.md`；
3. 本 Task 对应的领域分册；
4. `06_DATA_MODEL_AND_STATE_MACHINE.md`；
5. `07_FUNCTION_API_AND_MCP_CONTRACTS.md`；
6. `08_SECURITY_AUTHORIZATION_ISOLATION.md`；
7. `09_MECHANICAL_IMPLEMENTATION_PLAN.md`；
8. `10_TEST_EVAL_AND_OBSERVABILITY.md`；
9. `12_PROJECT_TREE_AND_CONFIG.md`；
10. 本文件；
11. 根目录 `IMPLEMENTATION_STATUS.md` 和 `TASKS.md`。

早期形式化、可行性分流或新颖性相关 Task 必须额外读取 `03_INCUBATOR_STAGE_CONTRACTS.md` 与 `03A_EARLY_FORMALIZATION_AND_NOVELTY_GATE.md`。ENG0–ENG10、机械工程蓝图、图示、V&V、应用/扩展路线或工程论文相关 Task 必须额外读取 `03B_ENGINEERING_TRANSLATION_AND_PUBLICATION_WORKFLOW.md`。任何理论论文、工程论文、母稿审计、正式稿决策、期刊/arXiv Profile、Venue Adapter 或 ComplianceMatrix Task 还必须读取 `03C_THEORY_PUBLICATION_AND_DUAL_TRACK_VENUE_PROFILES.md`。

### 2.2 生成物

`Synaisthesis_V2_完整工程蓝图_2026-08-13.md` 是分册的机械汇编版，便于人类阅读，不是单独编辑源。`Synaisthesis_V2_Blueprint_Manifest_2026-08-13.json` 记录分册与生成物的大小和 SHA-256，但不得记录 manifest 自身 hash。

分册与汇编内容冲突时，以分册为准并停止实现，先重建汇编与 manifest。不得在两处分别手工作不同语义修改。

## 3. `WorkUnitContract`

任何代码实现、测试、迁移或运行配置变更在开始前必须有一个且只有一个 `WorkUnitContract`。缺任一字段时状态为 `BLUEPRINT_GAP`，不得修改代码。

```text
task_id
milestone_id
objective
authoritative_sections[]
preconditions[]
allowed_files[]
forbidden_files[]
symbols_to_add_or_change[]
input_contracts[]
output_contracts[]
state_transitions[]
domain_events[]
invariants[]
error_paths[]
focused_tests[]
focused_commands[]
full_commands[]
acceptance_criteria[]
stop_conditions[]
rollback_boundary
status_document_update
```

规则：

- 一个 Task 默认修改 1–5 个生产文件；超过 5 个必须拆分，测试与迁移文件不计入该上限但仍须列出；
- 一个 Task 只交付一个可独立验收的纵向能力或一个基础层不变量；
- 不允许“实现 Stage N”作为 Task 标题；必须使用下文稳定 Task ID；
- 新增公开接口、Schema 字段、Event 或状态时，同一 Task 必须包含相应测试；
- 需要新生产依赖、公开接口变化、核心语义变化或跨 Task 重构时立即停止并回到规划；
- 未运行的命令必须记录原因，不得推断为 PASS。

## 4. 机械执行算法

执行者必须按固定顺序：

1. 从 `IMPLEMENTATION_STATUS.md` 读取当前 Milestone、当前 Task、已验证命令和唯一 `Next allowed task`；
2. 在下文任务图找到 Task ID，读取列出的分册；
3. 检查前置 Task 与 Human Gate；
4. 将该 Task 扩写为完整 `WorkUnitContract`；
5. 只读取并修改 `allowed_files`；
6. 先写或更新失败测试；
7. 做最小实现，不进行无关重构或批量格式化；
8. 运行 focused commands；
9. 运行项目通用完整检查；
10. 直接检查 diff、完整相关代码、错误路径和验收标准；
11. 只有核验 PASS 才更新 `IMPLEMENTATION_STATUS.md` 与 `TASKS.md`；
12. 停止，不自动开始下一 Task。

项目通用完整检查以当前仓库实际命令为准：

```text
uv run ruff check .
uv run ruff format --check .
uv run basedpyright
uv run pytest
```

外部工具 Task 还必须运行其真实适配器 smoke test；没有 Lean/Z3/Docker/Codex 环境时只能给 BLOCKED，不能用 Fake 结果替代。

## 5. 稳定任务图

下列 Task ID 是推荐的最小机械切片。每个条目的“文件”是允许修改的生产模块；测试文件使用相同主题名放入规定测试目录。

### M0 — 已完成的工程底座

#### `M0.QA.BASELINE`

- 前置：无。
- 文件：`pyproject.toml`、`src/synaisthesis/version.py`、`src/synaisthesis/config/*`、`src/synaisthesis/interfaces/cli/main.py`、`.github/workflows/ci-core.yml`。
- 验收：版本、严格配置加载、CLI 与四条通用检查通过。
- 停止：基线测试不通过时不得进入 M1。

### M1 — 领域模型、Event Store、Artifact Store

#### `M1.1.DOMAIN.PRIMITIVES`

- 前置：`M0.QA.BASELINE` PASS。
- 文件：`domain/enums.py`、`domain/errors.py`、`domain/event.py`、`domain/policies.py`。
- 符号：所有稳定 Enum、`DomainEvent`、领域错误、版本/幂等不变量。
- 验收：未知 Enum 被拒绝；事件 payload 可稳定序列化；领域层不导入 FastAPI/MCP/数据库。
- focused：`uv run pytest tests/unit/domain/test_primitives.py`。
- 停止：蓝图中同名状态含义冲突。

#### `M1.2.DOMAIN.AGGREGATES`

- 前置：M1.1。
- 文件：`domain/project.py`、`domain/research_spec.py`、`domain/stage.py`、`domain/revision.py`、`domain/evidence.py`。
- 符号：Project、ResearchSpec、StageRun、Revision、Evidence 及不可变规则。
- 验收：确认后的 Spec 不能原地覆盖；Revision/Evidence 撤回保留历史。
- focused：`uv run pytest tests/unit/domain/test_aggregates.py`。
- 停止：必须引入当前计划外公开字段或更改事件语义。

#### `M1.3.STORAGE.EVENT_ARTIFACT`

- 前置：M1.2。
- 文件：`storage/database.py`、`storage/hashing.py`、`storage/artifact_store.py`、`storage/repositories/event_repository.py`、首个 migration。
- 符号：`init_database`、`append_domain_event`、`save_artifact`、`verify_artifact_hash`。
- 验收：事件顺序稳定；Artifact 内容寻址；缺失/篡改可检测；migration 可升级和降级开发数据库。
- focused：`uv run pytest tests/integration/storage/test_event_artifact_store.py`。
- 停止：迁移需要删除历史数据或静默重建数据库。

#### `M1.4.PROJECT.VERTICAL_SLICE`

- 前置：M1.3。
- 文件：`application/project_service.py`、`storage/repositories/project_repository.py`、`interfaces/cli/commands/project.py`。
- 验收：CLI 创建项目后产生 Project、Artifact 和 DomainEvent，并可重新读取。
- focused：`uv run pytest tests/integration/test_project_vertical_slice.py`。
- 停止：状态无法从 Event/Repository 恢复。

### M2 — Durable Incubator 与早期研究资格

#### `M2.1.S0_S1.CONTRACTS`

- 前置：M1.4。
- 文件：`domain/stage.py`、`agents/schemas.py`、`application/incubation_service.py`、`prompts/incubator/s0*`、`prompts/incubator/s1*`。
- 验收：S0 原文保留；S1 必填字段齐全且只有真实用户事件可确认。
- focused：`uv run pytest tests/golden/test_s0_s1.py`。
- 停止：无法保存原文 hash 或用户确认来源。

#### `M2.2.S2_S4.CONTRACTS`

- 前置：M2.1。
- 文件：沿用 `domain/stage.py`、`agents/schemas.py`、`application/incubation_service.py` 与 S2–S4 Prompt Assets。
- 验收：机制、相关研究和范围输出通过 Schema；S3 同时生成学术与工程查询种子；S4 用户确认后派生 `NATURAL_LANGUAGE_DESIGN_READY`。
- focused：`uv run pytest tests/golden/test_s2_s4.py`。
- 停止：S1/S4 hash 未绑定或关键应用字段缺失。

#### `M2.3.RQ.DOMAIN`

- 前置：M2.2；必须读取 `03A`。
- 文件：`domain/qualification.py`、`domain/novelty.py`、`domain/gate.py`、`domain/enums.py`、migration。
- 符号：RQ0–RQ4 Artifact、可行性/route、状态、Gate、Event 与两套评分 Schema。
- 验收：未通过 RQ 不可转 S5/ENG0；两套总分函数对边界 69/70 确定且不可混用；记录不可变。
- focused：`uv run pytest tests/unit/domain/test_research_qualification.py`。
- 停止：评分权重或 70 分门槛与 `03A` 不一致。

#### `M2.4.RQ.FAKE_RETRIEVAL`

- 前置：M2.3。
- 文件：`providers/prior_art/base.py`、`providers/prior_art/fake.py`、`providers/prior_art/normalization.py`、`application/qualification_service.py`。
- 验收：Fake 学术/工程近邻可去重、排序、计算 coverage；不足门槛时不能 COMPLETE。
- focused：`uv run pytest tests/contract/prior_art/test_fake_prior_art.py`。
- 停止：相似度无证据引用或外部文本可触发 mutation。

#### `M2.4A.RQ.FEASIBILITY`

- 前置：M2.4；必须读取 `03A` RQ2F。
- 文件：`domain/qualification.py`、`agents/engineering_feasibility_assessor.py`、`agents/early_formalizer.py`、`application/qualification_service.py`、`prompts/formalization/feasibility*`、migration。
- 符号：TFO–TFP、EFS–EFF、`FormalizationFeasibilityAssessment`、`ENGINEERING_ROUTE_DECISION`、`FORMALIZATION_FEASIBILITY_DECISION`。
- 验收：双评估按 FAIL > UNKNOWN > PASS 聚合；理论 false/工程 true 只开用户 Gate；任何非用户 actor 不能选择工程路线。
- focused：`uv run pytest tests/unit/application/test_formalization_feasibility.py tests/golden/test_engineering_route_gate.py`。
- 停止：谓词缺来源、UNKNOWN 被当 PASS、模型自动选择工程路线或覆盖 S1/S4。

#### `M2.5.RQ.FORMALIZATION`

- 前置：M2.4A。
- 文件：`agents/early_formalizer.py`、`prompts/formalization/early*`、`application/qualification_service.py`、`agents/schemas.py`。
- 验收：能力 Profile 不合格即阻断；核心命题均为公式；符号、语义映射、失败公式与 hash 验证通过；只产生 candidate。
- focused：`uv run pytest tests/golden/test_early_formalization.py`。
- 停止：用自然语言段落代替核心公式或写入证明状态。

#### `M2.5B.RQ.ENGINEERING_CONCEPT`

- 前置：M2.4A，且当前 Gate 决定为绑定 hash 的 `TRY_ENGINEERING_PROJECT`。
- 文件：`domain/qualification.py`、`agents/engineering_feasibility_assessor.py`、`application/qualification_service.py`、`prompts/engineering/concept*`、`agents/schemas.py`。
- 符号：`EngineeringRouteSelection`、`EngineeringConceptBundle`、`EARLY_ENGINEERING_CONCEPT_REVIEW`。
- 验收：I/O、状态、要求谓词、质量阈值/未决标记、架构图候选、追踪与失败/恢复义务完整；只产生 candidate。
- focused：`uv run pytest tests/golden/test_engineering_concept.py tests/unit/application/test_engineering_concept_review.py`。
- 停止：工程构想伪装成定理、虚构阈值、写入 IMPLEMENTED/VALIDATED/NOVEL 或 route hash 不匹配。

#### `M2.6.RQ.NOVELTY_POLICY`

- 前置：理论路线 M2.5；工程路线 M2.5B。
- 文件：`application/novelty_service.py`、`domain/novelty.py`、`agents/novelty_reviewer.py`、`agents/auditor.py`。
- 验收：独立评分逐项取较小值；理论 policy 为 50+50 并在 `>=70` 自动 S5，工程 policy 为 60+40 并在 `>=70` 自动 ENG0；`<70`/INCONCLUSIVE 打开用户 Gate；所有项有近邻引用。
- focused：`uv run pytest tests/unit/application/test_novelty_service.py tests/golden/test_novelty_gate.py`。
- 停止：单 Reviewer、覆盖不完整、不独立结果或 route/policy 不匹配仍被自动放行。

#### `M2.7.S5.VERTICAL_SLICE`

- 前置：M2.6 或有效用户 override。
- 文件：S5 Schema/Prompt、`application/incubation_service.py`、`orchestration/nodes/incubator_nodes.py`。
- 验收：RQ 前置被强制；DEMONSTRATED 与 EXECUTED 分离；恢复后状态一致。
- focused：`uv run pytest tests/integration/test_qualification_to_s5.py`。
- 停止：任何路径可绕过 RQ3/RQ4。

#### `M2.8.ENGINEERING.WORKFLOW_DOMAIN`

- 前置：M2.6 的工程 route；必须读取 `03B`。
- 文件：`domain/engineering.py`、`domain/requirements.py`、`domain/architecture.py`、`domain/traceability.py`、`domain/publication.py`、`domain/gate.py`、`domain/event.py`、migration。
- 符号：ENG0–ENG10、Mission/ConOps/Requirement/TradeStudy/Architecture/Blueprint/V&V/Roadmap/Publication/Delivery Artifact 与状态事件。
- 验收：只有工程 novelty qualified 或绑定 override 可创建 ENG0；阶段 Artifact 不可变；S1/S4 或上游 hash 变化触发确定回归。
- focused：`uv run pytest tests/unit/domain/test_engineering_workflow.py tests/unit/domain/test_engineering_traceability.py`。
- 停止：工程路线可绕过用户 route 决定，或所有阶段写入单一不透明 JSON。

#### `M2.9.ENGINEERING.REQUIREMENTS_ARCHITECTURE`

- 前置：M2.8。
- 文件：`application/engineering_design_service.py`、`application/engineering_traceability_service.py`、`orchestration/nodes/engineering_nodes.py`、`providers/prior_art/*`、`renderers/*`、`prompts/engineering/*`。
- 验收：ConOps source coverage 100%；Critical requirements 都有阈值/验收/验证方法；Trade Study 硬淘汰未覆盖 Critical requirement 的方案；图有文本源、SVG 和稳定 ID；Architecture Gate 绑定三类 hash。
- focused：`uv run pytest tests/unit/application/test_engineering_requirements.py tests/integration/test_engineering_architecture.py tests/contract/renderers/test_diagram_renderers.py`。
- 停止：存在 Critical 未决阈值、事后改权重、图片成为唯一事实源或重大架构未由用户批准。

#### `M2.10.ENGINEERING.MECHANICAL_BLUEPRINT`

- 前置：M2.9 的 Architecture Baseline 已批准。
- 文件：`application/engineering_design_service.py`、`domain/engineering.py`、`domain/traceability.py`、`prompts/engineering/blueprint*`、`storage/export_bundle.py`。
- 验收：requirement→design→task→test Critical 链 100%；每个 WorkUnit 有文件/符号/动作/测试/验收/停止；无未决产品/架构决策；69/70 无关的普通实现选择不能被随意上抛。
- focused：`uv run pytest tests/unit/application/test_blueprint_completeness.py tests/golden/test_mechanical_engineering_blueprint.py`。
- 停止：模糊动作、接口无 Schema、任务无停止条件、图示断链或 Blueprint Gap 被当 PASS。

#### `M2.11.ENGINEERING.PUBLICATION_DELIVERY`

- 前置：M2.10；构建/实验只有另行 `PROTOTYPE_EXECUTION_AUTHORIZATION` 才能进入执行分支。
- 文件：`application/publication_service.py`、`application/engineering_delivery_audit_service.py`、`publication/*`、`prompts/publication/*`、`storage/export_bundle.py`。
- 验收：BLUEPRINT_ONLY 不产生完成态结果；每个论文结果 claim 绑定真实 receipt；先生成、独立审计并交付 EngineeringMasterManuscript，再打开 `FORMAL_MANUSCRIPT_DECISION`；KEEP_MASTER_ONLY 可完整交付，只有 WRITE 才允许 Profile Selection/Venue Adapter；指南 freshness、route/scope、作者输入、arXiv 身份、JOSS 软件门和 manifest/checksums 可验证；独立 Auditor 无 Major。
- focused：`uv run pytest tests/unit/application/test_publication_evidence_policy.py tests/contract/publication/test_profiles.py tests/integration/test_engineering_delivery_export.py`。
- 停止：虚构结果、母稿交付前选择 Profile、无用户 WRITE 决策却生成正式稿、把 arXiv 写成期刊、模型代填作者责任、过时指南仍 PASS、scope mismatch 仍适配、无软件却生成 JOSS submission candidate，或 Auditor 审自己初稿。

### M3 — S6–S10 与成熟门

#### `M3.1.S6_S7.THEORY_FORMAL_PLAN`

- 前置：M2.7。
- 文件：`domain/stage.py`、`agents/schemas.py`、`application/incubation_service.py`、S6/S7 Prompt Assets。
- 验收：S7 消费已批准早期公式但生成独立 FormalizationPlan；语义变化回退 S1/S4/RQ。
- focused：`uv run pytest tests/golden/test_s6_s7.py`。
- 停止：把早期形式化误标成 Tool-verified。

#### `M3.2.S8_S10.HANDOFF`

- 前置：M3.1。
- 文件：S8–S10 Schema/Prompt、`application/incubation_service.py`、`orchestration/nodes/incubator_nodes.py`。
- 验收：S8 仅 1–2 轮 readiness attack；Handoff 每个任务有 I/O/门槛；成熟门检查 RQ 状态。
- focused：`uv run pytest tests/integration/test_incubator_s6_s10.py`。
- 停止：S8 启动正式十轮 Council。

### M4 — Claim Compiler 与冻结

#### `M4.1.CLAIM.COMPILER`

- 前置：M3.2。
- 文件：`domain/claim.py`、`application/claim_compiler_service.py`、`agents/schemas.py`、`storage/repositories/claim_repository.py`。
- 验收：MIXED 被拆分；每个 Claim 有对象域、量词、证伪见证和 verifier。
- focused：`uv run pytest tests/unit/application/test_claim_compiler.py`。
- 停止：无法形成无歧义原子命题。

#### `M4.2.CLAIM.FREEZE`

- 前置：M4.1。
- 文件：`domain/claim_contract.py`、`application/claim_compiler_service.py`、`domain/gate.py`。
- 验收：冻结 hash 覆盖语义、工具、预算和策略；修改只生成新版本。
- focused：`uv run pytest tests/integration/test_claim_freeze.py`。
- 停止：冻结可被原地修改。

### M5 — ActionBroker、Gate 与委托

#### `M5.1.GATE.ACTION.POLICY`

- 前置：M4.2。
- 文件：`domain/action.py`、`domain/gate.py`、`domain/receipt.py`、`application/action_service.py`、`application/gate_service.py`。
- 验收：模型不能批准；风险与 Semantic Delta 的自动/Gate/拒绝路由确定；Receipt 缺 hash 失败。
- focused：`uv run pytest tests/security/test_action_gate_policy.py`。
- 停止：授权主体或风险分类无法确定。

### M6 — 模型 Provider 与隔离

#### `M6.1.LLM.PROVIDER`

- 前置：M5.1；新增生产依赖需单独获准。
- 文件：`providers/llm/base.py`、`providers/llm/fake_provider.py`、`providers/llm/structured_output.py`、`providers/llm/usage.py`。
- 验收：Provider 无关；结构错误不写领域状态；tokens/cost/hash 可追踪。
- focused：`uv run pytest tests/contract/llm/test_provider_contract.py`。
- 停止：业务逻辑绑定供应商。

#### `M6.2.ROLE.ISOLATION`

- 前置：M6.1。
- 文件：`domain/isolation.py`、`application/council_service.py`、`agents/supporter.py`、`agents/opponent.py`、`agents/independent_reviewer.py`。
- 验收：Phase A 不可见双方；同家族标记 degraded；违规阻断。
- focused：`uv run pytest tests/security/test_role_isolation.py`。
- 停止：无法证明 visibility bundle 来源。

#### `M6.3.RQ.REAL_MODELS`

- 前置：M6.1、M2.6。
- 文件：`providers/llm/router.py`、`agents/early_formalizer.py`、`agents/novelty_reviewer.py`、相关配置。
- 验收：能力评估决定 RQ0；两异构 Reviewer 可产生独立 scorecard；Fake 路径仍可 CI。
- focused：`uv run pytest tests/contract/llm/test_qualification_roles.py`；真实 smoke 仅手动运行。
- 停止：没有能力评估证据却标记 ADVANCED。

### M7 — Fake Council

#### `M7.1.COUNCIL.STATE_GRAPH`

- 前置：M6.2。
- 文件：`orchestration/state.py`、`orchestration/graph_builder.py`、`orchestration/nodes/council_nodes.py`、`application/council_service.py`、`orchestration/checkpointing.py`。
- 验收：有效轮、10 轮、checkpoint、pause/resume、Gate 恢复均由 Fake 端到端测试证明。
- focused：`uv run pytest tests/integration/test_fake_council.py`。
- 停止：无效轮被计数或重启后状态丢失。

### M8 — 确定性验证器

#### `M8.1.Z3.ADAPTER`

- 前置：M7.1。
- 文件：`verifiers/z3/*`、`verifiers/registry.py`。
- 验收：SAT/UNSAT/UNKNOWN 分离；witness 独立重验。
- focused：`uv run pytest tests/external/test_z3_adapter.py`。
- 停止：模型可注入任意 Python 或 UNKNOWN 变 PASS。

#### `M8.2.PYTHON.SANDBOX`

- 前置：M8.1。
- 文件：`verifiers/python/*`、`integrations/docker/policy.py`。
- 验收：无网络、无 secret、资源限制、超时和回执有效。
- focused：`uv run pytest tests/external/test_python_sandbox.py`。
- 停止：Docker 隔离不可验证。

#### `M8.3.LEAN.COMPILER`

- 前置：M8.2。
- 文件：`verifiers/lean/*`、`verifiers/registry.py`。
- 验收：真实 Lean 成功才写 E4；statement hash 变化退出 Proof Loop。
- focused：`uv run pytest tests/external/test_lean_adapter.py`。
- 停止：Lean 未真实调用或版本无法记录。

### M9 — 真实 Council

#### `M9.1.COUNCIL.REAL_VERTICAL_SLICE`

- 前置：M6.2、M8.3。
- 文件：`application/council_service.py`、Council/Verification/Repair/Semantic/Regression nodes。
- 验收：一个小 Claim 完成反例、修复、Semantic Gate、Lean、用户确认和 Bundle 事件链。
- focused：`uv run pytest tests/integration/test_real_council_smoke.py`；付费调用手动。
- 停止：无法区分环境失败、既有缺陷和本次缺陷。

#### `M9.2.THEORY.PUBLICATION_DELIVERY`

- 前置：M9.1；目标 Theory Revision 已冻结，所有 theorem/claim 都有 statement hash，Evidence 与未解决义务可枚举；必须读取 `03C`。
- 文件：`application/theory_publication_service.py`、`domain/publication.py`、`publication/theory_master_manuscript.py`、`publication/compliance.py`、`agents/theory_manuscript_auditor.py`、`prompts/publication/theory/*`、`storage/export_bundle.py`。
- 验收：TheoryMasterManuscript 包含定义/引理/定理/证明结构、证明依赖图、theorem/claim→statement/proof/evidence/citation 追踪和限制；独立审计无 Major 后先交付母稿；KEEP_MASTER_ONLY 完成交付；只有用户 WRITE 才进入 Profile Selection；Venue 适配不改变 statement hash、量词、假设、结论或 Evidence Scope。
- focused：`uv run pytest tests/unit/application/test_theory_master_manuscript.py tests/integration/test_theory_publication_delivery.py tests/golden/test_theory_claim_manuscript_trace.py`。
- 停止：伪造证明/引文、隐藏未解决义务、Auditor 审自己初稿、无用户 WRITE 决策生成正式稿，或任何适配造成理论语义变化。

### M0.5 — Codex 指令忠实通道（跨阶段门）

#### `M0.5.CODEX.FIDELITY`

- 前置：M1 领域/Event/Artifact 基础已存在；必须在 M10 开放任何外部 Codex mutation 前完成。
- 文件与细分任务完全按 `05A` §§7–25 和 `12` 的 Fidelity 目录执行；每个子任务仍限制 1–5 个生产文件。
- 验收：无可信 Hook/token 时 fail closed；prepare/commit、state version、idempotency、CommandReceipt、DisplayContract E2E 通过。
- focused：`uv run pytest tests/security/test_codex_fidelity.py tests/integration/test_prepare_commit.py`。
- 停止：平台无法取得原始指令或 mutation 可绕过 Gateway。

说明：编号 0.5 表示其 P0 安全优先级，不表示它必须先于 M1 的内部领域存储；其硬依赖位置是 M1 之后、M10 之前。

### M10–M12 — Codex 双向集成

#### `M10.CODEX.INBOUND`

- 前置：M0.5、M9.1。
- 文件：`interfaces/mcp/*`、plugin manifest/skills/hooks。
- 验收：Codex 经 Gateway 创建/查询/启动/处理 Gate/导出；MCP Inspector contract PASS。
- 停止：出现绕过 Fidelity Gateway 的 mutation。

#### `M11.CODEX.OUTBOUND`

- 前置：M10；安装 SDK 属单独依赖 Task。
- 文件：`integrations/codex/*`、`application/codex_delegation_service.py`、`orchestration/nodes/codex_nodes.py`。
- 验收：独立 worktree、受控文件、diff/test Receipt、适配器重验。
- 停止：Worker 可写主工作区或自称工具 PASS。

#### `M12.CODEX.RECURSION_GUARD`

- 前置：M11。
- 文件：`integrations/codex/recursion_guard.py`、profile、MCP auth/annotations。
- 验收：Operator→平台→Worker→平台路径返回 `REENTRANCY_BLOCKED`。
- 停止：origin chain 或 delegation depth 不可验证。

### M13 — 生产级相邻工作与新颖性

#### `M13.1.ACADEMIC.PROVIDERS`

- 前置：M2.4、M6.1。
- 文件：`providers/prior_art/openalex.py`、`crossref.py`、`arxiv.py`、`deduplication.py`、`normalization.py`。
- 验收：查询/时间/分页/元数据回执可追溯；去重稳定；失败为结构化 Blocker。
- focused：`uv run pytest tests/contract/prior_art/test_academic_providers.py`。
- 停止：Provider ToS、凭据、限流或元数据含义未确定。

#### `M13.2.ENGINEERING.PROVIDERS`

- 前置：M13.1。
- 文件：`providers/prior_art/engineering_base.py`、`repository_registry.py`、`package_registry.py`、`official_docs.py`、`maturity.py`。
- 验收：近邻功能/应用排序有来源；成熟度至少两项证据；外部文本隔离。
- focused：`uv run pytest tests/contract/prior_art/test_engineering_neighbors.py`。
- 停止：把 popularity 当新颖性或无官方来源验证。

#### `M13.3.RQ.PRODUCTION_E2E`

- 前置：M6.3、M13.2。
- 文件：`application/qualification_service.py`、`application/novelty_service.py`、`orchestration/nodes/qualification_nodes.py`、API/CLI/MCP intent adapters。
- 验收：真实自然语言设计完成 route-aware RQ0–RQ4；理论/工程路线 70 分别自动进入 S5/ENG0；69 返回用户；导出包含来源、可行性矩阵、route、形式化、评分与 Gate。
- focused：`uv run pytest tests/integration/test_research_qualification_e2e.py`；真实 Provider smoke 手动。
- 停止：检索覆盖不完整却产生自动通过。

#### `M13.4.DUAL_TRACK.REFERENCE_AND_PUBLICATION_PROFILES`

- 前置：M13.3、M2.11、M9.2。
- 文件：`providers/prior_art/standards.py`、engineering providers、`publication/official_guide_fetcher.py`、`publication/profile_registry.py`、`publication/profile_provider.py`、venue/arXiv adapters、`configs/publication_profiles/*`。
- 验收：ENG3 的仓库/标准/参考架构证据可追溯；理论四刊、工程四刊和双路线 arXiv Profile 均有 route、venue_kind、官方 URL、访问时间、template checksum、freshness、scope、机器/人工检查；Profile contract tests 使用冻结 fixture，真实刷新 smoke 为手动；arXiv 永远是 PREPRINT_REPOSITORY；软件工程四刊对非软件项目返回 SCOPE_MISMATCH。
- focused：`uv run pytest tests/contract/prior_art/test_engineering_reference_set.py tests/contract/publication/test_official_profiles.py tests/contract/publication/test_arxiv_profiles.py`。
- 停止：违反 Provider ToS、把星标当成熟度、把非官方页面当权威规则、指南更新无法检测、Profile 跨 route、scope mismatch 仍适配，或把 arXiv 标为同行评审期刊。

### M14–M16 — UI、评估与增强

#### `M14.WEB.OBSERVABILITY`

- 前置：M13.3；先冻结 API Schema。
- 文件：按页面逐个纵向 Task，实现资格流程时先做 Design、Feasibility/Route Gate、Formula/Engineering Concept Review、Novelty Score/Gate、Engineering Trace/Blueprint/Publication 页面。
- 验收：UI 不自行派生状态；输入/route/Artifact hash、路线化分数、追踪、蓝图缺口、证据等级和合规状态可见。
- 停止：需要修改 Core 状态语义。

#### `M15.CASE_STUDY.EVAL`

- 前置：M14。
- 文件：`examples/real_project_case_study`、eval dataset/report、case-study docs。
- 验收：理论案例至少一次失败、修复、Gate、真实工具和 RQ0–RQ4；工程案例展示用户分流、ENG0–ENG10 BLUEPRINT_ONLY、无虚构结果；两个 Bundle 均可复算。
- 停止：案例包含未授权私密研究或不能复现。

#### `M16.ENHANCEMENT.<NAME>`

- 前置：v1.0 之前的稳定性门按 `13`；每个增强单独 ADR/Task。
- 验收：不破坏 Provider 抽象、Evidence Scope、Semantic Gate、RQ 门和旧 Bundle reader。
- 停止：跨越多个独立增强或需要不可逆迁移。

## 6. 文档与 Schema 的一对一映射

执行者不得自行发明同义对象：

| 规范对象 | 权威定义 | 目标代码 |
|---|---|---|
| S0–S10 Stage | `03` | `domain/stage.py`, `agents/schemas.py` |
| RQ0–RQ4 与理论/工程分流 | `03A` | `domain/qualification.py`, `domain/novelty.py` |
| ENG0–ENG10 与机械蓝图 | `03B` | `domain/engineering.py`, `domain/requirements.py`, `domain/architecture.py`, `domain/traceability.py` |
| 双路线论文母稿、正式稿决策与发布 Profile | `03C`（工程阶段顺序同时受 `03B` 约束） | `domain/publication.py`, `application/publication_service.py`, `application/theory_publication_service.py`, `publication/*` |
| Claim/Council | `04` | `domain/claim*.py`, `application/council_service.py` |
| Codex Integration | `05`, `05A` | `src/synaisthesis/integrations/codex*`, `src/synaisthesis/fidelity/*`, `plugin/hooks/*` |
| 表、状态、事件 | `06` | `domain/*`, `storage/*`, migrations |
| 函数/API/MCP | `07` | `application/*`, `interfaces/*` |
| Gate/安全 | `08` | `domain/gate.py`, `security/*` |
| 测试/指标 | `10` | `tests/*`, `telemetry/*`, `evals/*` |
| 目录/配置 | `12` | 实际目录与 `configs/*` |

同一对象若在不同分册字段不一致，禁止自行合并；记录 `BLUEPRINT_CONFLICT` 并修正文档后再实现。

## 7. 验收状态

### PASS

- WorkUnitContract 全字段齐全；
- focused 与适用的完整检查真实通过；
- 状态、事件、Schema、API 和测试与权威分册一致；
- 没有未说明风险或越界改动；
- `IMPLEMENTATION_STATUS.md` 记录真实结果。

### FAIL

- 核心验收未满足、测试失败或存在重大兼容/安全问题；
- 只允许一轮按明确修复合同进行的定向返工。

### BLOCKED

- 缺环境、凭据、外部服务、Human Gate、产品决策或蓝图一致性；
- 必须列出已完成证据与精确阻断条件，不能描述为 PASS。

## 8. 蓝图同步与完整性检查

每次修改分册后必须：

1. 按 manifest 的 `authoritative_order` 重建汇编版；
2. 在每个分册前保留唯一的 HTML `SOURCE` marker，其值必须等于分册文件名；
3. 更新所有受影响文件的 byte size 与 SHA-256；
4. manifest 不记录自身 hash，只记录 `self_integrity = EXCLUDED_SELF_REFERENCE`；
5. 检查 manifest 中每个文件存在且 hash/size 一致；
6. 检查汇编版的 SOURCE 顺序与 `authoritative_order` 一致；
7. 检索重复章节编号、失效相对链接、未定义状态和越权措辞；
8. 在 `IMPLEMENTATION_STATUS.md` 记录蓝图版本，但不把文档修补写成代码功能已实现。

## 9. 本轮最终任务目标清单

- [x] 自然语言设计完成状态有确定计算条件。
- [x] RQ0 要求高能力模型或标准化外部导入。
- [x] RQ1 同时检索相邻研究与成熟工程项目。
- [x] RQ2F 在纯理论不适配但工程适配时强制由用户选择修订或工程路线。
- [x] RQ2M 核心内容全部使用数学公式，并有语义/来源映射。
- [x] RQ2E 使用公式化 I/O、状态、要求、阈值与追踪关系固定工程概念。
- [x] RQ3M/RQ3E 将当前 Artifact 与简明解释交给用户审查。
- [x] RQ4M 计算理论 50 + 应用 50，RQ4E 计算工程 60 + 应用 40。
- [x] 有效总分 `>=70` 按 route 自动进入 S5 或 ENG0。
- [x] `<70` 或 `INCONCLUSIVE` 返回用户决定是否重新研究。
- [x] ENG0–ENG10 定义可机械执行蓝图、文本图源/渲染图、V&V、应用/扩展路线和证据约束论文。
- [x] 理论路线最终交付追加 TheoryMasterManuscript、证明依赖图和 theorem/claim→statement/proof/evidence/citation 追踪。
- [x] 两条路线均先审计并交付母稿，再由用户决定 KEEP、WRITE、REVISE 或 PAUSE；无响应不默认 WRITE。
- [x] 期刊合规使用 MasterManuscript + PublicationProfile + VenueAdapter + ComplianceMatrix，且适配不改变研究语义或证据。
- [x] 理论四刊、工程四刊与双路线 arXiv Profile 均有稳定 ID、route/scope/freshness/官方来源合同；arXiv 明确为预印本仓储平台。
- [x] BLUEPRINT_ONLY 不执行代码/实验且禁止虚构结果。
- [x] 状态、数据、接口、Gate、测试、配置、路线和任务图均有对应合同。
- [x] 分册、汇编版和 manifest 有可验证的同步规则。

---
