# 03B — 工程转化、机械蓝图、验证与论文交付工作流

本文定义由 `03A` 的工程路线进入后，如何把已经通过用户审查和工程新颖性审验的 `EngineeringConceptBundle` 转化为可机械执行的工程蓝图、项目图示、应用/扩展路线及一篇证据约束的行业规范论文。

本工作流借鉴系统工程的“利益相关者期望 → 技术要求 → 逻辑分解 → 设计解 → 验证/确认”、规格驱动开发的“Spec → Plan → Tasks → Implement”、软件质量模型、安全开发框架、可复现科研工件和目标期刊模板适配思想。外部经验只提供方法，不构成对具体设计、结果或期刊录用的背书。

## 1. 入口、出口与授权边界

### 1.1 唯一入口

进入 ENG0 必须全部满足：

- 当前 S1/S4 hash 未变化；
- `EngineeringRouteSelection.decision = TRY_ENGINEERING_PROJECT`；
- RQ3E 已批准当前 `EngineeringConceptBundle` hash；
- RQ4E `status = ENGINEERING_NOVELTY_QUALIFIED` 且总分 `>= 70`，或存在绑定当前 route/artifact 的显式低分用户 override；
- 没有未解决的隐私、伦理、监管、付费或安全 Gate。

任何条件不满足都返回结构化 Blocker；不得凭自然语言备注绕过。

### 1.2 最终出口

ENG10 只允许产生：

- `ENGINEERING_DELIVERY_CANDIDATE`：蓝图完整，但真实实现或论文证据尚未达到相应等级；
- `ENGINEERING_DELIVERY_READY`：蓝图、图示、路线和稿件均通过确定性检查及独立审计；
- `BLOCKED_ENGINEERING_DELIVERY`：存在未解决的 Critical 缺口；
- `SUPERSEDED`：输入语义或架构基线已被新版本取代。

`ENGINEERING_DELIVERY_READY` 不表示工程已生产部署、论文已投稿、已录用、已获专利或商业上可行。

### 1.3 不自动授权的动作

本工作流的通过不授权：

- 新增或修改生产代码；
- 购买服务、设备、数据或算力；
- 连接真实用户、敏感数据或生产系统；
- 生产发布、数据迁移、破坏性操作；
- 对外公开仓库、上传工件或投稿论文；
- 代表用户接受许可证、作者责任或利益冲突声明。

这些动作必须进入其各自的 WorkUnit、ActionBroker 和 Human Gate。

## 2. 总流程

```text
ENGINEERING_NOVELTY_QUALIFIED / bound user override
                         ↓
ENG0 工程任务章程与基线导入
                         ↓
ENG1 利益相关者、场景与 ConOps
                         ↓
ENG2 可追踪技术要求与验收基线
                         ↓
ENG3 参考方案、技术路线与权衡研究
                         ↓
ENG4 架构、接口、数据、状态与安全设计
                         ↓
        ENGINEERING_ARCHITECTURE_REVIEW
                         ↓ APPROVE
ENG5 可机械执行实施蓝图与项目图示
                         ↓
ENG6 原型/实现选择与验证—确认闭环
        ├─ BLUEPRINT_ONLY → 只验证蓝图，不虚构结果
        └─ BUILD_AND_EVALUATE
                ↓ PROTOTYPE_EXECUTION_AUTHORIZATION
           独立代码 WorkUnit / 实验 / V&V
                         ↓
ENG7 预期应用与未来扩展路线
                         ↓
ENG8 期刊中立母稿、独立审计与用户交付
                         ↓ FORMAL_MANUSCRIPT_DECISION
        ├─ KEEP_MASTER_ONLY → ENG10
        └─ WRITE_FORMAL_MANUSCRIPT
                         ↓ PUBLICATION_PROFILE_SELECTION
ENG9 内置期刊/arXiv 适配稿、合规矩阵与可复现工件
                         ↓
ENG10 独立交付审计、打包与用户验收
                         ↓
           ENGINEERING_DELIVERY_READY
```

