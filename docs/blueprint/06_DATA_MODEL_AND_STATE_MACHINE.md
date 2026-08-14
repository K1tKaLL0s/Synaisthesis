# 06 — 数据模型、状态机与证据账本

## 1. 核心表

### `projects`
- id
- name
- description
- lifecycle_status
- active_spec_id
- active_claim_contract_id
- created_at
- updated_at

### `research_specs`
- id
- project_id
- version
- s1_natural_language_spec
- s4_scope_spec
- user_confirmed
- confirmed_at
- content_hash

### `formalization_capability_decisions`
- id
- project_id
- research_spec_id
- route
- model_profile_id
- capability_evidence_artifact_id
- input_spec_hash
- budget_snapshot_id
- privacy_policy_snapshot_id
- status
- blocker

### `prior_art_searches`
- id
- project_id
- research_spec_id
- input_spec_hash
- query_records_artifact_id
- academic_neighbor_count
- engineering_neighbor_count
- patent_neighbor_count
- coverage_status
- coverage_blockers_artifact_id
- artifact_hash
- created_at

### `prior_art_neighbors`
- id
- search_id
- neighbor_type
- stable_identifier
- canonical_url
- metadata_artifact_id
- metadata_verified
- maturity_evidence_artifact_id
- theory_proximity
- application_proximity
- similarity_evidence_artifact_id
- rank

### `early_formalizations`
- id
- project_id
- research_spec_id
- prior_art_search_id
- capability_decision_id
- version
- input_spec_hash
- formula_bundle_artifact_id
- formula_bundle_hash
- status
- supersedes_id
- created_at

### `formalization_feasibility_assessments`
- id
- project_id
- research_spec_id
- prior_art_search_id
- version
- input_spec_hash
- assessor_session_ids_artifact_id
- theory_predicates_artifact_id
- engineering_predicates_artifact_id
- route_classification
- recommended_route
- missing_information_artifact_id
- artifact_hash
- status
- supersedes_id

### `engineering_route_selections`
- id
- project_id
- feasibility_assessment_id
- decision
- user_actor_id
- decision_event_id
- bound_assessment_hash
- input_spec_hash
- created_at

### `engineering_concepts`
- id
- project_id
- research_spec_id
- feasibility_assessment_id
- route_selection_id
- prior_art_search_id
- version
- input_spec_hash
- concept_bundle_artifact_id
- concept_bundle_hash
- status
- supersedes_id
- created_at

### `novelty_reviews`
- id
- project_id
- route
- subject_artifact_type
- subject_artifact_id
- prior_art_search_id
- policy_version
- coverage_status
- theory_score
- application_score
- engineering_score
- engineering_application_score
- novelty_total
- status
- scorecard_artifact_id
- artifact_hash
- created_at

### `engineering_workflow_runs`
- id
- project_id
- engineering_concept_id
- stage_id
- input_artifact_ids
- output_artifact_id
- output_hash
- status
- gate_id
- started_at
- ended_at

### `engineering_requirements`
- id
- project_id
- baseline_version
- requirement_key
- requirement_type
- statement
- source_refs_artifact_id
- priority
- measurement_method
- unit
- threshold
- tolerance
- verification_method
- acceptance_criterion
- owner
- status
- content_hash

### `engineering_trace_edges`
- id
- project_id
- from_type
- from_id
- relation
- to_type
- to_id
- baseline_version
- evidence_artifact_id

### `publication_profiles`
- id
- profile_id
- profile_version
- route
- venue_kind
- venue_name
- publisher_or_operator
- article_type
- official_author_guide_urls_artifact_id
- official_policy_urls_artifact_id
- guide_accessed_at
- guide_last_modified_at
- freshness_days
- template_identifier
- template_checksum
- scope_fit_rules_artifact_id
- rules_artifact_id
- freshness_status
- content_hash

### `engineering_manuscripts`
- id
- project_id
- manuscript_type
- evidence_tier
- master_artifact_id
- master_version
- master_hash
- claim_evidence_matrix_artifact_id
- status
- content_hash
- supersedes_id

