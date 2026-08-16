"""Primary novelty reviewer role (M2.6)."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass

from synaisthesis.domain.enums import ResearchRoute
from synaisthesis.domain.event import sha256_hex
from synaisthesis.domain.novelty import (
    NoveltyItemEvidence,
    NoveltyScorecard,
    novelty_policy_for,
)


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


__all__ = ["NoveltyReviewer"]