阶段不得合并写入一个不透明 Artifact。每个阶段必须保存输入 hash、输出 hash、来源、决定、错误和回退目标。

## 3. ENG0 — 工程任务章程与基线导入

### 3.1 输入

- 冻结的 S1 `NaturalLanguageSpec`；
- 冻结的 S4 `ResearchScopeSpec`；
- `FormalizationFeasibilityAssessment`；
- `EngineeringRouteSelection`；
- 已批准的 `EngineeringConceptBundle`；
- RQ1 `NeighborEvidenceSet`；
- RQ4E `NoveltyReview`。

### 3.2 输出：`EngineeringMissionCharter`

- `charter_id`, `version`, `project_id`；
- `source_artifact_hashes[]`；
- `problem_statement`；
- `stakeholders[]`；
- `intended_users[]`；
- `operational_context`；
- `system_of_interest_boundary`；
- `objectives[]` 与 `non_goals[]`；
- `success_metrics[]`；
- `constraints[]`；
- `assumptions[]`；
- `regulatory_security_ethics_flags[]`；
- `delivery_mode = BLUEPRINT_ONLY | BUILD_AND_EVALUATE_UNDECIDED`；
- `artifact_hash`, `status`。

### 3.3 不变量

- 章程只导入已经冻结或经用户批准的内容；
- 模型新增内容必须进入 `proposed_additions[]`，不能混入基线；
- 出现对象域、用户、核心功能、数据分类或工程目标变化时，必须打开 `ENGINEERING_SCOPE_CHANGE`，不得继续 ENG1。

## 4. ENG1 — 利益相关者、场景与 ConOps

### 4.1 输出

`OperationalConceptBundle` 至少包含：

- stakeholder map 与责任边界；
- 主要、替代、失败、恢复和退役场景；
- system context；
- 外部系统、数据源、信任边界和人工参与点；
- 运行环境、规模、频率、延迟、可用性与约束假设；
- 可用性、无障碍、伦理、隐私、安全和监管需求；
- 每个场景的 precondition、trigger、main flow、alternate flow、postcondition；
- 未解决问题和决策所有者。

### 4.2 通过标准

- 每个 expected function 至少有一个场景；
- 每个 intended user 至少映射一个角色或明确标为非操作者；
- 每个外部依赖有 owner、failure mode 和 fallback；
- 所有敏感数据和外部动作已标注 trust zone；
- 用户意图与 ConOps 的双向追踪覆盖率为 100%。

## 5. ENG2 — 可追踪技术要求与验收基线

### 5.1 Requirement Schema

每个 `EngineeringRequirement` 必须包含：

- 稳定 `requirement_id`；
- `type = FUNCTIONAL | INTERFACE | DATA | QUALITY | SAFETY | SECURITY | PRIVACY | COMPLIANCE | OPERATIONS | CONSTRAINT`；
- 单一、明确、可测试的 statement；
- `source_refs[]`；
- priority 与 rationale；
- precondition、input、expected behavior/output；
- measurement method、unit、threshold、tolerance；
- `verification_method = TEST | ANALYSIS | INSPECTION | DEMONSTRATION`；
- acceptance criterion；
- owner；
- dependency/conflict refs；
- status 与 artifact hash。

禁止使用“尽量”“适当”“快速”“友好”“高性能”等无阈值形容词。无法确定阈值时必须标记 `UNRESOLVED_THRESHOLD` 并阻断 Architecture Baseline。

### 5.2 质量与安全框架

- 质量属性从适用的 ISO/IEC 25010 产品质量特性选择，并转成项目阈值；不得声称“符合 ISO”而没有逐项证据；
- 安全开发活动按 NIST SSDF 的 Prepare、Protect、Produce、Respond 四类映射到责任、工件和验证；
- 涉及 AI 的工程还必须记录数据来源、模型/Provider 边界、已知失效、人工监督、漂移和滥用场景；
- 涉及科研结论时，实验有效性、工程验证、语义对齐和新颖性保持独立状态。

