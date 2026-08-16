"""Dual-track publication profiles (03C sections 2-3; M2.11).

Every built-in profile is a versioned, refreshable, auditable data packet with
a content-bound profile_hash.  Software-engineering journals must return
SCOPE_MISMATCH for non-software projects; arXiv is always a
PREPRINT_REPOSITORY and can never be labelled peer-reviewed or accepted.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import UTC, datetime, timedelta
from typing import Any

from synaisthesis.domain.enums import ResearchRoute, StrictStrEnum
from synaisthesis.domain.errors import DomainError
from synaisthesis.domain.event import canonicalize, sha256_hex

DEFAULT_FRESHNESS_DAYS = 30


class VenueKind(StrictStrEnum):
    """Venue kinds (03C, section 2)."""

    PEER_REVIEWED_JOURNAL = "PEER_REVIEWED_JOURNAL"
    PREPRINT_REPOSITORY = "PREPRINT_REPOSITORY"
    EXTENDED_PROFILE = "EXTENDED_PROFILE"
    CUSTOM_VENUE = "CUSTOM_VENUE"


class ScopeFitStatus(StrictStrEnum):
    """Scope-fit verdicts (03C, section 2.1)."""

    SCOPE_FIT_CANDIDATE = "SCOPE_FIT_CANDIDATE"
    SCOPE_FIT_UNCERTAIN = "SCOPE_FIT_UNCERTAIN"
    SCOPE_MISMATCH = "SCOPE_MISMATCH"


class FreshnessStatus(StrictStrEnum):
    """Official-guide freshness (03C, section 3)."""

    FRESH = "FRESH"
    STALE_GUIDANCE = "STALE_GUIDANCE"


def _canonical_payload(value: Any) -> dict[str, Any]:
    payload = canonicalize(value)
    if not isinstance(payload, dict):
        raise TypeError("profile payload must canonicalize to an object")
    return payload


@dataclass(frozen=True, slots=True)
class ProfileTemplateFile:
    """One official template file (03C, section 3)."""

    path: str
    sha256: str
    license: str | None
    source_url: str | None = None


@dataclass(frozen=True, slots=True)
class PublicationProfile:
    """A versioned, refreshable publication profile (03C, section 3)."""

    profile_id: str
    profile_version: str
    route: ResearchRoute
    venue_kind: VenueKind
    venue_name: str
    publisher_or_operator: str
    scope_summary: str
    scope_fit_rules: tuple[str, ...]
    official_author_guide_urls: tuple[str, ...]
    official_policy_urls: tuple[str, ...]
    accessed_at: datetime
    last_modified_if_available: datetime | None
    freshness_days: int = DEFAULT_FRESHNESS_DAYS
    template_files: tuple[ProfileTemplateFile, ...] = ()
    article_types: tuple[str, ...] = ()
    submission_format: str = ""
    machine_checks: tuple[str, ...] = ()
    human_only_checks: tuple[str, ...] = ()
    blocking_checks: tuple[str, ...] = ()
    profile_hash: str | None = None

    def __post_init__(self) -> None:
        if self.route not in {ResearchRoute.THEORY, ResearchRoute.ENGINEERING}:
            raise DomainError(
                "profile must bind THEORY or ENGINEERING route",
                error_code="PROFILE_ROUTE_MISMATCH",
            )
        if self.freshness_days <= 0:
            raise DomainError(
                "freshness_days must be positive",
                error_code="PROFILE_INVALID",
            )
        expected = sha256_hex(self.content_payload())
        if self.profile_hash is not None and self.profile_hash != expected:
            raise DomainError(
                "profile_hash does not match the profile content",
                error_code="ARTIFACT_HASH_MISMATCH",
            )
        object.__setattr__(self, "profile_hash", expected)

    def content_payload(self) -> dict[str, Any]:
        payload = asdict(self)
        payload.pop("profile_hash", None)
        return _canonical_payload(payload)

    def to_event_payload(self) -> dict[str, Any]:
        return _canonical_payload(asdict(self))

    def freshness_status(self, now: datetime) -> FreshnessStatus:
        reference = self.last_modified_if_available or self.accessed_at
        if now - reference > timedelta(days=self.freshness_days):
            return FreshnessStatus.STALE_GUIDANCE
        return FreshnessStatus.FRESH

    def scope_fit(self, *, project_kind: str) -> ScopeFitStatus:
        """Apply the profile's deterministic scope-fit rules (03C, section 2.2)."""
        lowered = project_kind.strip().lower()
        software_only = {
            "ENG_IEEE_TSE",
            "ENG_ACM_TOSEM",
            "ENG_EMSE",
            "ENG_JSS",
            "JOSS_RESEARCH_SOFTWARE",
        }
        if self.profile_id in software_only and lowered != "software":
            return ScopeFitStatus.SCOPE_MISMATCH
        if self.profile_id == "NATURE_PORTFOLIO_METHODS_OR_SOFTWARE":
            if lowered not in {"software", "methods"}:
                return ScopeFitStatus.SCOPE_MISMATCH
            return ScopeFitStatus.SCOPE_FIT_CANDIDATE
        if self.profile_id == "ENG_ARXIV_PREPRINT":
            return ScopeFitStatus.SCOPE_FIT_CANDIDATE
        if self.profile_id == "CUSTOM_VENUE":
            return ScopeFitStatus.SCOPE_FIT_CANDIDATE
        return ScopeFitStatus.SCOPE_FIT_CANDIDATE


