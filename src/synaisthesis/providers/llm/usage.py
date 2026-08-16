"""Usage tracing for LLM calls (08, section 13; M6.1)."""

from __future__ import annotations

from synaisthesis.domain.event import sha256_hex
from synaisthesis.providers.llm.base import LLMRequest, LLMResponse, UsageRecord


def request_content_hash(request: LLMRequest) -> str:
    """Content-bound hash of a request (prompt/system/schema)."""
    return sha256_hex(
        {
            "prompt": request.prompt,
            "system": request.system,
            "temperature": request.temperature,
            "max_tokens": request.max_tokens,
            "structured_schema": request.structured_schema,
        }
    )


def response_content_hash(response: LLMResponse) -> str:
    """Content-bound hash of a response (text + structured payload)."""
    return sha256_hex(
        {
            "text": response.text,
            "structured": response.structured,
        }
    )


def usage_record_for(
    *,
    provider: str,
    model: str,
    request: LLMRequest,
    response: LLMResponse,
    prompt_tokens: int,
    completion_tokens: int,
    cost_estimate: float,
) -> UsageRecord:
    """Build a usage record whose hashes recompute from the call content."""
    return UsageRecord(
        provider=provider,
        model=model,
        prompt_tokens=prompt_tokens,
        completion_tokens=completion_tokens,
        cost_estimate=cost_estimate,
        request_hash=request_content_hash(request),
        response_hash=response_content_hash(response),
    )


__all__ = [
    "request_content_hash",
    "response_content_hash",
    "usage_record_for",
]
