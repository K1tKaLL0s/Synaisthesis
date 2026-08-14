# 03A — 早期形式化、可行性分流、相邻工作检索与新颖性资格门

本文是 S0–S10 孵化流程的强制子协议。它解决四个固定问题：自然语言设计成形后，系统应先判断其是否适合构建纯数学理论；如果适合，则生成可审查的数学早期形式化；如果不适合纯数学理论但可构建为工程项目，则必须由用户决定是否改设计或转工程路线；两条路线都必须在进入后续主流程前完成相邻工作检索、用户审查和与路线匹配的新颖性审验。

不得先进入最小范例、核心理论、工程蓝图、Claim 冻结或 Council，再补做本协议。

## 1. 适用位置、路线和唯一合法主路径

自然语言设计的完成状态定义为 `NATURAL_LANGUAGE_DESIGN_READY`，计算条件是：

- S0–S4 均为 PASS；
- S1 `NaturalLanguageSpec` 与 S4 `ResearchScopeSpec` 均已由用户确认；
- `expected_functions`、`target_applications`、`intended_users`、`operational_constraints`、`success_metrics` 均存在；
- 不存在未解决的 Critical 歧义。

用户一次性提交完整自然语言设计时，平台仍须将其规范化为 S0–S4 Artifact 并取得 S1、S4 确认。不得因为输入看似完整而跳过语义冻结。

唯一合法主路径：

```text
S0 → S1 → S2 → S3 → S4
                     ↓
        NATURAL_LANGUAGE_DESIGN_READY
                     ↓
RQ0 能力与执行路线确认
                     ↓
RQ1 相邻研究与成熟工程项目检索
                     ↓
RQ2F 形式化可行性分析
        ├─ THEORY_OR_HYBRID_FIT
        │       ↓
        │  RQ2M 数学公式化早期形式化
        │       ↓
        │  RQ3M 用户审查数学形式化
        │       ↓ APPROVE
        │  RQ4M 理论 50 + 应用 50 新颖性审查
        │       ├─ score >= 70 → NOVELTY_QUALIFIED → S5
        │       └─ score < 70 / INCONCLUSIVE → BLOCKED_NOVELTY_USER
        │
        ├─ ENGINEERING_PROJECT_CANDIDATE
        │       ↓
        │  ENGINEERING_ROUTE_DECISION（强制 Human Gate）
        │       ├─ REVISE_FOR_THEORY → 新 S1/S4 Revision → RQ1
        │       ├─ TRY_ENGINEERING_PROJECT
        │       │       ↓
        │       │  RQ2E 工程概念形式化
        │       │       ↓
        │       │  RQ3E 用户审查工程概念
        │       │       ↓ APPROVE
        │       │  RQ4E 工程 60 + 应用 40 新颖性审验
        │       │       ├─ score >= 70 → ENGINEERING_NOVELTY_QUALIFIED → ENG0
        │       │       └─ score < 70 / INCONCLUSIVE → BLOCKED_NOVELTY_USER
        │       └─ PAUSE / ARCHIVE
        │
        └─ NEITHER_FIT / INCONCLUSIVE
                ↓
          FORMALIZATION_FEASIBILITY_DECISION（强制 Human Gate）
                ├─ REVISE_DESIGN → 新 S1/S4 Revision → RQ1
                ├─ RESEARCH_MORE → RQ1
                └─ PAUSE / ARCHIVE
```

`RQ2` 是阶段族名称；`RQ2F`、`RQ2M`、`RQ2E` 是互斥或前后相接的稳定子阶段。V2.2 Artifact 中未带后缀的 `RQ2`、`RQ3`、`RQ4` 分别按 `RQ2M`、`RQ3M`、`RQ4M` 读取，不得把旧 Artifact 猜测为工程路线。

理论路线的 RQ3M 未批准时禁止启动 RQ4M。工程路线的 `ENGINEERING_ROUTE_DECISION` 未选择 `TRY_ENGINEERING_PROJECT`、RQ3E 未批准时，禁止启动 RQ4E。任何 RQ4 未形成有效结论时，均禁止自动进入后续主流程。

工程路线的后续唯一入口是 `03B_ENGINEERING_TRANSLATION_WORKFLOW.md` 的 ENG0；不得进入 S5、S6–S10 或纯理论 Claim Compiler，除非用户之后建立新的理论型 S1/S4 Revision 并重新通过本协议。

## 2. RQ0 — 能力与执行路线确认

### 2.1 目标