### `theory_publication_evidence_baselines`
- id
- project_id
- version
- research_spec_hash
- formalization_hash
- claim_contract_ids_artifact_id
- claim_statement_hashes_artifact_id
- proof_evidence_refs_artifact_id
- citation_evidence_set_id
- unresolved_obligations_artifact_id
- evidence_tier
- content_hash
- status
- supersedes_id

### `theory_manuscripts`
- id
- project_id
- manuscript_type
- evidence_baseline_id
- evidence_tier
- master_artifact_id
- master_hash
- proof_dependency_graph_artifact_id
- claim_evidence_matrix_artifact_id
- adapted_artifact_id
- publication_profile_id
- compliance_matrix_artifact_id
- status
- content_hash
- supersedes_id

### `manuscript_audits`
- id
- project_id
- route
- master_manuscript_type
- master_manuscript_id
- master_version
- master_hash
- producer_session_id
- auditor_session_id
- audit_profile_version
- findings_artifact_id
- compile_receipt_artifact_id
- status
- content_hash
- supersedes_id

### `formal_manuscript_decisions`
- id
- project_id
- route
- master_manuscript_type
- master_manuscript_id
- master_version
- master_hash
- bound_delivery_or_evidence_hash
- decision
- user_actor_id
- decision_event_id
- created_at
- content_hash
- supersedes_id

### `publication_profile_selections`
- id
- project_id
- route
- formal_manuscript_decision_id
- master_manuscript_type
- master_manuscript_id
- master_hash
- publication_profile_id
- publication_profile_version
- scope_fit_status
- selected_by_actor_id
- selection_event_id
- created_at
- content_hash

### `venue_manuscript_adaptations`
- id
- project_id
- route
- master_manuscript_type
- master_manuscript_id
- master_hash
- publication_profile_selection_id
- publication_profile_id
- publication_profile_version
- adapted_artifact_id
- compliance_matrix_artifact_id
- adaptation_trace_artifact_id
- compile_receipt_artifact_id
- status
- content_hash
- supersedes_id

### `novelty_score_items`
- id
- novelty_review_id
- reviewer_session_id
- criterion_id
- rating
- weight
- evidence_refs_artifact_id
- rationale_artifact_id

### `incubation_stage_runs`
- id
- project_id
- stage_id
- input_artifact_ids
- output_artifact_id
- status
- prompt_version
- model_invocation_ids
- started_at
- ended_at

### `claim_units`
- id
- project_id
- parent_claim_id
- claim_key
- natural_language_statement
- claim_class
- importance
- status

### `claim_contracts`
- id
- claim_id
- revision_id
- version
- contract_hash
- policy_snapshot_id
- user_confirmed
- frozen_at

### `theory_revisions`
- id
- claim_id
- parent_revision_id
- round_id
- natural_language_statement
- formal_statement
- assumptions_snapshot
- semantic_delta_level
- created_by
- immutable_hash

### `council_runs`
- id
- claim_contract_id
- configured_rounds
- current_round
- status
- primary_model_profile_id
- auditor_model_profile_id
- delegation_policy_id
- budget_policy_id
- started_at
- ended_at

### `council_rounds`
- id
- run_id
- round_number
- valid
- start_revision_id
- end_revision_id
- outcome
- stability_score
- snapshot_artifact_id

### `role_sessions`
- id
- run_id
- round_id
- role
- model_profile_id
- visibility_policy_id
- isolated_context_hash
- session_status

### `model_invocations`
- id
- role_session_id
- provider
- model
- request_hash
- response_artifact_id
- input_tokens
- output_tokens
- cost
- latency_ms
- status

### `attacks`
- id
- target_revision_id
- round_id
- source_role
- attack_family
- description
- witness
- severity
- status
- validation_plan
- resolved_by_revision_id

### `evidence`
- id
- claim_id
- revision_id
- evidence_type
- provenance_type
- status
- scope
- strength
- artifact_id
- tool_invocation_id
- model_invocation_id
- created_at
- revoked_at

### `evidence_edges`
- id
- evidence_id
- target_claim_id
- relation
- notes

### `tool_invocations`
- id
- run_id
- round_id
- tool_name
- input_artifact_id
- output_artifact_id
- execution_receipt_id
- status
- duration_ms
- timeout

