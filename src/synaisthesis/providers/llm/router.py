"""LLM role router (blueprint 19 §5 M6.3, 03A sections 2/8; M6.3).

Routes role-based calls to providers, enforces structured output (failures
raise StructuredOutputError and never touch domain state), derives RQ0
capability profiles from LLM evidence, and reports reviewer independence
(08 section 7: same-family reviewers are degraded, never silently treated as
independent).
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from synaisthesis.domain.errors import DomainError
from synaisthesis.domain.qualification import (
    FormalizationCapabilityProfile,
)
from synaisthesis.providers.llm.base import (
    LLMProvider,
    LLMRequest,
    LLMResponse,
)
from synaisthesis.providers.llm.structured_output import parse_structured_output

ROLE_EARLY_FORMALIZER = "early_formalizer"
ROLE_CAPABILITY_EVAL = "capability_eval"
ROLE_NOVELTY_PRIMARY = "novelty_primary"
ROLE_NOVELTY_AUDITOR = "novelty_auditor"

CAPABILITY_SCHEMA: dict[str, Any] = {
    "type": "object",
    "required": [
        "capability_tier",
        "formalization_eval_score",
        "math_schema_valid_rate",
        "source_citation_support",
        "structured_output_support",
        "context_budget_sufficient",
    ],
    "additionalProperties": False,
    "properties": {
        "capability_tier": {"type": "string"},
        "formalization_eval_score": {"type": "number"},
        "math_schema_valid_rate": {"type": "number"},
        "source_citation_support": {"type": "boolean"},
        "structured_output_support": {"type": "boolean"},
        "context_budget_sufficient": {"type": "boolean"},
    },
}


class LLMRouter:
    """Maps roles to providers and enforces the structured-output contract."""

    def __init__(
        self,
        providers: Mapping[str, LLMProvider],
        families: Mapping[str, str],
    ) -> None:
        if not providers:
            raise DomainError(
                "router requires at least one provider",
                error_code="ROUTER_INVALID",
            )
        self._providers = dict(providers)
        self._families = dict(families)

    def provider_for(self, role: str) -> LLMProvider:
        provider = self._providers.get(role)
        if provider is None:
            raise DomainError(
                f"no provider bound for role {role!r}",
                error_code="PROVIDER_UNAVAILABLE",
            )
        return provider

    def family_for(self, role: str) -> str | None:
        return self._families.get(role)

    def complete_for(self, role: str, request: LLMRequest) -> LLMResponse:
        """Call the role's provider and enforce strict structured output."""
        provider = self.provider_for(role)
        response = provider.complete(request)
        if request.structured_schema is not None and response.structured is None:
            parsed = parse_structured_output(response.text, request.structured_schema)
            response = LLMResponse(
                text=response.text,
                structured=parsed,
                usage=response.usage,
                model=response.model,
            )
        return response

    def reviewer_independence(self, role_a: str, role_b: str) -> tuple[bool, str]:
        """Two reviewers are independent only on different model families."""
        family_a = self.family_for(role_a)
        family_b = self.family_for(role_b)
        if family_a is None or family_b is None:
            return False, "SAME_MODEL_FAMILY_DEGRADED：角色未绑定模型家族，无法证明独立"
        if family_a == family_b:
            return False, "SAME_MODEL_FAMILY_DEGRADED：两 Reviewer 同模型家族"
        return True, "independent"


def capability_profile_from_llm(
    response: LLMResponse,
    *,
    model_profile_id: str,
    evaluated_at: Any,
) -> FormalizationCapabilityProfile:
    """Derive an RQ0 capability profile from validated LLM evidence (03A, 2.2)."""
    if response.structured is None:
        raise DomainError(
            "能力评估缺少结构化证据",
            error_code="CAPABILITY_UNAVAILABLE",
        )
    data = response.structured
    return FormalizationCapabilityProfile(
        model_profile_id=model_profile_id,
        capability_tier=str(data["capability_tier"]),
        formalization_eval_score=float(data["formalization_eval_score"]),
        math_schema_valid_rate=float(data["math_schema_valid_rate"]),
        source_citation_support=bool(data["source_citation_support"]),
        structured_output_support=bool(data["structured_output_support"]),
        context_budget_sufficient=bool(data["context_budget_sufficient"]),
        capability_evaluated_at=evaluated_at,
    )


__all__ = [
    "CAPABILITY_SCHEMA",
    "LLMRouter",
    "ROLE_CAPABILITY_EVAL",
    "ROLE_EARLY_FORMALIZER",
    "ROLE_NOVELTY_AUDITOR",
    "ROLE_NOVELTY_PRIMARY",
    "capability_profile_from_llm",
]
