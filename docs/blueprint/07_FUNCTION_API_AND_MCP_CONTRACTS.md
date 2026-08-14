# 07 — 函数、服务、API 与 MCP 契约

本文不提供实现代码，只规定应实现的函数、输入输出和责任边界。

## 1. 配置与启动

### `load_settings`
读取配置文件和环境变量，输出 Settings。

### `validate_settings`
检查：
- 默认轮数大于零；
- Primary/Auditor 已配置；
- 工作目录存在；
- 工具 timeout 合法；
- Codex 双向配置无递归风险。

### `doctor`
检查数据库、Artifact Store、模型、Lean、Z3、Docker、Git、Codex SDK、Codex 登录、MCP 与 Recursion Guard。

## 2. Incubator

### `capture_seed`
创建 SeedRecord。

### `validate_seed_record`
检查原文保留与观察/解释分离。

### `create_stage_run`
建立 StageRun。

### `execute_stage`
调用对应 Agent/Tool。

### `validate_stage_output`
执行 Schema 与业务规则。

### `evaluate_stage_gate`
计算 PASS/PARTIAL/BLOCKED/NOT_TESTED。

### `advance_stage`
合法状态转移。

### `rollback_stage`
创建回退事件，保留旧 Artifact。

### `create_wip_checkpoint`
每五个有效轮次执行。

### `evaluate_mature_idea_ready`
计算成熟门。

## 3. Early Research Qualification

### `evaluate_formalizer_capability`
按能力 Profile 计算 RQ0，不接受供应商名称作为能力证明。

### `select_early_formalization_route`
选择 `PLATFORM_ADVANCED_FORMALIZER` 或 `EXTERNAL_ADVANCED_MODEL_IMPORT`。

### `run_prior_art_search`
执行学术与成熟工程项目检索，返回 `NeighborEvidenceSet`。

### `validate_prior_art_coverage`
检查来源类别、数量、元数据、成熟度证据、未检索区域和外部内容隔离。

### `import_external_formalization`
验证外部模型身份、输入 spec hash、检索集引用、可行性矩阵、FormulaBundle/EngineeringConceptBundle Schema 与来源。

### `assess_formalization_feasibility`
建立隔离的理论与工程评估 Session，逐项计算 `03A` 的 TFO–TFP 与 EFS–EFF，保守聚合为 route classification。

### `open_formalization_feasibility_gate`
仅对 `ENGINEERING_PROJECT_CANDIDATE` 或 `NEITHER_CURRENTLY_FIT/INCONCLUSIVE` 打开对应 Gate，绑定 assessment/spec hash。

### `resolve_engineering_route_decision`
只接受 `REVISE_FOR_THEORY | TRY_ENGINEERING_PROJECT | PAUSE | ARCHIVE`；必须验证真实用户 actor。

### `build_early_formula_bundle`
生成符号表、数学公式、依赖、语义映射、近邻差异与简明解释。

### `validate_early_formula_bundle`
检查符号闭合、公式覆盖、语义对齐、失败公式、引用与 hash。

### `open_early_formalization_review`
打开 `EARLY_FORMALIZATION_REVIEW`，绑定 formula/spec hash。

### `resolve_early_formalization_review`
只接受 APPROVE / REQUEST_REVISION / RESEARCH_MORE / REVISE_DESIGN / REJECT / PAUSE。

### `build_engineering_concept_bundle`
在用户明确选择工程路线后生成 I/O、状态转移、要求谓词、质量阈值、架构图候选和追踪关系。

### `validate_engineering_concept_bundle`
检查符号/单位、功能覆盖、阈值、失败与恢复、安全义务、来源和 hash；禁止写入 implemented/validated/novel。

### `open_early_engineering_concept_review`
打开 `EARLY_ENGINEERING_CONCEPT_REVIEW`，绑定 concept/spec/route hash。

### `start_novelty_review`
在用户批准且检索 COMPLETE 后建立两个隔离 Reviewer Session。

### `calculate_conservative_novelty_score`
按 route 和 `03A` policy 逐项取较小评分：理论路线计算理论 50 + 应用 50，工程路线计算工程 60 + 应用 40。