确保早期形式化和可行性分流不是由只适合整理文本的低能力配置完成。产品不得把具体供应商或模型名称硬编码为“更智能”；使用可验证的能力 Profile。

### 2.2 两条允许路线

#### `PLATFORM_ADVANCED_FORMALIZER`

平台选择具有 `EARLY_FORMALIZER` 角色资格的 `ModelProfile`。全部满足才可用：

- `capability_tier >= ADVANCED`；
- `formalization_eval_score >= 80/100`；
- `math_schema_valid_rate >= 0.95`；
- 支持来源引用和结构化输出；
- 上下文预算可容纳 S1/S4、检索证据集和输出 Schema；
- 能力评估记录未过期，默认有效期 90 天；
- 当前调用预算与隐私策略允许。

若自然语言设计所用模型不满足上述要求，平台必须选择更高能力 Profile。若原模型已经满足，平台可以继续使用，但必须建立新的隔离 `EARLY_FORMALIZER` Session。

RQ2F 的工程适配判定还必须有 `ENGINEERING_FEASIBILITY_ASSESSOR` 角色。该角色可以与 Early Formalizer 使用同一模型 Profile，但必须使用隔离 Session、不同 Prompt Asset 和独立初始输出；正式科研 Profile 优先使用不同模型家族。

#### `EXTERNAL_ADVANCED_MODEL_IMPORT`

用户可在外部高能力模型中完成可行性分析或早期形式化并导入。导入包必须包含：

- `source_model_identity`；
- `source_provider` 或 `USER_REDACTED`；
- `created_at`；
- `input_spec_hash`；
- `neighbor_evidence_set_id`；
- `route_assessment`；
- `formula_bundle` 或 `engineering_concept_bundle`；
- `public_rationale`；
- `provenance = EXTERNAL_MODEL_IMPORT`。

外部导入不自动获得可信状态。平台仍要执行 Schema、公式覆盖、引用、语义对齐、分流规则和 hash 校验。

### 2.3 输出：`FormalizationCapabilityDecision`

- `decision_id`
- `project_id`
- `research_spec_id`
- `route`
- `model_profile_id`（外部导入可为空）
- `capability_evidence_refs`
- `input_spec_hash`
- `budget_snapshot_id`
- `privacy_policy_snapshot_id`
- `status`
- `blocker`

### 2.4 状态

- `CAPABILITY_READY`
- `CAPABILITY_UNAVAILABLE`
- `EXTERNAL_IMPORT_PENDING`
- `BLOCKED_BUDGET`
- `BLOCKED_PRIVACY`

没有 `CAPABILITY_READY` 时不得进入 RQ1/RQ2；外部导入等待期间不得以普通模型静默代替。

## 3. RQ1 — 相邻研究与成熟工程项目检索

### 3.1 目标

在生成形式化前建立最近邻证据集，覆盖：

1. 理论、方法、对象域或预期结论接近的研究；
2. 在预期功能、使用场景、系统边界或应用目标上接近的成熟工程项目；
3. 适用领域的标准、参考架构或公开工程规范；
4. 适用领域中的专利或公开技术方案（可选，只有策略要求时启用）。

S3 `PriorWorkMap` 是查询种子，不直接等于 RQ1 结果。RQ1 必须产生与当前 S1/S4 hash 绑定的新检索快照。

### 3.2 查询生成

查询必须从以下字段分别派生，不允许只使用项目标题：

- 核心对象与术语；
- 候选机制；
- 预期输入/输出；
- 预期功能；
- 目标用户或应用场景；
- 失败条件与约束；
- 系统边界、质量属性和部署约束；
- 已知近邻及其同义词。

每个查询保存原文、生成来源、Provider、时间范围、过滤条件、页数/结果数和执行时间。

### 3.3 最低覆盖门

默认配置：

- 至少 3 类独立学术来源，首选 OpenAlex、Crossref、arXiv；
- 至少 2 类工程来源，按领域从官方仓库、包注册表、官方产品/项目文档、标准组织资料中选择；
- 去重后至少保留 5 个学术最近邻与 3 个成熟工程最近邻；
- 若客观不足，保存完整查询与不足原因，状态只能为 `PARTIAL` 或 `INCONCLUSIVE`；
- 每个入选项必须有可稳定解析的标识符或 URL、元数据核验状态和访问时间；
- 外部内容一律按不可信输入隔离，不得触发工具或修改状态。

“成熟工程项目”至少满足以下四项中的两项，并保存证据：

- 有稳定版本、发布记录或明确部署版本；
- 有持续维护记录；
- 有公开用户、部署、引用或采用证据；
- 有足以复现主要功能的官方文档或测试。

