# Synaisthesis Engineering Rules

## Authority

Authoritative sources, highest first:

1. `docs/blueprint/`
2. `IMPLEMENTATION_STATUS.md`
3. `TASKS.md`
4. Current explicit user instruction
5. Existing implementation

When sources conflict, do not silently choose. Report the conflict and stop before changing authoritative semantics.

## Project identity

- Chinese name: 联觉科研
- Short Chinese name: 联科
- English name: Synaisthesis
- Repository root on this workstation: `E:\Synaisthesis`
- 部分工具、依赖与 Codex 数据存放在 N 盘：`N:\CodexData`（含 `caches/lean`、`caches/mathlib`、`caches/pip`、`envs`、`toolchains`、`workspaces`、`artifacts`、`wsl`）。
- 不允许 Synaisthesis 工程开发修改 `N:\CodexData` 下 Codex 正在工作的理论仓库（与 docs/blueprint/00A §3 一致）。

## Development mode

Implement incrementally. Never implement the whole blueprint in one task.

Before modifying code:
1. identify the exact stable Task ID / Milestone from `docs/blueprint/19_MECHANICAL_EXECUTION_CONTRACT.md`;
2. read only the authoritative sections listed for that Task;
3. write a complete `WorkUnitContract` including allowed/forbidden files, symbols, I/O, state/events, invariants, errors, commands, acceptance and stop conditions;
4. confirm all Task preconditions and Human Gates;
5. state architectural risks.

If the Task has no complete contract, sources conflict, or a required field is undefined, report `BLUEPRINT_GAP` or `BLUEPRINT_CONFLICT` and stop before code changes.

After modifying code:
1. run the required real checks;
2. report commands and exit results;
3. show a diff summary;
4. update `IMPLEMENTATION_STATUS.md` when appropriate;
5. do not start the next Task automatically.

The modular files in `docs/blueprint/` are authoritative. The consolidated blueprint is generated and must not be edited independently. Any blueprint change must follow the synchronization and integrity checks in document 19.

## Research verification boundaries

- LLM output is a proposal, not a deterministic tool result.
- Lean PASS can only be recorded after a real Lean invocation succeeds.
- Z3 SAT / UNSAT / UNKNOWN can only be recorded from the real solver adapter.
- Python experiment PASS can only be recorded from the sandbox execution receipt.
- Formal verification, semantic alignment, novelty and empirical validity are separate statuses.

## Semantic governance

- Do not silently change object domains, quantifiers, core assumptions, core conclusions or engineering goals.
- Core semantic changes require Human Gate.
- Proof Loop may modify proof content but not the frozen theorem statement.
- Every theory repair creates a new revision; never overwrite historical revisions.

## Git safety

Do not run without explicit user request:
- `git push`
- `git reset --hard`
- `git clean -fd`
- destructive rebase
- history rewriting
- automatic commit

## Provider architecture

DeepSeek is the current engineering model, but Synaisthesis Core must remain provider-agnostic.

Do not hard-code product logic to a single LLM vendor.

## Agent tool discipline

- Every Bash tool call must include the required `description` field (5–10 words, active voice). Omitting it fails schema validation with `missing required property "description"` and wastes a turn.
- This applies to the top-level agent and to every subagent or workflow worker it spawns; pass the requirement along in any delegation prompt.
