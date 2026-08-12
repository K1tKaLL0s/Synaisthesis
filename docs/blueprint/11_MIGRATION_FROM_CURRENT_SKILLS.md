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