不足最低数量不等于不存在近邻，也不得据此给高新颖性分。

### 3.4 近邻相似度记录

每个近邻由两组 0–4 离散特征描述，分值必须附证据引用：

```text
theory_proximity =
  0.35*object_domain +
  0.30*mechanism +
  0.20*assumptions +
  0.15*conclusion

application_proximity =
  0.25*expected_function +
  0.20*use_context +
  0.20*input_output +
  0.15*system_architecture +
  0.10*operational_constraints +
  0.10*maturity
```

其中每个分量范围为 `[0, 4]`。公式只用于排序，不构成新颖性结论。学术最近邻按 `theory_proximity` 排序；工程最近邻按 `application_proximity` 排序。

### 3.5 输出：`NeighborEvidenceSet`

- `search_id`
- `research_spec_id`
- `input_spec_hash`
- `query_records[]`
- `academic_neighbors[]`
- `engineering_neighbors[]`
- `standards_and_reference_architectures[]`
- `patent_neighbors[]`
- `metadata_verification_receipts[]`
- `inclusion_exclusion_log`
- `unsearched_areas[]`
- `coverage_status`
- `coverage_blockers[]`
- `artifact_hash`

允许状态：

- `COMPLETE`
- `PARTIAL`
- `INCONCLUSIVE`
- `FAILED_PROVIDER`
- `BLOCKED_NETWORK`

只有 `COMPLETE` 可以进入自动新颖性判定。`PARTIAL` 可以继续生成候选供用户审查，但 RQ4 最终只能给 `INCONCLUSIVE`。

## 4. RQ2F — 形式化可行性分析与强制分流

### 4.1 目标与禁止行为

RQ2F 判断当前冻结设计是否具备纯数学理论构造所需的语义材料，以及是否具备工程项目构造所需的可实施材料。它不判断设计“好坏”，也不得为了得到某条路线而改写 S1/S4。

系统不得把“目前缺少数学对象”自动解释为“工程项目”，也不得把工程需求包装成虚构定理。只有 `theory_fit = false` 且 `engineering_fit = true` 时才能产生 `ENGINEERING_PROJECT_CANDIDATE`，并且必须由用户明确选择 `TRY_ENGINEERING_PROJECT`。

### 4.2 理论适配的确定性谓词

每个谓词必须是 `PASS | FAIL | UNKNOWN` 并附 S1/S4 字段或 RQ1 证据引用：

- `TFO`：存在稳定的对象域、类型或集合；
- `TFR`：核心关系、运算、约束或动力学可定义；
- `TFC`：至少存在一个非平凡、可证明或可证伪的核心主张；
- `TFW`：可表达证明义务、反例或失败见证；
- `TFP`：数学抽象不删除预期功能、目标应用或关键边界。

```text
theory_fit = TFO ∧ TFR ∧ TFC ∧ TFW ∧ TFP
```

任何谓词为 `UNKNOWN` 时，`theory_fit` 不得为 true。

### 4.3 工程适配的确定性谓词

- `EFS`：存在明确的利益相关者、用户问题或应用场景；
- `EFI`：存在可定义的输入、输出、接口或操作行为；
- `EFA`：可以分解出系统边界、组件或责任；
- `EFM`：至少一个成功指标可转成带阈值的验收条件；
- `EFF`：在已知时间、预算、数据、依赖、安全与合规约束下存在可调查的实现路线。

```text
engineering_fit = EFS ∧ EFI ∧ EFA ∧ EFM ∧ EFF
```

`EFF` 只表示“值得进入工程设计”，不表示已证明项目能成功、已获预算或可直接生产部署。

### 4.4 双评估与保守聚合

Early Formalizer 和 Engineering Feasibility Assessor 分别输出自己的谓词矩阵。聚合器对每个谓词采用 `FAIL > UNKNOWN > PASS` 的保守顺序；任一评估器给 `FAIL`，聚合结果为 `FAIL`，任一评估器给 `UNKNOWN` 且无人给 `FAIL`，结果为 `UNKNOWN`。

固定分类：

| theory_fit | engineering_fit | `route_classification` | 路由 |
|---|---|---|---|
| true | true | `HYBRID_FIT` | 默认 RQ2M；保留工程映射 |
| true | false | `PURE_THEORY_FIT` | RQ2M |
| false | true | `ENGINEERING_PROJECT_CANDIDATE` | 强制 `ENGINEERING_ROUTE_DECISION` |
| false | false | `NEITHER_CURRENTLY_FIT` | 强制 `FORMALIZATION_FEASIBILITY_DECISION` |
| 任一 UNKNOWN | 任意 | `INCONCLUSIVE` | 强制 `FORMALIZATION_FEASIBILITY_DECISION` |

