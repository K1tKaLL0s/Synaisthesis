# 03C — 纯数学理论论文交付与双路线内置发布 Profile

本文定义纯数学理论路线的论文交付工作流，并统一规定理论路线、工程路线各自的四种内置主要期刊 Profile 与共享的 arXiv 预印本 Profile。

`arXiv` 是开放预印本平台，不是同行评审期刊。领域模型必须用 `venue_kind = PREPRINT_REPOSITORY` 区分；UI、论文和导出包不得把 arXiv 称为期刊、同行评审或录用状态。

## 1. 适用范围与总原则

### 1.1 理论路线最终交付物

理论路线在完成研究交付时必须追加：

- 一篇期刊中立的 `TheoryMasterManuscript`；
- theorem/claim → statement hash → proof/evidence → citation 的追踪矩阵；
- 符号、定义、引理、定理和证明依赖图；
- 形式证明、计算、代码、数据或反例附件（适用时）；
- 局限性、未解决义务和开放问题；
- AI 使用、作者责任、资助、利益冲突和可用性字段的结构化状态；
- 一份 Master Manuscript 独立审计报告。

母稿是固定交付物。期刊/预印本正式适配稿不是默认自动生成；母稿交付后必须询问用户是否需要按内置 Profile 编写正式论文。

### 1.2 两条路线共享的发布顺序

理论与工程路线都必须采用：

```text
evidence / design delivery ready
              ↓
build route-neutral MasterManuscript
              ↓
independent MasterManuscript audit
              ↓
deliver MasterManuscript to user
              ↓
FORMAL_MANUSCRIPT_DECISION
     ├─ KEEP_MASTER_ONLY → 保存母稿并完成交付
     ├─ WRITE_FORMAL_MANUSCRIPT → 选择内置/自定义 Profile
     ├─ REVISE_MASTER → 新母稿 revision → 重新审计
     └─ PAUSE
              ↓ WRITE
PUBLICATION_PROFILE_SELECTION
              ↓
refresh official author guide
              ↓
generate VenueAdaptedManuscript + ComplianceMatrix
              ↓
independent venue audit
              ↓
FORMAL_MANUSCRIPT_READY / BLOCKED
```

禁止在母稿生成前要求用户选择期刊后再反向塑造研究结论。期刊 Profile 只调整篇幅、结构、元数据、格式、声明、工件和投稿材料，不得改变 theorem statement、工程结果、证据范围或失败记录。

### 1.3 不自动授权的动作

生成母稿或正式适配稿不授权：

- 代表用户确定作者、作者顺序或通讯作者；
- 代表用户接受版权、许可、独家投稿或利益冲突声明；
- 代表用户确认伦理审批、机构批准或资助信息；
- 创建 arXiv/期刊账户、上传文件、正式投稿或发送编辑邮件；
- 把模型列为作者；
- 把预印本写成已同行评审成果。

上述字段状态必须是 `USER_CONFIRMED | NEEDS_AUTHOR_INPUT | NOT_APPLICABLE`；外部动作必须通过独立 Human Gate 和 ActionBroker。

## 2. 双路线内置 Profile Registry

### 2.1 纯数学理论方向四种主要期刊

| Profile ID | 期刊 | venue_kind | 主要适用范围 |
|---|---|---|---|
| `MATH_ANNALS_OF_MATHEMATICS` | Annals of Mathematics | `PEER_REVIEWED_JOURNAL` | 具有广泛数学重要性的重大原创理论结果 |
| `MATH_JAMS` | Journal of the American Mathematical Society | `PEER_REVIEWED_JOURNAL` | 数学各领域高质量、广泛兴趣的研究文章 |
| `MATH_INVENTIONES` | Inventiones mathematicae | `PEER_REVIEWED_JOURNAL` | 具有显著新颖性和深度的纯数学研究 |
| `MATH_ACTA_MATHEMATICA` | Acta Mathematica | `PEER_REVIEWED_JOURNAL` | 重要、完整且具有长期价值的数学研究 |

这些 Profile 是格式与合规适配器，不是“达到该期刊学术门槛”的自动判定器。平台可以给 `SCOPE_FIT_CANDIDATE | SCOPE_FIT_UNCERTAIN | SCOPE_MISMATCH`，不得输出录用概率或“符合顶刊水平”的保证。

### 2.2 工程/软件系统方向四种主要期刊

Synaisthesis 的工程分支主要交付可实施的软件、科研工具和系统工程蓝图，因此默认内置以下四种覆盖软件工程理论、方法、实证和系统实现的期刊：

