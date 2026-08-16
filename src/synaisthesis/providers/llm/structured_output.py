"""Strict structured-output parsing (M6.1).

Parsing failures raise StructuredOutputError; the caller must treat it as a
blocked operation and never write partial results to domain state.
"""

from __future__ import annotations

import json
from typing import Any

from synaisthesis.providers.llm.base import StructuredOutputError


def parse_structured_output(text: str, schema: dict[str, Any]) -> dict[str, Any]:
    """Parse JSON text and enforce the required top-level keys (strict)."""
    try:
        data = json.loads(text)
    except json.JSONDecodeError as exc:
        raise StructuredOutputError(
            f"structured output is not valid JSON: {exc}",
            error_code="STRUCTURED_OUTPUT_INVALID",
        ) from exc
    if not isinstance(data, dict):
        raise StructuredOutputError(
            "structured output must be a JSON object",
            error_code="STRUCTURED_OUTPUT_INVALID",
        )
    required = schema.get("required", [])
    for key in required:
        if key not in data:
            raise StructuredOutputError(
                f"structured output missing required key {key!r}",
                error_code="STRUCTURED_OUTPUT_INVALID",
            )
    if schema.get("additionalProperties", True) is False:
        allowed = set(schema.get("properties", {}))
        if allowed:
            extra = set(data) - allowed
            if extra:
                raise StructuredOutputError(
                    "structured output has unknown keys: " + ", ".join(sorted(extra)),
                    error_code="STRUCTURED_OUTPUT_INVALID",
                )
    return data


__all__ = ["parse_structured_output"]
