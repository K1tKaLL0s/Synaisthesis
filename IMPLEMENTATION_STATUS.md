# Synaisthesis Implementation Status

## Current milestone
`M2`（Stage 2.6 进行中：M2.10 已提交 PASS，M2.11 待推进）

## Current task
`M2.10.ENGINEERING.MECHANICAL_BLUEPRINT`

## Last verified commit
`3070c49`（M2.10 已提交）

## Blueprint baseline
正式文档基线为 `V2.4`（2026-08-14）：用户已整体采纳 V2.3 的 RQ2F 理论/工程可行性分流、强制工程路线决定、工程概念/新颖性审验及 ENG0–ENG10 设计；V2.4 进一步加入纯理论论文固定交付、双路线母稿独立审计、母稿交付后的正式稿决策，以及理论四刊、工程四刊和双路线 arXiv Profile。该基线只表示文档语义，不表示相关产品功能已实现。V2.4 已追加一处补丁：定义 `evidence.status` 枚举值 `ACTIVE`/`REVOKED`（`revoked_at` 为权威标记），并重建汇编版与 manifest。

## Active work unit
- Stable Task ID: `M6.2.ROLE.ISOLATION`
- Milestone: `M6`（Stage 6 第 2 个 Task：角色隔离与 Council 服务底座）
- WorkUnitContract: `workspace/workunit-contracts/M6.2.ROLE.ISOLATION.md`
- 交付：三轨隔离（SUPPORT/OPPOSE/INDEPENDENT_REVIEWER ≥ SESSION）、VisibilityBundle 来源可证、同家族 degraded、注入阻断；council_service run/round/会话底座。

## Environment
- Project root: `E:\Synaisthesis`
- Primary engineering client: OpenCode or official DeepSeek DSH
- Primary engineering model: DeepSeek V4 Pro
- Python: 3.14.4（WSL2）；兼容目标 >=3.11，已在 3.11.15 实测通过
- uv: 0.12.3
- Git: 2.53.0
- Docker: 29.7.2
- Z3: 5.0.0（M0 未使用，仅记录）
- Lean: 4.32.2（Lake 5.0.0，M0 未使用，仅记录）
- Node.js: WSL 全局 `NOT_FOUND`（项目仍使用 basedpyright）；DSH 使用 E 盘隔离 Linux Node.js 24.19.0
- venv: `/home/chaos/.venvs/synaisthesis`（WSL ext4）；仓库内 `.venv` 为符号链接
- SQLAlchemy: 2.0.52（M1.3 新增生产依赖）；Alembic: 1.19.1（M1.3 新增生产依赖）