| Profile ID | 期刊 | venue_kind | 主要适用范围 |
|---|---|---|---|
| `ENG_IEEE_TSE` | IEEE Transactions on Software Engineering | `PEER_REVIEWED_JOURNAL` | 软件工程方法、理论、工具与有证据的系统研究 |
| `ENG_ACM_TOSEM` | ACM Transactions on Software Engineering and Methodology | `PEER_REVIEWED_JOURNAL` | 重要、可复现的软件工程方法与系统成果 |
| `ENG_EMSE` | Empirical Software Engineering | `PEER_REVIEWED_JOURNAL` | 实证研究、研究设计、数据与可复现评价 |
| `ENG_JSS` | Journal of Systems and Software | `PEER_REVIEWED_JOURNAL` | 软件系统、架构、要求、V&V、维护及系统证据 |

工程项目不属于软件/计算系统时，系统必须给 `SCOPE_MISMATCH`，并允许选择 `CUSTOM_VENUE`；不得因为内置 Profile 存在而强迫硬件、生物、化学或其他工程项目套用软件工程期刊。

`JOSS_RESEARCH_SOFTWARE` 和 `NATURE_PORTFOLIO_METHODS_OR_SOFTWARE` 保留为可选扩展 Profile，但不计入本节固定的工程四刊。JOSS 只有在真实研究软件、可浏览源码、许可证、文档和测试均满足其门槛时可用。

### 2.3 两条路线共享的 arXiv Profile

| Profile ID | 显示名称 | venue_kind | 类别范围 |
|---|---|---|---|
| `MATH_ARXIV_PREPRINT` | arXiv Mathematics Preprint | `PREPRINT_REPOSITORY` | `math.*`，按实际主题选择主分类/交叉分类 |
| `ENG_ARXIV_PREPRINT` | arXiv Engineering/Computing Preprint | `PREPRINT_REPOSITORY` | `cs.*`、`eess.*` 或实际适用分类 |

arXiv Profile 必须验证：

- 内容是 topical、refereeable 的科学贡献；
- submitter/author 注册、endorsement、license 和 moderation 状态需要用户处理；
- 优先交付可编译 TeX/LaTeX、AMS-LaTeX 或 PDFLaTeX 源；
- 所有源文件、图、`.bib`/`.bbl`、宏和 ancillary files 完整；
- 文件名只使用 arXiv 允许字符，大小写引用完全一致；
- 在隔离环境使用目标 TeX 版本执行真实编译并保存日志；
- title、abstract、authors、category、comments、license 等 metadata 均有结构化检查；
- 上传前由用户检查 PDF、元数据、许可证和投稿类别；
- 状态只允许 `ARXIV_PACKAGE_READY`，不能写 `PEER_REVIEWED`、`ACCEPTED` 或 `PUBLISHED_IN_JOURNAL`。

## 3. PublicationProfile 的机械合同

每个内置 Profile 必须是版本化、可刷新、可审计的数据包，至少包含：

- `profile_id`, `profile_version`, `route`, `venue_kind`；
- `venue_name`, `publisher_or_operator`；
- `scope_summary` 与 `scope_fit_rules[]`；
- `official_author_guide_urls[]`；
- `official_policy_urls[]`；
- `accessed_at`, `last_modified_if_available`；
- `freshness_days`，默认 30 天；
- `template_files[]`、来源 URL、byte size、SHA-256 和许可证；
- `article_types[]`；
- `submission_format` 与可接受源文件；
- title/abstract/keywords/MSC/section/length/figure/reference 要求；
- anonymity/review model；
- preprint/concurrent-submission/overlap policy；
- author/ORCID/corresponding-author 要求；
- AI/LLM disclosure 规则；
- ethics/conflict/funding/copyright/license 要求；
- data/code/proof/artifact availability 规则；
- supplementary material 规则；
- machine checks、human-only checks 和 blocking checks；
- `profile_hash`。

Profile 的官方 author guide 超过 freshness window、官方页面不可访问或模板 hash 改变时，状态必须是 `STALE_GUIDANCE`，禁止生成 `FORMAL_MANUSCRIPT_READY`。允许生成带明确过时警告的 `VENUE_ADAPTATION_DRAFT`。

## 4. TP0 — 理论证据与语义基线冻结

### 4.1 入口

理论论文流程可以在以下任一状态启动：

- `CANDIDATE_STABLE`；
- `USER_ACCEPTED`；
- 用户明确要求形成研究札记、反例论文、未完成理论报告或开放问题稿件。