### 5.3 输出

- `RequirementsBaseline`；
- `RequirementsTraceabilityMatrix`；
- `AcceptanceCriteriaCatalog`；
- `QualityAttributeScenarioSet`；
- `SecurityPrivacyComplianceObligationSet`；
- `UnresolvedDecisionRegister`。

### 5.4 通过标准

```text
source_coverage = 100%
requirement_with_verification_method = 100%
critical_requirement_with_numeric_or_boolean_acceptance = 100%
unresolved_critical_conflicts = 0
unresolved_critical_thresholds = 0
```

## 6. ENG3 — 参考方案、技术路线与权衡研究

### 6.1 研究范围

复用 RQ1，但必须针对已冻结 Requirements Baseline 追加工程深检索：

- 同方向 GitHub/GitLab 官方仓库及其 release、architecture、test、issue 证据；
- 官方产品/项目文档与参考实现；
- 标准组织、政府或行业指南；
- 论文、技术报告、基准和可复现实验；
- 包注册表、依赖健康度、许可证与供应链信息。

星标、下载量、宣传文案或单一 benchmark 不得单独构成成熟度或路线优越性证据。

### 6.2 候选路线与权衡

至少生成一个基线方案和一个有意义的替代方案；客观上只有一条可行路线时，保存排除记录而不得虚构候选。

每个方案必须记录：

- 对 Requirements 的覆盖；
- 关键组件、依赖、接口和数据路径；
- 性能、可靠性、安全、可维护性和可扩展性预测；
- 实现复杂度、人员、时间、成本和基础设施；
- 许可证、供应链、锁定和弃用风险；
- 原型/风险刺探建议；
- 未知项和证据置信度。

固定权衡公式：

```text
weighted_score(option) = Σ_j w_j × normalized_score(option, criterion_j)

Σ_j w_j = 1
```

权重由 Requirements Baseline 派生并向用户展示；模型不得为了使推荐方案胜出而事后改权重。Critical requirement 未覆盖的方案直接淘汰，不参与加权补偿。

### 6.3 输出

- `EngineeringReferenceSet`；
- `OptionTradeStudy`；
- `TechnologySelectionRecord`；
- `RejectedOptionLog`；
- 初始 ADR 集。

## 7. ENG4 — 架构、接口、数据、状态与安全设计

### 7.1 必须产出的设计视图

- 系统上下文；
- 容器/子系统；
- 组件及责任；
- 运行时序列和关键流程；
- 数据模型、数据生命周期和数据流；
- 状态机、错误恢复、幂等与并发边界；
- 接口与版本策略；
- 部署拓扑、环境和运维边界；
- 信任边界、威胁模型和安全控制；
- 可观测性、审计、备份、恢复和退役；
- 硬件项目适用时的物理、连接、电源、热、机械与制造视图。

### 7.2 设计工件

- `ArchitectureBaseline`；
- C4 或等价层级的 architecture model；
- `InterfaceContractSet`（OpenAPI/AsyncAPI/Proto/JSON Schema 或领域等价物）；
- `DataContractSet`；
- `StateAndFailureModel`；
- `ThreatModel`；
- `DeploymentAndOperationsDesign`；
- `ArchitectureDecisionRecord[]`；
- 更新后的 Traceability Matrix。

### 7.3 图示规则

每张图必须同时保存：

- 可版本控制的源文件（优先 Mermaid、PlantUML/C4-PlantUML、Graphviz 或领域标准文本格式）；
- 渲染后的 SVG；必要时附 PNG/PDF；
- `diagram_id`、标题、版本、输入 hash、图例、节点/边语义；
- 图中元素到 requirement、component、interface 或 state 的稳定 ID 映射；
- 自动渲染回执和断链检查结果。

图片不得成为唯一事实来源；机器可读设计对象是权威，图片是投影视图。

