"""Deterministic fake LLM provider for contract tests and CI (M6.1).

The fake is fully deterministic: the same request always produces the same
text, structured payload and usage hashes.  Failure modes (invalid JSON,
unavailable provider) are injectable so error paths are contract-tested
without a network or real credentials.
"""

from __future__ import annotations

import json
from dataclasses import dataclass

from synaisthesis.providers.llm.base import (
    LLMRequest,
    LLMResponse,
)
from synaisthesis.providers.llm.usage import request_content_hash, usage_record_for

_PROVIDER_NAME = "fake-llm"
_MODEL_NAME = "fake-model-1"


def _deterministic_text(request: LLMRequest) -> str:
    digest = request_content_hash(request)
    return f"fake-response[{request.prompt[:24]}...]:{digest[:12]}"


@dataclass(frozen=True, slots=True)
class FakeLLMProvider:
    """Deterministic provider; configure failure via the constructor."""

    fail_with: Exception | None = None
    invalid_json: bool = False
    model_name: str = _MODEL_NAME

    @property
    def provider_name(self) -> str:
        return _PROVIDER_NAME

    def complete(self, request: LLMRequest) -> LLMResponse:
        if self.fail_with is not None:
            raise self.fail_with
        if request.structured_schema is not None and not self.invalid_json:
            structured = {
                key: f"fake-{key}-{request_content_hash(request)[:8]}"
                for key in request.structured_schema.get("required", [])
            }
            text = json.dumps(structured, ensure_ascii=False)
        else:
            structured = None
            text = "{not json" if self.invalid_json else _deterministic_text(request)
        usage = usage_record_for(
            provider=_PROVIDER_NAME,
            model=self.model_name,
            request=request,
            response=LLMResponse(text=text, structured=structured),
            prompt_tokens=len(request.prompt),
            completion_tokens=len(text),
            cost_estimate=0.001,
        )
        return LLMResponse(text=text, structured=structured, usage=usage, model=self.model_name)


__all__ = ["FakeLLMProvider"]