RQ4M 必须已通过或有绑定理论 route 的显式用户 override。工程 route 不得进入 TP0。

### 4.2 输出：`TheoryPublicationEvidenceBaseline`

- `baseline_id`, `version`, `project_id`；
- `research_spec_hash`；
- `formalization_hash`；
- `frozen_claim_contract_ids[]`；
- `claim_statement_hashes[]`；
- `theory_revision_ids[]`；
- `proof_artifact_ids[]`；
- `tool_receipt_ids[]`；
- `counterexample_ids[]`；
- `semantic_audit_ids[]`；
- `human_decision_ids[]`；
- `citation_evidence_set_id`；
- `unresolved_obligations[]`；
- `retracted_or_superseded_evidence[]`；
- `evidence_tier`；
- `artifact_hash`, `status`。

### 4.3 证据等级与允许论文类型

| evidence_tier | 允许类型 | 禁止主张 |
|---|---|---|
| `PROVED_AND_SEMANTICALLY_ACCEPTED` | `FULL_THEORY_ARTICLE` | 超出冻结 statement、对象域或假设的推广 |
| `FORMALLY_VERIFIED` | `FORMALIZED_THEORY_ARTICLE` | Lean/Z3 Scope 之外的绝对真值 |
| `COMPUTER_ASSISTED_PROOF` | `COMPUTER_ASSISTED_THEORY_ARTICLE` | 不披露代码、算法、误差与独立检查 |
| `COUNTEREXAMPLE_OR_NEGATIVE_RESULT` | `NEGATIVE_RESULT_ARTICLE` | 把有限反例推广为未证明的一般结论 |
| `PARTIAL_THEORY` | `RESEARCH_NOTE`, `CONJECTURE_OR_OPEN_PROBLEM_ARTICLE` | 把未完成命题写成 theorem/proved |
| `DESIGN_ONLY` | `THEORY_PROTOCOL_OR_PROGRAMME_DRAFT` | 已完成证明、实验或验证 |

Evidence tier 由确定性规则计算，不允许模型自由选择更高等级。

## 5. TP1 — TheoryMasterManuscript

### 5.1 母稿结构

母稿至少包含：

1. title、running title（适用时）；
2. self-contained abstract；
3. Mathematics Subject Classification、keywords；
4. introduction：问题、背景、意义和贡献边界；
5. related work 与最近邻差异；
6. notation and preliminaries；
7. definitions and assumptions；
8. main results；
9. proof architecture 与依赖顺序；
10. complete proofs，或对未完成部分的明确状态；
11. examples、counterexamples、boundary cases；
12. formal/computational verification methods 与 Scope；
13. limitations、threats to correctness、unresolved obligations；
14. implications、applications 和 open problems；
15. proof/code/data/materials availability；
16. acknowledgements、funding、conflicts、author contributions、AI-use disclosure 的结构化状态；
17. complete references。

### 5.2 `MathematicalManuscriptClaim`

每个定理性表述必须包含：

- `manuscript_claim_id`；
- `kind = DEFINITION | ASSUMPTION | LEMMA | PROPOSITION | THEOREM | COROLLARY | CONJECTURE | COUNTEREXAMPLE | APPLICATION_CLAIM`；
- `display_statement`；
- `normalized_statement_hash`；
- `source_claim_contract_id`；
- `object_domain`、`quantifiers`、`assumptions[]`、`conclusion`；
- `proof_status`；
- `proof_artifact_ids[]`；
- `tool_receipt_ids[]`；
- `semantic_status`；
- `citation_refs[]`；
- `limitations[]`；
- `manuscript_locations[]`。

`THEOREM | LEMMA | PROPOSITION | COROLLARY` 只有在对应 Evidence tier 允许且 proof status 非 `INCOMPLETE` 时才能出现。否则必须改成 `CONJECTURE`、`OPEN_PROBLEM` 或明确的 conditional statement，不能只在脚注中弱化。

### 5.3 Proof Dependency Graph

```text
G_proof = (V, E)

V = Definitions ∪ Assumptions ∪ Lemmas ∪ Theorems ∪ Corollaries

E = {(u, v) | proof(v) directly depends on u}
```

图必须无未声明循环；每个主定理的全部上游定义、假设、引理和外部定理可追踪。引用外部结果时必须记录精确版本、定理编号/位置和适用条件。

### 5.4 母稿源文件

至少交付：

- `master.tex`；
- `references.bib`；
- `macros.tex`；
- `sections/*.tex`；
- `figures/source/*` 与渲染图；
- `proof_dependency_graph.*`；
- `claim_evidence_matrix.yaml`；
- `compile_environment.yaml`；
- 编译命令与真实 log；
- PDF；
- checksums。

