"""Codex Instruction Fidelity Layer (CIFL) domain primitives (05A).

This package is framework-free: it depends only on the domain layer (enums,
errors, event) and the standard library, never on web, database, MCP or LLM
bindings. The persistence-backed Command Gateway lives in
``application/fidelity_service.py`` and reuses the M1 event-sourced pattern.
"""