### 4.5 输出：`FormalizationFeasibilityAssessment`

- `assessment_id`
- `version`
- `research_spec_id`
- `input_spec_hash`
- `neighbor_evidence_set_id`
- `assessor_session_ids[]`
- `theory_predicates[]`
- `engineering_predicates[]`
- `disagreements[]`
- `missing_information[]`
- `route_classification`
- `recommended_route`
- `public_explanation`
- `artifact_hash`
- `status`

`public_explanation` 最多 12 条，必须解释为什么不适合纯数学理论、为什么可能适合工程项目以及判断的不确定性；禁止使用贬低性语言。

### 4.6 Human Gate

`ENGINEERING_ROUTE_DECISION` 必须展示当前 S1/S4 hash、失败的理论谓词、通过的工程谓词、最近工程近邻、风险和两个可行动选项。合法决定：

- `REVISE_FOR_THEORY`：创建新的 S1/S4 Revision 草案；必须再次由用户冻结后从 RQ1 开始；
- `TRY_ENGINEERING_PROJECT`：创建 `EngineeringRouteSelection`，进入 RQ2E；
- `PAUSE`；
- `ARCHIVE`。

`FORMALIZATION_FEASIBILITY_DECISION` 的合法决定：

- `REVISE_DESIGN`：创建新的 S1/S4 Revision 草案；
- `RESEARCH_MORE`：返回 RQ1；
- `PAUSE`；
- `ARCHIVE`。

用户决定绑定 `assessment_id + version + artifact_hash + input_spec_hash`。任何绑定字段变化都会使旧决定失效。模型、工作流或管理员不得代替用户选择工程路线。

## 5. RQ2M — 数学公式化早期形式化

### 5.1 目标与边界

RQ2M 将理论或混合型自然语言设计翻译为可审查的数学候选，不声称已证明、已验证或已达到 Lean/Z3 可执行性。S7 仍负责后续正式构造，Verification Lab 仍负责真实工具结果。

核心形式化内容必须写成数学公式。自然语言只能用于符号释义、来源说明、不确定性和面向用户的简短解释；不得把核心命题只留在叙述中。

### 5.2 输出：`EarlyFormalizationBundle`

- `formalization_id`
- `version`
- `research_spec_id`
- `input_spec_hash`
- `feasibility_assessment_id`
- `neighbor_evidence_set_id`
- `formalizer_profile_or_import_id`
- `notation_table[]`
- `formula_items[]`
- `formula_dependency_graph`
- `semantic_alignment_matrix[]`
- `neighbor_difference_matrix[]`
- `uncertainty_register[]`
- `plain_language_explanation`
- `validator_results[]`
- `artifact_hash`
- `status`

### 5.3 `FormulaItem`

每个公式项必须包含：

- `formula_id`
- `formula_type`
- `latex`
- `normalized_math_ast`（若当前解析器支持）
- `symbols_used[]`
- `source_spec_fields[]`
- `assumption_formula_ids[]`
- `neighbor_refs[]`
- `origin = USER | DERIVED | PRIOR_WORK | MODEL_PROPOSAL`
- `confidence`
- `known_ambiguities[]`
- `falsification_or_failure_formula_id`

### 5.4 必须覆盖的公式类型

适用时必须包含：

- 对象域：例如 `x \in \mathcal{X}`；
- 输入/输出映射：例如 `f: \mathcal{X} \to \mathcal{Y}`；
- 状态与转移：例如 `s_{t+1}=T(s_t,u_t;\theta)`；
- 假设集合：例如 `A(x,\theta)=\bigwedge_i A_i(x,\theta)`；
- 不变量：例如 `\forall t,\ I(s_t)=1`；
- 核心主张：例如 `\forall x\in D,\ A(x)\Rightarrow C(x)`；
- 目标或评价函数：例如 `\theta^*=\arg\min_\theta L(\theta)`；
- 失败/证伪见证：例如 `\exists x\in D,\ A(x)\land\neg C(x)`；
- 理论到工程应用映射：例如 `\Phi:\mathcal{M}\to\mathcal{A}`；
- 后续验证义务：例如 `O=\{O_1,\ldots,O_n\}`。

