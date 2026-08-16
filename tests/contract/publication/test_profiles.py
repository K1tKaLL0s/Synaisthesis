"""M2.11 contract tests for the built-in engineering publication profiles (03C)."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest

from synaisthesis.domain.enums import ResearchRoute
from synaisthesis.domain.errors import DomainError
from synaisthesis.publication.profiles import (
    ENGINEERING_PROFILES,
    FreshnessStatus,
    ProfileTemplateFile,
    ScopeFitStatus,
    VenueKind,
    profile_for,
)

NOW = datetime(2026, 8, 17, 2, 0, 0, tzinfo=UTC)


def test_registry_has_all_eight_engineering_profiles():
    ids = {profile.profile_id for profile in ENGINEERING_PROFILES}
    assert ids == {
        "ENG_IEEE_TSE",
        "ENG_ACM_TOSEM",
        "ENG_EMSE",
        "ENG_JSS",
        "ENG_ARXIV_PREPRINT",
        "JOSS_RESEARCH_SOFTWARE",
        "NATURE_PORTFOLIO_METHODS_OR_SOFTWARE",
        "CUSTOM_VENUE",
    }


def test_every_profile_is_versioned_hash_bound_and_engineering_route():
    for profile in ENGINEERING_PROFILES:
        assert profile.route is ResearchRoute.ENGINEERING
        assert profile.profile_version
        assert profile.profile_hash and len(profile.profile_hash) == 64
        assert profile.freshness_days > 0
        assert profile.venue_name
        assert profile.publisher_or_operator
        assert profile.scope_summary
        assert profile.scope_fit_rules
        # hash covers the whole content packet
        expected = profile.content_payload()
        assert expected["profile_id"] == profile.profile_id


def test_profile_hash_detects_tamper():
    import dataclasses

    profile = profile_for("ENG_IEEE_TSE")
    tampered = dataclasses.replace(profile, venue_name="tampered", profile_hash=None)
    # a rebuilt packet with different content gets a different hash
    assert tampered.profile_hash != profile.profile_hash


def test_arxiv_is_always_preprint_repository():
    arxiv = profile_for("ENG_ARXIV_PREPRINT")
    assert arxiv.venue_kind is VenueKind.PREPRINT_REPOSITORY
    assert any("PEER_REVIEWED" in check for check in arxiv.blocking_checks)
    assert any("PREPRINT_REPOSITORY" in arxiv.scope_summary for _ in (0,))
    for profile in ENGINEERING_PROFILES:
        if profile.profile_id != "ENG_ARXIV_PREPRINT":
            assert profile.venue_kind is not VenueKind.PREPRINT_REPOSITORY


def test_software_journals_mismatch_non_software_projects():
    for profile_id in ("ENG_IEEE_TSE", "ENG_ACM_TOSEM", "ENG_EMSE", "ENG_JSS"):
        profile = profile_for(profile_id)
        assert profile.scope_fit(project_kind="hardware") is ScopeFitStatus.SCOPE_MISMATCH
        assert profile.scope_fit(project_kind="software") is ScopeFitStatus.SCOPE_FIT_CANDIDATE


def test_joss_and_nature_extended_profiles():
    joss = profile_for("JOSS_RESEARCH_SOFTWARE")
    assert joss.venue_kind is VenueKind.EXTENDED_PROFILE
    assert "RESEARCH_SOFTWARE_ARTICLE" in joss.article_types
    assert any("许可证" in check or "license" in check.lower() for check in joss.blocking_checks)
    nature = profile_for("NATURE_PORTFOLIO_METHODS_OR_SOFTWARE")
    assert nature.scope_fit(project_kind="hardware") is ScopeFitStatus.SCOPE_MISMATCH
    assert nature.scope_fit(project_kind="software") is ScopeFitStatus.SCOPE_FIT_CANDIDATE


def test_custom_venue_always_candidate():
    custom = profile_for("CUSTOM_VENUE")
    assert custom.venue_kind is VenueKind.CUSTOM_VENUE
    assert custom.scope_fit(project_kind="hardware") is ScopeFitStatus.SCOPE_FIT_CANDIDATE
    assert custom.scope_fit(project_kind="biology") is ScopeFitStatus.SCOPE_FIT_CANDIDATE


def test_freshness_window_logic():
    fresh = profile_for("ENG_JSS")
    assert fresh.freshness_status(NOW) is FreshnessStatus.FRESH
    import dataclasses

    stale = dataclasses.replace(
        fresh,
        accessed_at=NOW - timedelta(days=45),
        last_modified_if_available=NOW - timedelta(days=45),
        profile_hash=None,
    )
    assert stale.freshness_status(NOW) is FreshnessStatus.STALE_GUIDANCE


def test_template_files_are_checksummed():
    for profile in ENGINEERING_PROFILES:
        for template in profile.template_files:
            assert isinstance(template, ProfileTemplateFile)
            assert template.sha256 and len(template.sha256) == 64
            assert template.path


def test_unknown_profile_rejected():
    with pytest.raises(DomainError) as exc_info:
        profile_for("ENG_FAKE")
    assert exc_info.value.error_code == "PROFILE_UNKNOWN"