### `route_novelty_decision`
有效总分 `>=70` 时理论路线自动转 S5、工程路线自动转 ENG0；`<70` 或 INCONCLUSIVE 打开用户 Gate。

## 3A. Engineering Translation & Publication

### `initialize_engineering_workflow`
验证 route selection、concept approval、novelty status/override 和输入 hash，创建 ENG0 run。

### `build_engineering_mission_charter`
只从冻结 Artifact 导入 problem、stakeholder、boundary、objectives、constraints 和 success metrics；新增建议进入 proposed additions。

### `build_operational_concept`
生成 stakeholder map、主要/替代/失败/恢复场景、外部系统、信任边界和运行约束。

### `baseline_engineering_requirements`
创建稳定 Requirement ID、测量阈值、verification method、acceptance criterion 与 100% source trace。

### `run_engineering_trade_study`
检索公开工程证据，验证候选路线对 Critical requirements 的硬门并使用冻结权重计算方案分数。

### `build_architecture_baseline`
生成 context/container/component/runtime/data/state/deployment/security 机器对象、ADR 和接口/数据 Schema。

### `render_engineering_diagrams`
从机器对象生成版本化文本图源和 SVG/PNG/PDF，保存渲染回执及稳定 ID 映射。

### `open_engineering_architecture_review`
绑定 requirements/trade-study/architecture hashes，展示重大影响和不可逆决策。

### `build_mechanical_engineering_blueprint`
生成项目树、文件/模块/符号计划、依赖/迁移/错误/测试/回滚合同及原子 `EngineeringWorkUnitContract[]`。

### `validate_blueprint_completeness`
计算 requirement→design→task→test 覆盖、Schema、停止条件、断链和未决产品/架构决策；失败返回 `BLUEPRINT_GAP`。

### `select_engineering_delivery_mode`
选择 `BLUEPRINT_ONLY` 或请求 `BUILD_AND_EVALUATE`；后者只打开授权 Gate，不直接执行。

### `record_engineering_verification`
只接受真实 test/analysis/inspection/demonstration receipt；验证与确认分别存储。

### `build_application_and_extension_roadmaps`
为每个应用/扩展记录条件、指标、证据等级、影响、风险和时间层级。

### `build_engineering_master_manuscript`
按 evidence tier 生成期刊中立母稿和 claim-evidence matrix；无回执结果只能标 planned 或删除。

### `audit_master_manuscript`
由未参与初稿的 route-specific Auditor 检查语义、证据、引用、Scope、作者输入和真实编译；只有通过后才能交付母稿。

### `open_formal_manuscript_decision`
母稿交付后打开 `FORMAL_MANUSCRIPT_DECISION`，绑定 master/delivery-or-evidence hash。

### `resolve_formal_manuscript_decision`
只接受 `KEEP_MASTER_ONLY | WRITE_FORMAL_MANUSCRIPT | REVISE_MASTER | PAUSE`；无响应不得默认 WRITE。

### `select_publication_profile`
只有 decision 为 WRITE 时创建或选择 Profile；验证 route、`venue_kind`、官方指南时间、模板 checksum 和 scope-fit。作者责任字段只允许用户确认。

### `refresh_publication_profile`
从官方 author guide/policy/template URL 更新内置 Profile snapshot；超过 freshness window 或 hash 改变时使旧 Compliance 失效。

### `adapt_manuscript_to_venue`
从 Master + PublicationProfile 机械派生适配稿与 `VenueComplianceMatrix`，不得覆盖母稿。

### `audit_engineering_delivery`
由未参与初稿生成的 Auditor 检查追踪、机械性、图示、回执、引用、许可证、论文与敏感信息。

### `export_engineering_delivery`
按 `03B` 固定目录生成 manifest、checksums 和全部工件；只有最终条件满足才标 READY。

## 3B. Theory Publication

### `baseline_theory_publication_evidence`
验证理论 route，冻结 ResearchSpec、Formalization、FrozenClaim statement hash、Proof/Evidence、Semantic Audit、Citation 和未解决义务，确定 evidence tier。

### `build_theory_master_manuscript`
按 `03C` 生成期刊中立 TeX 母稿、`MathematicalManuscriptClaim[]`、Proof Dependency Graph 和 claim-evidence matrix。

