"""Provider-agnostic LLM contracts (blueprint 02, 08 section 5/13; M6.1).

Business code never imports a concrete vendor: it depends on LLMProvider and
consumes LLMResponse/UsageRecord.  Structured output parsing is strict and
its failures are structured errors that never touch domain state.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol, runtime_checkable

from synaisthesis.domain.errors import DomainError


@dataclass(frozen=True, slots=True)
class LLMRequest:
    """One provider call; structured_schema enables strict output parsing."""

    prompt: str
    system: str = ""
    temperature: float = 0.0
    max_tokens: int | None = None
    structured_schema: dict[str, Any] | None = None
    request_id: str | None = None

    def __post_init__(self) -> None:
        if not self.prompt.strip():
            raise DomainError(
                "LLM request requires a non-empty prompt",
                error_code="LLM_REQUEST_INVALID",
            )
        if not 0.0 <= self.temperature <= 2.0:
            raise DomainError(
                "temperature must be in [0, 2]",
                error_code="LLM_REQUEST_INVALID",
            )


@dataclass(frozen=True, slots=True)
class UsageRecord:
    """Tokens/cost/hash trace for one provider call (08, section 13)."""

    provider: str
    model: str
    prompt_tokens: int
    completion_tokens: int
    cost_estimate: float
    request_hash: str
    response_hash: str

    def __post_init__(self) -> None:
        for field_name in ("provider", "model", "request_hash", "response_hash"):
            if not getattr(self, field_name).strip():
                raise DomainError(
                    f"usage record missing {field_name}",
                    error_code="USAGE_RECORD_INVALID",
                )
        if self.prompt_tokens < 0 or self.completion_tokens < 0 or self.cost_estimate < 0:
            raise DomainError(
                "usage counters must be non-negative",
                error_code="USAGE_RECORD_INVALID",
            )


@dataclass(frozen=True, slots=True)
class LLMResponse:
    """One provider response; structured data is already validated."""

    text: str
    structured: dict[str, Any] | None = None
    usage: UsageRecord | None = None
    model: str = ""

    def __post_init__(self) -> None:
        if not self.text.strip() and self.structured is None:
            raise DomainError(
                "LLM response must carry text or structured data",
                error_code="LLM_RESPONSE_INVALID",
            )


class StructuredOutputError(DomainError):
    """Structured output parsing failed; nothing was written to domain state."""


@runtime_checkable
class LLMProvider(Protocol):
    """Synchronous LLM provider contract; implementations must be stateless."""

    @property
    def provider_name(self) -> str: ...

    @property
    def model_name(self) -> str: ...

    def complete(self, request: LLMRequest) -> LLMResponse: ...


__all__ = [
    "LLMProvider",
    "LLMRequest",
    "LLMResponse",
    "StructuredOutputError",
    "UsageRecord",
]