## 6. TP2 — 母稿审计与用户决策

### 6.1 独立母稿审计

未参与初稿生成的 `THEORY_MANUSCRIPT_AUDITOR` 必须检查：

- 题目、摘要、引言、定理与结论是否忠于冻结 ResearchSpec；
- object domain、quantifier、assumption、conclusion 与 statement hash 一致；
- 定理、引理和引用的 proof/evidence 状态没有越权；
- Proof Dependency Graph 闭合且外部定理适用条件完整；
- 反例、失败尝试、限制和 Scope 没有被隐藏；
- citation 可解析且没有捏造；
- TeX/PDF 在锁定环境真实编译；
- 作者责任字段没有被模型虚构。

Critical/Major finding 必须完成一次定向返工后重审；仍失败则状态 `BLOCKED_THEORY_MASTER_MANUSCRIPT`。

### 6.2 母稿交付

审计通过后状态为 `THEORY_MASTER_MANUSCRIPT_READY`。平台必须先向用户交付：

- Master PDF 与 TeX source；
- evidence tier；
- 核心 theorem/claim 列表；
- 未解决义务；
- 独立审计结论；
- 四种理论期刊和 arXiv Profile 的 scope-fit 候选结果；
- “正式适配不会改变数学结论”的说明。

### 6.3 `FORMAL_MANUSCRIPT_DECISION`

Gate 必须绑定 `master_manuscript_id + version + master_hash + evidence_baseline_hash`。合法决定：

- `KEEP_MASTER_ONLY`：母稿即论文交付物，不生成正式适配稿；
- `WRITE_FORMAL_MANUSCRIPT`：进入 `PUBLICATION_PROFILE_SELECTION`；
- `REVISE_MASTER`：生成新 revision 并返回 TP1；
- `PAUSE`。

禁止把无响应解释为同意编写正式论文。

## 7. TP3 — Profile 选择与正式适配

### 7.1 `PUBLICATION_PROFILE_SELECTION`

理论路线合法 Profile：

- `MATH_ANNALS_OF_MATHEMATICS`；
- `MATH_JAMS`；
- `MATH_INVENTIONES`；
- `MATH_ACTA_MATHEMATICA`；
- `MATH_ARXIV_PREPRINT`；
- `CUSTOM_VENUE`。

选择界面必须展示：venue kind、scope-fit、官方指南更新时间、模板、篇幅/结构关键差异、预印本/重复投稿政策、开放/版权要求和需要用户补充的字段。

用户选择期刊/平台只授权生成适配稿，不授权投稿。

### 7.2 适配动作

允许：

- 套用官方或允许的 LaTeX class/template；
- 调整 title page、abstract length、MSC、keywords、heading、references、figure placement 和 supplementary files；
- 生成 cover-letter draft、suggested editor/referee 字段或 submission checklist；
- 依据 Profile 生成 AI/LLM、code/data/proof availability 等声明草案；
- 为 arXiv 生成分类和 metadata 候选、source archive 和编译检查。

禁止：

- 删除或弱化关键假设以满足篇幅；
- 将 conjecture 升格为 theorem；
- 修改 statement hash；
- 隐藏负结果、限制或计算依赖；
- 虚构作者、机构、ORCID、编辑、审稿人、许可或声明；
- 为迎合期刊范围捏造应用。

## 8. TP4 — VenueComplianceMatrix 与正式论文审计

每条 Profile 要求输出：

- `requirement_id`；
- `source_url`、`accessed_at`；
- `check_type = MACHINE | HUMAN`；
- `status = PASS | FAIL | NEEDS_AUTHOR_INPUT | NOT_APPLICABLE | STALE_GUIDANCE`；
- `manuscript_location`；
- `evidence_artifact_id`；
- `blocking`；
- `rationale`。

正式论文只有在以下条件全部满足时为 `FORMAL_MANUSCRIPT_READY` 或 `ARXIV_PACKAGE_READY`：

- 母稿 hash 与适配输入一致；
- 指南未过期；
- 所有 machine blocking checks 为 PASS；
- human-only blocking 项已由用户确认，或保持 `NEEDS_AUTHOR_INPUT` 并将整体状态降为 `FORMAL_MANUSCRIPT_DRAFT`；
- statement/evidence/citation 追踪 100%；
- TeX 与 PDF 真实编译；
- 独立 Auditor 无 Critical/Major；
- 没有 unsupported theorem/result claim。

