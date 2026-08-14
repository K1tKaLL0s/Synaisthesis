# CURRENT_DECISIONS

- 正式中文名：联觉科研
- 简称：联科
- 英文名：Synaisthesis
- Windows 项目根目录：`E:\Synaisthesis`
- 当前工程客户端：OpenCode 或 DeepSeek 官方 DSH；两者共享同一工程规则与任务边界
- 当前工程模型：DeepSeek V4 Pro
- Codex：继续独立推进现有理论验证；产品最终仍需双向 Codex 集成
- 默认自主 Loop：最多 10 轮，用户可配置
- 产品正式科研模式：至少两个异构模型
- 核心验证工具：Lean + Z3 + Python Sandbox
- 核心治理：Semantic Delta、Human Gate、Evidence Ledger、Regression、Revocation
- 开发策略：小 Task、小 commit、FakeModel/FakeTool 先行、UI 后置
- 持久化 ORM：SQLAlchemy 2 + Alembic；不采用 SQLModel 作为领域模型层
- 类型检查：basedpyright（与当前 M0 CI 一致）
- 自然语言设计完成门：S0–S4 PASS 且 S1/S4 用户确认后进入 `NATURAL_LANGUAGE_DESIGN_READY`
- 强制早期资格：S4 后必须执行带 RQ2F 可行性分流的 RQ0–RQ4，不得绕过
- 早期形式化能力：平台 ADVANCED Formalizer 或标准化外部高能力模型导入
- 形式化可行性：理论 TFO–TFP、工程 EFS–EFF 双评估保守聚合；纯理论不适配但工程适配时必须由用户选择修改设计或尝试工程项目
- 理论早期形式化：核心内容必须是数学公式，用户审查 formula/spec hash 与简明解释
- 工程概念形式化：以 I/O、状态、要求谓词、质量阈值、架构图候选和追踪关系表达，不伪装成纯数学理论
- 新颖性：理论路线为理论 50 + 应用 50；工程路线为工程 60 + 应用 40；两个隔离 Reviewer 逐项取较小值
- 自动门槛：有效总分 >=70 时理论路线自动进入 S5、工程路线自动进入 ENG0；<70 或 INCONCLUSIVE 交还用户决定是否重新研究
- 工程交付：ENG0–ENG10 输出可机械执行蓝图、文本图源及渲染图、应用/扩展路线和证据约束 EngineeringMasterManuscript
- 理论论文交付：纯数学路线最终交付必须包含 TheoryMasterManuscript、证明依赖图和 theorem/claim→statement/proof/evidence/citation 追踪矩阵
- 论文顺序：两条路线都先生成并独立审计母稿、先交给用户，再打开 `FORMAL_MANUSCRIPT_DECISION`；无响应不得默认为正式稿
- 正式稿选择：只有用户选择 WRITE_FORMAL_MANUSCRIPT 才打开 PublicationProfile Selection，并生成 VenueAdapter 稿与 ComplianceMatrix；KEEP_MASTER_ONLY 也是完整交付
- 理论内置 Profile：Annals of Mathematics、JAMS、Inventiones mathematicae、Acta Mathematica，加 `MATH_ARXIV_PREPRINT`
- 工程内置 Profile：IEEE TSE、ACM TOSEM、Empirical Software Engineering、Journal of Systems and Software，加 `ENG_ARXIV_PREPRINT`；非软件工程使用 CUSTOM_VENUE
- arXiv 身份：arXiv 是 `PREPRINT_REPOSITORY`，不是期刊、同行评审或录用状态
- 论文适配：不承诺一篇稿件天然满足所有期刊；采用 MasterManuscript + PublicationProfile + VenueAdapter + ComplianceMatrix，且适配不得改变研究语义或证据
- 工程执行边界：默认 BLUEPRINT_ONLY；代码、实验、采购、生产发布与投稿均需各自授权，论文不得虚构结果
- 机械实施：任何代码 Task 必须满足 `19_MECHANICAL_EXECUTION_CONTRACT.md`

V2.3 工程分流与 ENG0–ENG10 已于 2026-08-14 被用户整体采纳；连同双路线论文交付补丁统一冻结为 `V2.4` 正式文档基线。文档冻结不表示相应产品功能已经实现。