确实不适用的类型记录 `NOT_APPLICABLE` 和理由。对象域、假设、至少一个核心主张、至少一个失败/证伪公式以及应用映射不得标记为不适用。

### 5.5 确定性验证

RQ2M 通过前必须满足：

- 所有使用的符号均在 `notation_table` 定义；
- 公式依赖不存在未声明环；
- 每个 S1/S4 核心语义字段至少映射到一个公式或明确的非目标；
- 每个核心公式至少引用一个源语义字段；
- 每个核心贡献都有最近邻差异记录；
- 每个核心主张都有失败/证伪公式；
- formula bundle 的 hash 可重算；
- 未出现 `PROVED`、`VERIFIED`、`NOVEL` 等越权状态。

允许状态：

- `EARLY_FORMALIZATION_CANDIDATE`
- `SCHEMA_INVALID`
- `SEMANTIC_GAP`
- `FORMULA_COVERAGE_INCOMPLETE`
- `READY_FOR_USER_REVIEW`
- `SUPERSEDED`

## 6. RQ2E — 工程概念形式化

### 6.1 目标与边界

RQ2E 不是把工程构想伪装成纯数学理论，而是用数学关系、可判定约束和机器可读 Schema 固定工程意图，使后续工程蓝图可以机械生成和验收。它不等于详细架构，不授权写代码、采购、部署或生产变更。

### 6.2 核心形式化

至少包含：

```text
system_boundary = (Actors, ExternalSystems, TrustZones)

F: X × C → Y

s_{t+1} = T(s_t, u_t, e_t)

R_i(z) ∈ {true, false}

Q_j(z) comparator_j threshold_j

G_arch = (V_components, E_interfaces, type)

Trace ⊆ Requirement × DesignElement × VerificationObligation

Risk_k = likelihood_k × impact_k
```

其中：

- `X`、`Y`、`C` 分别是输入、输出和运行约束；
- `R_i` 是功能、接口、安全或合规要求谓词；
- `Q_j` 是性能、可靠性、可维护性、可用性或领域特定质量指标；
- 每个阈值必须带单位、测量方法和允许误差；
- `Trace` 中每个 requirement 至少映射一个设计义务和一个验证义务；
- 未知阈值用 `UNRESOLVED_THRESHOLD`，不得由模型虚构数字。

### 6.3 输出：`EngineeringConceptBundle`

- `concept_id`
- `version`
- `research_spec_id`
- `input_spec_hash`
- `route_selection_id`
- `feasibility_assessment_id`
- `neighbor_evidence_set_id`
- `notation_table[]`
- `system_boundary_model`
- `actors_and_use_cases[]`
- `input_output_contracts[]`
- `state_transition_formulas[]`
- `requirement_predicates[]`
- `quality_metric_formulas[]`
- `architecture_graph_candidate`
- `traceability_relation`
- `verification_obligations[]`
- `neighbor_difference_matrix[]`
- `assumptions_and_constraints[]`
- `unresolved_thresholds[]`
- `plain_language_explanation`
- `artifact_hash`
- `status`

### 6.4 确定性验证

- 所有对象和单位均已定义；
- 每个 expected function 有 I/O 或状态转移表达；
- 每个 success metric 有公式、比较符、阈值或显式 unresolved 标记；
- 每个安全、隐私、伦理或监管约束都有验证义务；
- 设计元素不得超出 S1/S4，模型建议必须标为 `MODEL_PROPOSAL`；
- 至少一个失败状态和恢复义务被表达；
- Bundle hash 可重算；
- 未出现 `IMPLEMENTED`、`VALIDATED`、`PRODUCTION_READY` 或 `NOVEL`。

允许状态：

- `ENGINEERING_CONCEPT_CANDIDATE`
- `SCHEMA_INVALID`
- `SEMANTIC_GAP`
- `REQUIREMENT_COVERAGE_INCOMPLETE`
- `UNRESOLVED_THRESHOLD`
- `READY_FOR_USER_REVIEW`
- `SUPERSEDED`

## 7. RQ3M / RQ3E — 用户审查

### 7.1 理论路线 RQ3M

平台必须向用户同时展示：

1. formula bundle 的版本与 hash；
2. 符号表和核心公式；
3. 自然语言设计字段到公式的映射；
4. 与最近邻的主要差异；
5. 不确定性与未覆盖项；
6. 不超过 12 条的简明自然语言解释。

Gate 为 `EARLY_FORMALIZATION_REVIEW`。合法决定：

