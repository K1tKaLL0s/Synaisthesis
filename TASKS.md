# TASKS

## Done

- [x] M0 — 仓库与质量底座（Stage 0）：工程骨架、get_version / load_settings / validate_settings、CLI 版本命令、CI、项目文件、ADR 0001、AGENTS.md N 盘记录
- [x] DOC-V2.2 — 蓝图机械执行审计与修补：RQ0–RQ4、理论/应用新颖性百分制、机械任务合同、汇编与 manifest 完整性规则（仅文档，不代表功能已实现）
- [x] DOC-V2.3 — 形式化可行性分流、强制工程路线用户决定、工程/应用新颖性与 ENG0–ENG10 机械蓝图/论文交付设计；已由用户整体采纳（仅文档，不代表功能已实现）
- [x] DOC-V2.4 — 纯理论论文母稿、双路线母稿审计/正式稿决策、理论四刊、工程四刊及双路线 arXiv Profile；已冻结为正式文档基线（仅文档，不代表功能已实现）
- [x] M1.1 — 领域基元（Stage 1 第 1 个 Task）：稳定枚举（严格拒绝未知值）、DomainError、DomainEvent（稳定序列化 + 内容 hash）、版本/幂等策略；领域层零 Web/数据库/MCP 依赖
- [x] M1.2 — 领域聚合：Project、ResearchSpec（确认后不可原地覆盖）、StageRun、Revision（不可变链）、Evidence（撤回保留历史）
- [x] M1.3 — 持久化底座：init_database、append_domain_event（稳定顺序）、save_artifact（内容寻址）、verify_artifact_hash（缺失/篡改可检测）、首个 Alembic migration（可升级/降级）；新增 sqlalchemy + alembic 生产依赖
- [x] M1.4 — Project 纵向切片（Stage 1 最后一个 Task）：CLI `project create` 产生 Project、Artifact、DomainEvent，`project show`/服务可从有序事件流完整重读；payload 缺失/篡改可检测并 fail closed（8 个集成测试，全套 81 passed）
- [x] M2.1 — S0–S1 合同（Stage 2 第 1 个 Task）：S0 SeedRecord 原文逐字节保留 + raw_hash 可复算校验；S1 NaturalLanguageSpec 13 必填字段 Schema 强制、验证器判定，确认只接受真实用户事件并落库 provenance；evaluate_stage_gate 按 Schema + 验证器 + 用户确认计算；s0/s1 Prompt Asset（14 个 golden 测试，全套 95 passed）
- [x] M2.2 — S2–S4 合同与 NATURAL_LANGUAGE_DESIGN_READY 派生（Stage 2 最后一个 Task）：MechanismSketch/PriorWorkMap/ResearchScopeSpec Schema 与验证器；S3 学术+工程双查询种子；S4 真实用户确认并绑定 S1/S4 hash；事件流派生设计完成门并推进 Project 生命周期；s2/s3/s4 Prompt Asset（18 个 golden 测试，全套 113 passed）
- [x] M2.3 — RQ 领域底座（Stage 2.5 第 1 个 Task）：RQ0–RQ4 不可变领域 Artifact；RQ2F 谓词保守聚合与固定真值表；理论 50+50 / 工程 60+40 两套评分 policy、逐项取小、69/70 固定路由；Gate 绑定与未通过 RQ 禁止转 S5/ENG0；19 个 RQ 事件名；migration 0002（22 个单元测试，全套 135 passed）
- [x] M2.4 — Fake 检索纵切片（Stage 2.5 第 2 个 Task）：PriorArtProvider Protocol、ExternalText 隔离、相似度证据引用、去重/排序/rank、Fake 学术+工程语料、coverage 门槛与 NeighborEvidenceSet 生成（14 个 contract 测试，全套 149 passed）
- [x] M2.4A — RQ2F 双评估与强制分流（Stage 2.5 第 3 个 Task）：TFO–TFP / EFS–EFF 双评估、FAIL>UNKNOWN>PASS 聚合、固定真值表、ENGINEERING_ROUTE_DECISION / FORMALIZATION_FEASIBILITY_DECISION 用户 Gate、真实用户工程路线选择与 hash 绑定（17 个测试，全套 166 passed）
- [x] M2.5 — RQ2M 早期数学形式化（Stage 2.5 第 4 个 Task）：能力门、10 类公式骨架、符号闭合/依赖无环/语义映射/失败公式/hash 验证、EARLY_FORMALIZATION_REVIEW 用户审批（11 个 golden 测试）
- [x] M2.5B — RQ2E 工程概念形式化（Stage 2.5 第 5 个 Task）：TRY_ENGINEERING_PROJECT hash 绑定、I/O/状态/要求谓词/未决阈值/架构图候选/追踪/失败恢复验证、EARLY_ENGINEERING_CONCEPT_REVIEW 用户审批（9 个测试；全套 186 passed）
- [x] M2.6 — Novelty 路线审验（Stage 2.5 第 6 个 Task）：两个隔离 Reviewer/Auditor、逐项近邻证据、独立性与 route/policy 校验、理论/工程 69/70 路由、低分用户 Gate 与绑定 override（9 个测试，全套 195 passed）
- [x] M2.7 — S5 纵向切片（Stage 2.5 第 7 个 Task）：MinimalCaseBundle Schema/Prompt、RQ4M 前置强制、actually_executed/receipt 分离、事件溯源恢复一致、s5_qualification_node（7 个测试，全套 202 passed）
- [x] M2.8 — 工程工作流领域（Stage 2.6 第 1 个 Task，提交 `19be013`）：ENG0–ENG10 领域对象与状态事件（03B 全部阶段 Artifact）、ENG0 入口强制（用户 route/RQ3E/RQ4E 或绑定 override/S1·S4 hash 不变）、阶段 Artifact 不可变 + 内容 hash、S1/S4 与上游 hash 变化确定性回归、工程 Gate（架构评审/原型授权/母稿决策/Profile/交付验收）、requirements/architecture/traceability/publication 领域模块、migration 0004（66 个测试，全套 268 passed）
- [x] M2.9 — 需求与架构设计服务（Stage 2.6 第 2 个 Task，提交 `9d42022`）：ENG0–ENG4 事件溯源纵切片（charter/ConOps/Requirements Baseline/Trade Study/Architecture Baseline 全部持久化可重放）、ConOps source coverage 100%、Critical 阈值/验收/验证方法强制、工程深检索 5 类来源去重、Trade Study Critical 硬淘汰 + 权重冻结、确定性图源→SVG 渲染器（稳定 ID/双 hash/回执/断链）、Architecture Gate 三 hash 绑定且仅真实用户可批准、eng2/eng3/eng4 节点与节点前置、eng2/eng3/eng4 prompt assets（25 个测试，全套 293 passed）
- [x] M2.10 — 机械工程蓝图（Stage 2.6 第 3 个 Task，提交 `3070c49`）：ENG5 蓝图服务（未批准架构/三 hash 失配/追踪缺口/无停止条件 WorkUnit/上抛普通选择 全部 BLUEPRINT_GAP 或 ENGINEERING_ARCHITECTURE_REVIEW_REQUIRED）、Blueprint Completeness Gate 指标化、决策上抛范围规则（69/70 无关的普通实现选择不得上抛）、WorkUnit 14 项合同完备 golden、storage/export_bundle.py 确定性导出（manifest/checksums/篡改检测）、blueprint prompt asset（15 个测试，全套 308 passed）
- [x] M2.11 — 工程论文与交付（Stage 2.6 第 4 个 Task，提交 `3f88f46`）：ENG8 母稿服务（BLUEPRINT_ONLY 不产生完成态结果、claim 真实回执、作者输入 NEEDS_AUTHOR_INPUT）、独立母稿审计（不得审自己初稿、Major/Critical 阻断）、FORMAL_MANUSCRIPT_DECISION Gate（先审计交付后打开、仅用户决议、KEEP_MASTER_ONLY 完整合法）、ENG9 Profile Registry（8 个内置工程 Profile、profile_hash 内容绑定、freshness、scope-fit、arXiv 恒为 PREPRINT_REPOSITORY、JOSS 软件门、ComplianceMatrix）、ENG10 独立交付审计 + ENGINEERING_DELIVERY_ACCEPTANCE（manifest hash 绑定、变更即失效）+ 03B §13.3 readiness 全条件、导出包 role/checksums 扩展、eng8/eng10 prompt assets（31 个测试，全套 339 passed）
- [x] M3.1 — 理论路线 S6/S7（Stage 3 第 1 个 Task，提交 `275c9f9`）：S6 TheoryKernel（比较替代理论、保留反例、预测/解释分栏、核心概念变化回 S1/S4）、S7 FormalizationPlan（每个 Claim 有对象域/量词/证伪见证、依赖图无环或显式递归、工具或 NOT_APPLICABLE、消费已批准 RQ2M 公式但生成独立计划、S1/S4 hash 变化 → SEMANTIC_REGRESSION_REQUIRED 回退、AI 证明先标 PROOF_CANDIDATE 禁止 Tool-verified）、S6/S7 StageContract 与 prompt assets（16 个测试，全套 355 passed）
- [x] M3.2 — S8–S10 交接（Stage 3 第 2 个 Task，提交 `b50cd3b`）：S8 PreFreezeAttackReport（1–2 轮攻击强制、禁止正式十轮 Council、内部+独立外部攻击、Critical 已解决或明确阻断）、S9 OpenQuestionRegistry（来源标记 USER/AI_GENERATED/DERIVED/LITERATURE/TOOL_FAILURE 强制、AI_GENERATED 保留）、S10 ResearchHandoffBundle（无未归属证据、每任务有 input/output/threshold、成熟门检查理论 RQ4M）、s8/s9/s10 节点与 prompt assets（15 个测试，全套 370 passed）
- [x] M4.1 — Claim Compiler（Stage 4 第 1 个 Task，提交 `2de344d`，由并行子 agent 实现）：ClaimClass 七类（02 §8）、ClaimVerifier（NONE 必须显式 unverified）、MIXED 主张括号深度感知拆分（split_propositions）、原子 Claim 构造即拒绝 MIXED、对象域/量词/证伪见证/verifier 强制、ClaimUnit 字段（04 §1）、claim_repository 事件溯源 + hash 篡改检测（16 个测试；GAP：intended_verifiers 复数与 baseline/evidence_standard 延后）
- [x] M4.2 — Claim 冻结（Stage 4 第 2 个 Task，提交 `91b6a7e`）：ClaimContract 不可变对象（04 §2 全字段）、contract_hash 覆盖语义/工具/预算/策略、仅真实用户事件可冻结（CLAIM_FREEZE_REQUIRES_USER_EVENT）、修订只生成新版本（旧版保留、SUPERSEDES 链）、gate.py 增 CLAIM_ACCEPTANCE 决策（ACCEPT/REJECT/PAUSE）（7 个测试，全套 437 passed）
- [x] M5.1 — ActionBroker/Gate 策略（Stage 5 第 1 个 Task，提交 `d6dbfbe`）：A0–A3 委托 × R0–R6 风险确定性路由（R0 自动；R1 需 A2/A3+路径 allowlist；R2 域名 allowlist；R3 预算；R4–R6 恒 Human Gate）、Semantic Delta F4→GATE/F5→REJECT、模型/工作流/默认超时不能批准（CONFIRMATION_REQUIRES_USER_EVENT）、ActionRequest/ExecutionReceipt（08 §12 全字段，request/result hash 缺失即 RECEIPT_HASH_MISSING、绑定不符即 RECEIPT_HASH_MISMATCH）、无 Receipt 不形成 Tool Evidence、通用 gate_service 持久化任意 Gate（15 个测试）
- [x] M0.5 — Codex 指令忠实通道（P0；并行子 agent 实现，随 `d6dbfbe` 合并提交）：fidelity 10 模块 + fidelity_service（Capsule/Token/SessionBinding/ContextManifest/Delta/prepare-commit/CommandReceipt/DisplayContract/command_gateway，fail-closed 无 token、state version + idempotency、非用户确认拒绝）、29 个 security/integration 测试全绿（并入提交说明见 IMPLEMENTATION_STATUS.md）
- [x] M6.1 — LLM Provider 层（Stage 6 第 1 个 Task，提交 `cd62a2f`）：Provider 无关接口（LLMProvider Protocol）、FakeLLMProvider 确定性（同请求同响应同 usage hash）、结构化输出严格解析（缺失/未知键/非法 JSON → STRUCTURED_OUTPUT_INVALID，不写领域状态）、UsageRecord（tokens/cost/request·response hash 内容绑定）、零新依赖（8 个测试，全套 460 passed）
- [x] M6.3 — RQ 角色接入模型路由（Stage 6 第 3 个 Task）：LLMRouter（role→provider 绑定、结构化输出强制、reviewer_independence 同家族 degraded）、capability_profile_from_llm（RQ0 能力证据；无证据/非 ADVANCED → CAPABILITY_UNAVAILABLE，绝不无证据标记 ADVANCED）、early_formalizer.build_formula_items_from_llm 与 novelty_reviewer.review_scorecard_from_llm（Fake 骨架保留 CI）（9 个测试，全套 469 passed）

