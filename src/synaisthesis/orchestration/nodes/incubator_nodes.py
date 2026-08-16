"""Incubator orchestration nodes (M2.7)."""

from __future__ import annotations

from pathlib import Path

from sqlalchemy.orm import Session

from synaisthesis.agents.schemas import MinimalCaseBundle
from synaisthesis.application.incubation_service import propose_minimal_case_bundle
from synaisthesis.domain.enums import NoveltyStatus, ResearchRoute
from synaisthesis.domain.novelty import LowNoveltyOverride


def s5_qualification_node(
    session: Session,
    *,
    project_id: str,
    bundle: MinimalCaseBundle,
    qualification_route: ResearchRoute,
    novelty_status: NoveltyStatus,
    qualification_review_hash: str,
    override: LowNoveltyOverride | None = None,
    artifact_root: Path,
    bundle_id: str | None = None,
) -> MinimalCaseBundle:
    """RQ4M -> S5 orchestration node; delegates the enforced service path."""
    return propose_minimal_case_bundle(
        session,
        project_id=project_id,
        bundle=bundle,
        qualification_route=qualification_route,
        novelty_status=novelty_status,
        qualification_review_hash=qualification_review_hash,
        override=override,
        artifact_root=artifact_root,
        bundle_id=bundle_id,
    )


__all__ = ["s5_qualification_node"]