- `APPROVE`：记录 `UserFormalizationApproval`，进入 RQ4M；
- `REQUEST_REVISION`：生成新版本，返回 RQ2M；
- `RESEARCH_MORE`：返回 RQ1；
- `REVISE_DESIGN`：创建新 S1/S4 Revision；
- `REJECT`：状态 `BLOCKED_FORMALIZATION_USER`；
- `PAUSE`。

### 7.2 工程路线 RQ3E

平台必须展示系统边界、行为/I/O 公式、要求谓词、质量阈值、验证义务、近邻差异、未解决阈值和不超过 12 条的简明解释。

Gate 为 `EARLY_ENGINEERING_CONCEPT_REVIEW`。合法决定：

- `APPROVE`：记录 `UserEngineeringConceptApproval`，进入 RQ4E；
- `REQUEST_REVISION`：返回 RQ2E；
- `RESEARCH_MORE`：返回 RQ1；
- `RETURN_TO_ROUTE_DECISION`：重新打开 `ENGINEERING_ROUTE_DECISION`；
- `REJECT`；
- `PAUSE`。

两种用户确认都绑定 `artifact_id + version + artifact_hash + input_spec_hash + route`。任何绑定字段变化都会使旧确认失效。

## 8. RQ4M / RQ4E — 路线化新颖性审验

### 8.1 共同前置条件

- RQ3M 或 RQ3E 对当前 hash 为 `APPROVE`；
- RQ1 `coverage_status = COMPLETE`；
- 至少两个隔离 Novelty Reviewer 完成评分；
- 正式科研 Profile 下两个 Reviewer 必须属于不同模型家族；
- 每个评分项都引用 RQ1 近邻或明确引用“未检索区域”；
- 不允许 Reviewer 读取对方评分后再生成自己的初始评分。

任一条件不满足时结果为 `INCONCLUSIVE`，不得生成自动通行分数。

每个 Reviewer 对每个项目给出 `r_i ∈ {0,1,2,3,4,5}`。固定锚点：

- 0：与最近邻实质相同，或无证据支持差异；
- 1：仅表述、界面或参数级差异；
- 2：增量变化或常规组合；
- 3：有清楚、可引用的中等新贡献；
- 4：强且非显然的贡献；
- 5：在已检索范围内具有异常强、可能改变研究或实践方式的贡献。

每项采用保守聚合：

```text
q_i = min(r_i_primary, r_i_auditor)
```

### 8.2 RQ4M：理论 50 + 应用 50

理论新颖度最高 50 分：

| ID | 项目 | 权重 | 最高分 |
|---|---|---:|---:|
| T1 | 与最近理论在对象、定义或问题设定上的实质区别 | 3 | 15 |
| T2 | 机制、定理、推导或解释是否非显然 | 3 | 15 |
| T3 | 是否扩展知识、解释范围或产生新的可证伪预测 | 2 | 10 |
| T4 | 最近邻比较和差异主张的来源覆盖是否充分 | 2 | 10 |

应用新颖度最高 50 分：

| ID | 项目 | 权重 | 最高分 |
|---|---|---:|---:|
| A1 | 相对成熟工程项目的预期功能差异 | 3 | 15 |
| A2 | 目标用户、应用场景或任务设定的新颖性 | 2 | 10 |
| A3 | 系统机制、工作流或人机协作方式的新颖性 | 2 | 10 |
| A4 | 跨域迁移或组件组合是否具有非显然性 | 2 | 10 |
| A5 | 是否提出可测量、具有实践价值的新能力或收益 | 1 | 5 |

```text
theory_score = 3q_T1 + 3q_T2 + 2q_T3 + 2q_T4

application_score = 3q_A1 + 2q_A2 + 2q_A3 + 2q_A4 + q_A5

novelty_total = theory_score + application_score
```

### 8.3 RQ4E：工程 60 + 应用 40

工程新颖度最高 60 分：

| ID | 项目 | 权重 | 最高分 |
|---|---|---:|---:|
| E1 | 功能边界或系统能力相对成熟工程近邻的实质区别 | 3 | 15 |
| E2 | 核心技术机制、架构或算法是否非显然 | 3 | 15 |
| E3 | 组件集成、接口、数据流或人机工作流的新颖性 | 2 | 10 |
| E4 | 是否提出可测量且非微小的质量属性改进 | 2 | 10 |
| E5 | 工程近邻、标准和差异主张的证据覆盖是否充分 | 2 | 10 |

应用新颖度最高 40 分：

