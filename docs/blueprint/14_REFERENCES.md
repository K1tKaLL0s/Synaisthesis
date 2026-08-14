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