### 7.4 `ENGINEERING_ARCHITECTURE_REVIEW`

必须向用户展示推荐路线、重大权衡、不可逆选择、公开接口、数据边界、安全边界、成本区间和未解决风险。合法决定：

- `APPROVE_BASELINE`；
- `REQUEST_REVISION`；
- `RETURN_TO_TRADE_STUDY`；
- `REVISE_REQUIREMENTS`；
- `PAUSE`；
- `ARCHIVE`。

确认绑定 Requirements、Trade Study 和 Architecture 三者 hash。任一变化使旧确认失效。

## 8. ENG5 — 可机械执行实施蓝图与项目图示

### 8.1 `MechanicalEngineeringBlueprint`

蓝图必须足以让大多数合格开发者和主流代码执行模型在不补产品决策的前提下逐项实施。至少包含：

- 规范项目树及每个目录责任；
- 文件级新增/修改/禁止清单；
- 模块、组件、服务、接口、Schema 和关键符号；
- 依赖与版本锁定策略；
- 配置、密钥引用、环境和 feature flag 策略；
- 数据创建、迁移、回滚、备份和兼容策略；
- 每个运行流程的状态、事件、错误码和恢复动作；
- 性能、安全、隐私、可观测性和运维要求；
- 构建、测试、部署、验证与回滚命令模板；
- 从 requirement 到 design、task、test 的双向追踪；
- 风险登记表、停止条件和升级条件；
- 应生成但尚未生成的源码、配置、IaC、测试和文档清单。

### 8.2 `EngineeringWorkUnitContract`

每个机械任务必须包含：

1. 稳定 Task ID 和唯一目标；
2. 权威输入文档及精确章节；
3. 前置 Task、Gate 和环境；
4. allowed files/modules/symbols；
5. forbidden files/actions；
6. 输入、输出、接口、Schema、状态和事件；
7. 必须保持的不变量；
8. 逐步修改动作；
9. 错误、边界、兼容和回滚；
10. focused tests；
11. full checks；
12. 每项验收标准；
13. 失败时停止/升级条件；
14. 交付 diff、命令、回执和未验证事项格式。

任务粒度必须满足：一次只实现一个可独立核验的行为；不得用“适当修改”“完善相关代码”“视情况测试”等措辞。

### 8.3 Blueprint Completeness Gate

```text
requirements_traced_to_design = 100%
requirements_traced_to_task = 100%
critical_requirements_traced_to_test = 100%
public_interfaces_with_schema = 100%
tasks_with_stop_condition = 100%
unresolved_product_decisions = 0
unresolved_architecture_decisions = 0
broken_diagram_references = 0
```

未满足时状态为 `BLUEPRINT_GAP`，禁止 ENG6 的 Build 路线。

## 9. ENG6 — 原型/实现选择与验证—确认闭环

### 9.1 两种合法交付模式

#### `BLUEPRINT_ONLY`

只完成静态可执行性审计、Schema 检查、图示渲染、追踪覆盖和必要的设计模拟。论文只能是：

- `DESIGN_ARTICLE_DRAFT`；或
- `PROTOCOL_MANUSCRIPT_DRAFT`。

不得出现假造的实现、性能、用户实验或比较结果。

#### `BUILD_AND_EVALUATE`

必须先通过 `PROTOTYPE_EXECUTION_AUTHORIZATION`，再按独立代码/实验 WorkUnit 实施。该 Gate 展示范围、环境、预算、数据、安全风险、外部动作和停止条件。

代码任务必须遵守 `19_MECHANICAL_EXECUTION_CONTRACT.md`；本文件不能替代代码任务固定的规划—实施交接或用户授权。

### 9.2 Verification 与 Validation

- Verification 回答“是否按要求构建”，每条 requirement 使用预定的 test/analysis/inspection/demonstration；
- Validation 回答“是否在预期环境解决用户问题”，必须基于 ConOps、代表性用户/场景和预注册成功指标；
- 两者状态独立，不得用单元测试 PASS 代替应用有效性，不得用用户满意代替安全/接口要求通过。

