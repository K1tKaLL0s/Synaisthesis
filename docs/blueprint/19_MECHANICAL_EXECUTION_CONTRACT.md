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
