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
