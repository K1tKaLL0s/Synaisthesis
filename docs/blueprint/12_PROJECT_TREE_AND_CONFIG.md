# 12 — 完整项目目录与配置设计

本文件给出可直接照着建立仓库的目录结构。目录名可以调整，但模块边界不应随意合并。

## 1. 推荐仓库结构

```text
synaisthesis/
├─ README.md
├─ README.zh-CN.md
├─ LICENSE
├─ SECURITY.md
├─ CONTRIBUTING.md
├─ CHANGELOG.md
├─ ROADMAP.md
├─ pyproject.toml
├─ uv.lock
├─ .env.example
├─ .gitignore
├─ docker-compose.yml
├─ Makefile                         # 可选；只包装常用命令
│
├─ configs/
│  ├─ default.yaml
│  ├─ development.yaml
│  ├─ test.yaml
│  ├─ profiles/
│  │  ├─ a1_assisted.yaml
│  │  ├─ a2_delegated.yaml
│  │  ├─ a3_autonomous_bounded.yaml
│  │  ├─ codex_worker_readonly.yaml
│  │  └─ codex_worker_workspace_write.yaml
│  └─ policies/
│     ├─ semantic_delta.yaml
│     ├─ evidence_status.yaml
│     ├─ action_authorization.yaml
│     └─ isolation.yaml
│
├─ src/synaisthesis/
│  ├─ __init__.py
│  ├─ version.py
│  ├─ config/
│  │  ├─ settings.py
│  │  ├─ loaders.py
│  │  └─ validation.py
│  │
│  ├─ domain/
│  │  ├─ enums.py
│  │  ├─ project.py
│  │  ├─ research_spec.py
│  │  ├─ stage.py
│  │  ├─ claim.py
│  │  ├─ claim_contract.py
│  │  ├─ revision.py
│  │  ├─ evidence.py
│  │  ├─ attack.py
│  │  ├─ gate.py
│  │  ├─ action.py
│  │  ├─ receipt.py
│  │  ├─ budget.py
│  │  ├─ isolation.py
│  │  ├─ event.py
│  │  ├─ policies.py
│  │  └─ errors.py
│  │
│  ├─ application/
│  │  ├─ incubation_service.py
│  │  ├─ claim_compiler_service.py
│  │  ├─ council_service.py
│  │  ├─ verification_service.py
│  │  ├─ semantic_audit_service.py
│  │  ├─ regression_service.py
│  │  ├─ gate_service.py
│  │  ├─ action_service.py
│  │  ├─ codex_delegation_service.py
│  │  ├─ export_service.py
│  │  └─ project_service.py
│  │
│  ├─ orchestration/
│  │  ├─ state.py
│  │  ├─ graph_builder.py
│  │  ├─ nodes/
│  │  │  ├─ incubator_nodes.py
│  │  │  ├─ council_nodes.py
│  │  │  ├─ verification_nodes.py
│  │  │  ├─ repair_nodes.py
│  │  │  ├─ semantic_nodes.py
│  │  │  ├─ regression_nodes.py
│  │  │  └─ codex_nodes.py
│  │  ├─ routes.py
│  │  ├─ checkpointing.py
│  │  ├─ run_worker.py
│  │  ├─ job_queue.py
│  │  └─ recovery.py
│  │
│  ├─ agents/
│  │  ├─ schemas.py
│  │  ├─ primary_researcher.py
│  │  ├─ auditor.py
│  │  ├─ supporter.py
│  │  ├─ opponent.py
│  │  ├─ independent_reviewer.py
│  │  ├─ formalizer.py
│  │  ├─ repairer.py
│  │  ├─ semantic_auditor.py
│  │  ├─ literature_reviewer.py
│  │  └─ synthesis_agent.py
│  │
│  ├─ providers/
│  │  ├─ llm/
│  │  │  ├─ base.py
│  │  │  ├─ litellm_provider.py
│  │  │  ├─ fake_provider.py
│  │  │  ├─ router.py
│  │  │  ├─ retry.py
│  │  │  ├─ usage.py
│  │  │  └─ structured_output.py
│  │  └─ literature/
│  │     ├─ base.py
│  │     ├─ openalex.py
│  │     ├─ crossref.py
│  │     ├─ arxiv.py
│  │     ├─ semantic_scholar.py
│  │     ├─ normalization.py
│  │     └─ deduplication.py
│  │
│  ├─ verifiers/
│  │  ├─ base.py
│  │  ├─ lean/
│  │  │  ├─ adapter.py
│  │  │  ├─ compiler.py
│  │  │  ├─ parser.py
│  │  │  ├─ statement_lock.py
│  │  │  └─ leandojo_adapter.py
│  │  ├─ z3/
│  │  │  ├─ adapter.py
│  │  │  ├─ constraint_spec.py
│  │  │  ├─ encoder.py
│  │  │  ├─ model_extractor.py
│  │  │  └─ witness_validator.py
│  │  ├─ python/
│  │  │  ├─ adapter.py
│  │  │  ├─ sandbox_job.py
│  │  │  ├─ docker_runner.py
│  │  │  └─ output_collector.py
│  │  └─ registry.py
│  │
│  ├─ integrations/
│  │  ├─ codex/
│  │  │  ├─ base.py
│  │  │  ├─ sdk_adapter.py
│  │  │  ├─ mcp_adapter.py
│  │  │  ├─ exec_adapter.py
│  │  │  ├─ app_server_bridge.py
│  │  │  ├─ task_spec.py
│  │  │  ├─ session.py
│  │  │  ├─ worktree.py
│  │  │  ├─ recursion_guard.py
│  │  │  ├─ receipt.py
│  │  │  └─ profile.py
│  │  ├─ git/
│  │  │  ├─ repository.py
│  │  │  ├─ worktree.py
│  │  │  └─ diff.py
│  │  └─ docker/
│  │     ├─ client.py
│  │     └─ policy.py
│  │
│  ├─ storage/
│  │  ├─ database.py
│  │  ├─ migrations/
│  │  ├─ repositories/
│  │  │  ├─ project_repository.py
│  │  │  ├─ claim_repository.py
│  │  │  ├─ event_repository.py
│  │  │  ├─ evidence_repository.py
│  │  │  └─ run_repository.py
│  │  ├─ artifact_store.py
│  │  ├─ hashing.py
│  │  ├─ snapshots.py
│  │  └─ export_bundle.py
│  │
│  ├─ security/
│  │  ├─ authorization.py
│  │  ├─ allowlist.py
│  │  ├─ secret_filter.py
│  │  ├─ prompt_injection.py
│  │  ├─ provenance.py
│  │  └─ audit.py
│  │
│  ├─ interfaces/
│  │  ├─ api/
│  │  │  ├─ main.py
│  │  │  ├─ dependencies.py
│  │  │  ├─ routes/
│  │  │  └─ schemas/
│  │  ├─ cli/
│  │  │  ├─ main.py
│  │  │  ├─ doctor.py
│  │  │  └─ commands/
│  │  └─ mcp/
│  │     ├─ server.py
│  │     ├─ tools.py
│  │     ├─ resources.py
│  │     ├─ auth.py
│  │     └─ annotations.py
│  │
│  ├─ prompts/
│  │  ├─ registry.py
│  │  ├─ incubator/
│  │  ├─ council/
│  │  ├─ formalization/
│  │  ├─ semantic_audit/
│  │  ├─ literature/
│  │  └─ codex_worker/
│  │
│  ├─ telemetry/
│  │  ├─ logging.py
│  │  ├─ metrics.py
│  │  ├─ tracing.py
│  │  └─ redaction.py
│  │
│  └─ evals/
│     ├─ runner.py
│     ├─ graders.py
│     ├─ datasets.py
│     └─ reports.py
│
├─ plugin/
│  ├─ .codex-plugin/
│  │  └─ plugin.json
│  ├─ .mcp.json
│  ├─ skills/
│  │  ├─ synaisthesis-incubator-operator/
│  │  │  └─ SKILL.md
│  │  ├─ synaisthesis-council-operator/
│  │  │  └─ SKILL.md
│  │  └─ synaisthesis-admin/
│  │     └─ SKILL.md
│  ├─ hooks/
│  │  └─ hooks.json
│  ├─ assets/
│  └─ README.md
│
├─ web/
│  ├─ package.json
│  ├─ vite.config.ts
│  ├─ src/
│  │  ├─ api/
│  │  ├─ components/
│  │  ├─ pages/
│  │  ├─ routes/
│  │  ├─ state/
│  │  └─ types/
│  └─ tests/
│
├─ examples/
│  ├─ simple_integer_counterexample/
│  ├─ lean_statement_drift/
│  ├─ finite_graph_claim/
│  └─ real_project_case_study/
│
├─ tests/
│  ├─ unit/
│  ├─ contract/
│  ├─ integration/
│  ├─ external/
│  ├─ security/
│  ├─ golden/
│  ├─ fixtures/
│  └─ fake_runtime/
│
├─ docs/
│  ├─ architecture/
│  ├─ protocols/
│  ├─ adr/
│  ├─ user-guide/
│  ├─ developer-guide/
│  └─ case-studies/
│
├─ scripts/
│  ├─ bootstrap_dev_environment.*
│  ├─ install_lean.*
│  ├─ install_codex_worker_profile.*
│  ├─ run_local_mcp.*
│  └─ export_demo_bundle.*
│
└─ .github/
   ├─ workflows/
   │  ├─ ci-core.yml
   │  ├─ ci-integration.yml
   │  ├─ ci-formal.yml
   │  ├─ ci-mcp.yml
   │  └─ release.yml
   ├─ ISSUE_TEMPLATE/
   └─ pull_request_template.md
```