### `action_requests`
- id
- run_id
- round_id
- action_type
- risk_class
- requested_by
- parameters_artifact_id
- status
- required_approval

### `approval_decisions`
- id
- action_request_id
- actor
- decision
- reason
- decided_at

### `execution_receipts`
- id
- action_request_id
- executor
- parameters_hash
- result_hash
- stdout_artifact_id
- stderr_artifact_id
- diff_artifact_id
- started_at
- ended_at
- exit_status

### `human_gates`
- id
- project_id
- run_id
- gate_type
- reason
- semantic_diff_artifact_id
- status
- decision
- resolved_at

### `codex_sessions`
- id
- task_id
- transport
- thread_id
- profile
- cwd
- sandbox
- approval_policy
- origin_chain
- status

### `codex_tasks`
- id
- run_id
- round_id
- task_type
- task_spec_artifact_id
- session_id
- execution_receipt_id
- status

### `artifacts`
- id
- project_id
- relative_path
- media_type
- sha256
- immutable
- created_at

### `domain_events`
- id
- project_id
- aggregate_type
- aggregate_id
- event_type
- event_payload_artifact_id
- event_hash
- created_at

### `prompt_versions`
- id
- prompt_key
- version
- content_hash
- active
- evaluation_score

### `model_profiles`
- id
- provider
- model
- family
- reasoning_tier
- structured_output_support
- cost_profile
- privacy_profile
- enabled

### `visibility_policies`
- id
- name
- allowed_artifact_types
- denied_roles
- blind_phase
- notes

## 2. 项目生命周期

```text
SEED
→ INCUBATING
→ NATURAL_LANGUAGE_DESIGN_READY
→ EARLY_RESEARCH_QUALIFYING
→ FORMALIZATION_FEASIBILITY_REVIEWING
   ├─ THEORY_OR_HYBRID_ROUTE
   │  → FORMALIZATION_CANDIDATE → FORMALIZATION_USER_REVIEW
   │  → NOVELTY_REVIEWING
   │  → NOVELTY_QUALIFIED / BLOCKED_NOVELTY_USER
   │  → MATURE_IDEA_READY → THEORY_BUILDING → CLAIM_COMPILED
   │  → CLAIM_FROZEN → COUNCIL_RUNNING → CANDIDATE_STABLE
   │  → THEORY_MASTER_MANUSCRIPT_BUILDING
   │  → THEORY_MASTER_MANUSCRIPT_AUDITING
   │  → THEORY_MASTER_MANUSCRIPT_READY
   │  → FORMAL_MANUSCRIPT_DECISION_REQUIRED
   │  → MASTER_ONLY_DELIVERED / MASTER_REVISION_REQUIRED / FORMAL_MANUSCRIPT_PAUSED
   │  → PUBLICATION_PROFILE_REQUIRED → FORMAL_MANUSCRIPT_READY / ARXIV_PACKAGE_READY
   │
   ├─ ENGINEERING_ROUTE_USER_DECISION
   │  → ENGINEERING_CONCEPT_CANDIDATE → ENGINEERING_CONCEPT_USER_REVIEW
   │  → ENGINEERING_NOVELTY_REVIEWING
   │  → ENGINEERING_NOVELTY_QUALIFIED / BLOCKED_NOVELTY_USER
   │  → ENGINEERING_DESIGNING → ENGINEERING_ARCHITECTURE_REVIEW
   │  → ENGINEERING_BLUEPRINTING → ENGINEERING_VALIDATING
   │  → ENGINEERING_PUBLISHING → ENGINEERING_DELIVERY_READY
   │
   └─ FORMALIZATION_FEASIBILITY_USER_DECISION

任一路线 → BLOCKED_HUMAN / BLOCKED_TOOL
任一路线 → USER_ACCEPTED / REVOKED
```

允许回退：

- THEORY_BUILDING → INCUBATING；
- ENGINEERING_DESIGNING → EARLY_RESEARCH_QUALIFYING；
- ENGINEERING_BLUEPRINTING → ENGINEERING_DESIGNING；
- ENGINEERING_VALIDATING → ENGINEERING_DESIGNING；
- ENGINEERING_PUBLISHING → ENGINEERING_VALIDATING；
- CLAIM_COMPILED → THEORY_BUILDING；
- COUNCIL_RUNNING → CLAIM_COMPILED；
- CANDIDATE_STABLE → COUNCIL_RUNNING；
- USER_ACCEPTED → REVOKED。

