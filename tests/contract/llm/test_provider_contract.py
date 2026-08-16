"""M6.1 contract tests for the provider-agnostic LLM layer."""

from __future__ import annotations

import pytest

from synaisthesis.domain.errors import DomainError
from synaisthesis.providers.llm.base import (
    LLMProvider,
    LLMRequest,
    LLMResponse,
    StructuredOutputError,
    UsageRecord,
)
from synaisthesis.providers.llm.fake_provider import FakeLLMProvider
from synaisthesis.providers.llm.structured_output import parse_structured_output
from synaisthesis.providers.llm.usage import (
    request_content_hash,
    response_content_hash,
    usage_record_for,
)

SCHEMA = {
    "type": "object",
    "required": ["claim_id", "statement"],
    "additionalProperties": False,
    "properties": {"claim_id": {"type": "string"}, "statement": {"type": "string"}},
}


def test_fake_provider_is_deterministic():
    provider = FakeLLMProvider()
    request = LLMRequest(prompt="编译 claim", temperature=0.0)
    first = provider.complete(request)
    second = provider.complete(request)
    assert first.text == second.text
    assert first.usage == second.usage
    assert first.usage is not None
    assert first.usage.prompt_tokens == len(request.prompt)
    assert first.usage.request_hash == request_content_hash(request)
    assert first.usage.response_hash == response_content_hash(first)


def test_provider_is_swappable_without_vendor_imports():
    # business code depends only on the protocol: swap fake <-> stub freely
    class OtherProvider:
        provider_name = "other"
        model_name = "other-1"

        def complete(self, request: LLMRequest) -> LLMResponse:
            return LLMResponse(text="other", model=self.model_name)

    providers: list[LLMProvider] = [FakeLLMProvider(), OtherProvider()]  # type: ignore[list-item]
    for provider in providers:
        response = provider.complete(LLMRequest(prompt="x"))
        assert response.text


def test_structured_output_parses_valid_json():
    provider = FakeLLMProvider()
    request = LLMRequest(prompt="生成 claim", structured_schema=SCHEMA)
    response = provider.complete(request)
    assert response.structured is not None
    assert "claim_id" in response.structured
    assert "statement" in response.structured
    parsed = parse_structured_output(response.text, SCHEMA)
    assert parsed == response.structured


def test_structured_output_failure_never_writes_state():
    provider = FakeLLMProvider(invalid_json=True)
    request = LLMRequest(prompt="生成 claim", structured_schema=SCHEMA)
    response = provider.complete(request)
    with pytest.raises(StructuredOutputError) as exc_info:
        parse_structured_output(response.text, SCHEMA)
    assert exc_info.value.error_code == "STRUCTURED_OUTPUT_INVALID"
    # nothing was produced that could be written to domain state
    assert response.structured is None


def test_structured_output_rejects_missing_and_unknown_keys():
    with pytest.raises(StructuredOutputError):
        parse_structured_output('{"claim_id": "c1"}', SCHEMA)
    with pytest.raises(StructuredOutputError):
        parse_structured_output('{"claim_id": "c1", "statement": "s", "extra": 1}', SCHEMA)
    with pytest.raises(StructuredOutputError):
        parse_structured_output("not json", SCHEMA)


def test_provider_failure_is_structured_blocker():
    provider = FakeLLMProvider(fail_with=RuntimeError("network down"))
    with pytest.raises(RuntimeError):
        provider.complete(LLMRequest(prompt="x"))


def test_usage_hashes_are_content_bound():
    request = LLMRequest(prompt="p")
    response = LLMResponse(text="t")
    usage = usage_record_for(
        provider="fake-llm",
        model="fake-model-1",
        request=request,
        response=response,
        prompt_tokens=1,
        completion_tokens=1,
        cost_estimate=0.01,
    )
    assert isinstance(usage, UsageRecord)
    assert usage.request_hash == request_content_hash(request)
    assert usage.response_hash == response_content_hash(response)
    other = LLMRequest(prompt="q")
    assert usage.request_hash != request_content_hash(other)


def test_request_validation():
    with pytest.raises(DomainError):
        LLMRequest(prompt="   ")
    with pytest.raises(DomainError):
        LLMRequest(prompt="x", temperature=3.0)
    assert LLMRequest(prompt="x").temperature == 0.0
