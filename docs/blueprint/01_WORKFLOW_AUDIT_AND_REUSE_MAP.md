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