## Implemented
- 工程骨架：`pyproject.toml`（uv、requires-python >=3.11）、`src/synaisthesis` 布局、`configs/`、`tests/unit/`、`.github/workflows/ci-core.yml`（CI matrix 3.11 / 3.14）
- `get_version`（version.py）、`load_settings`（config/loaders.py）、`validate_settings`（config/validation.py，Pydantic v2 严格校验，拒绝未知键/越界端口/非法枚举/类型错误）
- CLI `synaisthesis --version`（interfaces/cli/main.py，Typer）
- 项目文件：README、LICENSE（Apache-2.0）、SECURITY、CONTRIBUTING、.gitignore
- `docs/adr/0001-python-compatibility-311-plus.md`
- AGENTS.md：新增 N 盘 `N:\CodexData` 记录与不得修改 Codex 理论仓库条款
- 蓝图文档：`03A` 已升级为路线化可行性/形式化/新颖性合同；`03B` 定义工程转化与机械蓝图；新增 `03C_THEORY_PUBLICATION_AND_DUAL_TRACK_VENUE_PROFILES.md`，定义理论论文固定交付、双路线母稿审计/用户决策、八种期刊 Profile 与两种 arXiv 预印本 Profile，并同步数据、API/CLI/MCP、Gate、实施、测试、配置、路线、参考与机械 Task（不代表功能已实现）
- M1.1 领域基元：`domain/enums.py`（StageId/ProgressKind/StageGateStatus/ProjectLifecycleStatus/ProvenanceType/EvidenceType/EvidenceStrength/IndependenceStatus，`StrictStrEnum` 严格拒绝未知值）、`domain/errors.py`（DomainError/ConflictError/InvalidEnumValueError，07 §19 统一错误对象）、`domain/event.py`（DomainEvent，确定性 SHA-256 内容 hash + 稳定 JSON 序列化）、`domain/policies.py`（IdempotencyContext + check_expected_version，expected_version 不匹配 → CONFLICT）
- M1.2 领域聚合：`domain/project.py`（Project，frozen + change_lifecycle）、`domain/research_spec.py`（ResearchSpec，确认后不可原地覆盖、改动必须 new_version）、`domain/stage.py`（StageRun，complete 一次性）、`domain/revision.py`（Revision，不可变链 + immutable_hash + create_child）、`domain/evidence.py`（Evidence，revoke 保留历史）；`domain/event.py` 公开 `canonicalize/canonical_json/sha256_hex` 供聚合复用
- 蓝图补丁（evidence.status 缺口）：06 §1 定义 `EvidenceStatus = ACTIVE | REVOKED`，同步 `domain/enums.py::EvidenceStatus` 与 `domain/evidence.py::Evidence.status`（派生属性，`revoked_at` 为权威标记）
- M1.3 持久化底座：`storage/database.py`（Base + init_database，不静默建表）、`storage/hashing.py`（sha256_bytes/sha256_file/verify_artifact_hash）、`storage/artifact_store.py`（ArtifactRecord + save_artifact 内容寻址）、`storage/repositories/event_repository.py`（DomainEventRecord + append_domain_event）、首个 Alembic migration（`storage/migrations/`，可 upgrade/downgrade）
- M1.4 Project 纵向切片：`storage/repositories/project_repository.py`（事件溯源 save_project/load_project、ProjectCreated/ProjectLifecycleChanged、project_state_dict/project_from_state）、`application/project_service.py`（create_project/get_project）、`interfaces/cli/commands/project.py`（`project create`/`project show`，schema 自动 upgrade，DomainError → exit 1）、`interfaces/cli/main.py` 注册 project 子命令
- M2.1 S0–S1 合同：`domain/stage.py` 新增 StageContract 15 字段合同 + `S0_STAGE_CONTRACT`/`S1_STAGE_CONTRACT` + `validate_seed_record`/`validate_natural_language_spec`（duck-typed，领域层零框架依赖）；`agents/schemas.py`（SeedRecord、NaturalLanguageSpec，Pydantic v2，extra="forbid"，13 必填字段强制）；`application/incubation_service.py`（capture_seed/load_seed 带 raw_hash 校验、propose/confirm/load_natural_language_spec 带真实用户事件 provenance、validate_stage_output、evaluate_stage_gate）；`prompts/incubator/s0_capture_seed.md`、`s1_natural_language_spec.md`（prompt_key/version/golden/forbidden）
- M2.2 S2–S4 合同与设计完成门：`domain/stage.py` 新增 `S2_STAGE_CONTRACT`/`S3_STAGE_CONTRACT`/`S4_STAGE_CONTRACT` + `validate_mechanism_sketch`/`validate_prior_work_map`/`validate_research_scope_spec`；`agents/schemas.py`（MechanismSketch、PriorWorkMap、ResearchScopeSpec，Pydantic v2，extra="forbid"；`search_queries` 用稳定键 `academic`/`engineering`）；`application/incubation_service.py`（S2/S3/S4 propose/load、S4 真实用户确认、`ResearchSpecBound` 事件绑定 S1/S4 hash + content_hash、`evaluate_natural_language_design_ready` 纯函数/事件流版本、`derive_natural_language_design_ready` 追加 Project 生命周期事件）；`prompts/incubator/s2_mechanism_sketch.md`、`s3_prior_work_map.md`、`s4_research_scope_spec.md`（prompt_key/version/golden/forbidden）
- M2.3 RQ 领域底座：`domain/enums.py` 追加 21 个 M2.3 稳定枚举；`domain/qualification.py`（ModelProfile、FormalizationCapabilityProfile/Decision、PriorArtQueryRecord/PriorArtNeighbor/NeighborEvidenceSet、T*/E* 谓词、FormalizationFeasibilityAssessment、EngineeringRouteSelection、FormulaItem/EarlyFormalizationBundle/EngineeringConceptBundle、RQ3 审批、19 个事件名 + build_qualification_event）；`domain/novelty.py`（THEORY_NOVELTY_POLICY/ENGINEERING_NOVELTY_POLICY、NoveltyScorecard、保守 min 聚合、route_novelty_decision、NoveltyReview、LowNoveltyOverride）；`domain/gate.py`（GateBinding、Gate、allowed_decisions_for_gate、qualification_next_target）；migration 0002（12 张表）
- M2.4 Fake 检索纵切片：`providers/prior_art/base.py`（PriorArtProvider Protocol、ExternalText、ProximityFeature、ProviderNeighborRecord、PriorArtQueryRequest）；`providers/prior_art/normalization.py`（相似度权重计算、去重、排序、rank）；`providers/prior_art/fake.py`（确定性 Fake 学术/工程语料，去重后 5 学术 + 3 工程，来源 3+2）；`application/qualification_service.py`（run_prior_art_search、validate_prior_art_coverage、neighbor_evidence_content_payload）
- M2.4A RQ2F 双评估与 Gate：`domain/qualification.py`（FeasibilityPredicate 强制证据引用、FeasibilityPredicateMatrix、merge_feasibility_matrices、FeasibilityAssessmentSession、assessment_context_hash）；`agents/early_formalizer.py` + `agents/engineering_feasibility_assessor.py`（确定性 T*/E* 矩阵）；`application/qualification_service.py`（assess_formalization_feasibility_from_matrices/assess_formalization_feasibility/open_formalization_feasibility_gate/resolve_engineering_route_decision/resolve_formalization_feasibility_decision）；`prompts/formalization/feasibility_*`；migration 0003（role_sessions）
- M2.5 RQ2M：`agents/schemas.py`（FormulaItemModel/EarlyFormalizationBundleModel）；`agents/early_formalizer.py`（10 类公式类型常量、build_formula_items、validate_formula_items）；`application/qualification_service.py`（build_early_formula_bundle、validate_early_formula_bundle、open/resolve_early_formalization_review）；`prompts/formalization/early_formalization.md`
- M2.5B RQ2E：`agents/engineering_feasibility_assessor.py`（build_engineering_concept_bundle、engineering_concept_content_payload）；`application/qualification_service.py`（validate_engineering_concept_bundle、open/resolve_early_engineering_concept_review）；`prompts/engineering/concept_engineering.md`
- M2.6 Novelty 服务：`domain/novelty.py`（NoveltyItemEvidence、NoveltyReview.create review_valid）；`agents/novelty_reviewer.py` + `agents/auditor.py`（隔离 Reviewer/Auditor）；`application/novelty_service.py`（start_novelty_review、open/resolve_low_novelty_research_decision）
- M2.7 S5 纵切片：`agents/schemas.py`（MinimalCaseBundle）；`application/incubation_service.py`（propose/load_minimal_case_bundle、MinimalCaseProposed）；`orchestration/nodes/incubator_nodes.py`（s5_qualification_node）；`prompts/incubator/s5_minimal_case.md`
- M2.8 工程工作流领域：`domain/engineering.py`（EngineeringStageId ENG0–ENG10、EngineeringArtifactStatus、EngineeringDeliveryMode、EngineeringDeliveryStatus 全表 32 值、EngineeringChangeKind、EngineeringGateType 与四组工程 Gate 决策枚举、ENGINEERING_EVENT_TYPES + build_engineering_event、finalize_artifact_hash/superseded、eng0_entry_blockers 03B §1.1 结构化 Blocker、EngineeringMissionCharter（proposed_additions 分离 + ENGINEERING_SCOPE_CHANGE）、OperationalConceptBundle + conops_blockers、EngineeringReferenceSet/OptionTradeStudy（Σw=1、Critical 硬淘汰、eligible_ranking）/TechnologySelectionRecord/RejectedOptionLog、MechanicalEngineeringBlueprint + EngineeringWorkUnitContract（模糊措辞拒绝）+ blueprint_completeness_blockers、ApplicationDirectionPortfolio/ExtensionRoadmap、engineering_regression_check 03B §14 确定性最早回退 + artifact_needs_regression）；`domain/requirements.py`（RequirementType/VerificationMethod/RequirementPriority、EngineeringRequirement（无阈值形容词拒绝/UNRESOLVED_THRESHOLD）、RequirementsBaseline + requirements_baseline_blockers 03B §5.4、AcceptanceCriteriaCatalog、QualityAttributeScenarioSet、SecurityPrivacyComplianceObligationSet（AI 义务六字段）、UnresolvedDecisionRegister）；`domain/architecture.py`（ArchitectureComponent 稳定 ID、ArchitectureDiagram（源/SVG hash + 渲染回执 + 断链拒绝）、InterfaceContractSet/DataContractSet/StateAndFailureModel/ThreatModel/DeploymentAndOperationsDesign、ArchitectureBaseline、ArchitectureReviewBinding 三 hash）；`domain/traceability.py`（RequirementsTraceabilityMatrix + traceability_coverage、VerificationPlan/ValidationPlan/VerificationReport/ValidationReport（PASS 必须真实回执））；`domain/publication.py`（EngineeringEvidenceTier/EngineeringPaperType + paper_type_allowed_by_evidence 03B §11.1、ClaimEvidenceMatrix（SUPPORTED 必须回执）、EngineeringMasterManuscript（author 字段 NEEDS_AUTHOR_INPUT/USER_PROVIDED 强制、master_hash 内容绑定）、VenueComplianceStatus PASS/FAIL/NEEDS_AUTHOR_INPUT/NOT_APPLICABLE/STALE_GUIDANCE）；`domain/gate.py`（EngineeringGateBinding + EngineeringGate + engineering_allowed_decisions_for_gate，仅真实用户事件可决议）；`domain/__init__.py` 导出；migration 0004（engineering_workflow_runs/engineering_requirements/engineering_trace_edges/engineering_manuscripts，按 06 §）；`.gitignore` 追加 `.dsh-upstream/`（DSH 环境本会话在仓库内创建的未跟踪目录，避免误提交与本地门禁污染）