## 2. 配置分组

### `platform`
- `workspace_root`
- `database_url`
- `artifact_root`
- `log_level`
- `environment`
- `event_sourcing_enabled`
- `api_host`
- `api_port`
- `mcp_transport`

### `loop`
- `default_rounds = 10`
- `max_rounds_allowed`
- `minimum_rounds_before_early_stop = 4`
- `stable_rounds_required = 2`
- `checkpoint_every_valid_rounds = 5`
- `maturity_review_round = 20`
- `max_repair_candidates = 3`
- `max_proof_attempts_per_round`
- `allow_early_stop`
- `allow_auto_extension = false`

这里必须明确：原工作流的“每 5 个实质轮次 checkpoint、20 轮成熟化复核”属于长期研究对话节律；Council 的默认 10 轮是单次自主验证预算。两套计数不可混用。

### `models`
- `primary`
- `auditor`
- `utility`
- `synthesis`
- `fallbacks`
- `require_model_diversity`
- `allow_same_family_with_warning`
- `structured_output_retries`
- `context_budget`

每个 ModelProfile：
- provider
- model
- endpoint
- credential_env
- timeout
- max_output_tokens
- reasoning_effort
- temperature 或等效参数
- cost metadata
- allowed_roles

### `budget`
- `max_total_model_calls`
- `max_input_tokens`
- `max_output_tokens`
- `max_reported_cost`
- `max_wall_time`
- `max_codex_tasks`
- `max_codex_turns_per_task`
- `max_tool_runtime`