回退只写事件，不删除历史。

## 3. ProvenanceType

- USER_INPUT
- USER_DECISION
- EXTERNAL_MODEL_IMPORT
- EXTERNAL_SOURCE
- ASSISTANT_PROPOSAL
- DERIVED
- TOOL_EXECUTION
- CODEX_EXECUTION
- HUMAN_VERIFIED

## 4. EvidenceType

- LITERATURE_METADATA
- LITERATURE_INTERPRETATION
- PRIOR_ART_METADATA_VERIFIED
- ENGINEERING_MATURITY_EVIDENCE
- FORMALIZATION_FEASIBILITY_ASSESSMENT
- EARLY_FORMALIZATION_ALIGNMENT
- ENGINEERING_CONCEPT_ALIGNMENT
- NOVELTY_SCORECARD
- REQUIREMENTS_BASELINE
- ARCHITECTURE_BASELINE
- ENGINEERING_TRACEABILITY
- VERIFICATION_REPORT
- VALIDATION_REPORT
- MANUSCRIPT_CLAIM_EVIDENCE
- VENUE_COMPLIANCE_MATRIX
- COUNTEREXAMPLE
- SMT_MODEL
- SMT_UNSAT_WITHIN_ENCODING
- PYTHON_EXPERIMENT
- LEAN_KERNEL_ACCEPTED
- LEAN_ERROR
- CODEX_EXECUTION_RECEIPT
- SEMANTIC_AUDIT
- REGRESSION_RESULT
- HUMAN_CONFIRMATION
- CONSTRUCTION_ARTIFACT

## 5. Evidence 强度

- E0：未经验证的模型提案；
- E1：可复述自然语言论证；
- E2：可复现计算或构造；
- E3：有限模型或范围验证；
- E4：形式证明器接受；
- E5：外部独立复核或多形式系统交叉验证。

强度不替代 scope：

- Z3 UNSAT 可以是 E3，但只在当前编码范围；
- Lean PASS 是 E4，但只针对形式 statement；
- 用户语义确认不是数学证据，但决定 semantic_status。

## 6. 独立性状态

- INDEPENDENT_VERIFIED
- INDEPENDENT_PARTIAL
- SAME_MODEL_FAMILY
- CONTEXT_LEAK_SUSPECTED
- ISOLATION_VIOLATION
- NOT_APPLICABLE

如果 Primary 与 Auditor 是同一模型或模型家族，系统可继续，但必须显示 `INDEPENDENCE_DEGRADED`，不能当成真正独立复核。

## 7. Artifact Store

```text
workspace/{project_id}/
  spec/
  stages/
  literature/
  prior_art/academic/
  prior_art/engineering/
  formalization/early/
  novelty/
  theory/
  publication/theory/master/
  publication/theory/adapted/
  publication/engineering/master/
  publication/engineering/adapted/
  publication/profiles/
  claims/
  formal/lean/
  formal/smt/
  experiments/
  codex/
  attacks/
  evidence/
  receipts/
  checkpoints/
  reports/
  exports/
```

规则：

- 内容不可变；
- SHA-256；
- 更新生成新文件；
- 数据库保存相对路径；
- 导出包含 manifest；
- 数据库状态引用具体 hash；
- 文件缺失时状态转 BLOCKED_ARTIFACT。

## 8. Public Rationale

平台保存：
- 结论摘要；
- 公开理由；
- 证据引用；
- 失败说明；
- 决策依据。

不要求保存模型隐藏推理过程。`public_rationale` 是可审计产物，不等于私有 chain-of-thought。

## 9. 状态派生

`overall_status` 不由模型输出，而由以下轴派生：

- stage_status
- early_qualification_status
- formal_status
- empirical_status
- semantic_status
- novelty_status
- regression_status
- independence_status
- human_review_status
- tool_availability_status

例如：

```text
overall_status = CANDIDATE_STABLE
early_qualification_status = NOVELTY_QUALIFIED
formal_status = LEAN_PASS
semantic_status = AI_AUDITED
human_review_status = PENDING
novelty_status = POSSIBLY_ORIGINAL
```

