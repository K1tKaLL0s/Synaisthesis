"""Dual-track publication profile registry (03C section 2; 19 §5 M13.4).

Route locking is mandatory: a profile bound to one route can never be
selected for the other route (PROFILE_ROUTE_MISMATCH).  Scope candidates
exclude SCOPE_MISMATCH venues; CUSTOM_VENUE stays available as the fallback
for non-software engineering projects (03C, section 2.2).
"""

from __future__ import annotations

from dataclasses import dataclass

from synaisthesis.domain.enums import ResearchRoute
from synaisthesis.domain.errors import DomainError
from synaisthesis.publication.profiles import (
    ENGINEERING_PROFILES,
    THEORY_PROFILES,
    PublicationProfile,
    ScopeFitStatus,
    profile_for,
)


@dataclass(frozen=True, slots=True)
class ProfileRegistry:
    """Route-locked registry over the built-in dual-track profiles."""

    profiles: tuple[PublicationProfile, ...] = (*ENGINEERING_PROFILES, *THEORY_PROFILES)

    def all(self) -> tuple[PublicationProfile, ...]:
        return self.profiles

    def by_route(self, route: ResearchRoute) -> tuple[PublicationProfile, ...]:
        return tuple(profile for profile in self.profiles if profile.route is route)

    def get(self, profile_id: str) -> PublicationProfile:
        for profile in self.profiles:
            if profile.profile_id == profile_id:
                return profile
        return profile_for(profile_id)

    def require_route(self, route: ResearchRoute, profile_id: str) -> PublicationProfile:
        """Route-lock a profile selection; cross-route selection is rejected."""
        profile = self.get(profile_id)
        if profile.route is not route:
            raise DomainError(
                f"profile {profile_id!r} 绑定 route={profile.route.value}，"
                f"不能用于 route={route.value}",
                error_code="PROFILE_ROUTE_MISMATCH",
            )
        return profile

    def scope_candidates(
        self, route: ResearchRoute, project_kind: str
    ) -> tuple[PublicationProfile, ...]:
        """Profiles that are not SCOPE_MISMATCH for this project kind."""
        candidates: list[PublicationProfile] = []
        for profile in self.by_route(route):
            if profile.scope_fit(project_kind=project_kind) is ScopeFitStatus.SCOPE_MISMATCH:
                continue
            candidates.append(profile)
        return tuple(candidates)

    def arxiv_profiles(self) -> tuple[PublicationProfile, ...]:
        """Both arXiv profiles; theory first, engineering second; PREPRINT only."""
        by_id = {profile.profile_id: profile for profile in self.profiles}
        order = ("MATH_ARXIV_PREPRINT", "ENG_ARXIV_PREPRINT")
        arxiv = tuple(by_id[profile_id] for profile_id in order if profile_id in by_id)
        if len(arxiv) != 2:
            raise DomainError(
                "arXiv profile registry must contain exactly two route-locked profiles",
                error_code="PROFILE_INVALID",
            )
        from synaisthesis.publication.profiles import VenueKind

        for profile in arxiv:
            if profile.venue_kind is not VenueKind.PREPRINT_REPOSITORY:
                raise DomainError(
                    f"arXiv profile {profile.profile_id!r} 必须是 PREPRINT_REPOSITORY",
                    error_code="ARXIV_NOT_PREPRINT",
                )
        return arxiv


__all__ = ["ProfileRegistry"]
