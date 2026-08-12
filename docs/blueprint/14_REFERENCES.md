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