## Next

- [ ] M6.2.ROLE.ISOLATION — 三轨隔离：Phase A 互不可见、同家族 degraded、违规阻断（前置 M6.1；并行子 agent 实现中）

## Backlog

- [ ] Stage 2.5 — route-aware RQ0–RQ4、S5/ENG0 前置门与 Fake/外部导入纵向切片
- [ ] Stage 2.6 — ENG0–ENG10 工程转化、机械蓝图、图示、V&V 与论文交付纵向切片
- [ ] Stage 3 — S5–S10 与 MATURE_IDEA_READY
- [ ] Stage 4 — Claim Compiler 与 FrozenClaim
- [ ] Stage 5 — ActionBroker、Gate、A0–A3
- [ ] Stage 6 — 双模型 Provider 与真实隔离
- [ ] Stage 7 — Fake Council 十轮
- [ ] Stage 8 — Z3、Python Sandbox、Lean Compiler
- [ ] Stage 9 — 真实 Council
- [ ] Stage 9.2 — 理论论文母稿、独立审计、用户正式稿决策与可选 Profile 适配
- [ ] Stage 0.5 — Codex 指令忠实通道（CIFL；M1 后可实施，必须先于 Stage 10 的任何外部 mutation）
- [ ] Stage 10 — Codex 入站（MCP）
- [ ] Stage 11 — Codex 出站
- [ ] Stage 12 — 双向递归防护
- [ ] Stage 13 — 生产级学术/成熟工程近邻检索与新颖性
- [ ] Stage 14 — Web UI
- [ ] Stage 15 — 评估与真实 Case Study
- [ ] Stage 16 — 后期增强
