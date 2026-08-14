from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

from alembic import command
from alembic.config import Config
from sqlalchemy import inspect, select

from synaisthesis.domain.event import DomainEvent, canonical_json
from synaisthesis.storage.artifact_store import save_artifact
from synaisthesis.storage.database import init_database
from synaisthesis.storage.hashing import sha256_bytes, verify_artifact_hash
from synaisthesis.storage.repositories.event_repository import (
    DomainEventRecord,
    append_domain_event,
)

REPO_ROOT = Path(__file__).resolve().parents[3]
MIGRATIONS_DIR = REPO_ROOT / "src" / "synaisthesis" / "storage" / "migrations"


def _alembic_config(db_url: str) -> Config:
    cfg = Config()
    cfg.set_main_option("script_location", str(MIGRATIONS_DIR))
    cfg.set_main_option("sqlalchemy.url", db_url)
    return cfg


def _event(**overrides):
    base = {
        "aggregate_type": "Project",
        "aggregate_id": "p1",
        "event_type": "ProjectCreated",
        "payload": {"name": "demo"},
        "sequence": 1,
        "created_at": datetime(2026, 8, 15, 10, 0, 0, tzinfo=UTC),
        "event_id": "evt-1",
    }
    base.update(overrides)
    return DomainEvent(**base)


def test_migration_upgrades_and_downgrades(tmp_path):
    db_url = f"sqlite:///{tmp_path / 'test.db'}"
    engine, _ = init_database(db_url)

    command.upgrade(_alembic_config(db_url), "head")
    tables = set(inspect(engine).get_table_names())
    assert {"artifacts", "domain_events"} <= tables

    command.downgrade(_alembic_config(db_url), "base")
    tables = set(inspect(engine).get_table_names())
    assert "artifacts" not in tables
    assert "domain_events" not in tables


def test_events_are_appended_in_stable_order(tmp_path):
    db_url = f"sqlite:///{tmp_path / 'test.db'}"
    command.upgrade(_alembic_config(db_url), "head")
    _, session_factory = init_database(db_url)
    artifact_root = tmp_path / "artifacts"

    events = [
        _event(event_type="Created", sequence=1, event_id="e1"),
        _event(event_type="Renamed", sequence=2, event_id="e2"),
        _event(event_type="Confirmed", sequence=3, event_id="e3"),
    ]
    with session_factory() as session:
        for event in events:
            append_domain_event(session, event, project_id="p1", artifact_root=artifact_root)
        session.commit()

    with session_factory() as session:
        rows = (
            session.execute(select(DomainEventRecord).order_by(DomainEventRecord.id))
            .scalars()
            .all()
        )
        assert [r.event_type for r in rows] == ["Created", "Renamed", "Confirmed"]
        ids = [r.id for r in rows]
        assert ids == sorted(ids)


def test_artifact_content_addressing(tmp_path):
    db_url = f"sqlite:///{tmp_path / 'test.db'}"
    command.upgrade(_alembic_config(db_url), "head")
    _, session_factory = init_database(db_url)
    artifact_root = tmp_path / "artifacts"

    with session_factory() as session:
        a = save_artifact(
            session,
            project_id=None,
            relative_path="a.txt",
            media_type="text/plain",
            content=b"hello",
            artifact_root=artifact_root,
        )
        b = save_artifact(
            session,
            project_id=None,
            relative_path="b.txt",
            media_type="text/plain",
            content=b"hello",
            artifact_root=artifact_root,
        )
        c = save_artifact(
            session,
            project_id=None,
            relative_path="c.txt",
            media_type="text/plain",
            content=b"world",
            artifact_root=artifact_root,
        )
        session.commit()

    assert a.sha256 == sha256_bytes(b"hello")
    assert b.sha256 == a.sha256
    assert c.sha256 != a.sha256


def test_verify_artifact_hash_detects_missing_and_tampered(tmp_path):
    artifact_root = tmp_path / "artifacts"
    content = b"immutable content"
    sha = sha256_bytes(content)
    path = artifact_root / "x.bin"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(content)

    assert verify_artifact_hash(path, sha) is True

    path.write_bytes(b"tampered")
    assert verify_artifact_hash(path, sha) is False

    path.unlink()
    assert verify_artifact_hash(path, sha) is False


def test_append_domain_event_stores_payload_artifact(tmp_path):
    db_url = f"sqlite:///{tmp_path / 'test.db'}"
    command.upgrade(_alembic_config(db_url), "head")
    _, session_factory = init_database(db_url)
    artifact_root = tmp_path / "artifacts"
    event = _event(payload={"name": "demo", "n": 1}, event_id="evt-x")

    with session_factory() as session:
        record = append_domain_event(session, event, project_id="p1", artifact_root=artifact_root)
        session.commit()

    assert record.event_hash == event.event_hash
    assert record.event_payload_artifact_id is not None
    payload_file = artifact_root / "events" / "p1" / "evt-x.json"
    assert payload_file.exists()
    assert payload_file.read_bytes() == canonical_json({"name": "demo", "n": 1}).encode("utf-8")
