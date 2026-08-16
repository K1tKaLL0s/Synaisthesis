"""M2.7 integration tests for the RQ4M -> S5 vertical slice."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import select

from synaisthesis.agents.schemas import MinimalCaseBundle
from synaisthesis.application.incubation_service import (
    EVENT_MINIMAL_CASE_PROPOSED,
    S5_AGGREGATE_TYPE,
    load_minimal_case_bundle,
    propose_minimal_case_bundle,
)
from synaisthesis.domain.enums import (
    NoveltyStatus,
    ProvenanceType,
    ResearchRoute,
)
from synaisthesis.domain.errors import DomainError
from synaisthesis.domain.novelty import LowNoveltyOverride
from synaisthesis.orchestration.nodes.incubator_nodes import s5_qualification_node
from synaisthesis.storage.database import init_database
from synaisthesis.storage.repositories.event_repository import DomainEventRecord

NOW = datetime(2026, 8, 17, 2, 0, 0, tzinfo=UTC)
REPO_ROOT = Path(__file__).resolve().parents[2]
MIGRATIONS_DIR = REPO_ROOT / "src" / "synaisthesis" / "storage" / "migrations"

BUNDLE = MinimalCaseBundle(
    input="A,B finite matrices",
    control_or_baseline="direct trace equality check",
    expected_output="tr(AB)=tr(BA)",
    failure_condition="non-multiplicable shapes",
    reproduction_steps=["compute tr(AB)", "compute tr(BA)", "compare"],
    actually_executed=False,
    execution_receipt_id=None,
    toy_or_real="toy",
    limitations=["not a proof"],
)


def _fresh_database(tmp_path: Path):
    db_url = f"sqlite:///{tmp_path / 's5.db'}"
    cfg = Config()
    cfg.set_main_option("script_location", str(MIGRATIONS_DIR))
    cfg.set_main_option("sqlalchemy.url", db_url)
    command.upgrade(cfg, "head")
    _, session_factory = init_database(db_url)
    return session_factory


def _propose(session_factory, artifact_root, **overrides):
    params = {
        "novelty_status": NoveltyStatus.NOVELTY_QUALIFIED,
        "override": None,
    }
    params.update(overrides)
    with session_factory() as session:
        result = propose_minimal_case_bundle(
            session,
            project_id="p-1",
            bundle=BUNDLE,
            qualification_route=ResearchRoute.THEORY,
            qualification_review_hash="r" * 64,
            artifact_root=artifact_root,
            bundle_id="s5-1",
            **params,
        )
        session.commit()
    return result


def test_qualified_theory_route_persists_and_replays(tmp_path):
    session_factory = _fresh_database(tmp_path)
    artifact_root = tmp_path / "artifacts"
    _propose(session_factory, artifact_root)

    with session_factory() as session:
        reloaded = load_minimal_case_bundle(session, "s5-1", artifact_root=artifact_root)
        events = (
            session.execute(
                select(DomainEventRecord).where(DomainEventRecord.aggregate_id == "s5-1")
            )
            .scalars()
            .all()
        )
    assert reloaded == BUNDLE
    assert [event.event_type for event in events] == [EVENT_MINIMAL_CASE_PROPOSED]
    assert events[0].aggregate_type == S5_AGGREGATE_TYPE


def test_engineering_route_cannot_enter_s5(tmp_path):
    session_factory = _fresh_database(tmp_path)
    artifact_root = tmp_path / "artifacts"
    with session_factory() as session, pytest.raises(DomainError) as exc_info:
        propose_minimal_case_bundle(
            session,
            project_id="p-1",
            bundle=BUNDLE,
            qualification_route=ResearchRoute.ENGINEERING,
            novelty_status=NoveltyStatus.ENGINEERING_NOVELTY_QUALIFIED,
            qualification_review_hash="r" * 64,
            artifact_root=artifact_root,
        )
    assert exc_info.value.error_code == "EARLY_QUALIFICATION_REQUIRED"


def test_unqualified_novelty_status_cannot_enter_s5(tmp_path):
    session_factory = _fresh_database(tmp_path)
    artifact_root = tmp_path / "artifacts"
    for status in (NoveltyStatus.NOVELTY_RESEARCH_REQUIRED, NoveltyStatus.INCONCLUSIVE):
        with session_factory() as session, pytest.raises(DomainError) as exc_info:
            propose_minimal_case_bundle(
                session,
                project_id="p-1",
                bundle=BUNDLE,
                qualification_route=ResearchRoute.THEORY,
                novelty_status=status,
                qualification_review_hash="r" * 64,
                artifact_root=artifact_root,
            )
        assert exc_info.value.error_code == "EARLY_QUALIFICATION_REQUIRED"


def test_bound_user_override_allows_s5(tmp_path):
    session_factory = _fresh_database(tmp_path)
    artifact_root = tmp_path / "artifacts"
    override = LowNoveltyOverride(
        review_id="nr-1",
        route=ResearchRoute.THEORY,
        review_artifact_hash="r" * 64,
        actor=ProvenanceType.USER_DECISION,
        user_event_id="uev-override",
        decided_at=NOW,
    )
    _propose(
        session_factory,
        artifact_root,
        novelty_status=NoveltyStatus.USER_OVERRIDDEN_BELOW_THRESHOLD,
        override=override,
    )


def test_unbound_or_stale_override_is_rejected(tmp_path):
    session_factory = _fresh_database(tmp_path)
    artifact_root = tmp_path / "artifacts"
    override = LowNoveltyOverride(
        review_id="nr-1",
        route=ResearchRoute.THEORY,
        review_artifact_hash="s" * 64,
        actor=ProvenanceType.USER_DECISION,
        user_event_id="uev-override",
        decided_at=NOW,
    )
    with session_factory() as session, pytest.raises(DomainError) as exc_info:
        propose_minimal_case_bundle(
            session,
            project_id="p-1",
            bundle=BUNDLE,
            qualification_route=ResearchRoute.THEORY,
            novelty_status=NoveltyStatus.USER_OVERRIDDEN_BELOW_THRESHOLD,
            qualification_review_hash="r" * 64,
            override=override,
            artifact_root=artifact_root,
        )
    assert exc_info.value.error_code == "EARLY_QUALIFICATION_REQUIRED"


def test_executed_bundle_requires_receipt(tmp_path):
    session_factory = _fresh_database(tmp_path)
    artifact_root = tmp_path / "artifacts"
    executed = BUNDLE.model_copy(update={"actually_executed": True, "execution_receipt_id": None})
    with session_factory() as session, pytest.raises(DomainError) as exc_info:
        propose_minimal_case_bundle(
            session,
            project_id="p-1",
            bundle=executed,
            qualification_route=ResearchRoute.THEORY,
            novelty_status=NoveltyStatus.NOVELTY_QUALIFIED,
            qualification_review_hash="r" * 64,
            artifact_root=artifact_root,
        )
    assert exc_info.value.error_code == "EXECUTION_RECEIPT_REQUIRED"


def test_node_enforces_same_qualification_precondition(tmp_path):
    session_factory = _fresh_database(tmp_path)
    artifact_root = tmp_path / "artifacts"
    with session_factory() as session, pytest.raises(DomainError) as exc_info:
        s5_qualification_node(
            session,
            project_id="p-1",
            bundle=BUNDLE,
            qualification_route=ResearchRoute.ENGINEERING,
            novelty_status=NoveltyStatus.ENGINEERING_NOVELTY_QUALIFIED,
            qualification_review_hash="r" * 64,
            artifact_root=artifact_root,
        )
    assert exc_info.value.error_code == "EARLY_QUALIFICATION_REQUIRED"
