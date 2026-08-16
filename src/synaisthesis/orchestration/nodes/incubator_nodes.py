"""Incubator orchestration nodes (M2.7)."""

from __future__ import annotations

from pathlib import Path

from sqlalchemy.orm import Session

from synaisthesis.agents.schemas import (
    MinimalCaseBundle,
    OpenQuestionRegistry,
    PreFreezeAttackReport,
    ResearchHandoffBundle,
)
from synaisthesis.application.incubation_service import (
    propose_minimal_case_bundle,
    propose_open_question_registry,
    propose_prefreeze_attack_report,
    propose_research_handoff_bundle,
)
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


def s8_readiness_attack_node(
    session: Session,
    *,
    project_id: str,
    report: PreFreezeAttackReport,
    artifact_root: Path,
) -> PreFreezeAttackReport:
    """S8 node: bounded readiness attack (1-2 rounds), never the full Council."""
    return propose_prefreeze_attack_report(
        session,
        project_id=project_id,
        report=report,
        artifact_root=artifact_root,
    )


def s9_open_question_node(
    session: Session,
    *,
    project_id: str,
    registry: OpenQuestionRegistry,
    artifact_root: Path,
) -> OpenQuestionRegistry:
    """S9 node: open question registry with preserved origin markers."""
    return propose_open_question_registry(
        session,
        project_id=project_id,
        registry=registry,
        artifact_root=artifact_root,
    )


def s10_handoff_node(
    session: Session,
    *,
    project_id: str,
    bundle: ResearchHandoffBundle,
    qualification_route: ResearchRoute,
    novelty_status: NoveltyStatus,
    qualification_review_hash: str,
    override: LowNoveltyOverride | None = None,
    artifact_root: Path,
) -> ResearchHandoffBundle:
    """S10 node: maturity gate (RQ4M) enforced through the same service path."""
    return propose_research_handoff_bundle(
        session,
        project_id=project_id,
        bundle=bundle,
        qualification_route=qualification_route,
        novelty_status=novelty_status,
        qualification_review_hash=qualification_review_hash,
        override=override,
        artifact_root=artifact_root,
    )


__all__ = [
    "s10_handoff_node",
    "s5_qualification_node",
    "s8_readiness_attack_node",
    "s9_open_question_node",
]