### `validate_mathematical_manuscript_claims`
逐项检查对象域、量词、假设、结论、statement hash、proof/evidence status 与稿件类型；禁止把 conjecture/partial/solver-scope 结果升格为 theorem。

### `audit_theory_master_manuscript`
由隔离 Theory Manuscript Auditor 检查语义、证明依赖、引用、失败/限制、AI/作者字段和真实 TeX 编译。

### `deliver_theory_master_manuscript`
交付母稿、evidence tier、主 theorem/claim、未解决义务、审计报告和四刊/arXiv scope-fit；随后打开 `FORMAL_MANUSCRIPT_DECISION`。

### `export_theory_publication_delivery`
按 `03C` 固定目录导出母稿、proof/reproducibility artifact、决定、可选适配稿、Compliance 和 checksums。

## 4. Claim Compiler

### `extract_candidate_claims`
从 S6/S7 提取候选主张。

### `split_claim_into_atomic_units`
拆分混合命题。

### `classify_claim`
输出 ClaimClass。

### `define_falsification_witness`
定义反例结构。

### `build_claim_dependency_graph`
建立依赖。

### `validate_claim_atomicity`
检查能否独立验证。

### `build_claim_contract`
生成冻结候选。

### `freeze_claim_contract`
只有用户确认或策略允许时执行。

### `verify_claim_contract_hash`
每轮开始检查。

## 5. Role Isolation

### `create_role_session`
创建独立会话。

### `build_visibility_bundle`
根据 role/phase 生成最小上下文。

### `validate_role_visibility`
检查是否读取禁止内容。

### `record_isolation_violation`
保存违规并阻断。

### `run_support_track`
生成 SupportPacket。

### `run_oppose_track`
生成 AttackPacket。

### `run_independent_phase_a`
盲审。

### `run_independent_phase_b`
去角色复核。

## 6. Model Provider

### `call_model`
统一异步入口。

输入：
- model profile；
- role；
- prompt version；
- visibility bundle；
- response schema；
- budget；
- trace metadata。

输出：
- StructuredModelResult。

### `validate_model_diversity`
检查 provider、model、family 与 session isolation。

### `repair_structured_output`
只修复格式，不改变研究内容。

### `record_model_invocation`
保存 tokens、成本、延迟、hash。

### `enforce_budget_before_model_call`
调用前验证剩余预算。

## 7. Council

### `start_council_run`
创建 Run。

### `begin_round`
创建快照。

### `run_council_round`
执行单轮。

### `validate_round`
判断有效性。

### `select_tool_plan`
按 ClaimClass 路由。

### `merge_round_packets`
合并结构化 Packet。

### `detect_blocking_failures`
识别 Critical/High。

### `propose_revision_candidates`
最多 N 个。

### `score_revision_candidate`
固定评分。

### `audit_semantic_delta`
S0–S4。

### `commit_revision`
不可变写入。

### `run_regression`
重跑依赖。

### `assess_round`
计算稳定分。

### `should_continue_council`
继续、早停或阻断。

### `pause_run`
暂停。

### `resume_run`
从 checkpoint 恢复。

### `cancel_run`
终止但保留历史。

## 8. ActionBroker

### `create_action_request`
创建请求。

### `classify_action_risk`
READ / WRITE / NETWORK / COST / SECRET / DESTRUCTIVE。

### `evaluate_action_policy`
自动允许、Gate 或拒绝。

### `approve_action`
仅授权主体调用。

### `execute_authorized_action`
调用对应 Adapter。

### `create_execution_receipt`
绑定参数、结果、时间与 hash。

### `verify_execution_receipt`
检查完整性。

## 9. Lean

### `prepare_lean_workspace`
建立独立环境。

### `write_lean_candidate`
写入 Artifact。

### `freeze_lean_statement_hash`
锁定 theorem statement。

### `run_lean_check`
调用 Lean/Lake。

### `parse_lean_feedback`
错误分类。

### `verify_statement_unchanged`
Proof Loop 保护。

### `record_lean_evidence`
只有真实成功才写 LEAN_KERNEL_ACCEPTED。