### 9.3 输出

- `VerificationPlan` 与 `ValidationPlan`；
- `ExperimentProtocol` 与预注册指标（适用时）；
- real tool receipts、版本、环境和随机种子；
- `VerificationReport`；
- `ValidationReport`；
- discrepancy、corrective action 与 residual risk；
- `ClaimEvidenceMatrix`。

任何论文结果主张必须在 `ClaimEvidenceMatrix` 中绑定真实回执；缺证据时只能标 `PLANNED` 或从稿件删除。

## 10. ENG7 — 预期应用与未来扩展路线

### 10.1 `ApplicationDirectionPortfolio`

每个应用方向包含：

- 用户/利益相关者；
- 问题和使用场景；
- 所需能力与当前覆盖；
- 数据、接口、部署和合规条件；
- 可测量价值指标；
- 采用障碍和失败模式；
- 证据等级；
- `NOW | NEXT | LATER | RESEARCH_ONLY` 时间层级。

### 10.2 `ExtensionRoadmap`

每个未来扩展包含：

- 扩展目标与非目标；
- 触发条件；
- 被影响的 requirements/components/interfaces；
- 兼容与迁移策略；
- 依赖的新研究、数据、基础设施或监管条件；
- 风险、成本级别和可逆性；
- 独立 ADR/Task 建议；
- 不得提前耦合到当前版本的理由。

“可扩展”必须落到稳定 extension point、接口或迁移路径；宣传性愿景不能算路线项。

## 11. ENG8 — 工程论文母稿与母稿后用户决策

### 11.1 证据决定论文类型

| 证据状态 | 允许 `paper_type` | 禁止主张 |
|---|---|---|
| 仅蓝图 | `DESIGN_ARTICLE`, `PROTOCOL_ARTICLE` | 已实现、优于基线、用户有效、生产可用 |
| 原型 + 工程验证 | `SYSTEMS_ARTICLE`, `METHODS_ARTICLE` | 未执行的长期/真实场景效果 |
| 原型 + Verification + Validation | `FULL_ENGINEERING_RESEARCH_ARTICLE` | 超出样本、场景和统计功效的推广 |
| 成熟开源软件 + 文档/测试/许可证 | `RESEARCH_SOFTWARE_ARTICLE` | 未满足目标期刊软件门槛的合规声明 |

### 11.2 `EngineeringMasterManuscript`

期刊中立母稿至少包含：

1. title、abstract、keywords；
2. problem、stakeholders、statement of need；
3. related work 与最近学术/工程近邻；
4. requirements、ConOps 和设计目标；
5. method、architecture、interfaces 与实现；
6. verification/validation/experiment methods；
7. results（只有真实证据时）；
8. 与基线的定量/定性比较；
9. threats to validity、limitations、failure modes；
10. 应用方向与扩展方向；
11. security、privacy、ethics 和 sustainability；
12. data/code/materials availability；
13. reproducibility instructions；
14. conclusion；
15. references；
16. author contributions、AI-use disclosure、funding、conflicts 和 acknowledgements；未由用户提供的字段必须是结构化 `NEEDS_AUTHOR_INPUT`，不得生成虚构占位文本。

每个实质主张必须分配 `claim_id` 并绑定：source requirement、design element、evidence receipt、figure/table 和 citation。无证据主张不得使用完成时或确定性语言。

### 11.3 母稿审计与交付

未参与母稿生成的 `ENGINEERING_MANUSCRIPT_AUDITOR` 必须检查 claim-evidence、V&V Scope、近邻引用、结果/时态、限制、AI 使用、作者输入状态和真实编译。通过后状态为 `ENGINEERING_MASTER_MANUSCRIPT_READY`，平台先向用户交付母稿、evidence tier、主要主张、未解决义务、审计结果和工程四刊/arXiv 的 scope-fit 候选。

