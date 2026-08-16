"""Auditor novelty reviewer role (M2.6)."""

from __future__ import annotations

from collections.abc import Mapping

from synaisthesis.agents.novelty_reviewer import NoveltyReviewer
from synaisthesis.domain.enums import ResearchRoute


class NoveltyAuditor(NoveltyReviewer):
    """An isolated auditor reviewer session.

    The score-producing contract is identical to NoveltyReviewer; the role is
    distinguished by caller-supplied model_family and session_id.
    """

    @classmethod
    def create(
        cls,
        *,
        session_id: str,
        route: ResearchRoute,
        model_family: str,
        scores: Mapping[str, int] | None = None,
    ) -> NoveltyAuditor:
        reviewer = super().create(
            session_id=session_id,
            route=route,
            model_family=model_family,
            scores=scores,
        )
        return cls(
            session_id=reviewer.session_id,
            route=reviewer.route,
            model_family=reviewer.model_family,
            scores=reviewer.scores,
            isolated_context_hash=reviewer.isolated_context_hash,
        )


__all__ = ["NoveltyAuditor"]
