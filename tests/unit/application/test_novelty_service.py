"""M2.6 unit tests for novelty service independence and routing."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from synaisthesis.agents.auditor import NoveltyAuditor
from synaisthesis.agents.novelty_reviewer import NoveltyReviewer
from synaisthesis.application.novelty_service import start_novelty_review
from synaisthesis.domain.enums import (
    NoveltyStatus,
    PriorArtCoverageStatus,
    ResearchRoute,
)
from synaisthesis.domain.errors import DomainError
from synaisthesis.domain.novelty import (
    ENGINEERING_NOVELTY_POLICY,
    THEORY_NOVELTY_POLICY,
)

NOW = datetime(2026, 8, 17, 0, 0, 0, tzinfo=UTC)


def _scores(route: ResearchRoute, value: int) -> dict[str, int]:
    policy = THEORY_NOVELTY_POLICY if route is ResearchRoute.THEORY else ENGINEERING_NOVELTY_POLICY
    return {item.item_id: value for item in policy.items}


def _review(
    *,
    primary: NoveltyReviewer,
    auditor: NoveltyAuditor,
    coverage=PriorArtCoverageStatus.COMPLETE,
):
    return start_novelty_review(
        review_id="nr-1",
        project_id="p-1",
        route=ResearchRoute.THEORY,
        policy_version=THEORY_NOVELTY_POLICY.policy_version,
        subject_artifact_type="EarlyFormalizationBundle",
        subject_artifact_id="ef-1",
        subject_artifact_hash="f" * 64,
        neighbor_evidence_set_id="ps-1",
        primary_reviewer=primary,
        auditor_reviewer=auditor,
        coverage_status=coverage,
        nearest_overlap_refs=("n-1",),
        strongest_difference_refs=("n-2",),
        limitations=("patents unsearched",),
        at=NOW,
    )


def _reviewer(session_id: str, family: str = "family-a", score: int = 4):
    return NoveltyReviewer.create(
        session_id=session_id,
        route=ResearchRoute.THEORY,
        model_family=family,
        scores=_scores(ResearchRoute.THEORY, score),
    )


def _auditor(session_id: str, family: str = "family-b", score: int = 4):
    return NoveltyAuditor.create(
        session_id=session_id,
        route=ResearchRoute.THEORY,
        model_family=family,
        scores=_scores(ResearchRoute.THEORY, score),
    )


def test_same_session_is_inconclusive():
    reviewer = _reviewer("s1")
    review = _review(primary=reviewer, auditor=_auditor("s1"))
    assert review.status is NoveltyStatus.INCONCLUSIVE


def test_same_model_family_is_inconclusive():
    review = _review(
        primary=_reviewer("s1", family="same"),
        auditor=_auditor("s2", family="same"),
    )
    assert review.status is NoveltyStatus.INCONCLUSIVE


def test_partial_coverage_is_inconclusive():
    review = _review(
        primary=_reviewer("s1"),
        auditor=_auditor("s2"),
        coverage=PriorArtCoverageStatus.PARTIAL,
    )
    assert review.status is NoveltyStatus.INCONCLUSIVE


def test_theory_70_is_automatic_qualification():
    review = _review(primary=_reviewer("s1"), auditor=_auditor("s2"))
    assert review.status is NoveltyStatus.NOVELTY_QUALIFIED
    assert review.novelty_total >= 70


def test_route_policy_mismatch_is_rejected():
    with pytest.raises(DomainError) as exc_info:
        start_novelty_review(
            review_id="nr-bad",
            project_id="p-1",
            route=ResearchRoute.THEORY,
            policy_version=THEORY_NOVELTY_POLICY.policy_version,
            subject_artifact_type="EarlyFormalizationBundle",
            subject_artifact_id="ef-1",
            subject_artifact_hash="f" * 64,
            neighbor_evidence_set_id="ps-1",
            primary_reviewer=NoveltyReviewer.create(
                session_id="s1",
                route=ResearchRoute.ENGINEERING,
                model_family="family-a",
                scores=_scores(ResearchRoute.ENGINEERING, 5),
            ),
            auditor_reviewer=_auditor("s2"),
            coverage_status=PriorArtCoverageStatus.COMPLETE,
            nearest_overlap_refs=(),
            strongest_difference_refs=(),
            limitations=(),
            at=NOW,
        )
    assert exc_info.value.error_code == "NOVELTY_ROUTE_MISMATCH"