### 11.4 `FORMAL_MANUSCRIPT_DECISION`

母稿交付后打开 Gate，绑定 `master_manuscript_id + version + master_hash + engineering_delivery_hash`。合法决定：

- `KEEP_MASTER_ONLY`：母稿即正式交付物，不生成期刊/arXiv 适配稿；
- `WRITE_FORMAL_MANUSCRIPT`：进入 ENG9 的 `PUBLICATION_PROFILE_SELECTION`；
- `REVISE_MASTER`：生成新母稿 revision 并重新审计；
- `PAUSE`。

模型不得在用户无响应时默认选择正式论文。

## 12. ENG9 — Profile 选择、正式适配与可复现工件

### 12.1 内置 Profile

工程路线内置：

- `ENG_IEEE_TSE`；
- `ENG_ACM_TOSEM`；
- `ENG_EMSE`；
- `ENG_JSS`；
- `ENG_ARXIV_PREPRINT`（`venue_kind = PREPRINT_REPOSITORY`）；
- 扩展 `JOSS_RESEARCH_SOFTWARE`、`NATURE_PORTFOLIO_METHODS_OR_SOFTWARE` 与 `CUSTOM_VENUE`。

完整字段、官方指南 freshness、模板 checksum、arXiv 边界和两路线 Registry 见 `03C_THEORY_PUBLICATION_AND_DUAL_TRACK_VENUE_PROFILES.md`。

### 12.2 `PUBLICATION_PROFILE_SELECTION`

只有 `FORMAL_MANUSCRIPT_DECISION = WRITE_FORMAL_MANUSCRIPT` 才可打开。系统根据领域、论文证据类型和篇幅给出 scope-fit 推荐；用户选择期刊、arXiv 或自定义 Profile。模型不得代表用户确认作者顺序、投稿声明、伦理审批或版权/许可证。选择只授权生成适配稿，不授权投稿。

### 12.3 期刊/arXiv 适配

`VenueAdaptedManuscript` 必须由 Master + PublicationProfile 机械派生，保存转换记录而不得覆盖母稿。`VenueComplianceMatrix` 对每条要求给出：

- `PASS`：有具体稿件位置或工件证据；
- `FAIL`：不满足且阻断 submission candidate；
- `NEEDS_AUTHOR_INPUT`：作者、伦理、利益冲突、版权等必须由用户提供；
- `NOT_APPLICABLE`：有明确理由；
- `STALE_GUIDANCE`：官方指南超过配置的 freshness window，必须重新检索。

arXiv 必须显示为预印本平台，适配包使用 `ARXIV_PACKAGE_READY`，不得产生 `PEER_REVIEWED`、`JOURNAL_ACCEPTED` 或同义状态。

### 12.4 可复现工件

`ReproducibilityArtifact` 至少包含：

- README：目的、系统要求、安装、运行、测试、复现实验和预期输出；
- immutable version/tag/commit 和 checksum；
- 环境/依赖锁定；
- 数据清单、来源、许可证、隐私与获取方式；
- 一键或分步 reproduction commands；
- claim-to-artifact mapping；
- 时间/算力/存储要求；
- 已知差异、随机性和容差；
- LICENSE、CITATION、贡献者与 AI 使用说明；
- 失败排查与支持边界。

软件论文 Profile 只有在软件实际存在、可安装、文档和自动化测试通过且许可证兼容时，才能到 `SUBMISSION_CANDIDATE`。

## 13. ENG10 — 独立交付审计、打包与用户验收

### 13.1 独立审计

至少一个未参与 ENG3–ENG9 初稿生成的 `ENGINEERING_DELIVERY_AUDITOR` 检查：

- S1/S4 → concept → requirement → design → task → test → paper 的双向追踪；
- 蓝图是否仍有需要实施者自行做出的产品/架构选择；
- 图、接口、状态、错误、单位和 Schema 是否一致；
- V&V 与论文主张是否有真实回执；
- 最近邻、引用、许可证和合规 Profile 是否可追溯；
- 论文是否含夸大、虚构结果或过时指南；
- 敏感信息、密钥、隐私数据和不安全执行说明是否泄露。

