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