## Verified
- `uv run pytest`：11 passed（Python 3.14.4 与 3.11.15 均通过）
- `uv run ruff check .`：通过；`uv run ruff format --check .`：通过
- `uv run basedpyright`：0 errors, 0 warnings
- `uv run synaisthesis --version`：输出 `0.1.0.dev0`
- 依赖零 LLM（pydantic / pydantic-settings / pyyaml / typer）
- DOC-V2.2 蓝图完整性：manifest 26 个记录全部 size/SHA-256 匹配；24 个权威分册与汇编版逐字重建一致；24 个 SOURCE marker 顺序匹配；分册无重复编号 H2
- DOC-V2.3-draft 蓝图完整性：manifest 27 个记录全部 size/SHA-256 匹配；25 个权威分册与汇编版逐字重建一致；25 个 SOURCE marker 顺序匹配；代码围栏平衡；分册无重复 H2；本地 Markdown 链接均可解析
- DOC-V2.4 蓝图完整性：manifest 28 个记录全部 size/SHA-256 匹配；26 个权威分册与汇编版逐字重建一致；26 个 SOURCE marker 顺序匹配；代码围栏平衡；分册无重复 H2；本地 Markdown 链接均可解析；活动状态文件无 V2.3 待确认残留
- 工程开发 Profile：允许 OpenCode 或 DeepSeek 官方 DSH 作为工程客户端；两者共享 `AGENTS.md`、WorkUnitContract、Human Gate 与验证规则
- DeepSeek Harness：E 盘隔离安装 `@deepseek-ai/dsh@0.1.0-rc.6`；Node 24.19.0 官方 SHA-256 PASS；530 个包 registry signature PASS、63 个 attestation PASS；`npm audit --omit=dev` 为 0 vulnerabilities
- DSH 桌面壳目标命令：systemd user service active、官方默认 `http://127.0.0.1:3080` 返回 HTTP 200（12109 bytes）、Chrome 顶层窗口标题为 `DeepSeek Harness`、单实例 keeper 持锁；桌面快捷方式改为直接调用 `wsl.exe` 后连续 30 秒持久性检查 PASS；未录入或读取 API key，未执行真实模型请求
- `git diff --check`：通过（仅有仓库既有的 LF→CRLF 提示，无 whitespace error）
- M1.1：`uv run --no-sync pytest tests/unit/domain/test_primitives.py` 36 passed；全套 `uv run --no-sync pytest` 47 passed；`uv run --no-sync ruff check .` 通过；`uv run --no-sync ruff format --check .` 通过；`uv run --no-sync basedpyright` 0 errors, 0 warnings（只读 venv 沙箱使用 `UV_CACHE_DIR` + `--no-sync`，见 CONTRIBUTING.md）
- M1.2：`uv run --no-sync pytest tests/unit/domain/test_aggregates.py` 20 passed；全套 `uv run --no-sync pytest` 67 passed；`uv run --no-sync ruff check .` 通过；`uv run --no-sync ruff format --check .` 通过；`uv run --no-sync basedpyright` 0 errors, 0 warnings
- 蓝图补丁（evidence.status）：重建汇编版后 manifest 全量完整性校验 `integrity ok: True`；代码侧全套 pytest 68 passed、ruff/basedpyright 通过
- M1.3：`pytest tests/integration/storage/test_event_artifact_store.py` 5 passed；全套 `pytest` 73 passed；`ruff check .` 通过；`ruff format --check .` 通过（72 files）；`basedpyright` 0 errors, 0 warnings（沙箱只读 venv 无法安装新依赖，改用 `workspace/.venv-m13` 独立 venv 运行，basedpyright 以 `--pythonpath` 指向该 venv）
- M1.4：`workspace/.venv-m13/bin/python -m pytest tests/integration/test_project_vertical_slice.py` 8 passed；全套 `workspace/.venv-m13/bin/python -m pytest` 81 passed；`workspace/.venv-m13/bin/ruff check .` 通过；`workspace/.venv-m13/bin/ruff format --check .` 通过（78 files）；`UV_CACHE_DIR=/tmp basedpyright --pythonpath workspace/.venv-m13/bin/python` 0 errors, 0 warnings
- M1.4 CLI 真实 smoke：`workspace/.venv-m13/bin/synaisthesis --version` 输出 `0.1.0.dev0`；在 `/tmp` 独立目录真实执行 `project create --name "联觉纵向切片 smoke" --description "M1.4 real CLI"` 后：输出单行 canonical JSON、payload Artifact 落盘（`events/{id}/{event_id}.json`）、`project show` 输出与 create 逐字节一致（ROUNDTRIP OK）、不存在的 project 输出 `PROJECT_NOT_FOUND` 且 exit=1；测试目录随后已清理
- M2.1：`workspace/.venv-m13/bin/python -m pytest tests/golden/test_s0_s1.py` 14 passed；全套 `workspace/.venv-m13/bin/python -m pytest` 95 passed；`workspace/.venv-m13/bin/ruff check .` 通过；`workspace/.venv-m13/bin/ruff format --check .` 通过（84 files）；`UV_CACHE_DIR=/tmp basedpyright --pythonpath workspace/.venv-m13/bin/python` 0 errors, 0 warnings；`git diff --check` 通过
- M2.2：`workspace/.venv-m13/bin/python -m pytest tests/golden/test_s2_s4.py` 18 passed；全套 `workspace/.venv-m13/bin/python -m pytest` 113 passed；`workspace/.venv-m13/bin/ruff check .` 通过；`workspace/.venv-m13/bin/ruff format --check .` 通过（88 files）；`UV_CACHE_DIR=/tmp /home/chaos/.venvs/synaisthesis/bin/basedpyright --pythonpath /mnt/e/Synaisthesis/workspace/.venv-m13/bin/python` 0 errors, 0 warnings；`git diff --check` 通过
- M2.3：`workspace/.venv-m13/bin/python -m pytest tests/unit/domain/test_research_qualification.py` 22 passed；全套 `workspace/.venv-m13/bin/python -m pytest` 135 passed；`workspace/.venv-m13/bin/ruff check .` 通过；`workspace/.venv-m13/bin/ruff format --check .` 通过（93 files）；`UV_CACHE_DIR=/tmp /home/chaos/.venvs/synaisthesis/bin/basedpyright --pythonpath /mnt/e/Synaisthesis/workspace/.venv-m13/bin/python` 0 errors, 0 warnings；`git diff --check` 通过
- M2.4：`workspace/.venv-m13/bin/python -m pytest tests/contract/prior_art/test_fake_prior_art.py` 14 passed；全套 `workspace/.venv-m13/bin/python -m pytest` 149 passed；`workspace/.venv-m13/bin/ruff check .` 通过；`workspace/.venv-m13/bin/ruff format --check .` 通过（100 files）；`UV_CACHE_DIR=/tmp /home/chaos/.venvs/synaisthesis/bin/basedpyright --pythonpath /mnt/e/Synaisthesis/workspace/.venv-m13/bin/python` 0 errors, 0 warnings；`git diff --check` 通过
- M2.4A：`workspace/.venv-m13/bin/python -m pytest tests/unit/application/test_formalization_feasibility.py tests/golden/test_engineering_route_gate.py` 17 passed；全套 `workspace/.venv-m13/bin/python -m pytest` 166 passed；`workspace/.venv-m13/bin/ruff check .` 通过；`workspace/.venv-m13/bin/ruff format --check .` 通过（107 files）；`UV_CACHE_DIR=/tmp /home/chaos/.venvs/synaisthesis/bin/basedpyright --pythonpath /mnt/e/Synaisthesis/workspace/.venv-m13/bin/python` 0 errors, 0 warnings；`git diff --check` 通过
- M2.5：`workspace/.venv-m13/bin/python -m pytest tests/golden/test_early_formalization.py` 11 passed；M2.5B：`tests/golden/test_engineering_concept.py tests/unit/application/test_engineering_concept_review.py` 9 passed；全套 `workspace/.venv-m13/bin/python -m pytest` 186 passed；`ruff check .` 通过；`ruff format --check .` 通过（112 files）；`basedpyright` 0 errors, 0 warnings；`git diff --check` 通过
- M2.6：`workspace/.venv-m13/bin/python -m pytest tests/unit/application/test_novelty_service.py tests/golden/test_novelty_gate.py` 9 passed；全套 `workspace/.venv-m13/bin/python -m pytest` 195 passed；`ruff check .` 通过；`ruff format --check .` 通过（117 files）；`basedpyright` 0 errors, 0 warnings；`git diff --check` 通过
- M2.7：`workspace/.venv-m13/bin/python -m pytest tests/integration/test_qualification_to_s5.py` 7 passed；全套 `workspace/.venv-m13/bin/python -m pytest` 202 passed；`ruff check .` 通过；`ruff format --check .` 通过（122 files）；`basedpyright` 0 errors, 0 warnings；`git diff --check` 通过
- M2.8：`workspace/.venv-m13/bin/python -m pytest tests/unit/domain/test_engineering_workflow.py tests/unit/domain/test_engineering_traceability.py` 66 passed；全套 `workspace/.venv-m13/bin/python -m pytest` 268 passed（含 migration 0004 升级/降级）；`ruff check .` 通过；`ruff format --check .` 通过（130 files）；`basedpyright` 0 errors, 0 warnings；`git diff --check` 通过
- M2.9：`workspace/.venv-m13/bin/python -m pytest tests/unit/application/test_engineering_requirements.py tests/integration/test_engineering_architecture.py tests/contract/renderers/test_diagram_renderers.py` 25 passed；全套 `workspace/.venv-m13/bin/python -m pytest` 293 passed；`ruff check .` 通过；`ruff format --check .` 通过（141 files）；`basedpyright` 0 errors, 0 warnings；`git diff --check` 通过
- M2.10：`workspace/.venv-m13/bin/python -m pytest tests/unit/application/test_blueprint_completeness.py tests/golden/test_mechanical_engineering_blueprint.py` 15 passed；全套 `workspace/.venv-m13/bin/python -m pytest` 308 passed；`ruff check .` 通过；`ruff format --check .` 通过（145 files）；`basedpyright` 0 errors, 0 warnings；`git diff --check` 通过
- M2.11：`workspace/.venv-m13/bin/python -m pytest tests/unit/application/test_publication_evidence_policy.py tests/contract/publication/test_profiles.py tests/integration/test_engineering_delivery_export.py` 31 passed；全套 `workspace/.venv-m13/bin/python -m pytest` 339 passed；`ruff check .` 通过；`ruff format --check .` 通过（155 files）；`basedpyright` 0 errors, 0 warnings；`git diff --check` 通过
- M3.1：`workspace/.venv-m13/bin/python -m pytest tests/golden/test_s6_s7.py` 16 passed；全套 `workspace/.venv-m13/bin/python -m pytest` 355 passed；`ruff check .` 通过；`ruff format --check .` 通过（158 files）；`basedpyright` 0 errors, 0 warnings；`git diff --check` 通过
- M3.2：`workspace/.venv-m13/bin/python -m pytest tests/integration/test_incubator_s6_s10.py` 15 passed；全套 `workspace/.venv-m13/bin/python -m pytest` 370 passed；`ruff check .` 通过；`ruff format --check .` 通过（160 files）；`basedpyright` 0 errors, 0 warnings；`git diff --check` 通过
- M4.1：`workspace/.venv-m13/bin/python -m pytest tests/unit/application/test_claim_compiler.py` 16 passed；`ruff/basedpyright` 由主 agent 复核通过（提交 `2de344d`）
- M4.2：`workspace/.venv-m13/bin/python -m pytest tests/integration/test_claim_freeze.py` 7 passed；全套 `workspace/.venv-m13/bin/python -m pytest` 437 passed；`ruff check --no-cache` 通过；`ruff format --check` 通过；`basedpyright` 0 errors, 0 warnings；`git diff --check` 通过
- M5.1：`workspace/.venv-m13/bin/python -m pytest tests/security/test_action_gate_policy.py` 15 passed；全套 `workspace/.venv-m13/bin/python -m pytest` 452 passed（含 M0.5 的 29 个）；`ruff check --no-cache` 通过；`ruff format --check` 通过；`basedpyright` 0 errors, 0 warnings；`git diff --check` 通过
- M6.1：`workspace/.venv-m13/bin/python -m pytest tests/contract/llm/test_provider_contract.py` 8 passed；全套 `workspace/.venv-m13/bin/python -m pytest` 460 passed；`ruff check --no-cache` 通过；`ruff format --check` 通过；`basedpyright` 0 errors, 0 warnings；`git diff --check` 通过
- M6.3：`workspace/.venv-m13/bin/python -m pytest tests/contract/llm/test_qualification_roles.py` 9 passed；全套 `workspace/.venv-m13/bin/python -m pytest` 469 passed；`ruff check --no-cache` 通过；`ruff format --check` 通过；`basedpyright` 0 errors, 0 warnings；`git diff --check` 通过
- M6.2：`workspace/.venv-m13/bin/python -m pytest tests/security/test_role_isolation.py` 12 passed；全套 `workspace/.venv-m13/bin/python -m pytest` 481 passed；`ruff check --no-cache` 通过；`ruff format --check` 通过；`basedpyright` 0 errors, 0 warnings；`git diff --check` 通过
- M0.5（并入 d6dbfbe）：`workspace/.venv-m13/bin/python -m pytest tests/security/test_codex_fidelity.py tests/integration/test_prepare_commit.py` 29 passed；`ruff check --no-cache src/synaisthesis/fidelity/ src/synaisthesis/application/fidelity_service.py` 通过；format 通过