这表示形式命题已通过，但原始语义尚未由用户最终确认。

`early_qualification_status` 的允许值：

- NOT_STARTED
- CAPABILITY_PENDING
- RETRIEVAL_RUNNING
- FEASIBILITY_REVIEWING
- ENGINEERING_ROUTE_USER_DECISION
- FORMALIZATION_FEASIBILITY_USER_DECISION
- FORMALIZATION_CANDIDATE
- FORMALIZATION_USER_REVIEW
- ENGINEERING_CONCEPT_CANDIDATE
- ENGINEERING_CONCEPT_USER_REVIEW
- NOVELTY_REVIEWING
- NOVELTY_QUALIFIED
- ENGINEERING_NOVELTY_QUALIFIED
- NOVELTY_RESEARCH_REQUIRED
- USER_OVERRIDDEN_BELOW_THRESHOLD
- INCONCLUSIVE
- NEEDS_REQUALIFICATION

任何 S1/S4 hash 变化都把已有 RQ 产物派生为 `NEEDS_REQUALIFICATION`；不得沿用旧用户确认或新颖性分数。

`engineering_delivery_status` 的允许值：

- NOT_STARTED
- MISSION_BASELINING
- CONOPS_DEFINING
- REQUIREMENTS_BASELINING
- TRADE_STUDY_RUNNING
- ARCHITECTURE_DESIGNING
- ARCHITECTURE_USER_REVIEW
- BLUEPRINT_BUILDING
- BLUEPRINT_GAP
- BLUEPRINT_ONLY
- BUILD_AUTHORIZATION_REQUIRED
- VERIFYING
- VALIDATING
- APPLICATION_ROADMAP_BUILDING
- MASTER_MANUSCRIPT_BUILDING
- ENGINEERING_MASTER_MANUSCRIPT_AUDITING
- ENGINEERING_MASTER_MANUSCRIPT_READY
- FORMAL_MANUSCRIPT_DECISION_REQUIRED
- MASTER_ONLY_DELIVERED
- MASTER_REVISION_REQUIRED
- FORMAL_MANUSCRIPT_PAUSED
- PUBLICATION_PROFILE_REQUIRED
- VENUE_MANUSCRIPT_BUILDING
- FORMAL_MANUSCRIPT_DRAFT
- FORMAL_MANUSCRIPT_READY
- ARXIV_PACKAGE_READY
- DELIVERY_AUDITING
- ENGINEERING_DELIVERY_CANDIDATE
- ENGINEERING_DELIVERY_READY
- BLOCKED_ENGINEERING_DELIVERY
- NEEDS_REGRESSION
- SUPERSEDED

`theory_publication_status` 的允许值：

- NOT_STARTED
- EVIDENCE_BASELINING
- THEORY_MASTER_MANUSCRIPT_BUILDING
- THEORY_MASTER_MANUSCRIPT_AUDITING
- THEORY_MASTER_MANUSCRIPT_READY
- FORMAL_MANUSCRIPT_DECISION_REQUIRED
- MASTER_ONLY_DELIVERED
- MASTER_REVISION_REQUIRED
- FORMAL_MANUSCRIPT_PAUSED
- PUBLICATION_PROFILE_REQUIRED
- VENUE_MANUSCRIPT_BUILDING
- FORMAL_MANUSCRIPT_DRAFT
- FORMAL_MANUSCRIPT_READY
- ARXIV_PACKAGE_READY
- BLOCKED_THEORY_MASTER_MANUSCRIPT
- BLOCKED_FORMAL_MANUSCRIPT
- NEEDS_AUTHOR_INPUT
- STALE_GUIDANCE
- NEEDS_REGRESSION
- SUPERSEDED

`venue_kind` 的允许值：

- `PEER_REVIEWED_JOURNAL`
- `PREPRINT_REPOSITORY`
- `CUSTOM_PUBLICATION_VENUE`

`formal_manuscript_decisions.decision` 的允许值：

- `KEEP_MASTER_ONLY`
- `WRITE_FORMAL_MANUSCRIPT`
- `REVISE_MASTER`
- `PAUSE`

