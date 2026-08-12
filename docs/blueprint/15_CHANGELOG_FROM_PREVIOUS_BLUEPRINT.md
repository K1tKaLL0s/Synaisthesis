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
