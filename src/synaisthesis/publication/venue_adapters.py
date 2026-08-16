"""Venue adapters: arXiv and peer-reviewed journal adaptation checks (03C §2.3/§3; M13.4).

arXiv is always a PREPRINT_REPOSITORY: status may only be ARXIV_PACKAGE_READY,
and PEER_REVIEWED / ACCEPTED / PUBLISHED_IN_JOURNAL labels are rejected.
Journal adapters apply the profile's machine/blocking checks and never adapt a
SCOPE_MISMATCH or STALE_GUIDANCE selection.
"""

from __future__ import annotations

from synaisthesis.domain.errors import DomainError
from synaisthesis.publication.profiles import (
    PublicationProfile,
    VenueKind,
)

ARXIV_PACKAGE_READY = "ARXIV_PACKAGE_READY"
ARXIV_PACKAGE_BLOCKED = "ARXIV_PACKAGE_BLOCKED"
FORBIDDEN_ARXIV_STATUSES = ("PEER_REVIEWED", "ACCEPTED", "PUBLISHED_IN_JOURNAL")


def arxiv_metadata_checks(
    *,
    profile: PublicationProfile,
    title: str,
    abstract: str,
    authors: tuple[str, ...],
    category: str,
    license_ref: str,
) -> tuple[str, ...]:
    """Structured arXiv metadata checks (03C, section 2.3)."""
    issues: list[str] = []
    if profile.venue_kind is not VenueKind.PREPRINT_REPOSITORY:
        issues.append("arXiv 适配必须使用 PREPRINT_REPOSITORY Profile")
    if not title.strip():
        issues.append("title 缺失")
    if not abstract.strip():
        issues.append("abstract 缺失")
    if not authors:
        issues.append("authors 缺失")
    if not category.strip():
        issues.append("category 缺失")
    elif profile.profile_id == "MATH_ARXIV_PREPRINT" and not category.startswith("math."):
        issues.append(f"理论 arXiv category 必须以 math. 开头，当前 {category!r}")
    elif profile.profile_id == "ENG_ARXIV_PREPRINT" and not (
        category.startswith("cs.") or category.startswith("eess.")
    ):
        issues.append(f"工程 arXiv category 必须以 cs./eess. 开头，当前 {category!r}")
    if not license_ref.strip():
        issues.append("license 缺失")
    return tuple(issues)


def assert_arxiv_preprint_only(status: str) -> None:
    """Fail closed: arXiv may never be labelled peer-reviewed or accepted."""
    if status in FORBIDDEN_ARXIV_STATUSES:
        raise DomainError(
            f"arXiv 状态 {status!r} 被禁止：arXiv 永远是 PREPRINT_REPOSITORY",
            error_code="ARXIV_LABELED_PEER_REVIEWED",
        )


def arxiv_package_status(
    *,
    profile: PublicationProfile,
    metadata_checks: tuple[str, ...],
    status: str,
) -> str:
    """Return ARXIV_PACKAGE_READY only when checks pass and status is allowed."""
    assert_arxiv_preprint_only(status)
    if metadata_checks:
        return ARXIV_PACKAGE_BLOCKED
    if status != ARXIV_PACKAGE_READY:
        raise DomainError(
            f"arXiv 状态只允许 {ARXIV_PACKAGE_READY}，当前 {status!r}",
            error_code="ARXIV_STATUS_INVALID",
        )
    return ARXIV_PACKAGE_READY


def missing_blocking_evidence(
    profile: PublicationProfile, evidence_keys: tuple[str, ...]
) -> tuple[str, ...]:
    """Which blocking checks have no supporting evidence key (03C, section 3)."""
    available = " ".join(evidence_keys).lower()
    missing: list[str] = []
    for check in profile.blocking_checks:
        missing_evidence = "证据" in check and "证据" not in available and not evidence_keys
        missing_hash = "hash" in check.lower() and "hash" not in available
        missing_template = "模板" in check and "template" not in available
        if missing_evidence or missing_hash or missing_template:
            missing.append(check)
    return tuple(missing)


__all__ = [
    "ARXIV_PACKAGE_BLOCKED",
    "ARXIV_PACKAGE_READY",
    "FORBIDDEN_ARXIV_STATUSES",
    "arxiv_metadata_checks",
    "arxiv_package_status",
    "assert_arxiv_preprint_only",
    "missing_blocking_evidence",
]