## Known failures
- 当前无安装阻断。原先以隐藏 PowerShell 为目标的 `C:\Users\27499\Desktop\DeepSeek Harness.lnk` 会被外部环境自动移除；本轮改为直接调用 `C:\Windows\System32\wsl.exe` 与现有 WSL runner 后，快捷方式字段回读一致且连续 30 秒存在。Computer Use 仍因 Codex 本地目录 `EPERM` 不可用，因此未执行真实桌面双击。

## Pending Human Gates
- 无（「M0 人工确认」已于本轮由用户确认通过）。

## Next allowed task
- 文档方面：V2.4 已冻结；后续只有新需求或实现中发现 `BLUEPRINT_GAP/CONFLICT` 时再变更。
- 代码方面：`M13.1.ACADEMIC.PROVIDERS`（并行子 agent 441dd195 实现中；落地后为 `M7.1.COUNCIL.STATE_GRAPH`，合同已备）

## Notes
- 原计划 Pyright（npm 版）在无 Node 的 WSL 环境中安装失败且极慢，按蓝图「Pyright 或 mypy」改用 basedpyright（Pyright 兼容实现）；检查命令为 `uv run basedpyright`。
- drvfs（`/mnt/e`）上 venv 反复损坏且性能差，venv 实际建在 WSL ext4（`~/.venvs/synaisthesis`），仓库 `.venv` 为符号链接；`uv run` 已验证可用。
- 仅记录真实执行结果；未执行的内容（如 Lean/Z3 调用）不记录为已验证。
- 本沙箱 venv 只读，`uv run` 需 `--no-sync` 并把 `UV_CACHE_DIR` 指向可写路径（`/tmp`）；该命令形式已由 CONTRIBUTING.md 与提交 `f2640d0` 记录。
- M1.3/M1.4/M2.1 因只读 venv 无法新增 sqlalchemy/alembic，故在 `workspace/.venv-m13`（gitignored）另建独立 venv 运行集成测试与检查；`/tmp` 跨命令会被清空，venv 必须落在 workspace 内才持久。
- M1.4 采用事件溯源持久化（Project 状态 = canonical JSON payload Artifact + 有序 DomainEvent 流），未新建 `projects` 表；三处蓝图缺口记录见 `workspace/workunit-contracts/M1.4.PROJECT.VERTICAL_SLICE.md`（GAP-1 注册点、GAP-2 无 projects migration、SCOPE-1 幂等 envelope 延后）。
- M2.1 沿用事件溯源（Seed/NaturalLanguageSpec 聚合）；issue→Gate 状态映射、07 §2 函数家族范围（create_stage_run/execute_stage/advance_stage 延后到 M2.2）、source_type 不发明枚举三处缺口记录见 `workspace/workunit-contracts/M2.1.S0_S1.CONTRACTS.md`。
- M2.2 沿用事件溯源（MechanismSketch/PriorWorkMap/ResearchScopeSpec/ResearchSpec 聚合）；S1/S4 hash 覆盖语义内容，排除 `assistant_proposed`/`user_confirmed`/`user_confirmed_scope` 确认标记，确认 provenance 由事件流单独恢复。07 §2 的 `create_stage_run`/`execute_stage`/`advance_stage` 不在 19 §5 M2.2 文件与验收内，且真实 execute 依赖 M6 Provider，故继续延后（GAP-4 见 M2.2 WorkUnitContract）。
- M2.2 已提交：`5c880ee`。
- M2.3 领域层保持零 Web/数据库/MCP/Provider 依赖（migration 文件除外）；RQ Artifact 与 Gate 均为 frozen dataclass。`FormalizationFeasibilityAssessment.status`/`recommended_route` 为 GAP-2 派生映射；`GateStatus` 为 GAP-4 保守映射；migration 表清单为 GAP-5 按 06 §1 推导。
- M2.3 已提交：`e86f28a`。
- M2.4 只返回内存中的 `NeighborEvidenceSet`，未写 DomainEvent/Artifact；持久化需后续含 storage 文件的 Task 接入。
- M2.4 已提交：`4ea5912`。
- M2.4A 的两个 Assessor 是确定性结构评估器；真实 LLM 接入在 M6.x，但 `assess()` 契约、谓词证据引用与 FAIL > UNKNOWN > PASS 聚合不得放宽。
- M2.4A 已提交：`b914e52`。
- M2.5/M2.5B 仍为确定性骨架（真实 LLM 在 M6.x 接入）；验证不变量不得放宽。
- M2.5/M2.5B 已提交：`4609db8`。
- M2.6 已提交：`1c2cb58`。
- M2.7 已提交：`0c4edeb`。
- M2.8 已提交：`19be013`。
- M2.9 已提交：`9d42022`。
- M2.10 已提交：`3070c49`。
- M2.11 已提交：`3f88f46`。
- M3.1 已提交：`275c9f9`。
- M3.2 已提交：`b50cd3b`。
- M4.1 已提交：`2de344d`（并行子 agent 实现，主 agent 复核）。
- M4.2 已提交：`91b6a7e`。
- M5.1 已提交：`d6dbfbe`（注意：该提交因并发暂存竞争一并包含 M0.5 的文件；按仓库规则不做历史改写，M0.5 里程碑随此提交记录）。
- M6.1 已提交：`cd62a2f`。
- M6.3 已提交：`ec120ed`。
- M6.2 已提交：`8ecd361`（并行子 agent 实现，主 agent 复核；子 agent 多轮未提交，主 agent 按预案中断并以其已验证工作树内容提交）。
- M5.1 记录：ActionGate 与其决策常量按架构放在 `domain/action.py`（gate.py 无需改动，M4.2 已为其加入 CLAIM_ACCEPTANCE 决策），合同 GAP-1 注明。
- 并发协作记录：M0.5 子 agent 已 `git add` 暂存其文件后，主 agent 的 `git commit` 将暂存区一并提交；后续并行批次将要求子 agent 在提交前检查 `git status` 暂存区并改用 `git commit -- <files>` 精确路径提交，避免再次混入。
- M0.5 验收覆盖（子 agent 最终报告）：05A §25 全量覆盖 13/18（1–11、14、15）；延后：12 compact 恢复（M10 Sidecar）、13 并发 E2E（逻辑已覆盖）、16 Sidecar spool 恢复（M10）、17 附件 hash 重验（字段已定义未接线）、18 Recursion Guard（M12）。
- M0.5.CODEX.FIDELITY 并行子 agent 进行中（fidelity/* + fidelity_service.py + 两个测试文件已在工作树，未提交）。
- M2.11 蓝图缺口记录：GAP-1（“母稿交付用户”以 audit_status=AUDITED_CLEAN 为确定性代理，交付回执事件由后续 WorkUnit 补充）；GAP-2（JOSS/Nature venue_kind 03C 未枚举，定为 EXTENDED_PROFILE 并记录在案）。
- M2.11 内置 Profile 为冻结 fixture（官方 URL 为示例域名）；真实指南刷新与模板 checksum 由后续生产级 WorkUnit 接入。
- M2.10 WorkUnit 合同字段为 15 个（03B §8.2 第 1 项“稳定 Task ID 与唯一目标”拆分为 task_id + unique_objective 两个字段），golden 测试按 14 项合同逐一断言非空。
- M2.9 蓝图缺口记录：GAP-1（真实 Mermaid/Graphviz 渲染依赖外部工具，M2.9 提供确定性内置文本源→SVG 渲染器作为合同，真实渲染器后续 WorkUnit 替换，合同不得放宽）；GAP-2（ENG0/ENG1 服务未单列于 19 §5 M2.9 文件清单，纳入 engineering_design_service 以支撑纵向切片前置）。
- M2.9 事件负载为 dataclass canonical JSON，`rebuild_dataclass` 按字段注解重建枚举/嵌套 dataclass/datetime，round-trip 由 focused 测试覆盖。
- M2.8 蓝图缺口记录：GAP-1（03B §14 回归表部分行给出多个回退点，领域层 `EARLIEST_ROLLBACK` 固定取最早保守回退点并注释在案）；GAP-2（06 §engineering_manuscripts 无 compliance 字段，ComplianceMatrix 由 `domain/publication.py` 领域对象承载，migration 0004 未加列）。
- M2.8 工程枚举按 19 §5 M2.8 文件清单落在 `domain/engineering.py`（`domain/enums.py` 不在清单内），与 enums.py 模块 docstring 的“里程碑枚举归里程碑文件”约定一致。
- M2.8/M2.9 本会话期间 DSH 环境在仓库内创建未跟踪目录 `.dsh-upstream/` 与 `.dsh-probe/`（modeltest 检查点），已在 `.gitignore` 追加忽略，避免误提交与本地 ruff 门禁污染；CI 全新检出不受影响。
- DOC-V2.4 只改文档与生成型蓝图资产，未修改 Python、运行配置或 CI，因此未重复运行代码测试、类型检查和构建；上面的 M0 代码验证记录保持历史事实，不视为本轮重跑。
- DSH 位于 `/mnt/e` drvfs；依赖安装约 13 分钟，Web profile 每次冷启动实测约 2 分 49 秒。启动器使用 240 秒有界健康等待；若后续体验不可接受，应另建迁移到 WSL ext4/VHDX 的独立 WorkUnit，不得静默移动到 C 盘或 N 盘。
