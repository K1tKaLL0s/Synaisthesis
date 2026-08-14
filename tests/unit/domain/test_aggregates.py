from __future__ import annotations

from dataclasses import FrozenInstanceError
from datetime import UTC, datetime

import pytest

from synaisthesis.domain.enums import (
    EvidenceStrength,
    EvidenceType,
    ProjectLifecycleStatus,
    ProvenanceType,
    StageGateStatus,
    StageId,
)
from synaisthesis.domain.errors import ConflictError
from synaisthesis.domain.evidence import Evidence
from synaisthesis.domain.project import Project
from synaisthesis.domain.research_spec import ResearchSpec
from synaisthesis.domain.revision import Revision
from synaisthesis.domain.stage import StageRun

NOW = datetime(2026, 8, 15, 10, 0, 0, tzinfo=UTC)


# ---------------------------------------------------------------------------
# Project
# ---------------------------------------------------------------------------


def test_project_defaults_to_seed_lifecycle():
    project = Project(id="p-1", name="demo")
    assert project.lifecycle_status is ProjectLifecycleStatus.SEED
    assert project.description == ""


def test_project_is_immutable():
    project = Project(id="p-1", name="demo")
    with pytest.raises(FrozenInstanceError):
        project.name = "changed"  # type: ignore[misc]


def test_change_lifecycle_returns_new_instance():
    project = Project(id="p-1", name="demo", created_at=NOW, updated_at=NOW)
    changed = project.change_lifecycle(ProjectLifecycleStatus.INCUBATING, at=NOW)
    assert changed is not project
    assert changed.lifecycle_status is ProjectLifecycleStatus.INCUBATING
    assert project.lifecycle_status is ProjectLifecycleStatus.SEED


# ---------------------------------------------------------------------------
# ResearchSpec: confirmed spec cannot be overwritten in place
# ---------------------------------------------------------------------------


def _spec(**overrides):
    base = {
        "project_id": "p-1",
        "version": 1,
        "s1_natural_language_spec": {"core_definition": "x"},
        "s4_scope_spec": {"main_question": "q"},
    }
    base.update(overrides)
    return ResearchSpec(**base)


def test_research_spec_defaults_to_unconfirmed():
    spec = _spec()
    assert spec.is_confirmed is False
    assert spec.confirmed_at is None


def test_research_spec_is_immutable():
    spec = _spec()
    with pytest.raises(FrozenInstanceError):
        spec.user_confirmed = True  # type: ignore[misc]


def test_confirm_returns_confirmed_copy_without_mutating():
    spec = _spec()
    confirmed = spec.confirm(at=NOW)
    assert confirmed is not spec
    assert confirmed.is_confirmed is True
    assert confirmed.confirmed_at == NOW
    assert spec.is_confirmed is False


def test_confirm_twice_raises_conflict():
    confirmed = _spec().confirm(at=NOW)
    with pytest.raises(ConflictError):
        confirmed.confirm(at=NOW)


def test_confirmed_spec_requires_new_version_not_overwrite():
    confirmed = _spec().confirm(at=NOW)
    next_spec = confirmed.new_version(s1_natural_language_spec={"core_definition": "y"})
    assert next_spec.version == 2
    assert next_spec.is_confirmed is False
    # original confirmed spec is untouched
    assert confirmed.version == 1
    assert confirmed.is_confirmed is True
    assert confirmed.s1_natural_language_spec == {"core_definition": "x"}


def test_new_version_resets_confirmation_and_scopes():
    spec = _spec()
    next_spec = spec.new_version(s1_natural_language_spec={"core_definition": "z"})
    assert next_spec.version == 2
    assert next_spec.s4_scope_spec is None
    assert next_spec.is_confirmed is False


def test_content_hash_is_deterministic_and_content_bound():
    a = _spec()
    b = _spec()
    assert a.content_hash == b.content_hash
    assert len(a.content_hash) == 64
    changed = _spec(s1_natural_language_spec={"core_definition": "other"})
    assert changed.content_hash != a.content_hash


