from __future__ import annotations

import ast
import json
from datetime import UTC, datetime
from pathlib import Path

import pytest

from synaisthesis import domain
from synaisthesis.domain import enums, errors, event, policies
from synaisthesis.domain.enums import (
    EvidenceStrength,
    EvidenceType,
    IndependenceStatus,
    ProgressKind,
    ProjectLifecycleStatus,
    ProvenanceType,
    StageGateStatus,
    StageId,
)
from synaisthesis.domain.errors import ConflictError, DomainError, InvalidEnumValueError
from synaisthesis.domain.event import DomainEvent
from synaisthesis.domain.policies import IdempotencyContext, check_expected_version

# ---------------------------------------------------------------------------
# Enums: strict rejection of unknown values
# ---------------------------------------------------------------------------


def test_stage_id_parses_known_value():
    assert StageId.parse("S4") is StageId.S4
    assert StageId.parse("S10") is StageId.S10


def test_stage_id_parse_accepts_existing_member():
    assert StageId.parse(StageId.S0) is StageId.S0


def test_stage_id_rejects_unknown_value():
    with pytest.raises(InvalidEnumValueError):
        StageId.parse("S11")


def test_enum_rejects_non_string_value():
    with pytest.raises(InvalidEnumValueError):
        StageId.parse(42)


def test_enum_direct_construction_rejects_unknown_value():
    with pytest.raises(ValueError):
        StageId("S99")
    with pytest.raises(ValueError):
        ProgressKind("NOT_A_KIND")


def test_evidence_strength_rejects_out_of_range():
    with pytest.raises(InvalidEnumValueError):
        EvidenceStrength.parse("E9")


@pytest.mark.parametrize(
    ("enum_cls", "expected"),
    [
        (
            StageId,
            ["S0", "S1", "S2", "S3", "S4", "S5", "S6", "S7", "S8", "S9", "S10"],
        ),
        (
            ProgressKind,
            [
                "DEFINITION",
                "BOUNDARY",
                "MECHANISM",
                "EVIDENCE",
                "TEST",
                "ASSUMPTION",
                "FORMALIZATION",
                "COUNTEREXAMPLE",
                "HANDOFF",
            ],
        ),
        (StageGateStatus, ["PASS", "PARTIAL", "BLOCKED", "NOT_TESTED"]),
        (
            ProvenanceType,
            [
                "USER_INPUT",
                "USER_DECISION",
                "EXTERNAL_MODEL_IMPORT",
                "EXTERNAL_SOURCE",
                "ASSISTANT_PROPOSAL",
                "DERIVED",
                "TOOL_EXECUTION",
                "CODEX_EXECUTION",
                "HUMAN_VERIFIED",
            ],
        ),
        (EvidenceStrength, ["E0", "E1", "E2", "E3", "E4", "E5"]),
        (
            IndependenceStatus,
            [
                "INDEPENDENT_VERIFIED",
                "INDEPENDENT_PARTIAL",
                "SAME_MODEL_FAMILY",
                "CONTEXT_LEAK_SUSPECTED",
                "ISOLATION_VIOLATION",
                "NOT_APPLICABLE",
            ],
        ),
    ],
)
def test_enum_exposes_exact_ordered_values(enum_cls, expected):
    assert [member.value for member in enum_cls] == expected


def test_project_lifecycle_includes_core_milestones():
    values = {m.value for m in ProjectLifecycleStatus}
    for required in ("SEED", "INCUBATING", "NATURAL_LANGUAGE_DESIGN_READY", "MATURE_IDEA_READY"):
        assert required in values


def test_project_lifecycle_includes_terminal_and_blocked_states():
    values = {m.value for m in ProjectLifecycleStatus}
    for required in ("USER_ACCEPTED", "REVOKED", "BLOCKED_HUMAN", "BLOCKED_TOOL"):
        assert required in values


def test_evidence_type_includes_tool_and_human_sources():
    values = {m.value for m in EvidenceType}
    for required in ("LEAN_KERNEL_ACCEPTED", "PYTHON_EXPERIMENT", "HUMAN_CONFIRMATION"):
        assert required in values


def test_string_enum_is_json_serializable():
    assert json.dumps(StageId.S4) == '"S4"'
    assert StageId.S4 == "S4"


# ---------------------------------------------------------------------------
# DomainEvent: stable serialization
# ---------------------------------------------------------------------------


def _event(**overrides):
    base = {
        "aggregate_type": "Project",
        "aggregate_id": "proj-1",
        "event_type": "ProjectCreated",
        "payload": {"name": "demo", "lifecycle": "SEED"},
        "sequence": 1,
        "created_at": datetime(2026, 8, 14, 12, 0, 0, tzinfo=UTC),
        "event_id": "evt-1",
    }
    base.update(overrides)
    return DomainEvent(**base)


