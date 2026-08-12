# Contributing

## Authority

Authoritative sources, highest first: `docs/blueprint/`, `IMPLEMENTATION_STATUS.md`, `TASKS.md`, explicit user instruction, existing implementation. When sources conflict, report the conflict before changing authoritative semantics.

## Development loop

1. Identify the exact Task / Milestone.
2. Read only the relevant blueprint sections.
3. List files expected to change, acceptance tests, and architectural risks.
4. Implement only within the Task boundary; do not cross milestones.
5. Run the real checks and report exit codes.
6. Show a diff summary.
7. Update `IMPLEMENTATION_STATUS.md` when appropriate.
8. Commit in small granular steps. Do not push automatically.

## Checks

```bash
uv sync --all-groups
uv run pytest
uv run ruff check .
uv run ruff format --check .
uv run basedpyright
```

## Rules

- Python `>=3.11`; CI verifies 3.11 and 3.14.
- Provider-agnostic core: no hard-coded LLM vendor logic.
- Every theory repair creates a new Revision; never overwrite history.
- Core semantic changes require a Human Gate.
