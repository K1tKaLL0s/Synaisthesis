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

`M0` — repository skeleton and quality base. No research functionality yet.

Blueprint baseline: `V2.4` (2026-08-14) — freezes route-aware formalization feasibility, the mandatory engineering-route decision, ENG0–ENG10 mechanical-blueprint delivery, and dual-track audited paper masters with optional journal/arXiv adaptation after a user decision. This is documentation only; the corresponding product functionality is not implemented yet.

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

## Governance

- 权威文档：`docs/blueprint/`（完整工程蓝图）
- 实现状态：`IMPLEMENTATION_STATUS.md`
- 待办任务：`TASKS.md`
- 工程规则：`AGENTS.md`

License: Apache-2.0