## 9. TP5 — 理论论文交付包

```text
theory_publication_delivery/
├── 00_manifest.yaml
├── 01_evidence_baseline/
├── 02_master_manuscript/
│   ├── master.tex
│   ├── master.pdf
│   ├── sections/
│   ├── macros.tex
│   ├── references.bib
│   ├── figures/
│   ├── proof_dependency_graph.*
│   └── claim_evidence_matrix.yaml
├── 03_master_audit/
├── 04_formal_manuscript_decision.yaml
├── 05_publication_profile/             # 用户选择正式适配时存在
├── 06_venue_adapted_manuscript/        # 用户选择正式适配时存在
├── 07_compliance_matrix/                # 用户选择正式适配时存在
├── 08_proof_and_reproducibility_artifact/
├── 09_author_input_register/
└── 10_checksums.sha256
```

`KEEP_MASTER_ONLY` 时 05–07 不存在是合法状态；manifest 必须明确 `formal_manuscript_requested = false`，不能把缺失误报为不完整。

## 10. 与工程论文流程的统一约束

工程路线的 03B 必须遵守本文件第 1–3 节：

- ENG8 先生成并审计 `EngineeringMasterManuscript`；
- 母稿交付后打开同名 `FORMAL_MANUSCRIPT_DECISION`；
- 用户选择 `WRITE_FORMAL_MANUSCRIPT` 后才允许选择工程四刊、工程 arXiv 或扩展 Profile；
- `KEEP_MASTER_ONLY` 是完整合法交付；
- 期刊/预印本适配不得改变 Requirement、Architecture、V&V 或 Evidence；
- arXiv 始终是 `PREPRINT_REPOSITORY`。

## 11. 回归与撤回

| 变化 | 回退点 |
|---|---|
| ResearchSpec、对象域、量词或核心假设变化 | RQ / TP0 |
| FrozenClaim statement hash 变化 | TP0 |
| Proof/Evidence 撤回或工具版本使结果失效 | TP0 / TP1 |
| 新最近邻改变引用或新颖性边界 | RQ1 / TP1 |
| 母稿内容变化 | TP2 独立审计 |
| 用户改 Profile | TP3，新适配稿 revision |
| 官方指南或模板更新 | TP3 / TP4 |
| 作者、机构、许可或声明变化 | TP4 |
| arXiv 新版本 | 新 package revision，保留旧版本 |

所有母稿、适配稿、Profile snapshot、审计和用户决定不可覆盖；只能新建 revision 并标记旧版本 `SUPERSEDED`、`RETRACTED` 或 `NEEDS_REGRESSION`。

## 12. 最小验收场景

1. 理论路线完成交付但没有论文母稿，最终 Bundle 不得 READY。
2. 工程 route 尝试进入 TP0，返回 `THEORY_ROUTE_REQUIRED`。
3. 未完成证明被写成 theorem，母稿审计失败。
4. Lean PASS 的 statement hash 与稿件定理不同，阻断母稿。
5. Z3 UNSAT 被写成无 Scope 的一般定理，阻断母稿。
6. 负结果论文隐藏反例范围或失败记录，阻断母稿。
7. 母稿未先交付用户就直接选择期刊，阻断正式适配。
8. 用户选择 KEEP_MASTER_ONLY，论文交付完整且不生成期刊稿。
9. 用户选择 WRITE_FORMAL_MANUSCRIPT 后才打开 Profile Selection。
10. 用户无响应不能被当作 WRITE。
11. Profile 选择 Annals，系统按官方指南快照检查摘要、完整参考文献、LaTeX/图源和 AI 责任字段。
12. Profile 选择 JAMS，系统检查 MSC、投稿独占性、author package 和用户责任字段。
13. Inventiones 或 Acta 官方指南超过 freshness window，状态为 STALE_GUIDANCE。
14. arXiv 被 UI 或导出称为期刊，测试失败。
15. arXiv TeX 在锁定环境不能编译，不得 ARXIV_PACKAGE_READY。
16. arXiv 源缺图、`.bib/.bbl` 或自定义宏，不得 READY。
17. 用户选择工程四刊中的不适用 Profile 时显示 SCOPE_MISMATCH，并要求确认 custom venue，而不是静默套用。
18. 期刊适配改变 theorem statement hash，立即阻断并撤销旧合规状态。
19. `NEEDS_AUTHOR_INPUT` 未解决时可生成 Draft，但不得 Ready 或投稿。
20. manifest、TeX/PDF、Profile、矩阵、proof graph 和 checksums 可重算一致。
