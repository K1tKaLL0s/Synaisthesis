"""M13.4 official publication profile contract tests (19 §5 M13.4, 03C §2-3).

Frozen fixtures under configs/publication_profiles must exactly match the
built-in profiles; route locking rejects cross-route selection; SCOPE_MISMATCH
and STALE_GUIDANCE never produce an adaptable selection.
"""

from __future__ import annotations

import dataclasses
import json
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any, cast

import pytest

from synaisthesis.domain.enums import ResearchRoute
from synaisthesis.domain.errors import DomainError
from synaisthesis.publication.official_guide_fetcher import (
    FixtureGuide,
    FixtureOfficialGuideFetcher,
    require_fresh_guide,
)
from synaisthesis.publication.profile_provider import (
    available_profile_selections,
    select_publication_profile,
)
from synaisthesis.publication.profile_registry import ProfileRegistry
from synaisthesis.publication.profiles import (
    ENGINEERING_PROFILES,
    THEORY_PROFILES,
    FreshnessStatus,
    ScopeFitStatus,
    profile_for,
)

NOW = datetime(2026, 8, 17, 2, 0, 0, tzinfo=UTC)
REPO_ROOT = Path(__file__).resolve().parents[3]
FIXTURES = REPO_ROOT / "configs" / "publication_profiles"


def _serialize(profile) -> dict[str, Any]:
    def convert(value: Any) -> Any:
        if isinstance(value, dict):
            return {key: convert(item) for key, item in value.items()}
        if isinstance(value, (list, tuple)):
            return [convert(item) for item in value]
        if hasattr(value, "isoformat"):
            return value.isoformat()
        if hasattr(value, "value"):
            return value.value
        return value

    result = convert(dataclasses.asdict(profile))
    assert isinstance(result, dict)
    return result


def _fixture(name: str) -> dict[str, dict[str, Any]]:
    payload = cast(
        list[dict[str, Any]],
        json.loads((FIXTURES / name).read_text(encoding="utf-8")),
    )
    return {entry["profile_id"]: entry for entry in payload}


def test_builtin_profiles_match_frozen_fixtures() -> None:
    fixtures = {
        **_fixture("theory.json"),
        **_fixture("engineering.json"),
        **_fixture("arxiv.json"),
    }
    for profile in (*THEORY_PROFILES, *ENGINEERING_PROFILES):
        assert profile.profile_id in fixtures
        assert _serialize(profile) == fixtures[profile.profile_id]
    assert len(fixtures) == len(THEORY_PROFILES) + len(ENGINEERING_PROFILES)


def test_registry_route_counts() -> None:
    registry = ProfileRegistry()
    theory = {profile.profile_id for profile in registry.by_route(ResearchRoute.THEORY)}
    engineering = {profile.profile_id for profile in registry.by_route(ResearchRoute.ENGINEERING)}
    assert theory == {profile.profile_id for profile in THEORY_PROFILES}
    assert engineering == {profile.profile_id for profile in ENGINEERING_PROFILES}


def test_cross_route_selection_is_rejected() -> None:
    registry = ProfileRegistry()
    with pytest.raises(DomainError) as exc_info:
        registry.require_route(ResearchRoute.THEORY, "ENG_IEEE_TSE")
    assert exc_info.value.error_code == "PROFILE_ROUTE_MISMATCH"
    with pytest.raises(DomainError) as exc_info:
        registry.require_route(ResearchRoute.ENGINEERING, "MATH_JAMS")
    assert exc_info.value.error_code == "PROFILE_ROUTE_MISMATCH"


def test_software_journals_are_excluded_for_non_software_projects() -> None:
    registry = ProfileRegistry()
    candidates = registry.scope_candidates(ResearchRoute.ENGINEERING, "hardware")
    candidate_ids = {profile.profile_id for profile in candidates}
    assert {"ENG_IEEE_TSE", "ENG_ACM_TOSEM", "ENG_EMSE", "ENG_JSS"} & candidate_ids == set()
    assert "CUSTOM_VENUE" in candidate_ids
    assert "ENG_ARXIV_PREPRINT" in candidate_ids


def _fetcher(template_sha: str = "t" * 64, *, unreachable_url: str | None = None):
    corpus: dict[str, FixtureGuide] = {}
    for profile in (*THEORY_PROFILES, *ENGINEERING_PROFILES):
        for url in profile.official_author_guide_urls:
            if url == unreachable_url:
                continue
            corpus[url] = FixtureGuide(
                url=url,
                body=f"official guide body for {profile.profile_id}",
                template_sha256s=tuple(t.sha256 for t in profile.template_files),
            )
    if template_sha != "t" * 64:
        corpus = {
            url: FixtureGuide(url=url, body=guide.body, template_sha256s=(template_sha,))
            for url, guide in corpus.items()
        }
    return FixtureOfficialGuideFetcher(corpus)


