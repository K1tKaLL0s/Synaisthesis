"""M13.4 arXiv profile contract tests (19 §5 M13.4, 03C §2.3).

arXiv is always PREPRINT_REPOSITORY on both routes; metadata is
structurally checked; PEER_REVIEWED / ACCEPTED / PUBLISHED_IN_JOURNAL labels
are rejected; only ARXIV_PACKAGE_READY is an allowed package status.
"""

from __future__ import annotations

import pytest

from synaisthesis.domain.enums import ResearchRoute
from synaisthesis.domain.errors import DomainError
from synaisthesis.publication.profile_registry import ProfileRegistry
from synaisthesis.publication.profiles import VenueKind, profile_for
from synaisthesis.publication.venue_adapters import (
    ARXIV_PACKAGE_READY,
    FORBIDDEN_ARXIV_STATUSES,
    arxiv_metadata_checks,
    arxiv_package_status,
    assert_arxiv_preprint_only,
)


def test_both_routes_have_preprint_only_arxiv_profiles() -> None:
    theory, engineering = ProfileRegistry().arxiv_profiles()
    assert theory.profile_id == "MATH_ARXIV_PREPRINT"
    assert theory.route is ResearchRoute.THEORY
    assert engineering.profile_id == "ENG_ARXIV_PREPRINT"
    assert engineering.route is ResearchRoute.ENGINEERING
    for profile in (theory, engineering):
        assert profile.venue_kind is VenueKind.PREPRINT_REPOSITORY
        assert any("PEER_REVIEWED" in check for check in profile.blocking_checks)


def test_arxiv_is_never_peer_reviewed_journal() -> None:
    assert profile_for("MATH_ARXIV_PREPRINT").venue_kind is VenueKind.PREPRINT_REPOSITORY
    assert profile_for("ENG_ARXIV_PREPRINT").venue_kind is VenueKind.PREPRINT_REPOSITORY
    for profile in ProfileRegistry().all():
        if profile.profile_id in {"MATH_ARXIV_PREPRINT", "ENG_ARXIV_PREPRINT"}:
            continue
        assert profile.venue_kind is not VenueKind.PREPRINT_REPOSITORY


def test_metadata_checks_cover_all_required_fields() -> None:
    theory = profile_for("MATH_ARXIV_PREPRINT")
    issues = arxiv_metadata_checks(
        profile=theory,
        title=" ",
        abstract="",
        authors=(),
        category="",
        license_ref="",
    )
    assert any("title" in issue for issue in issues)
    assert any("abstract" in issue for issue in issues)
    assert any("authors" in issue for issue in issues)
    assert any("category" in issue for issue in issues)
    assert any("license" in issue for issue in issues)


def test_theory_category_must_be_math() -> None:
    issues = arxiv_metadata_checks(
        profile=profile_for("MATH_ARXIV_PREPRINT"),
        title="t",
        abstract="a",
        authors=("A",),
        category="cs.AI",
        license_ref="https://arxiv.org/licenses/nonexclusive-distrib/1.0",
    )
    assert any("math." in issue for issue in issues)


def test_engineering_category_must_be_cs_or_eess() -> None:
    issues = arxiv_metadata_checks(
        profile=profile_for("ENG_ARXIV_PREPRINT"),
        title="t",
        abstract="a",
        authors=("A",),
        category="math.CT",
        license_ref="https://arxiv.org/licenses/nonexclusive-distrib/1.0",
    )
    assert any("cs." in issue for issue in issues)
    clean = arxiv_metadata_checks(
        profile=profile_for("ENG_ARXIV_PREPRINT"),
        title="t",
        abstract="a",
        authors=("A",),
        category="cs.SE",
        license_ref="https://arxiv.org/licenses/nonexclusive-distrib/1.0",
    )
    assert clean == ()


@pytest.mark.parametrize("status", FORBIDDEN_ARXIV_STATUSES)
def test_peer_reviewed_labels_are_rejected(status: str) -> None:
    with pytest.raises(DomainError) as exc_info:
        assert_arxiv_preprint_only(status)
    assert exc_info.value.error_code == "ARXIV_LABELED_PEER_REVIEWED"


def test_arxiv_package_status_only_ready() -> None:
    profile = profile_for("MATH_ARXIV_PREPRINT")
    assert (
        arxiv_package_status(profile=profile, metadata_checks=(), status=ARXIV_PACKAGE_READY)
        == ARXIV_PACKAGE_READY
    )
    assert (
        arxiv_package_status(
            profile=profile, metadata_checks=("title 缺失",), status=ARXIV_PACKAGE_READY
        )
        == "ARXIV_PACKAGE_BLOCKED"
    )
    with pytest.raises(DomainError) as exc_info:
        arxiv_package_status(profile=profile, metadata_checks=(), status="DRAFT")
    assert exc_info.value.error_code == "ARXIV_STATUS_INVALID"
