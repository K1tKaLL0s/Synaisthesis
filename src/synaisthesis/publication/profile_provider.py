"""Publication profile selection provider (03C sections 2-3; 19 §5 M13.4).

A selection is adaptable only when the profile is route-locked, in scope
(not SCOPE_MISMATCH) and the official guide is FRESH.  SCOPE_MISMATCH and
STALE_GUIDANCE never produce an adapted manuscript; they produce a blocked
selection the caller must return to the user.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from synaisthesis.domain.enums import ResearchRoute
from synaisthesis.publication.official_guide_fetcher import (
    FixtureOfficialGuideFetcher,
    OfficialGuideFetcher,
    OfficialGuideSnapshot,
    guide_freshness,
)
from synaisthesis.publication.profile_registry import ProfileRegistry
from synaisthesis.publication.profiles import (
    FreshnessStatus,
    PublicationProfile,
    ScopeFitStatus,
)


@dataclass(frozen=True, slots=True)
class ProfileSelection:
    """One route-locked, scope-checked, freshness-checked profile selection."""

    profile: PublicationProfile
    scope_fit: ScopeFitStatus
    freshness: FreshnessStatus
    freshness_reasons: tuple[str, ...]
    template_checksum: str | None
    official_author_guide_url: str | None
    accessed_at: datetime
    machine_checks: tuple[str, ...]
    human_only_checks: tuple[str, ...]
    blocking_checks: tuple[str, ...]
    adaptable: bool

    def to_event_payload(self) -> dict[str, object]:
        return {
            "profile_id": self.profile.profile_id,
            "profile_version": self.profile.profile_version,
            "route": self.profile.route.value,
            "venue_kind": self.profile.venue_kind.value,
            "scope_fit": self.scope_fit.value,
            "freshness": self.freshness.value,
            "freshness_reasons": list(self.freshness_reasons),
            "template_checksum": self.template_checksum,
            "official_author_guide_url": self.official_author_guide_url,
            "accessed_at": self.accessed_at.isoformat(),
            "machine_checks": list(self.machine_checks),
            "human_only_checks": list(self.human_only_checks),
            "blocking_checks": list(self.blocking_checks),
            "adaptable": self.adaptable,
        }


def _snapshot_for(
    profile: PublicationProfile, fetcher: OfficialGuideFetcher
) -> OfficialGuideSnapshot | None:
    if not profile.official_author_guide_urls:
        return None
    return fetcher.fetch(
        profile_id=profile.profile_id,
        url=profile.official_author_guide_urls[0],
    )


def select_publication_profile(
    *,
    registry: ProfileRegistry,
    route: ResearchRoute,
    project_kind: str,
    profile_id: str,
    fetcher: OfficialGuideFetcher,
    now: datetime,
) -> ProfileSelection:
    """Select one route-locked profile with scope/freshness verdicts."""
    profile = registry.require_route(route, profile_id)
    scope_fit = profile.scope_fit(project_kind=project_kind)

    snapshot = _snapshot_for(profile, fetcher)
    if snapshot is None:
        freshness = FreshnessStatus.FRESH
        reasons = ("无官方 author guide URL（自定义场合由用户提供指南）",)
    else:
        freshness, reasons = guide_freshness(snapshot, profile, now)

    template_checksum = profile.template_files[0].sha256 if profile.template_files else None
    adaptable = (
        scope_fit is not ScopeFitStatus.SCOPE_MISMATCH and freshness is FreshnessStatus.FRESH
    )
    return ProfileSelection(
        profile=profile,
        scope_fit=scope_fit,
        freshness=freshness,
        freshness_reasons=reasons,
        template_checksum=template_checksum,
        official_author_guide_url=(
            profile.official_author_guide_urls[0] if profile.official_author_guide_urls else None
        ),
        accessed_at=snapshot.fetched_at if snapshot is not None else profile.accessed_at,
        machine_checks=profile.machine_checks,
        human_only_checks=profile.human_only_checks,
        blocking_checks=profile.blocking_checks,
        adaptable=adaptable,
    )


def available_profile_selections(
    *,
    registry: ProfileRegistry,
    route: ResearchRoute,
    project_kind: str,
    fetcher: OfficialGuideFetcher,
    now: datetime,
) -> tuple[ProfileSelection, ...]:
    """All in-scope selections for a route/project kind, each with verdicts."""
    return tuple(
        select_publication_profile(
            registry=registry,
            route=route,
            project_kind=project_kind,
            profile_id=profile.profile_id,
            fetcher=fetcher,
            now=now,
        )
        for profile in registry.scope_candidates(route, project_kind)
    )


__all__ = [
    "ProfileSelection",
    "FixtureOfficialGuideFetcher",
    "available_profile_selections",
    "select_publication_profile",
]