### 13.2 最终交付目录

```text
engineering_delivery/
├── 00_manifest.yaml
├── 01_executive_summary.md
├── 02_mission_and_conops/
├── 03_requirements/
│   ├── requirements.yaml
│   ├── acceptance_criteria.yaml
│   └── traceability_matrix.csv
├── 04_reference_and_trade_study/
├── 05_architecture/
│   ├── architecture_baseline.yaml
│   ├── adr/
│   ├── interfaces/
│   ├── data/
│   ├── states/
│   ├── security/
│   └── deployment/
├── 06_diagrams/
│   ├── source/
│   └── rendered/
├── 07_implementation_blueprint/
│   ├── project_tree.md
│   ├── module_and_file_plan.yaml
│   ├── work_units/
│   ├── build_test_deploy.md
│   └── rollback_and_migration.md
├── 08_verification_and_validation/
├── 09_applications_and_extensions/
├── 10_risk_register/
├── 11_publication/
│   ├── master_manuscript.*
│   ├── master_audit.yaml
│   ├── formal_manuscript_decision.yaml
│   ├── venue_profile.yaml              # 用户选择正式适配时存在
│   ├── venue_adapted_manuscript.*      # 用户选择正式适配时存在
│   └── compliance_matrix.yaml          # 用户选择正式适配时存在
├── 12_reproducibility_artifact/
├── 13_audit/
└── 14_checksums.sha256
```

`00_manifest.yaml` 必须记录每个文件的 role、source artifact、version、byte size、checksum、generation method 和验证状态。

### 13.3 最终通过条件

全部满足才可 `ENGINEERING_DELIVERY_READY`：

- ENG0–ENG9 当前版本均非 BLOCKED/SUPERSEDED；
- Blueprint Completeness Gate 全通过；
- 所有图可从源文件重渲染且无断链；
- 关键要求的 Verification 计划完整；已有实现时，声称 PASS 的项有真实回执；
- 应用与扩展路线含条件、指标、风险和证据等级；
- MasterManuscript 完整；
- MasterManuscript 已独立审计并先交付用户；
- `KEEP_MASTER_ONLY` 时 manifest 明确 `formal_manuscript_requested = false`；
- `WRITE_FORMAL_MANUSCRIPT` 时，选择的 Profile 当前有效且 Compliance Matrix 无 FAIL/STALE_GUIDANCE；
- 不存在虚构结果、伪造引用或未披露 AI 辅助；
- 独立审计无 Critical/Major finding；
- 用户通过 `ENGINEERING_DELIVERY_ACCEPTANCE` 接受当前 manifest hash。

用户验收只确认交付范围与语义，不替代工程测试、同行评审、伦理审查或期刊编辑决定。

## 14. 回归、修订与撤回

以下变化必须产生新 revision，并按影响范围回退：

| 变化 | 最早回退点 |
|---|---|
| S1/S4 核心语义变化 | RQ1 / RQ2F |
| 新近邻改变新颖性判断 | RQ4E |
| stakeholder / ConOps 变化 | ENG1 |
| requirement 或阈值变化 | ENG2 |
| 技术路线或重大依赖变化 | ENG3 |
| 公开接口、数据或安全边界变化 | ENG4 |
| 机械任务发现蓝图缺口 | ENG4 或 ENG5 |
| 实现证伪架构假设 | ENG3 或 ENG4 |
| 新实验结果改变论文主张 | ENG6 / ENG8 |
| 母稿主张变化 | ENG8 |
| 期刊/arXiv 指南更新 | ENG9 |
| 证据撤回或许可证不兼容 | ENG6 / ENG8 / ENG9 / ENG10 |

历史 Artifact、评分、决定、稿件和回执不可覆盖；只能标 `SUPERSEDED`、`RETRACTED` 或 `NEEDS_REGRESSION`。

