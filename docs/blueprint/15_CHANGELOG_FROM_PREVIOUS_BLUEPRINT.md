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
