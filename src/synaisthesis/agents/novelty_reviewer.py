"""Primary novelty reviewer role (M2.6)."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

from synaisthesis.domain.enums import ResearchRoute
from synaisthesis.domain.errors import DomainError
from synaisthesis.domain.event import sha256_hex
from synaisthesis.domain.novelty import (
    NoveltyItemEvidence,
    NoveltyScorecard,
    novelty_policy_for,
)
from synaisthesis.providers.llm.base import StructuredOutputError


@dataclass(frozen=True, slots=True)
class NoveltyReviewer:
    """An isolated primary Novelty Reviewer session."""

    session_id: str
    route: ResearchRoute
    model_family: str
    scores: Mapping[str, int]
    isolated_context_hash: str

    @classmethod
    def create(
        cls,
        *,
        session_id: str,
        route: ResearchRoute,
        model_family: str,
        scores: Mapping[str, int] | None = None,
    ) -> NoveltyReviewer:
        policy = novelty_policy_for(route)
        resolved_scores = (
            dict(scores) if scores is not None else {item.item_id: 0 for item in policy.items}
        )
        return cls(
            session_id=session_id,
            route=route,
            model_family=model_family,
            scores=NoveltyScorecard(
                reviewer_session_id=session_id,
                route=route,
                item_scores=resolved_scores,
            ).item_scores,
            isolated_context_hash=sha256_hex(
                {
                    "session_id": session_id,
                    "route": route.value,
                    "model_family": model_family,
                    "scores": resolved_scores,
                }
            ),
        )

    def score(
        self,
        *,
        subject_artifact_id: str,
        subject_artifact_hash: str,
    ) -> tuple[NoveltyScorecard, tuple[NoveltyItemEvidence, ...]]:
        del subject_artifact_hash
        policy = novelty_policy_for(self.route)
        scorecard = NoveltyScorecard(
            reviewer_session_id=self.session_id,
            route=self.route,
            item_scores=dict(self.scores),
        )
        evidence = tuple(
            NoveltyItemEvidence(
                item_id=item.item_id,
                evidence_refs=(f"RQ1:{subject_artifact_id}:{item.item_id}",),
            )
            for item in policy.items
        )
        return scorecard, evidence


# ---------------------------------------------------------------------------
# M6.3 — LLM-routed novelty scorecards (03A section 8, 19 §5 M6.3)
# ---------------------------------------------------------------------------

NOVELTY_SCORECARD_SCHEMA: dict[str, Any] = {
    "type": "object",
    "required": ["item_scores"],
    "additionalProperties": False,
    "properties": {"item_scores": {"type": "object"}},
}


def review_scorecard_from_llm(
    *,
    router: Any,
    session_id: str,
    route: ResearchRoute,
    role: str,
    subject_artifact_id: str,
) -> tuple[NoveltyScorecard, tuple[NoveltyItemEvidence, ...]]:
    """Generate one reviewer's scorecard through the LLM router (03A, 8.1).

    The router enforces strict structured output; item ids are validated
    against the route policy and ratings against [0, 5] by NoveltyScorecard,
    so an invalid scorecard fails closed and never reaches domain state.
    """
    from synaisthesis.providers.llm.base import LLMRequest
    from synaisthesis.providers.llm.router import LLMRouter

    if not isinstance(router, LLMRouter):
        raise DomainError(
            "review_scorecard_from_llm 需要 LLMRouter",
            error_code="ROUTER_INVALID",
        )
    policy = novelty_policy_for(route)
    response = router.complete_for(
        role,
        LLMRequest(
            prompt=(
                f"按 {policy.policy_version} 逐项评分（0-5）：route={route.value}，"
                f"subject={subject_artifact_id}"
            ),
            structured_schema=NOVELTY_SCORECARD_SCHEMA,
        ),
    )
    if response.structured is None:
        raise StructuredOutputError(
            "新颖性评分缺少结构化输出",
            error_code="STRUCTURED_OUTPUT_INVALID",
        )
    raw_scores = response.structured["item_scores"]
    scorecard = NoveltyScorecard(
        reviewer_session_id=session_id,
        route=route,
        item_scores={str(key): int(value) for key, value in raw_scores.items()},
    )
    evidence = tuple(
        NoveltyItemEvidence(
            item_id=item.item_id,
            evidence_refs=(f"RQ1:{subject_artifact_id}:{item.item_id}",),
        )
        for item in policy.items
    )
    return scorecard, evidence


__all__ = ["NoveltyReviewer", "review_scorecard_from_llm"]