### `lean`
- `enabled`
- `mode = compiler | interactive`
- `lean_bin`
- `lake_bin`
- `project_template`
- `mathlib_cache`
- `timeout`
- `proof_attempt_budget`
- `statement_hash_required = true`

### `z3`
- `enabled`
- `timeout_ms`
- `supported_sorts`
- `max_model_size`
- `independent_witness_validation = true`

### `python_sandbox`
- `enabled`
- `runtime = docker`
- `image`
- `network = none`
- `memory_limit`
- `cpu_limit`
- `pids_limit`
- `timeout`
- `allowed_output_size`

### `codex`
- `enabled`
- `preferred_transport = sdk`
- `fallback_transports = [mcp, exec]`
- `model`
- `operator_profile`
- `worker_profile`
- `worker_codex_home`
- `sandbox = read-only | workspace-write`
- `approval_policy`
- `network_policy`
- `use_git_worktree = true`
- `cleanup_worktree_on_success`
- `retain_failed_worktree`
- `max_delegation_depth = 1`
- `worker_synaisthesis_mcp_enabled = false`
- `max_turns`
- `timeout`
- `cost_budget`
- `allowed_task_types`

### `literature`
- providers
- request rate
- result count
- full-text policy
- metadata verification
- deduplication strategy
- query budget
- novelty wording policy