def test_content_hash_ignores_version_number():
    same_content = _spec(version=7)
    assert same_content.content_hash == _spec(version=1).content_hash


# ---------------------------------------------------------------------------
# StageRun
# ---------------------------------------------------------------------------


def _run(**overrides):
    base = {"id": "r-1", "project_id": "p-1", "stage_id": StageId.S1, "started_at": NOW}
    base.update(overrides)
    return StageRun(**base)


def test_stage_run_is_unfinished_until_completed():
    run = _run()
    assert run.is_finished is False
    assert run.ended_at is None
    assert run.status is StageGateStatus.NOT_TESTED


def test_complete_returns_new_instance():
    run = _run()
    done = run.complete(
        status=StageGateStatus.PASS,
        output_artifact_id="art-1",
        ended_at=NOW,
    )
    assert done is not run
    assert done.is_finished is True
    assert done.status is StageGateStatus.PASS
    assert done.output_artifact_id == "art-1"
    assert run.is_finished is False


def test_complete_twice_raises_conflict():
    done = _run().complete(
        status=StageGateStatus.PASS,
        output_artifact_id="art-1",
        ended_at=NOW,
    )
    with pytest.raises(ConflictError):
        done.complete(status=StageGateStatus.PASS, output_artifact_id="art-2", ended_at=NOW)


# ---------------------------------------------------------------------------
# Revision: immutable chain
# ---------------------------------------------------------------------------


def _revision(**overrides):
    base = {
        "id": "rev-1",
        "parent_revision_id": None,
        "natural_language_statement": "all objects satisfy P",
        "semantic_delta_level": 2,
        "created_by": "user",
    }
    base.update(overrides)
    return Revision(**base)


def test_revision_immutable_hash_is_content_bound():
    a = _revision()
    b = _revision()
    assert a.immutable_hash == b.immutable_hash
    assert len(a.immutable_hash) == 64
    changed = _revision(natural_language_statement="some objects fail P")
    assert changed.immutable_hash != a.immutable_hash


def test_revision_is_immutable():
    rev = _revision()
    with pytest.raises(FrozenInstanceError):
        rev.natural_language_statement = "changed"  # type: ignore[misc]


def test_create_child_links_parent_and_preserves_history():
    parent = _revision()
    child = parent.create_child(
        id="rev-2",
        natural_language_statement="refined statement",
        semantic_delta_level=3,
        created_by="user",
    )
    assert child.id == "rev-2"
    assert child.parent_revision_id == "rev-1"
    assert parent.parent_revision_id is None
    assert parent.natural_language_statement == "all objects satisfy P"


# ---------------------------------------------------------------------------
# Evidence: revocation preserves history
# ---------------------------------------------------------------------------


def _evidence(**overrides):
    base = {
        "id": "e-1",
        "evidence_type": EvidenceType.PYTHON_EXPERIMENT,
        "provenance_type": ProvenanceType.TOOL_EXECUTION,
        "strength": EvidenceStrength.E3,
        "scope": "encoding X",
        "artifact_id": "art-1",
        "created_at": NOW,
    }
    base.update(overrides)
    return Evidence(**base)


def test_evidence_defaults_to_active():
    evidence = _evidence()
    assert evidence.is_revoked is False
    assert evidence.revoked_at is None


def test_revoke_returns_revoked_copy_and_preserves_content():
    evidence = _evidence()
    revoked = evidence.revoke(at=NOW)
    assert revoked is not evidence
    assert revoked.is_revoked is True
    assert revoked.revoked_at == NOW
    # original record is preserved (not deleted) and content identical
    assert evidence.is_revoked is False
    assert revoked.evidence_type is evidence.evidence_type
    assert revoked.artifact_id == "art-1"
    assert revoked.strength is EvidenceStrength.E3


def test_revoke_twice_raises_conflict():
    revoked = _evidence().revoke(at=NOW)
    with pytest.raises(ConflictError):
        revoked.revoke(at=NOW)