def test_event_hash_is_deterministic_for_same_content():
    a = _event()
    b = _event(event_id="evt-2")
    assert a.event_hash == b.event_hash
    assert len(a.event_hash) == 64


def test_event_hash_changes_when_payload_changes():
    a = _event()
    b = _event(payload={"name": "other", "lifecycle": "SEED"})
    assert a.event_hash != b.event_hash


def test_event_hash_ignores_payload_key_order():
    a = _event(payload={"x": 1, "y": 2})
    b = _event(payload={"y": 2, "x": 1})
    assert a.event_hash == b.event_hash


def test_event_to_json_is_stable_across_equal_content():
    a = _event()
    b = _event()
    assert a.to_json() == b.to_json()


def test_event_to_json_roundtrips():
    data = json.loads(_event().to_json())
    assert data["aggregate_type"] == "Project"
    assert data["event_type"] == "ProjectCreated"
    assert data["payload"] == {"name": "demo", "lifecycle": "SEED"}
    assert data["sequence"] == 1
    assert data["event_hash"] == _event().event_hash


def test_event_to_dict_contains_all_record_fields():
    data = _event().to_dict()
    assert set(data) == {
        "event_id",
        "aggregate_type",
        "aggregate_id",
        "event_type",
        "payload",
        "sequence",
        "created_at",
        "event_hash",
    }


# ---------------------------------------------------------------------------
# Domain errors
# ---------------------------------------------------------------------------


def test_domain_error_defaults_are_empty():
    err = DomainError("boom")
    assert err.error_code == "DOMAIN_ERROR"
    assert err.message == "boom"
    assert err.recoverable is False
    assert err.retry_after is None
    assert err.blocker_type is None
    assert err.required_user_action is None
    assert err.artifact_refs == ()
    assert err.trace_id is None


def test_domain_error_to_dict_is_structured():
    err = DomainError(
        "need user input",
        error_code="SPEC_CONFIRMATION_REQUIRED",
        recoverable=True,
        blocker_type="HumanGate",
        required_user_action="confirm spec",
        artifact_refs=("a1", "a2"),
        trace_id="t-1",
    )
    assert err.to_dict() == {
        "error_code": "SPEC_CONFIRMATION_REQUIRED",
        "message": "need user input",
        "recoverable": True,
        "retry_after": None,
        "blocker_type": "HumanGate",
        "required_user_action": "confirm spec",
        "artifact_refs": ["a1", "a2"],
        "trace_id": "t-1",
    }


def test_conflict_error_has_conflict_code():
    err = ConflictError("version mismatch", trace_id="t-2")
    assert err.error_code == "CONFLICT"
    assert err.trace_id == "t-2"


def test_invalid_enum_value_error_carries_context():
    err = InvalidEnumValueError(field="stage", value="S99", allowed=["S0", "S1"])
    assert err.error_code == "INVALID_ENUM_VALUE"
    assert err.field == "stage"
    assert err.value == "S99"
    assert err.allowed == ["S0", "S1"]


# ---------------------------------------------------------------------------
# Version / idempotency invariants
# ---------------------------------------------------------------------------


def test_check_expected_version_matches_silently():
    check_expected_version(3, 3)


def test_check_expected_version_mismatch_raises_conflict():
    with pytest.raises(ConflictError) as exc_info:
        check_expected_version(3, 4, trace_id="t-3")
    assert exc_info.value.error_code == "CONFLICT"
    assert exc_info.value.trace_id == "t-3"


def test_check_expected_version_none_skips_check():
    check_expected_version(None, 7)


def test_idempotency_context_holds_all_fields():
    ctx = IdempotencyContext(idempotency_key="k-1", trace_id="t-1", expected_version=2)
    assert ctx.idempotency_key == "k-1"
    assert ctx.trace_id == "t-1"
    assert ctx.expected_version == 2


def test_idempotency_context_defaults_to_no_version():
    ctx = IdempotencyContext(idempotency_key="k-1", trace_id="t-1")
    assert ctx.expected_version is None


# ---------------------------------------------------------------------------
# Layering: domain must not depend on web / database / mcp
# ---------------------------------------------------------------------------

FORBIDDEN_PREFIXES = (
    "fastapi",
    "sqlalchemy",
    "alembic",
    "sqlmodel",
    "starlette",
    "synaisthesis.interfaces",
)


def _imported_modules(source: str) -> set[str]:
    tree = ast.parse(source)
    modules: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            modules.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            modules.add(node.module)
    return modules


@pytest.mark.parametrize("module", [domain, enums, errors, event, policies])
def test_domain_module_has_no_framework_imports(module):
    assert module.__file__ is not None
    source = Path(module.__file__).read_text(encoding="utf-8")
    for name in _imported_modules(source):
        assert not name.startswith(FORBIDDEN_PREFIXES), f"{module.__name__} imports {name!r}"