def test_fresh_selection_is_adaptable_with_checksums() -> None:
    registry = ProfileRegistry()
    selection = select_publication_profile(
        registry=registry,
        route=ResearchRoute.ENGINEERING,
        project_kind="software",
        profile_id="ENG_IEEE_TSE",
        fetcher=_fetcher(),
        now=NOW,
    )
    assert selection.scope_fit is ScopeFitStatus.SCOPE_FIT_CANDIDATE
    assert selection.freshness is FreshnessStatus.FRESH
    assert selection.adaptable is True
    assert selection.template_checksum == "t" * 64
    assert selection.official_author_guide_url == "https://example.org/ieee-tse/guide"
    assert selection.machine_checks and selection.human_only_checks and selection.blocking_checks
    payload = selection.to_event_payload()
    assert payload["venue_kind"] == "PEER_REVIEWED_JOURNAL"
    assert payload["route"] == "ENGINEERING"


def test_scope_mismatch_never_adapts() -> None:
    selection = select_publication_profile(
        registry=ProfileRegistry(),
        route=ResearchRoute.ENGINEERING,
        project_kind="hardware",
        profile_id="ENG_IEEE_TSE",
        fetcher=_fetcher(),
        now=NOW,
    )
    assert selection.scope_fit is ScopeFitStatus.SCOPE_MISMATCH
    assert selection.adaptable is False


def test_template_change_detects_guide_update() -> None:
    registry = ProfileRegistry()
    selection = select_publication_profile(
        registry=registry,
        route=ResearchRoute.ENGINEERING,
        project_kind="software",
        profile_id="ENG_JSS",
        fetcher=_fetcher(template_sha="u" * 64),
        now=NOW,
    )
    assert selection.freshness is FreshnessStatus.STALE_GUIDANCE
    assert selection.adaptable is False
    assert any("SHA-256" in reason for reason in selection.freshness_reasons)


def test_expired_window_is_stale() -> None:
    stale_profile = dataclasses.replace(
        profile_for("ENG_JSS"),
        accessed_at=NOW - timedelta(days=45),
        last_modified_if_available=NOW - timedelta(days=45),
        profile_hash=None,
    )
    registry = ProfileRegistry(profiles=(stale_profile,))
    selection = select_publication_profile(
        registry=registry,
        route=ResearchRoute.ENGINEERING,
        project_kind="software",
        profile_id="ENG_JSS",
        fetcher=_fetcher(),
        now=NOW,
    )
    assert selection.freshness is FreshnessStatus.STALE_GUIDANCE
    assert selection.adaptable is False


def test_unreachable_guide_is_stale() -> None:
    registry = ProfileRegistry()
    selection = select_publication_profile(
        registry=registry,
        route=ResearchRoute.THEORY,
        project_kind="theory",
        profile_id="MATH_ANNALS_OF_MATHEMATICS",
        fetcher=_fetcher(unreachable_url="https://example.org/annals/guide"),
        now=NOW,
    )
    assert selection.freshness is FreshnessStatus.STALE_GUIDANCE
    assert any("不可访问" in reason for reason in selection.freshness_reasons)


def test_custom_venue_has_no_official_guide_and_stays_adaptable() -> None:
    selection = select_publication_profile(
        registry=ProfileRegistry(),
        route=ResearchRoute.ENGINEERING,
        project_kind="hardware",
        profile_id="CUSTOM_VENUE",
        fetcher=_fetcher(),
        now=NOW,
    )
    assert selection.freshness is FreshnessStatus.FRESH
    assert selection.template_checksum is None
    assert selection.adaptable is True


def test_require_fresh_guide_fails_closed_on_stale() -> None:
    profile = profile_for("ENG_JSS")
    fetcher = _fetcher(template_sha="u" * 64)
    guide_url = profile.official_author_guide_urls[0]
    snapshot = fetcher.fetch(profile_id=profile.profile_id, url=guide_url)
    with pytest.raises(DomainError) as exc_info:
        require_fresh_guide(snapshot, profile, NOW)
    assert exc_info.value.error_code == "STALE_GUIDANCE"


def test_available_selections_include_only_in_scope_fresh() -> None:
    selections = available_profile_selections(
        registry=ProfileRegistry(),
        route=ResearchRoute.ENGINEERING,
        project_kind="hardware",
        fetcher=_fetcher(),
        now=NOW,
    )
    ids = {selection.profile.profile_id for selection in selections}
    assert {"ENG_IEEE_TSE", "ENG_ACM_TOSEM", "ENG_EMSE", "ENG_JSS"} & ids == set()
    assert "CUSTOM_VENUE" in ids
    assert "ENG_ARXIV_PREPRINT" in ids
    for selection in selections:
        assert selection.scope_fit is not ScopeFitStatus.SCOPE_MISMATCH