| ID | 项目 | 权重 | 最高分 |
|---|---|---:|---:|
| EA1 | 用户、场景或任务设定的新增价值 | 2 | 10 |
| EA2 | 部署、使用或运维方式的实践新颖性 | 2 | 10 |
| EA3 | 可验证的效益、可采用性或运营优势 | 2 | 10 |
| EA4 | 跨域迁移、平台化或未来扩展潜力 | 2 | 10 |

```text
engineering_score = 3q_E1 + 3q_E2 + 2q_E3 + 2q_E4 + 2q_E5

engineering_application_score = 2q_EA1 + 2q_EA2 + 2q_EA3 + 2q_EA4

novelty_total = engineering_score + engineering_application_score
```

两套 `novelty_total` 范围均为 `[0,100]`，但 policy 不可互换。评分是研究资格信号，不是论文录用、专利有效性、商业成功预测或法律意见。

### 8.4 固定路由

```text
if review_valid and novelty_total >= 70 and route == THEORY:
    status = NOVELTY_QUALIFIED
    open_gate = false
    next = S5
elif review_valid and novelty_total >= 70 and route == ENGINEERING:
    status = ENGINEERING_NOVELTY_QUALIFIED
    open_gate = false
    next = ENG0
elif review_valid and novelty_total < 70:
    status = NOVELTY_RESEARCH_REQUIRED
    open_gate = LOW_NOVELTY_RESEARCH_DECISION
else:
    status = INCONCLUSIVE
    open_gate = LOW_NOVELTY_RESEARCH_DECISION
```

分数达到 70 分及以上时必须按已由用户确认的路线自动进入后续流程，不得额外要求普通确认。分数低于 70 或结果不确定时，必须交还用户，不得自动重做研究。

`LOW_NOVELTY_RESEARCH_DECISION` 的合法决定：

- `RERUN_RESEARCH`：保留旧版本，返回 RQ1；
- `REVISE_DESIGN`：生成新的 S1/S4 Revision，旧可行性分析、形式化和评分失效；
- `CONTINUE_WITH_RECORDED_OVERRIDE`：按当前已确认路线继续，但保持 `novelty_status = USER_OVERRIDDEN_BELOW_THRESHOLD`；
- `RETURN_TO_ROUTE_DECISION`：仅工程路线可用；返回 `ENGINEERING_ROUTE_DECISION`；
- `ARCHIVE`；
- `PAUSE`。

### 8.5 输出：`NoveltyReview`

- `review_id`
- `route`
- `policy_version`
- `subject_artifact_id`
- `subject_artifact_hash`
- `neighbor_evidence_set_id`
- `reviewer_session_ids[]`
- `reviewer_scorecards[]`
- `conservative_item_scores`
- `theory_score`（理论路线）
- `application_score`（理论路线）
- `engineering_score`（工程路线）
- `engineering_application_score`（工程路线）
- `novelty_total`
- `coverage_status`
- `status`
- `nearest_overlap_refs[]`
- `strongest_difference_refs[]`
- `limitations[]`
- `artifact_hash`

## 9. 状态、事件与回退不变量

必须写入以下事件：

- `NaturalLanguageDesignReady`
- `FormalizationCapabilitySelected`
- `NeighborSearchCompleted`
- `FormalizationFeasibilityAssessed`
- `EngineeringRouteDecisionOpened`
- `EngineeringRouteSelected`
- `EarlyFormalizationCreated`
- `EngineeringConceptCreated`
- `EarlyFormalizationReviewOpened`
- `EarlyEngineeringConceptReviewOpened`
- `EarlyFormalizationApproved`
- `EarlyEngineeringConceptApproved`
- `NoveltyReviewStarted`
- `NoveltyReviewScored`
- `NoveltyThresholdPassed`
- `EngineeringNoveltyThresholdPassed`
- `NoveltyResearchDecisionOpened`
- `NoveltyResearchRequested`
- `NoveltyOverrideAccepted`

不变量：

1. 所有搜索、可行性分析、形式化、评分和用户决定均不可变；修订创建新版本。
2. S1/S4 hash 变化使下游 RQ Artifact 进入 `NEEDS_REQUALIFICATION`。
3. 邻近工作被新增、撤回或元数据纠正时，Novelty Review 进入 `NEEDS_REGRESSION`。
4. 外部模型输出只属于 Proposal；用户批准只确认语义，不证明理论成立或工程可行。
5. 用户选择工程路线会创建派生 `EngineeringRouteSelection`，不会覆盖原 NaturalLanguageSpec。
6. `NOVELTY_QUALIFIED` 或 `ENGINEERING_NOVELTY_QUALIFIED` 只表示在记录的检索范围和评分政策下达到 70 分。
7. 理论路线不得消费工程评分，工程路线不得消费理论评分。
8. 不得输出“绝对原创”“已获学术认可”“可授予专利”“生产就绪”。

