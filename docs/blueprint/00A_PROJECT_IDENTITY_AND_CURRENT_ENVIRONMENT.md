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
