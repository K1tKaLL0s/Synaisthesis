# 联觉科研 / 联科 — Synaisthesis

> Synaisthesis is a human-governed, dual-model research orchestration platform that turns natural-language research intent into versioned claims, adversarial verification loops, formal-tool evidence, and auditable human decisions—with bidirectional Codex integration.

```text
Idea / Spec
    ↓
Adjacent Research · Mature Engineering Neighbors
    ↓
Formula-First Early Formalization · User Review
    ↓
Theory Novelty + Application Novelty (>=70 auto-continue)
    ↓
Claim Compiler
    ↓
Frozen ClaimContract
    ↓
Support · Oppose · Independent
    ↓
Lean · Z3 · Python · Literature · Codex Worker
    ↓
Semantic Audit · Regression · Human Gate
    ↓
Versioned Research Bundle
```

## Status

`M15` — mandatory milestones M0–M15 are implemented and verified. Remaining work is optional `M16.ENHANCEMENT.<NAME>` items, one ADR/Task at a time. See `IMPLEMENTATION_STATUS.md` and `TASKS.md` for the exact verified state.

Blueprint baseline: `V2.4` (2026-08-14) — freezes route-aware formalization feasibility, the mandatory engineering-route decision, ENG0–ENG10 mechanical-blueprint delivery, and dual-track audited paper masters with optional journal/arXiv adaptation after a user decision. The baseline records blueprint semantics; product functionality is implemented incrementally milestone-by-milestone through M15, not as one big-bang release.

## Development

- Python `>=3.11`（uv 管理解释器与依赖）
- 推荐在 WSL2 中运行

```bash
uv sync --all-groups
uv run pytest
uv run ruff check .
uv run ruff format --check .
uv run basedpyright
uv run synaisthesis --version
```

> In a read-only-venv environment (e.g. the DSH workspace sandbox, where `.venv` resolves outside the writable workspace), append `--no-sync` to `uv run` and set `UV_CACHE_DIR` to a writable path. See `CONTRIBUTING.md`.

## Governance

- 权威文档：`docs/blueprint/`（完整工程蓝图）
- 实现状态：`IMPLEMENTATION_STATUS.md`
- 待办任务：`TASKS.md`
- 工程规则：`AGENTS.md`

License: Apache-2.0
