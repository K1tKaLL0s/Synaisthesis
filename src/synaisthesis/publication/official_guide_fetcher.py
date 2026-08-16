"""Official author-guide fetching with update detection (03C section 3; M13.4).

A guide snapshot is a quarantined, content-addressed fetch result.  Freshness
is STALE_GUIDANCE when the official page is unreachable, the freshness window
expired, or the template SHA-256 no longer matches the profile — in all such
cases formal manuscript readiness must not be produced (03C, section 3).
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Protocol, runtime_checkable

from synaisthesis.domain.errors import DomainError
from synaisthesis.domain.event import sha256_hex
from synaisthesis.providers.prior_art.base import ExternalText
from synaisthesis.publication.profiles import FreshnessStatus, PublicationProfile


@dataclass(frozen=True, slots=True)
class FixtureGuide:
    """Deterministic guide corpus entry (frozen fixture; real fetch is manual smoke)."""

    url: str
    body: str
    template_sha256s: tuple[str, ...]
    reachable: bool = True


@dataclass(frozen=True, slots=True)
class OfficialGuideSnapshot:
    """One content-addressed official guide fetch (03C, section 3)."""

    profile_id: str
    url: str
    fetched_at: datetime
    content_hash: str
    template_sha256s: tuple[str, ...]
    raw_text: ExternalText | None
    reachable: bool

    def to_event_payload(self) -> dict[str, object]:
        return {
            "profile_id": self.profile_id,
            "url": self.url,
            "fetched_at": self.fetched_at.isoformat(),
            "content_hash": self.content_hash,
            "template_sha256s": list(self.template_sha256s),
            "raw_text": (
                {"content": self.raw_text.content, "source_ref": self.raw_text.source_ref}
                if self.raw_text
                else None
            ),
            "reachable": self.reachable,
        }


@runtime_checkable
class OfficialGuideFetcher(Protocol):
    """Synchronous official author-guide fetcher contract."""

    def fetch(self, *, profile_id: str, url: str) -> OfficialGuideSnapshot: ...


class FixtureOfficialGuideFetcher:
    """Deterministic fetcher over a frozen corpus; real HTTP fetch is a manual smoke."""

    def __init__(self, corpus: dict[str, FixtureGuide]) -> None:
        self._corpus = dict(corpus)

    def fetch(self, *, profile_id: str, url: str) -> OfficialGuideSnapshot:
        guide = self._corpus.get(url)
        if guide is None:
            return OfficialGuideSnapshot(
                profile_id=profile_id,
                url=url,
                fetched_at=datetime.now(),
                content_hash=sha256_hex({"url": url, "missing": True}),
                template_sha256s=(),
                raw_text=None,
                reachable=False,
            )
        content_hash = sha256_hex(
            {"url": guide.url, "body": guide.body, "templates": list(guide.template_sha256s)}
        )
        return OfficialGuideSnapshot(
            profile_id=profile_id,
            url=guide.url,
            fetched_at=datetime.now(),
            content_hash=content_hash,
            template_sha256s=guide.template_sha256s,
            raw_text=ExternalText(content=guide.body, source_ref=guide.url),
            reachable=guide.reachable,
        )


def guide_freshness(
    snapshot: OfficialGuideSnapshot,
    profile: PublicationProfile,
    now: datetime,
) -> tuple[FreshnessStatus, tuple[str, ...]]:
    """Combine reachability, freshness window and template checksum checks."""
    reasons: list[str] = []
    if not snapshot.reachable:
        reasons.append(f"官方指南不可访问: {snapshot.url}")
    if profile.freshness_status(now) is FreshnessStatus.STALE_GUIDANCE:
        reasons.append("官方指南超过 freshness window")
    profile_hashes = {template.sha256 for template in profile.template_files}
    if profile_hashes and snapshot.template_sha256s:
        snapshot_hashes = set(snapshot.template_sha256s)
        if profile_hashes != snapshot_hashes:
            reasons.append("官方模板 SHA-256 已改变（指南更新）")
    elif profile_hashes and not snapshot.template_sha256s:
        reasons.append("官方指南未提供模板校验和，无法确认模板未变")
    if reasons:
        return FreshnessStatus.STALE_GUIDANCE, tuple(reasons)
    return FreshnessStatus.FRESH, ()


def require_fresh_guide(
    snapshot: OfficialGuideSnapshot,
    profile: PublicationProfile,
    now: datetime,
) -> OfficialGuideSnapshot:
    """Fail closed: STALE_GUIDANCE forbids formal-manuscript readiness (03C §3)."""
    status, reasons = guide_freshness(snapshot, profile, now)
    if status is not FreshnessStatus.FRESH:
        raise DomainError(
            "STALE_GUIDANCE: " + "; ".join(reasons),
            error_code="STALE_GUIDANCE",
        )
    return snapshot


__all__ = [
    "FixtureGuide",
    "FixtureOfficialGuideFetcher",
    "OfficialGuideFetcher",
    "OfficialGuideSnapshot",
    "guide_freshness",
    "require_fresh_guide",
]