def _template(path: str, sha: str, license: str | None = None) -> ProfileTemplateFile:
    return ProfileTemplateFile(path=path, sha256=sha, license=license)


_ACCESSED_AT = datetime(2026, 8, 17, 0, 0, 0, tzinfo=UTC)


ENGINEERING_PROFILES: tuple[PublicationProfile, ...] = (
    PublicationProfile(
        profile_id="ENG_IEEE_TSE",
        profile_version="1.0.0",
        route=ResearchRoute.ENGINEERING,
        venue_kind=VenueKind.PEER_REVIEWED_JOURNAL,
        venue_name="IEEE Transactions on Software Engineering",
        publisher_or_operator="IEEE",
        scope_summary="软件工程方法、理论、工具与有证据的系统研究",
        scope_fit_rules=("project_kind 必须是 software，否则 SCOPE_MISMATCH",),
        official_author_guide_urls=("https://example.org/ieee-tse/guide",),
        official_policy_urls=("https://example.org/ieee-tse/policy",),
        accessed_at=_ACCESSED_AT,
        last_modified_if_available=_ACCESSED_AT,
        template_files=(_template("ieee-tse.tex", "t" * 64),),
        article_types=("SYSTEMS_ARTICLE", "METHODS_ARTICLE"),
        submission_format="TeX/LaTeX",
        machine_checks=("title/abstract/references 结构化检查",),
        human_only_checks=("作者顺序与利益冲突由用户确认",),
        blocking_checks=("证据类型与 article_type 不匹配即阻断",),
    ),
    PublicationProfile(
        profile_id="ENG_ACM_TOSEM",
        profile_version="1.0.0",
        route=ResearchRoute.ENGINEERING,
        venue_kind=VenueKind.PEER_REVIEWED_JOURNAL,
        venue_name="ACM Transactions on Software Engineering and Methodology",
        publisher_or_operator="ACM",
        scope_summary="重要、可复现的软件工程方法与系统成果",
        scope_fit_rules=("project_kind 必须是 software，否则 SCOPE_MISMATCH",),
        official_author_guide_urls=("https://example.org/acm-tosem/guide",),
        official_policy_urls=("https://example.org/acm-tosem/policy",),
        accessed_at=_ACCESSED_AT,
        last_modified_if_available=_ACCESSED_AT,
        template_files=(_template("tosem.tex", "t" * 64),),
        article_types=("SYSTEMS_ARTICLE", "METHODS_ARTICLE"),
        submission_format="TeX/LaTeX",
        machine_checks=("ACM 模板字段检查",),
        human_only_checks=("作者贡献声明由用户确认",),
        blocking_checks=("复现工件缺失即阻断",),
    ),
    PublicationProfile(
        profile_id="ENG_EMSE",
        profile_version="1.0.0",
        route=ResearchRoute.ENGINEERING,
        venue_kind=VenueKind.PEER_REVIEWED_JOURNAL,
        venue_name="Empirical Software Engineering",
        publisher_or_operator="Springer",
        scope_summary="实证研究、研究设计、数据与可复现评价",
        scope_fit_rules=("project_kind 必须是 software，否则 SCOPE_MISMATCH",),
        official_author_guide_urls=("https://example.org/emse/guide",),
        official_policy_urls=("https://example.org/emse/policy",),
        accessed_at=_ACCESSED_AT,
        last_modified_if_available=_ACCESSED_AT,
        template_files=(_template("emse.tex", "t" * 64),),
        article_types=("FULL_ENGINEERING_RESEARCH_ARTICLE",),
        submission_format="TeX/LaTeX",
        machine_checks=("数据可用性声明检查",),
        human_only_checks=("伦理与数据许可由用户确认",),
        blocking_checks=("无实证数据即阻断",),
    ),
    PublicationProfile(
        profile_id="ENG_JSS",
        profile_version="1.0.0",
        route=ResearchRoute.ENGINEERING,
        venue_kind=VenueKind.PEER_REVIEWED_JOURNAL,
        venue_name="Journal of Systems and Software",
        publisher_or_operator="Elsevier",
        scope_summary="软件系统、架构、要求、V&V、维护及系统证据",
        scope_fit_rules=("project_kind 必须是 software，否则 SCOPE_MISMATCH",),
        official_author_guide_urls=("https://example.org/jss/guide",),
        official_policy_urls=("https://example.org/jss/policy",),
        accessed_at=_ACCESSED_AT,
        last_modified_if_available=_ACCESSED_AT,
        template_files=(_template("jss.tex", "t" * 64),),
        article_types=("SYSTEMS_ARTICLE", "METHODS_ARTICLE"),
        submission_format="TeX/LaTeX",
        machine_checks=("系统证据与图源检查",),
        human_only_checks=("系统描述准确性由作者确认",),
        blocking_checks=("无系统证据即阻断",),
    ),
    PublicationProfile(
        profile_id="ENG_ARXIV_PREPRINT",
        profile_version="1.0.0",
        route=ResearchRoute.ENGINEERING,
        venue_kind=VenueKind.PREPRINT_REPOSITORY,
        venue_name="arXiv Engineering/Computing Preprint",
        publisher_or_operator="arXiv",
        scope_summary="cs.*/eess.* 预印本；arXiv 始终是 PREPRINT_REPOSITORY",
        scope_fit_rules=("任何工程路线项目均可作为预印本候选",),
        official_author_guide_urls=("https://example.org/arxiv/guide",),
        official_policy_urls=("https://example.org/arxiv/policy",),
        accessed_at=_ACCESSED_AT,
        last_modified_if_available=_ACCESSED_AT,
        template_files=(_template("arxiv.tex", "t" * 64),),
        article_types=("DESIGN_ARTICLE", "PROTOCOL_ARTICLE", "SYSTEMS_ARTICLE"),
        submission_format="TeX/LaTeX",
        machine_checks=("metadata/title/abstract/authors/category/license 结构化检查",),
        human_only_checks=("submitter 注册、endorsement、moderation 由用户处理",),
        blocking_checks=("不得标注 PEER_REVIEWED/ACCEPTED/PUBLISHED_IN_JOURNAL",),
    ),
    PublicationProfile(
        profile_id="JOSS_RESEARCH_SOFTWARE",
        profile_version="1.0.0",
        route=ResearchRoute.ENGINEERING,
        venue_kind=VenueKind.EXTENDED_PROFILE,
        venue_name="Journal of Open Source Software",
        publisher_or_operator="JOSS",
        scope_summary="研究软件论文：真实软件、可浏览源码、许可证、文档与测试",
        scope_fit_rules=("project_kind 必须是 software；软件必须真实存在",),
        official_author_guide_urls=("https://example.org/joss/guide",),
        official_policy_urls=("https://example.org/joss/policy",),
        accessed_at=_ACCESSED_AT,
        last_modified_if_available=_ACCESSED_AT,
        template_files=(_template("joss-paper.tex", "t" * 64),),
        article_types=("RESEARCH_SOFTWARE_ARTICLE",),
        submission_format="TeX/LaTeX + paper.md",
        machine_checks=("软件存在/许可证/自动化测试检查",),
        human_only_checks=("作者责任与软件维护承诺由用户确认",),
        blocking_checks=("无开源许可证或自动化测试即阻断",),
    ),
    PublicationProfile(
        profile_id="NATURE_PORTFOLIO_METHODS_OR_SOFTWARE",
        profile_version="1.0.0",
        route=ResearchRoute.ENGINEERING,
        venue_kind=VenueKind.EXTENDED_PROFILE,
        venue_name="Nature Portfolio (Methods / Scientific Software)",
        publisher_or_operator="Springer Nature",
        scope_summary="方法或科研软件类扩展 Profile",
        scope_fit_rules=("project_kind 必须是 software 或 methods，否则 SCOPE_MISMATCH",),
        official_author_guide_urls=("https://example.org/nature/guide",),
        official_policy_urls=("https://example.org/nature/policy",),
        accessed_at=_ACCESSED_AT,
        last_modified_if_available=_ACCESSED_AT,
        template_files=(_template("nature.tex", "t" * 64),),
        article_types=("METHODS_ARTICLE", "RESEARCH_SOFTWARE_ARTICLE"),
        submission_format="TeX/LaTeX",
        machine_checks=("方法可复现性检查",),
        human_only_checks=("伦理与数据可用性由用户确认",),
        blocking_checks=("无方法/软件证据即阻断",),
    ),
    PublicationProfile(
        profile_id="CUSTOM_VENUE",
        profile_version="1.0.0",
        route=ResearchRoute.ENGINEERING,
        venue_kind=VenueKind.CUSTOM_VENUE,
        venue_name="Custom Venue",
        publisher_or_operator="user-defined",
        scope_summary="非软件工程或其他自定义目标场合",
        scope_fit_rules=("始终候选；由用户提供 venue 元数据",),
        official_author_guide_urls=(),
        official_policy_urls=(),
        accessed_at=_ACCESSED_AT,
        last_modified_if_available=None,
        template_files=(),
        article_types=("DESIGN_ARTICLE", "PROTOCOL_ARTICLE"),
        submission_format="user-defined",
        machine_checks=(),
        human_only_checks=("venue 元数据与指南由用户提供",),
        blocking_checks=("无用户提供指南时只能生成草稿",),
    ),
)


