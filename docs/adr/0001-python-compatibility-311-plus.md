# ADR 0001 — Python Compatibility Policy: 3.11+

- Status: Accepted
- Date: 2026-08-13

## Context

The V2 blueprint (docs/blueprint/00_README.md) recommends Python 3.11. The current
WSL2 environment has Python 3.14.4. The user decided to support Python `>=3.11`
rather than pinning exactly 3.11.

## Decision

- `requires-python = ">=3.11"` in pyproject.toml.
- CI (`ci-core.yml`) verifies both bounds: 3.11 and 3.14.
- `uv` manages interpreters and the virtual environment.
- Ruff `target-version = "py311"`, Pyright `pythonVersion = "3.11"` so local
  checks enforce 3.11-compatible syntax/typing regardless of the runtime used.

## Consequences

- Any future use of stdlib or syntax must exist in 3.11.
- Local development may run on 3.14; compatibility is proven by CI and by
  running the full check suite under 3.11 before merging.