### `request_codex_lean_repair`
将受控修复任务交给 Codex。

## 10. Z3

### `build_constraint_spec`
模型输出结构化约束，不能直接注入任意 Python。

### `compile_constraint_spec_to_z3`
构造 Z3 对象。

### `search_counterexample`
检查假设 + 否定结论。

### `extract_model_witness`
提取反例。

### `revalidate_model_witness`
独立 evaluator 再检查。

### `record_z3_evidence`
区分 SAT/UNSAT/UNKNOWN。

## 11. Python Sandbox

### `create_sandbox_job`
定义输入与资源。

### `validate_sandbox_job`
禁止 secrets、宿主路径和未授权网络。

### `run_sandbox_job`
Docker 执行。

### `collect_sandbox_receipt`
收集日志和结果。

### `terminate_sandbox_job`
超时停止。

## 12. Codex Worker

### `route_task_to_codex`
判断是否工程型。

### `build_codex_task_spec`
生成最小任务。

### `start_codex_session`
使用 SDK/MCP/exec。

### `run_codex_task`
执行。

### `continue_codex_session`
继续 thread。

### `collect_codex_execution_receipt`
收集 diff、测试与 hash。

### `verify_codex_output`
由确定性工具复验。

### `detect_codex_reentrancy`
阻止循环调用。

### `close_codex_session`
结束。

## 13. Evidence

### `create_evidence`
保存 Evidence。

### `bind_evidence_to_claim`
建立关系。

### `calculate_evidence_scope`
确定范围。

### `revoke_evidence`
撤回。

### `cascade_revalidation`
触发依赖回归。

### `build_claim_evidence_view`
形成账本视图。

## 14. Human Gate

### `open_gate`
创建。

### `resolve_gate`
保存用户决定。

### `validate_gate_actor`
防止模型代替用户。

### `resume_after_gate`
继续。

## 15. FastAPI 端点

- POST `/projects`
- GET `/projects`
- GET `/projects/{id}`
- POST `/projects/{id}/seed`
- POST `/projects/{id}/stages/{stage_id}/run`
- POST `/specs/{id}/confirm`
- POST `/projects/{id}/qualification/capability`
- POST `/projects/{id}/qualification/prior-art-searches`
- POST `/projects/{id}/qualification/feasibility-assessments`
- GET `/feasibility-assessments/{id}`
- POST `/feasibility-assessments/{id}/route-decision`
- POST `/projects/{id}/qualification/formalizations/generate`
- POST `/projects/{id}/qualification/formalizations/import`
- GET `/formalizations/{id}`
- POST `/formalizations/{id}/review`
- POST `/projects/{id}/qualification/engineering-concepts/generate`
- GET `/engineering-concepts/{id}`
- POST `/engineering-concepts/{id}/review`
- POST `/qualification-subjects/{type}/{id}/novelty-reviews`
- GET `/novelty-reviews/{id}`
- POST `/projects/{id}/engineering-workflows`
- POST `/engineering-workflows/{id}/stages/{stage_id}/run`
- GET `/engineering-workflows/{id}`
- POST `/engineering-workflows/{id}/architecture-review`
- POST `/engineering-workflows/{id}/delivery-mode`
- POST `/engineering-workflows/{id}/master-manuscript`
- POST `/manuscripts/{type}/{id}/audit`
- POST `/manuscripts/{type}/{id}/formal-manuscript-decision`
- POST `/manuscripts/{type}/{id}/publication-profile`
- POST `/manuscripts/{type}/{id}/adapt`
- GET `/engineering-workflows/{id}/traceability`
- POST `/engineering-workflows/{id}/audit`
- POST `/engineering-workflows/{id}/export`
- POST `/projects/{id}/theory-publications`
- POST `/theory-publications/{id}/evidence-baseline`
- POST `/theory-publications/{id}/master-manuscript`
- GET `/theory-publications/{id}`
- POST `/theory-publications/{id}/export`
- GET `/publication-profiles`
- POST `/publication-profiles/{profile_id}/refresh`
- POST `/projects/{id}/claims/compile`
- POST `/claims/{id}/freeze`
- POST `/claims/{id}/council-runs`
- GET `/runs/{id}`
- GET `/runs/{id}/rounds`
- POST `/runs/{id}/pause`
- POST `/runs/{id}/resume`
- POST `/runs/{id}/cancel`
- GET `/gates`
- POST `/gates/{id}/resolve`
- GET `/claims/{id}/evidence`
- GET `/artifacts/{id}`
- POST `/projects/{id}/export`
- GET `/events`