_THEORY_ACCESSED_AT = datetime(2026, 8, 17, 0, 0, 0, tzinfo=UTC)


THEORY_PROFILES: tuple[PublicationProfile, ...] = (
    PublicationProfile(
        profile_id="MATH_ANNALS_OF_MATHEMATICS",
        profile_version="1.0.0",
        route=ResearchRoute.THEORY,
        venue_kind=VenueKind.PEER_REVIEWED_JOURNAL,
        venue_name="Annals of Mathematics",
        publisher_or_operator="Princeton University / IAS",
        scope_summary="具有广泛数学重要性的重大原创理论结果",
        scope_fit_rules=("理论路线候选",),
        official_author_guide_urls=("https://example.org/annals/guide",),
        official_policy_urls=("https://example.org/annals/policy",),
        accessed_at=_THEORY_ACCESSED_AT,
        last_modified_if_available=_THEORY_ACCESSED_AT,
        template_files=(_template("annals.tex", "t" * 64),),
        article_types=("FULL_THEORY_ARTICLE",),
        submission_format="TeX/LaTeX",
        machine_checks=("statement hash 与冻结一致",),
        human_only_checks=("作者责任与投稿独占性由用户确认",),
        blocking_checks=("unsupported theorem claim 即阻断",),
    ),
    PublicationProfile(
        profile_id="MATH_JAMS",
        profile_version="1.0.0",
        route=ResearchRoute.THEORY,
        venue_kind=VenueKind.PEER_REVIEWED_JOURNAL,
        venue_name="Journal of the American Mathematical Society",
        publisher_or_operator="American Mathematical Society",
        scope_summary="数学各领域高质量、广泛兴趣的研究文章",
        scope_fit_rules=("理论路线候选",),
        official_author_guide_urls=("https://example.org/jams/guide",),
        official_policy_urls=("https://example.org/jams/policy",),
        accessed_at=_THEORY_ACCESSED_AT,
        last_modified_if_available=_THEORY_ACCESSED_AT,
        template_files=(_template("jams.tex", "t" * 64),),
        article_types=("FULL_THEORY_ARTICLE",),
        submission_format="TeX/LaTeX",
        machine_checks=("MSC/完整参考文献检查",),
        human_only_checks=("作者包与责任字段由用户确认",),
        blocking_checks=("statement hash 变化即阻断",),
    ),
    PublicationProfile(
        profile_id="MATH_INVENTIONES",
        profile_version="1.0.0",
        route=ResearchRoute.THEORY,
        venue_kind=VenueKind.PEER_REVIEWED_JOURNAL,
        venue_name="Inventiones mathematicae",
        publisher_or_operator="Springer",
        scope_summary="具有显著新颖性和深度的纯数学研究",
        scope_fit_rules=("理论路线候选",),
        official_author_guide_urls=("https://example.org/inventiones/guide",),
        official_policy_urls=("https://example.org/inventiones/policy",),
        accessed_at=_THEORY_ACCESSED_AT,
        last_modified_if_available=_THEORY_ACCESSED_AT,
        template_files=(_template("inventiones.tex", "t" * 64),),
        article_types=("FULL_THEORY_ARTICLE", "FORMALIZED_THEORY_ARTICLE"),
        submission_format="TeX/LaTeX",
        machine_checks=("proof dependency 闭合检查",),
        human_only_checks=("伦理与作者确认",),
        blocking_checks=("未解决义务被隐藏即阻断",),
    ),
    PublicationProfile(
        profile_id="MATH_ACTA_MATHEMATICA",
        profile_version="1.0.0",
        route=ResearchRoute.THEORY,
        venue_kind=VenueKind.PEER_REVIEWED_JOURNAL,
        venue_name="Acta Mathematica",
        publisher_or_operator="Institut Mittag-Leffler",
        scope_summary="重要、完整且具有长期价值的数学研究",
        scope_fit_rules=("理论路线候选",),
        official_author_guide_urls=("https://example.org/acta/guide",),
        official_policy_urls=("https://example.org/acta/policy",),
        accessed_at=_THEORY_ACCESSED_AT,
        last_modified_if_available=_THEORY_ACCESSED_AT,
        template_files=(_template("acta.tex", "t" * 64),),
        article_types=("FULL_THEORY_ARTICLE",),
        submission_format="TeX/LaTeX",
        machine_checks=("statement/evidence 追踪 100%",),
        human_only_checks=("作者确认",),
        blocking_checks=("引用捏造即阻断",),
    ),
    PublicationProfile(
        profile_id="MATH_ARXIV_PREPRINT",
        profile_version="1.0.0",
        route=ResearchRoute.THEORY,
        venue_kind=VenueKind.PREPRINT_REPOSITORY,
        venue_name="arXiv Mathematics Preprint",
        publisher_or_operator="arXiv",
        scope_summary="math.* 预印本；arXiv 始终是 PREPRINT_REPOSITORY",
        scope_fit_rules=("理论路线均可作为预印本候选",),
        official_author_guide_urls=("https://example.org/arxiv/guide",),
        official_policy_urls=("https://example.org/arxiv/policy",),
        accessed_at=_THEORY_ACCESSED_AT,
        last_modified_if_available=_THEORY_ACCESSED_AT,
        template_files=(_template("arxiv.tex", "t" * 64),),
        article_types=("FULL_THEORY_ARTICLE", "RESEARCH_NOTE"),
        submission_format="TeX/LaTeX",
        machine_checks=("metadata/TeX 源完整性检查",),
        human_only_checks=("submitter/endorsement 由用户处理",),
        blocking_checks=("不得标注 PEER_REVIEWED/ACCEPTED/PUBLISHED_IN_JOURNAL",),
    ),
)


def profile_for(profile_id: str) -> PublicationProfile:
    for profile in (*ENGINEERING_PROFILES, *THEORY_PROFILES):
        if profile.profile_id == profile_id:
            return profile
    raise DomainError(
        f"unknown publication profile {profile_id!r}",
        error_code="PROFILE_UNKNOWN",
    )


__all__ = [
    "DEFAULT_FRESHNESS_DAYS",
    "ENGINEERING_PROFILES",
    "THEORY_PROFILES",
    "FreshnessStatus",
    "ProfileTemplateFile",
    "PublicationProfile",
    "ScopeFitStatus",
    "VenueKind",
    "profile_for",
]