该字段不得为自由文本，也没有默认值；缺少绑定当前 master hash 的真实用户决定时，状态保持 `FORMAL_MANUSCRIPT_DECISION_REQUIRED`。

`publication_profiles.route`、`formal_manuscript_decisions.route`、`publication_profile_selections.route` 与 `venue_manuscript_adaptations.route` 的允许值统一为：

- `THEORY`
- `ENGINEERING`

四者必须相等；跨 route 选择返回 `PUBLICATION_PROFILE_ROUTE_MISMATCH`，不得自动转换。

arXiv Profile 只能使用 `PREPRINT_REPOSITORY`。状态机禁止从 `ARXIV_PACKAGE_READY` 派生 `PEER_REVIEWED`、`JOURNAL_ACCEPTED` 或同义状态。

## 10. 依赖与回归

`dependency_edges` 表示：

- DEFINITION_USED_BY
- LEMMA_USED_BY
- EVIDENCE_SUPPORTS
- COUNTEREXAMPLE_REFUTES
- CLAIM_SPECIALIZES
- CLAIM_GENERALIZES
- ENGINEERING_DEPENDS_ON
- MANUSCRIPT_CLAIM_DERIVED_FROM
- PROOF_SUPPORTS_MANUSCRIPT_CLAIM
- REQUIREMENT_SUPPORTS_MANUSCRIPT_CLAIM
- PROFILE_ADAPTS_MASTER

Revision 或 Evidence 撤回后：

1. 查询下游依赖；
2. 标为 NEEDS_REGRESSION；
3. 生成 RegressionPlan；
4. 重跑；
5. 更新有效 Evidence；
6. 不删除旧记录。

## 11. 数据库迁移

使用 Alembic。每次 Schema 变更：

- 先写 migration；
- 更新 schema_version；
- 更新 export manifest；
- 为旧 bundle 提供 reader；
- 不允许应用启动时静默重建数据库。

## v2.1 新增数据模型：Codex 指令忠实传递

### `codex_session_bindings`
- id
- codex_session_id
- project_id
- claim_id
- mode
- active_state_version
- sequence_number
- bound_at
- expires_at
- status

### `user_instruction_events`
- id
- session_binding_id
- turn_id
- raw_user_text_artifact_id
- raw_user_text_hash
- sequence_number
- supersedes_instruction_id
- context_manifest_id
- privacy_class
- status

### `instruction_tokens`
- id
- instruction_id
- token_hash
- nonce
- allowed_operation_class
- state_version
- issued_at
- expires_at
- consumed_at
- signer_key_id

### `command_proposals`
- id
- instruction_id
- codex_interpretation_artifact_id
- platform_interpretation_artifact_id
- instruction_delta_level
- mismatch_fields
- status

### `prepared_commands`
- id
- command_proposal_id
- intended_state_diff_artifact_id
- preserved_constraints_artifact_id
- confirmation_nonce
- expected_state_version
- expires_at
- status

### `command_receipts`
- id
- instruction_id
- command_id
- starting_state_version
- ending_state_version
- executed_operation
- accepted_parameters_artifact_id
- rejected_parameters_artifact_id
- evidence_ids
- pending_gate_ids
- receipt_hash
- status

### `display_contracts`
- id
- command_receipt_id
- exact_summary_artifact_id
- mandatory_statuses
- mandatory_warnings
- prohibited_claims
- display_hash
- fulfilled_at
- status

### `context_manifests`
- id
- workspace_root
- git_revision
- file_refs
- line_ranges
- attached_artifacts
- research_spec_id
- claim_contract_id
- unresolved_refs
- manifest_hash

### 指令状态
- CAPTURED
- TOKEN_ISSUED
- INTERPRETED
- FIDELITY_MATCH
- FIDELITY_AMBIGUOUS
- FIDELITY_MISMATCH
- PREPARED
- COMMITTED
- EXECUTED
- SUPERSEDED
- EXPIRED
- REJECTED

### 指令忠实状态
- FIDELITY_UNCHECKED
- FIDELITY_VERIFIED
- FIDELITY_DEGRADED_READ_ONLY
- FIDELITY_UNAVAILABLE
- MISSING_CONTEXT
- STALE_STATE
