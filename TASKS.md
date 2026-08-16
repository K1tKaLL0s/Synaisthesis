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

## Next

- [ ] M3.1.S6_S7.THEORY_FORMAL_PLAN — 理论路线 S6/S7：S7 消费已批准早期公式生成独立 FormalizationPlan、语义变化回退 S1/S4/RQ（前置 M2.7，理论路线；M2.11 后理论/工程双路线可并行）

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