## 10. 失败与阻断

| 条件 | 状态 | 可恢复动作 |
|---|---|---|
| 无合格高能力模型且无外部导入 | `BLOCKED_CAPABILITY` | 用户配置模型或选择外部导入 |
| 学术或工程来源不可用 | `BLOCKED_RETRIEVAL` | 重试、切换 Provider、用户提供来源 |
| 检索覆盖不足 | `INCONCLUSIVE` | 用户决定是否 RQ1 继续研究 |
| 可行性谓词缺少证据 | `FEASIBILITY_INCONCLUSIVE` | 补研究、修订设计或暂停 |
| 纯理论不适配但工程适配 | `ENGINEERING_ROUTE_DECISION_REQUIRED` | 用户修订或选择工程路线 |
| 理论与工程均不适配 | `FORMALIZATION_FEASIBILITY_USER_DECISION_REQUIRED` | 用户修订、补研究、暂停或归档 |
| 公式 Schema 或符号不闭合 | `FORMULA_COVERAGE_INCOMPLETE` | 返回 RQ2M |
| 工程要求或阈值覆盖不足 | `REQUIREMENT_COVERAGE_INCOMPLETE` | 返回 RQ2E 或 S1/S4 |
| Artifact 与 S1/S4 语义不一致 | `SEMANTIC_GAP` | 返回对应 RQ2 或 S1/S4 |
| 用户不批准 | `BLOCKED_FORMALIZATION_USER` | 修订、补检索、暂停或拒绝 |
| Novelty Reviewer 不独立 | `INDEPENDENCE_DEGRADED` | 建立异构隔离 Reviewer；否则仅人工判定 |
| 分数低于 70 | `NOVELTY_RESEARCH_REQUIRED` | 打开用户研究决定 Gate |

## 11. 非目标

- RQ2M 不替代 S7 的正式构造。
- RQ2E 不替代 03B 的需求基线、详细架构、实现蓝图或验证执行。
- RQ4 不替代同行评审、系统综述、查新机构或专利检索意见。
- 新颖性分数不参与 Lean/Z3/Python 的真值判定。
- 用户批准形式化不自动确认后续 ClaimContract 或工程架构。
- 工程项目成熟度只用于选择可信近邻，不直接增加新颖性分。
- 选择工程路线不授权自动实现、付费采购、外部发布、生产部署或论文投稿。

## 12. 最小验收场景

1. S4 通过后直接运行 S5 或 ENG0，返回 `EARLY_QUALIFICATION_REQUIRED`。
2. 普通整理模型未达到能力门，RQ2F 被阻断。
3. 外部包的 `input_spec_hash` 不匹配，导入失败。
4. 只搜索学术文献、不搜索成熟工程项目，RQ1 不得 COMPLETE。
5. 理论谓词全部 PASS，工程谓词任意时按 RQ2M 继续。
6. 理论谓词 FAIL、工程谓词 PASS 时只打开 `ENGINEERING_ROUTE_DECISION`，不得自动转工程。
7. 用户选 `REVISE_FOR_THEORY` 后创建新 Revision，旧 RQ Artifact 保留并失效。
8. 用户选 `TRY_ENGINEERING_PROJECT` 后进入 RQ2E，而不是 RQ2M 或 ENG0。
9. 理论和工程均 FAIL 时不展示“尝试工程项目”的自动继续动作。
10. 核心理论主张只用自然语言时 RQ2M 失败。
11. 工程 success metric 没有阈值也没有 unresolved 标记时 RQ2E 失败。
12. 用户未批准当前 Artifact hash，RQ4 不得启动。
13. 两个 Reviewer 每项评分不同，最终使用逐项较小值。
14. 理论有效总分 70 自动进入 S5。
15. 工程有效总分 70 自动进入 ENG0。
16. 任一路线有效总分 69 打开 `LOW_NOVELTY_RESEARCH_DECISION`。
17. coverage PARTIAL 时即使模型给高分也只能 INCONCLUSIVE。
18. 用户选择重新研究后产生新检索/评分版本，旧记录不删除。
19. 用户低分继续时保留 `USER_OVERRIDDEN_BELOW_THRESHOLD` 和 route。
20. 新发现最近邻后，原 Novelty Review 自动进入 `NEEDS_REGRESSION`。