### `security`
- `manual_approval_default = true`
- `action_allowlist`
- `protected_paths`
- `secret_patterns`
- `prompt_injection_quarantine = true`
- `external_content_trust = untrusted`
- `evidence_hashing = true`
- `audit_log_immutable = true`

## 3. 推荐运行 Profile

### A1 — AI_ASSISTED
- 用户逐阶段决定下一步；
- 模型只产候选；
- 所有外部写操作人工批准；
- 不运行自主 Council。

### A2 — AI_DELEGATED
- 用户冻结任务后，平台可自主完成指定阶段；
- S2 以上 Semantic Delta 暂停；
- 工具写操作使用 allowlist；
- 默认不调 Codex Workspace Write。

### A3 — AI_AUTONOMOUS_BOUNDED
- 在 FrozenClaim、预算、工具权限和停止条件内运行；
- 默认最多 10 轮；
- S0/S1 自动提交；
- S2 进入 Gate；
- S3/S4 强制 Gate；
- 不允许自动延长预算；
- 不允许 Worker 递归调用。

### Codex Worker Readonly
- 只读仓库；
- 用于分析、计划、审查；
- 不加载 Synaisthesis MCP；
- 网络关闭；
- 不得写 Evidence PASS。

### Codex Worker Workspace Write
- 仅写独立 worktree；
- 只允许指定文件；
- 运行指定测试；
- diff 与日志进入 Receipt；
- 完成后由 Verification Adapter 重验。

## 4. 环境变量

`.env.example` 只列变量名，不提交真实值：
- Synaisthesis 数据库与 workspace；
- 各模型 provider credential；
- OpenAlex/Crossref 等可选 key；
- Codex Worker `CODEX_HOME`；
- 日志/追踪 endpoint；
- 可选 PostgreSQL/Redis。

任何 credential 都不得进入：
- Prompt Artifact；
- CodexTaskSpec；
- ResearchBundle；
- ExecutionReceipt；
- Git diff；
- 测试 fixture。

## 5. 版本化规则

配置文件也属于研究环境证据。每次 Run 保存：
- resolved config snapshot；
- config hash；
-模型 profile ID；
- Prompt version；
- Tool version；
- Codex transport/version；
- Lean/Z3/Python runtime version。

这样才能解释“为什么同一研究任务在不同日期得到不同结果”。

## v2.1 新增目录：Codex Fidelity

建议增加：

```text
app/
  fidelity/
    instruction_capsule.py
    instruction_token.py
    instruction_delta.py
    context_manifest.py
    command_gateway.py
    prepare_commit.py
    command_receipt.py
    display_contract.py
    session_binding.py

integrations/
  codex_bridge/
    sidecar.py
    local_spool.py
    hook_ingress.py
    token_client.py
    healthcheck.py

codex-plugin/
  hooks/
    hooks.json
    user_prompt_submit.py
    pre_synaisthesis_tool.py
    post_synaisthesis_tool.py
    stop_response_fidelity.py

configs/
  fidelity/
    strict_bound_session.yaml
    explicit_command.yaml
    degraded_read_only.yaml
```

新增配置：

- `fidelity.mode`
- `fidelity.fail_closed_for_mutations = true`
- `fidelity.capture_raw_prompt = true`
- `fidelity.raw_prompt_privacy = private`
- `fidelity.instruction_token_ttl_seconds`
- `fidelity.prepared_command_ttl_seconds`
- `fidelity.require_state_version = true`
- `fidelity.require_context_manifest_for_mutation = true`
- `fidelity.require_stop_display_audit = true`
- `fidelity.sidecar_transport`
- `fidelity.local_spool_path`
- `fidelity.spool_encryption`
- `fidelity.max_unresolved_references = 0`
- `fidelity.ide_extension_install_mode`
- `fidelity.plugin_hooks_required`
