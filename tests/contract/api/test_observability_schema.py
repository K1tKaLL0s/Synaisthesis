"""M14.WEB.OBSERVABILITY contract tests (19 §5 M14).

The UI/API never derives state: payload fields are copied verbatim from the
hash-verified event store, tampered artifacts fail closed, and the payload
validates against the frozen API schema.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import select

from synaisthesis.application.gate_service import open_human_gate
from synaisthesis.application.observability_service import (
    PAGE_SPECS,
    project_observability_payload,
)
from synaisthesis.domain.enums import (
    PriorArtCoverageStatus,
    QualificationGateType,
    ResearchRoute,
)
from synaisthesis.domain.errors import DomainError
from synaisthesis.domain.event import DomainEvent
from synaisthesis.domain.gate import Gate, GateBinding
from synaisthesis.interfaces.api.observability import (
    handle_observability_get,
    validate_observability_payload,
)
from synaisthesis.interfaces.mcp.tools import TOOL_GET_OBSERVABILITY, call_tool
from synaisthesis.storage.database import init_database
from synaisthesis.storage.repositories.event_repository import (
    DomainEventRecord,
    append_domain_event,
)

NOW = datetime(2026, 8, 17, 4, 0, 0, tzinfo=UTC)
REPO_ROOT = Path(__file__).resolve().parents[3]
MIGRATIONS_DIR = REPO_ROOT / "src" / "synaisthesis" / "storage" / "migrations"
SCHEMA_FILE = REPO_ROOT / "configs" / "api" / "observability_schema.json"

PROJECT_ID = "p-obs"


def _fresh_database(tmp_path: Path):
    db_url = f"sqlite:///{tmp_path / 'obs.db'}"
    cfg = Config()
    cfg.set_main_option("script_location", str(MIGRATIONS_DIR))
    cfg.set_main_option("sqlalchemy.url", db_url)
    command.upgrade(cfg, "head")
    _, session_factory = init_database(db_url)
    return session_factory


def _append(session, *, aggregate_type: str, aggregate_id: str, payload: dict, event_type: str):
    stream = list(
        session.execute(
            select(DomainEventRecord)
            .where(
                DomainEventRecord.aggregate_type == aggregate_type,
                DomainEventRecord.aggregate_id == aggregate_id,
            )
            .order_by(DomainEventRecord.id)
        )
        .scalars()
        .all()
    )
    event = DomainEvent(
        aggregate_type=aggregate_type,
        aggregate_id=aggregate_id,
        event_type=event_type,
        payload=payload,
        sequence=len(stream) + 1,
    )
    append_domain_event(session, event, project_id=PROJECT_ID, artifact_root=ARTIFACT_ROOT)


ARTIFACT_ROOT: Path


def _seed_project_state(session_factory, tmp_path: Path) -> dict:
    """Persist a spec aggregate, an OPEN novelty gate and nothing else."""
    global ARTIFACT_ROOT
    ARTIFACT_ROOT = tmp_path / "artifacts"
    with session_factory() as session:
        _append(
            session,
            aggregate_type="NaturalLanguageSpec",
            aggregate_id="rs-1",
            event_type="NaturalLanguageSpecProposed",
            payload={
                "artifact": {
                    "core_definition": "cyclic trace invariance",
                    "expected_functions": ["preserve trace"],
                    "artifact_hash": "a" * 64,
                }
            },
        )
        gate = Gate(
            gate_id="gate-low-novelty",
            project_id=PROJECT_ID,
            gate_type=QualificationGateType.LOW_NOVELTY_RESEARCH_DECISION,
            binding=GateBinding(
                gate_type=QualificationGateType.LOW_NOVELTY_RESEARCH_DECISION,
                artifact_id="nr-1",
                version=None,
                artifact_hash="r" * 64,
                input_spec_hash="s" * 64,
                route=ResearchRoute.ENGINEERING,
                coverage_status=PriorArtCoverageStatus.COMPLETE,
                novelty_total=63,
                nearest_overlap_refs=("openalex:W1",),
                limitations=("coverage partial",),
            ),
            reason="novelty_total=63 < 70",
        )
        open_human_gate(session, project_id=PROJECT_ID, gate=gate, artifact_root=ARTIFACT_ROOT)
        session.commit()
    return {"spec_hash": "a" * 64, "review_hash": "r" * 64, "novelty_total": 63}


def test_frozen_schema_is_versioned() -> None:
    schema = json.loads(SCHEMA_FILE.read_text(encoding="utf-8"))
    assert schema["schema_version"] == "1.0.0"
    assert schema["frozen_at"]
    assert schema["$defs"]["page"]["properties"]["rendered_from_store"]["const"] is True


def test_page_specs_match_frozen_schema_pages() -> None:
    page_ids = {page[0] for page in PAGE_SPECS}
    assert page_ids == {
        "design",
        "feasibility_route_gate",
        "formula_concept_review",
        "novelty_score_gate",
        "engineering_trace_blueprint",
        "publication",
    }
    # every page in the schema contract is produced by the service
    assert len(page_ids) == 6


def test_empty_project_payload_validates(tmp_path: Path) -> None:
    session_factory = _fresh_database(tmp_path)
    with session_factory() as session:
        payload = handle_observability_get(
            session, project_id="p-empty", artifact_root=tmp_path / "artifacts"
        )
        validate_observability_payload(payload)
    assert payload["schema_version"] == "1.0.0"
    assert payload["rendered_from_store"] is True
    assert len(payload["pages"]) == 6
    assert all(page["status"] == "NOT_STARTED" for page in payload["pages"])
    assert all(page["route"] is None for page in payload["pages"])


def test_stored_artifacts_and_gates_appear_verbatim(tmp_path: Path) -> None:
    session_factory = _fresh_database(tmp_path)
    stored = _seed_project_state(session_factory, tmp_path)
    with session_factory() as session:
        payload = project_observability_payload(
            session, project_id=PROJECT_ID, artifact_root=tmp_path / "artifacts"
        )
        validate_observability_payload(payload)

    design = next(page for page in payload["pages"] if page["page_id"] == "design")
    assert design["status"] == "IN_PROGRESS"  # only one of the five S1/S4 aggregates stored
    spec_input = next(
        item for item in design["inputs"] if item["aggregate_type"] == "NaturalLanguageSpec"
    )
    assert spec_input["artifact"]["artifact_hash"] == stored["spec_hash"]
    assert spec_input["artifact"]["core_definition"] == "cyclic trace invariance"

    novelty = next(page for page in payload["pages"] if page["page_id"] == "novelty_score_gate")
    assert novelty["status"] == "IN_PROGRESS"  # gate OPEN
    assert novelty["route"] == "ENGINEERING"  # read from the stored binding, not derived
    gate = novelty["gates"][0]
    assert gate["gate_type"] == "LOW_NOVELTY_RESEARCH_DECISION"
    assert gate["status"] == "OPEN"
    # the stored novelty_total is shown verbatim even though scores would
    # recompute differently — no derivation is allowed
    assert gate["binding"]["novelty_total"] == stored["novelty_total"] == 63


def test_unknown_project_is_not_started(tmp_path: Path) -> None:
    session_factory = _fresh_database(tmp_path)
    with session_factory() as session:
        payload = project_observability_payload(
            session, project_id="p-other", artifact_root=tmp_path / "artifacts"
        )
    assert all(page["status"] == "NOT_STARTED" for page in payload["pages"])


def test_tampered_artifact_fails_closed(tmp_path: Path) -> None:
    session_factory = _fresh_database(tmp_path)
    _seed_project_state(session_factory, tmp_path)
    artifact_files = list((tmp_path / "artifacts").rglob("*.json"))
    assert artifact_files
    target = next(path for path in artifact_files if "gate-low-novelty" in str(path))
    target.write_text('{"gate": {"tampered": true}}', encoding="utf-8")
    with session_factory() as session, pytest.raises(DomainError) as exc_info:
        project_observability_payload(
            session, project_id=PROJECT_ID, artifact_root=tmp_path / "artifacts"
        )
    assert exc_info.value.error_code == "ARTIFACT_HASH_MISMATCH"


def test_mcp_observability_tool(tmp_path: Path) -> None:
    from synaisthesis.application.fidelity_service import FidelityConfig

    session_factory = _fresh_database(tmp_path)
    _seed_project_state(session_factory, tmp_path)
    with session_factory() as session:
        payload = call_tool(
            session,
            tool_name=TOOL_GET_OBSERVABILITY,
            arguments={"project_id": PROJECT_ID},
            fidelity=FidelityConfig(signing_key=b"k" * 32, now_fn=lambda: NOW),
            artifact_root=tmp_path / "artifacts",
        )
    assert payload["project_id"] == PROJECT_ID
    assert len(payload["pages"]) == 6
    novelty = next(page for page in payload["pages"] if page["page_id"] == "novelty_score_gate")
    assert novelty["gates"][0]["binding"]["novelty_total"] == 63


def test_web_renderer_files_present() -> None:
    html = REPO_ROOT / "src" / "synaisthesis" / "interfaces" / "web" / "observability.html"
    js = REPO_ROOT / "src" / "synaisthesis" / "interfaces" / "web" / "observability.js"
    assert html.exists() and js.exists()
    source = js.read_text(encoding="utf-8")
    # renderer only reads fields; it must not compute or derive any score
    assert "rendered_from_store" in source
    assert "novelty_total" not in source
    assert "schema_version" in source
