"""M1.4 vertical slice: CLI/service create a project that persists as
Project state + Artifact + DomainEvent and can be re-read from the event
stream (blueprint 19, M1.4.PROJECT.VERTICAL_SLICE).
"""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import select
from typer.testing import CliRunner

from synaisthesis.application.project_service import create_project, get_project
from synaisthesis.domain.enums import ProjectLifecycleStatus
from synaisthesis.domain.errors import DomainError
from synaisthesis.interfaces.cli.main import app
from synaisthesis.storage.artifact_store import ArtifactRecord
from synaisthesis.storage.database import init_database
from synaisthesis.storage.hashing import verify_artifact_hash
from synaisthesis.storage.repositories.event_repository import DomainEventRecord
from synaisthesis.storage.repositories.project_repository import (
    EVENT_PROJECT_CREATED,
    EVENT_PROJECT_LIFECYCLE_CHANGED,
    PROJECT_AGGREGATE_TYPE,
    load_project,
    project_from_state,
    save_project,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
MIGRATIONS_DIR = REPO_ROOT / "src" / "synaisthesis" / "storage" / "migrations"


def _alembic_config(db_url: str) -> Config:
    cfg = Config()
    cfg.set_main_option("script_location", str(MIGRATIONS_DIR))
    cfg.set_main_option("sqlalchemy.url", db_url)
    return cfg


def _fresh_database(tmp_path: Path, name: str = "test.db"):
    db_url = f"sqlite:///{tmp_path / name}"
    command.upgrade(_alembic_config(db_url), "head")
    _, session_factory = init_database(db_url)
    return db_url, session_factory


def _create_args(db_url: str, artifact_root: Path, name: str) -> list[str]:
    return [
        "project",
        "create",
        "--name",
        name,
        "--database-url",
        db_url,
        "--artifact-root",
        str(artifact_root),
    ]


def _project_from_output(output: str):
    state = json.loads(output)
    return project_from_state(state)


# ---------------------------------------------------------------------------
# CLI create -> Project + Artifact + DomainEvent, then re-read
# ---------------------------------------------------------------------------


def test_cli_create_produces_project_event_and_artifact(tmp_path):
    db_url, session_factory = _fresh_database(tmp_path)
    artifact_root = tmp_path / "artifacts"
    runner = CliRunner()

    result = runner.invoke(app, _create_args(db_url, artifact_root, "demo"))
    assert result.exit_code == 0, result.output

    created = _project_from_output(result.output)
    assert created.name == "demo"
    assert created.lifecycle_status is ProjectLifecycleStatus.SEED

    with session_factory() as session:
        events = (
            session.execute(
                select(DomainEventRecord).where(DomainEventRecord.project_id == created.id)
            )
            .scalars()
            .all()
        )
        assert len(events) == 1
        event = events[0]
        assert event.aggregate_type == PROJECT_AGGREGATE_TYPE
        assert event.aggregate_id == created.id
        assert event.event_type == EVENT_PROJECT_CREATED

        artifact = session.get(ArtifactRecord, event.event_payload_artifact_id)
        assert artifact is not None
        payload_file = artifact_root / artifact.relative_path
        assert payload_file.exists()
        assert verify_artifact_hash(payload_file, artifact.sha256) is True

        reloaded = get_project(session, project_id=created.id, artifact_root=artifact_root)
    assert reloaded == created


def test_cli_show_reads_created_project(tmp_path):
    db_url, _ = _fresh_database(tmp_path)
    artifact_root = tmp_path / "artifacts"
    runner = CliRunner()

    create_result = runner.invoke(app, _create_args(db_url, artifact_root, "demo"))
    assert create_result.exit_code == 0, create_result.output
    project_id = _project_from_output(create_result.output).id

    show_result = runner.invoke(
        app,
        [
            "project",
            "show",
            "--project-id",
            project_id,
            "--database-url",
            db_url,
            "--artifact-root",
            str(artifact_root),
        ],
    )
    assert show_result.exit_code == 0, show_result.output
    assert _project_from_output(show_result.output).id == project_id
    assert show_result.output.strip() == create_result.output.strip()


def test_cli_create_blank_name_fails_cleanly(tmp_path):
    db_url, _ = _fresh_database(tmp_path)
    artifact_root = tmp_path / "artifacts"
    runner = CliRunner()

    result = runner.invoke(app, _create_args(db_url, artifact_root, "   "))
    assert result.exit_code == 1
    assert "INVALID_PROJECT_NAME" in result.output


# ---------------------------------------------------------------------------
# Service layer round-trip and replay
# ---------------------------------------------------------------------------


def test_service_create_then_get_roundtrip(tmp_path):
    db_url, session_factory = _fresh_database(tmp_path)
    artifact_root = tmp_path / "artifacts"

    with session_factory() as session:
        project = create_project(
            session, name="roundtrip", description="desc", artifact_root=artifact_root
        )
        session.commit()

    with session_factory() as session:
        reloaded = get_project(session, project_id=project.id, artifact_root=artifact_root)
    assert reloaded == project
    assert reloaded.description == "desc"


def test_state_recovers_from_replayed_event_stream(tmp_path):
    db_url, session_factory = _fresh_database(tmp_path)
    artifact_root = tmp_path / "artifacts"

    with session_factory() as session:
        project = create_project(session, name="replay", artifact_root=artifact_root)
        changed = project.change_lifecycle(
            ProjectLifecycleStatus.INCUBATING, at=datetime(2026, 8, 15, 12, 0, 0, tzinfo=UTC)
        )
        save_project(session, changed, artifact_root=artifact_root)
        session.commit()

    with session_factory() as session:
        records = (
            session.execute(
                select(DomainEventRecord)
                .where(DomainEventRecord.aggregate_id == project.id)
                .order_by(DomainEventRecord.id)
            )
            .scalars()
            .all()
        )
        assert [r.event_type for r in records] == [
            EVENT_PROJECT_CREATED,
            EVENT_PROJECT_LIFECYCLE_CHANGED,
        ]

        reloaded = load_project(session, project.id, artifact_root=artifact_root)

    assert reloaded == changed
    assert reloaded.lifecycle_status is ProjectLifecycleStatus.INCUBATING


def test_tampered_event_payload_blocks_recovery(tmp_path):
    db_url, session_factory = _fresh_database(tmp_path)
    artifact_root = tmp_path / "artifacts"

    with session_factory() as session:
        project = create_project(session, name="tamper", artifact_root=artifact_root)
        session.commit()

    with session_factory() as session:
        event = session.execute(
            select(DomainEventRecord).where(DomainEventRecord.aggregate_id == project.id)
        ).scalar_one()
        artifact = session.get(ArtifactRecord, event.event_payload_artifact_id)
        assert artifact is not None
        payload_file = artifact_root / artifact.relative_path
    payload_file.write_bytes(b"tampered")

    with session_factory() as session, pytest.raises(DomainError) as exc_info:
        load_project(session, project.id, artifact_root=artifact_root)
    assert exc_info.value.error_code == "ARTIFACT_HASH_MISMATCH"


def test_load_unknown_project_raises_not_found(tmp_path):
    db_url, session_factory = _fresh_database(tmp_path)
    artifact_root = tmp_path / "artifacts"

    with session_factory() as session, pytest.raises(DomainError) as exc_info:
        load_project(session, "missing", artifact_root=artifact_root)
    assert exc_info.value.error_code == "PROJECT_NOT_FOUND"


def test_create_project_rejects_blank_name(tmp_path):
    db_url, session_factory = _fresh_database(tmp_path)
    artifact_root = tmp_path / "artifacts"

    with session_factory() as session, pytest.raises(DomainError) as exc_info:
        create_project(session, name="  ", artifact_root=artifact_root)
    assert exc_info.value.error_code == "INVALID_PROJECT_NAME"
