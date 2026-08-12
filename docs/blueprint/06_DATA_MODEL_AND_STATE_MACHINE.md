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
→ MATURE_IDEA_READY
→ THEORY_BUILDING
→ CLAIM_COMPILED
→ CLAIM_FROZEN
→ COUNCIL_RUNNING
→ BLOCKED_HUMAN / BLOCKED_TOOL
→ CANDIDATE_STABLE
→ USER_ACCEPTED
→ REVOKED
```

允许回退：

- THEORY_BUILDING → INCUBATING；
- CLAIM_COMPILED → THEORY_BUILDING；
- COUNCIL_RUNNING → CLAIM_COMPILED；
- CANDIDATE_STABLE → COUNCIL_RUNNING；
- USER_ACCEPTED → REVOKED。

回退只写事件，不删除历史。

## 3. ProvenanceType

- USER_INPUT
- USER_DECISION
- EXTERNAL_SOURCE
- ASSISTANT_PROPOSAL
- DERIVED
- TOOL_EXECUTION
- CODEX_EXECUTION
- HUMAN_VERIFIED

## 4. EvidenceType

- LITERATURE_METADATA
- LITERATURE_INTERPRETATION
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
  theory/
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
formal_status = LEAN_PASS
semantic_status = AI_AUDITED
human_review_status = PENDING
novelty_status = POSSIBLY_ORIGINAL
```

这表示形式命题已通过，但原始语义尚未由用户最终确认。

## 10. 依赖与回归

`dependency_edges` 表示：

- DEFINITION_USED_BY
- LEMMA_USED_BY
- EVIDENCE_SUPPORTS
- COUNTEREXAMPLE_REFUTES
- CLAIM_SPECIALIZES
- CLAIM_GENERALIZES
- ENGINEERING_DEPENDS_ON

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