## 16. CLI 命令

- `synaisthesis init`
- `synaisthesis serve`
- `synaisthesis doctor`
- `synaisthesis project create`
- `synaisthesis seed import`
- `synaisthesis stage run`
- `synaisthesis spec confirm`
- `synaisthesis qualification capability`
- `synaisthesis qualification search`
- `synaisthesis qualification feasibility`
- `synaisthesis qualification route-decision`
- `synaisthesis formalization generate`
- `synaisthesis formalization import`
- `synaisthesis formalization review`
- `synaisthesis engineering concept generate`
- `synaisthesis engineering concept review`
- `synaisthesis engineering workflow start`
- `synaisthesis engineering stage run`
- `synaisthesis engineering trace show`
- `synaisthesis engineering blueprint validate`
- `synaisthesis engineering manuscript master`
- `synaisthesis manuscript audit`
- `synaisthesis manuscript formal-decision`
- `synaisthesis engineering publication select`
- `synaisthesis manuscript adapt`
- `synaisthesis engineering audit`
- `synaisthesis engineering export`
- `synaisthesis theory publication start`
- `synaisthesis theory manuscript master`
- `synaisthesis theory publication export`
- `synaisthesis publication profiles list`
- `synaisthesis publication profile refresh`
- `synaisthesis novelty start`
- `synaisthesis novelty show`
- `synaisthesis claim compile`
- `synaisthesis claim freeze`
- `synaisthesis council start`
- `synaisthesis run status`
- `synaisthesis run pause`
- `synaisthesis run resume`
- `synaisthesis gate list`
- `synaisthesis gate resolve`
- `synaisthesis export`

## 17. MCP Tools

保持粗粒度。禁止暴露：
- 直接写数据库；
- 直接赋予 PASS；
- 直接调用 Lean/Z3；
- 直接修改 FrozenClaim。

推荐：

- `research_create_project`
- `research_capture_seed`
- `research_get_project_state`
- `research_advance_stage`
- `research_confirm_spec`
- `research_prepare_early_formalization`
- `research_get_formalization_feasibility`
- `research_submit_engineering_route_decision`
- `research_get_early_formalization`
- `research_submit_early_formalization_review`
- `research_prepare_engineering_concept`
- `research_get_engineering_concept`
- `research_submit_engineering_concept_review`
- `research_start_novelty_review`
- `research_get_novelty_review`
- `research_resolve_novelty_gate`
- `research_start_engineering_workflow`
- `research_advance_engineering_stage`
- `research_get_engineering_traceability`
- `research_validate_engineering_blueprint`
- `research_build_engineering_master_manuscript`
- `research_get_master_manuscript`
- `research_submit_formal_manuscript_decision`
- `research_select_publication_profile`
- `research_adapt_manuscript_to_profile`
- `research_get_engineering_delivery_status`
- `research_export_engineering_delivery`
- `research_start_theory_publication`
- `research_build_theory_master_manuscript`
- `research_get_theory_publication_status`
- `research_export_theory_publication_delivery`
- `research_list_publication_profiles`
- `research_compile_claims`
- `research_freeze_claim`
- `research_start_council`
- `research_get_run_status`
- `research_get_pending_gates`
- `research_resolve_gate`
- `research_pause_run`
- `research_resume_run`
- `research_cancel_run`
- `research_export_bundle`

外部 Codex 使用时，上述 mutation 名称只表示 `research_prepare_command` 支持的业务意图，不得绕过 Fidelity Gateway 暴露为直接 mutation。

## 18. 幂等性

所有 mutation 接口接受：
- `idempotency_key`
- `trace_id`
- `expected_version`

若 expected_version 不匹配：
- 返回 CONFLICT；
- 不自动覆盖；
- 要求重新读取状态。

## 19. 错误对象