## 15. 失败与停止条件

| 条件 | 状态 | 停止/恢复 |
|---|---|---|
| 工程路线未由用户选择 | `ENGINEERING_ROUTE_DECISION_REQUIRED` | 返回 03A Gate |
| 新颖性未达门且无 override | `ENGINEERING_NOVELTY_REQUIRED` | 返回 RQ4E |
| Critical requirement 无阈值 | `REQUIREMENTS_BASELINE_BLOCKED` | 返回 ENG2 |
| 无可行技术路线 | `TRADE_STUDY_BLOCKED` | 修订要求或用户暂停 |
| 重大架构选择未确认 | `ENGINEERING_ARCHITECTURE_REVIEW_REQUIRED` | 打开 Gate |
| 蓝图仍要求实施者补产品决策 | `BLUEPRINT_GAP` | 返回 ENG2–ENG5 |
| 用户未授权实现 | `BLUEPRINT_ONLY` | 不运行代码/实验 |
| 实验/验证环境不可用 | `EVIDENCE_BLOCKED` | 稿件降级或记录 Blocker |
| 结果主张无真实回执 | `MANUSCRIPT_CLAIM_UNSUPPORTED` | 删除/降级主张或补执行 |
| 目标期刊指南过期 | `STALE_GUIDANCE` | 重新读取官方指南 |
| 软件论文不满足代码/测试/许可证要求 | `SOFTWARE_ARTICLE_INELIGIBLE` | 换 paper type 或补工件 |
| 独立审计有 Critical/Major | `BLOCKED_ENGINEERING_DELIVERY` | 一轮定向返工后重审 |

## 16. 最小验收场景

1. 未选择工程路线时直接 ENG0，必须失败。
2. RQ4E 总分 70 自动进入 ENG0；69 返回用户 Gate。
3. ENG0 尝试静默新增核心功能，触发 `ENGINEERING_SCOPE_CHANGE`。
4. requirement 写“响应要快”但无指标，ENG2 不得通过。
5. Critical requirement 未被候选方案覆盖时，该方案即使总分最高也必须淘汰。
6. 架构图节点没有稳定 component ID，ENG4 不得通过。
7. 用户未批准 Architecture hash，ENG5 不得冻结。
8. WorkUnit 使用“适当修改相关文件”，Blueprint Completeness Gate 失败。
9. BLUEPRINT_ONLY 模式的母稿写入虚构 benchmark，ENG8/ENG10 阻断。
10. BUILD_AND_EVALUATE 未通过授权 Gate，不得执行代码或实验。
11. 单元测试通过但未做预期场景 Validation，不得标应用有效。
12. 新实现结果与原假设冲突，必须回退 ENG3/ENG4，而不是修改论文掩盖。
13. 母稿未先交付用户就打开 Profile Selection，工作流阻断。
14. 用户选择 `KEEP_MASTER_ONLY`，工程交付仍可 READY 且不生成适配稿。
15. 用户选择 `WRITE_FORMAL_MANUSCRIPT` 后才允许选择工程四刊、工程 arXiv 或扩展 Profile。
16. 目标期刊官方指南超出 freshness window，Compliance Matrix 标 `STALE_GUIDANCE`。
17. arXiv 被标成期刊或同行评审，测试失败。
18. JOSS Profile 下软件无开源许可证或自动化测试，不得到 SUBMISSION_CANDIDATE。
19. 图示源和 SVG hash 对不上，最终包不得 READY。
20. 论文每个结果 claim 都能追踪到真实 receipt 和图表。
21. 应用方向只有宣传文本、没有指标/风险/证据等级，ENG7 失败。
22. 独立审计发现实施者仍需选择数据库或公开接口，返回 BLUEPRINT_GAP。
23. 用户接受新 manifest 后修改任一权威文件，旧验收自动失效。
24. 完整包重建后，manifest、checksums、图示、追踪和稿件合规检查全部可复算。
