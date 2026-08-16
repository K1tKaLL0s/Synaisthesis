"""PreToolUse hook skeleton: fail closed when a mutation has no fidelity token.

The hook is a defense-in-depth layer; the MCP server re-validates tokens,
hashes and state versions independently (05A section 19).
"""

from __future__ import annotations

from typing import Any

MUTATION_TOOLS = {
    "research_prepare_command",
    "research_commit_command",
    "research_cancel_prepared_command",
}


def pre_tool_use(
    *,
    tool_name: str,
    tool_input: dict[str, Any],
) -> dict[str, Any]:
    """Block Synaisthesis mutations without an instruction token."""
    if tool_name in MUTATION_TOOLS:
        token = tool_input.get("instruction_token")
        if not token:
            return {
                "decision": "block",
                "reason": "FIDELITY_CHANNEL_REQUIRED: mutation 缺少 instruction_token",
            }
        return {
            "decision": "allow",
            "injectedArguments": {
                "instruction_token": token,
                "required_transport_fields": ["expected_state_version", "idempotency_key"],
            },
        }
    return {"decision": "allow", "injectedArguments": {}}


__all__ = ["MUTATION_TOOLS", "pre_tool_use"]