统一错误：

- error_code
- message
- recoverable
- retry_after
- blocker_type
- required_user_action
- artifact_refs
- trace_id

不得只返回自然语言“失败了”。

早期资格固定错误码：

- `EARLY_QUALIFICATION_REQUIRED`
- `FORMALIZER_CAPABILITY_UNAVAILABLE`
- `PRIOR_ART_COVERAGE_INCOMPLETE`
- `FORMALIZATION_FEASIBILITY_INCONCLUSIVE`
- `ENGINEERING_ROUTE_DECISION_REQUIRED`
- `FORMALIZATION_FEASIBILITY_USER_DECISION_REQUIRED`
- `FORMULA_BUNDLE_INVALID`
- `ENGINEERING_CONCEPT_BUNDLE_INVALID`
- `FORMALIZATION_USER_APPROVAL_REQUIRED`
- `ENGINEERING_CONCEPT_USER_APPROVAL_REQUIRED`
- `NOVELTY_REVIEW_INCONCLUSIVE`
- `LOW_NOVELTY_USER_DECISION_REQUIRED`
- `ENGINEERING_NOVELTY_REQUIRED`
- `REQUIREMENTS_BASELINE_BLOCKED`
- `ENGINEERING_ARCHITECTURE_REVIEW_REQUIRED`
- `ENGINEERING_BLUEPRINT_GAP`
- `PROTOTYPE_EXECUTION_AUTHORIZATION_REQUIRED`
- `PUBLICATION_PROFILE_REQUIRED`
- `MASTER_MANUSCRIPT_REQUIRED`
- `MASTER_MANUSCRIPT_AUDIT_FAILED`
- `FORMAL_MANUSCRIPT_DECISION_REQUIRED`
- `THEORY_ROUTE_REQUIRED`
- `THEOREM_CLAIM_UNSUPPORTED`
- `PUBLICATION_PROFILE_ROUTE_MISMATCH`
- `VENUE_SCOPE_MISMATCH`
- `ARXIV_PACKAGE_INVALID`
- `MANUSCRIPT_CLAIM_UNSUPPORTED`
- `STALE_PUBLICATION_GUIDANCE`
- `BLOCKED_ENGINEERING_DELIVERY`

## 20. Codex Instruction Fidelity Layer

### Sidecar / Hook 函数

- `capture_codex_user_prompt`：接收 UserPromptSubmit 事件并保存原始指令。
- `bind_codex_session`：绑定 Codex session 与 Synaisthesis project。
- `persist_instruction_capsule`：创建不可变原文 Artifact 和 hash。
- `issue_instruction_token`：签发短期、turn-scoped token。
- `load_current_instruction_for_tool_call`：为 PreToolUse 取得当前指令。
- `inject_instruction_transport_fields`：重写 Synaisthesis MCP 参数，加入 token、instruction_id、state_version。
- `record_tool_display_contract`：保存 PostToolUse 返回的展示要求。
- `validate_codex_final_response`：Stop 阶段检查是否忠实展示。

### Command Gateway 函数

- `validate_instruction_token`
- `resolve_instruction_capsule`
- `resolve_context_manifest`
- `build_platform_interpretation`
- `compare_command_proposal_to_instruction`
- `classify_instruction_delta`
- `enforce_expected_state_version`
- `enforce_instruction_sequence`
- `prepare_command`
- `issue_confirmation_challenge`
- `capture_user_confirmation`
- `commit_prepared_command`
- `invalidate_superseded_commands`
- `create_command_receipt`
- `create_display_contract`
- `reconcile_instruction_change`

### 对外 MCP Tools

只读：
- `research_get_project_state`
- `research_get_run_status`
- `research_get_pending_gates`
- `research_get_bound_session`
- `research_get_command_receipt`
- `research_codex_doctor`

会话与上下文：
- `research_bind_codex_session`
- `research_unbind_codex_session`
- `research_register_context`

统一 mutation：
- `research_prepare_command`
- `research_commit_command`
- `research_cancel_prepared_command`
- `research_reconcile_instruction`

所有 mutation 的业务处理最终仍调用原 Core Service，但外部 Codex 不再直接调用底层 mutation tools。
