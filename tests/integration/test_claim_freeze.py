"""M4.2 integration tests for claim contract freeze and revision (04 section 2)."""

from __future__ import annotations

import dataclasses
from datetime import UTC, datetime
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config

from synaisthesis.agents.schemas import ClaimCandidate
from synaisthesis.application.claim_compiler_service import (
    compile_claims,
    freeze_claim_contract,
    load_claim_contract,
    revise_claim_contract,
    save_compiled_claims,
)
from synaisthesis.domain.claim import Claim, ClaimClass, ClaimVerifier
from synaisthesis.domain.claim_contract import (
    EVENT_CLAIM_CONTRACT_FROZEN,
    EVENT_CLAIM_CONTRACT_REVISED,
    ClaimContract,
)
from synaisthesis.domain.enums import ProvenanceType
from synaisthesis.domain.errors import DomainError
from synaisthesis.domain.gate import (
    claim_acceptance_allowed_decisions,
)
from synaisthesis.storage.database import init_database
from synaisthesis.storage.repositories.event_repository import DomainEventRecord

NOW = datetime(2026, 8, 17, 2, 0, 0, tzinfo=UTC)
REPO_ROOT = Path(__file__).resolve().parents[2]
MIGRATIONS_DIR = REPO_ROOT / "src" / "synaisthesis" / "storage" / "migrations"


def _fresh_database(tmp_path: Path):
    db_url = f"sqlite:///{tmp_path / 'claim-freeze.db'}"
    cfg = Config()
    cfg.set_main_option("script_location", str(MIGRATIONS_DIR))
    cfg.set_main_option("sqlalchemy.url", db_url)
    command.upgrade(cfg, "head")
    _, session_factory = init_database(db_url)
    return session_factory


def _compile_and_save(session_factory, artifact_root: Path) -> Claim:
    candidate = ClaimCandidate(
        statement="∀A,B ∈ M_n，tr(AB)=tr(BA)",
        object_domain="有限矩阵 M_n",
        quantifiers=["forall A", "forall B"],
        falsification_witness="非方阵输入",
        claim_class=ClaimClass.FORMAL,
        verifier=ClaimVerifier.LEAN,
        formal_statement_candidate="trace(mul A B) = trace(mul B A)",
        assumptions=["A,B 为方阵"],
        conclusion="tr(AB)=tr(BA)",
        claim_key="trace-cyclic",
    )
    (claim,) = compile_claims((candidate,), project_id="p-1")
    with session_factory() as session:
        save_compiled_claims(
            session, project_id="p-1", claims=(claim,), artifact_root=artifact_root
        )
        session.commit()
    return claim


def _freeze(
    session_factory,
    artifact_root: Path,
    claim: Claim,
    *,
    actor: ProvenanceType = ProvenanceType.USER_DECISION,
    contract_id: str | None = "cc-1",
    **overrides,
) -> ClaimContract:
    params = {
        "tool_plan": ("Lean 4",),
        "network_policy": "no network",
        "data_policy": "public only",
        "budget_policy": "100k tokens",
        "allowed_semantic_delta": "F0 EXACT",
        "approval_policy": "A2 AI_DELEGATED",
        "model_role_assignments": ("primary=model-x", "auditor=model-y"),
    }
    params.update(overrides)
    with session_factory() as session:
        contract = freeze_claim_contract(
            session,
            project_id="p-1",
            claim=claim,
            actor=actor,
            user_event_id="uev-freeze",
            at=NOW,
            artifact_root=artifact_root,
            contract_id=contract_id,
            stop_conditions=("counterexample found",),
            output_scope="theorem only",
            baseline_snapshot="s1@abc",
            **params,
        )
        session.commit()
    return contract


def test_freeze_requires_real_user_event(tmp_path):
    session_factory = _fresh_database(tmp_path)
    artifact_root = tmp_path / "artifacts"
    claim = _compile_and_save(session_factory, artifact_root)
    with pytest.raises(DomainError) as exc_info:
        _freeze(
            session_factory,
            artifact_root,
            claim,
            actor=ProvenanceType.ASSISTANT_PROPOSAL,
        )
    assert exc_info.value.error_code == "CLAIM_FREEZE_REQUIRES_USER_EVENT"


def test_freeze_succeeds_and_hash_covers_content(tmp_path):
    session_factory = _fresh_database(tmp_path)
    artifact_root = tmp_path / "artifacts"
    claim = _compile_and_save(session_factory, artifact_root)
    contract = _freeze(session_factory, artifact_root, claim)
    assert contract.user_confirmed is True
    assert contract.frozen_at == NOW
    assert contract.version == 1
    assert contract.contract_hash and len(contract.contract_hash) == 64
    assert claim_acceptance_allowed_decisions() == ("ACCEPT", "REJECT", "PAUSE")

    # hash covers semantics, tools, budget and policies
    changed = dataclasses.replace(contract, budget_policy="1M tokens", contract_hash=None)
    assert changed.contract_hash != contract.contract_hash
    changed = dataclasses.replace(contract, tool_plan=("Z3",), contract_hash=None)
    assert changed.contract_hash != contract.contract_hash
    changed = dataclasses.replace(contract, natural_language_hash="0" * 64, contract_hash=None)
    assert changed.contract_hash != contract.contract_hash


def test_freeze_round_trip_and_event(tmp_path):
    session_factory = _fresh_database(tmp_path)
    artifact_root = tmp_path / "artifacts"
    claim = _compile_and_save(session_factory, artifact_root)
    contract = _freeze(session_factory, artifact_root, claim)
    with session_factory() as session:
        reloaded = load_claim_contract(session, "cc-1", artifact_root=artifact_root)
        events = (
            session.execute(
                __import__("sqlalchemy")
                .select(DomainEventRecord)
                .where(DomainEventRecord.aggregate_id == "cc-1")
            )
            .scalars()
            .all()
        )
    assert reloaded == contract
    assert [event.event_type for event in events] == [EVENT_CLAIM_CONTRACT_FROZEN]
    assert reloaded.frozen_at == NOW


def test_freeze_tamper_detected(tmp_path):
    session_factory = _fresh_database(tmp_path)
    artifact_root = tmp_path / "artifacts"
    claim = _compile_and_save(session_factory, artifact_root)
    _freeze(session_factory, artifact_root, claim)
    payload_files = list((artifact_root / "events" / "cc-1").glob("*.json"))
    assert payload_files
    payload_files[0].write_text('{"tampered": true}', encoding="utf-8")
    with session_factory() as session, pytest.raises(DomainError) as exc_info:
        load_claim_contract(session, "cc-1", artifact_root=artifact_root)
    assert exc_info.value.error_code == "ARTIFACT_HASH_MISMATCH"


def test_revision_creates_new_version_and_preserves_old(tmp_path):
    session_factory = _fresh_database(tmp_path)
    artifact_root = tmp_path / "artifacts"
    claim = _compile_and_save(session_factory, artifact_root)
    contract = _freeze(session_factory, artifact_root, claim)

    with session_factory() as session:
        revised = revise_claim_contract(
            session,
            project_id="p-1",
            current=contract,
            actor=ProvenanceType.USER_DECISION,
            user_event_id="uev-revise",
            at=NOW,
            artifact_root=artifact_root,
            budget_policy="200k tokens",
        )
        session.commit()
    assert revised.version == 2
    assert revised.supersedes_id == "cc-1"
    assert revised.budget_policy == "200k tokens"
    # old contract is unchanged
    assert contract.version == 1
    assert contract.budget_policy == "100k tokens"
    # new contract has its own content-bound hash
    assert revised.contract_hash != contract.contract_hash

    with session_factory() as session:
        reloaded = load_claim_contract(session, "cc-1", artifact_root=artifact_root)
        events = (
            session.execute(
                __import__("sqlalchemy")
                .select(DomainEventRecord)
                .where(DomainEventRecord.aggregate_id == "cc-1")
            )
            .scalars()
            .all()
        )
    assert reloaded == revised
    assert [event.event_type for event in events] == [
        EVENT_CLAIM_CONTRACT_FROZEN,
        EVENT_CLAIM_CONTRACT_REVISED,
    ]


def test_revision_rejects_immutable_field_change(tmp_path):
    session_factory = _fresh_database(tmp_path)
    artifact_root = tmp_path / "artifacts"
    claim = _compile_and_save(session_factory, artifact_root)
    contract = _freeze(session_factory, artifact_root, claim)
    with session_factory() as session, pytest.raises(DomainError) as exc_info:
        revise_claim_contract(
            session,
            project_id="p-1",
            current=contract,
            actor=ProvenanceType.USER_DECISION,
            user_event_id="uev-bad",
            at=NOW,
            artifact_root=artifact_root,
            claim_id="other-claim",
        )
    assert exc_info.value.error_code == "CLAIM_CONTRACT_FROZEN"


def test_revision_requires_real_user(tmp_path):
    session_factory = _fresh_database(tmp_path)
    artifact_root = tmp_path / "artifacts"
    claim = _compile_and_save(session_factory, artifact_root)
    contract = _freeze(session_factory, artifact_root, claim)
    with session_factory() as session, pytest.raises(DomainError) as exc_info:
        revise_claim_contract(
            session,
            project_id="p-1",
            current=contract,
            actor=ProvenanceType.ASSISTANT_PROPOSAL,
            user_event_id="uev-bad",
            at=NOW,
            artifact_root=artifact_root,
            budget_policy="x",
        )
    assert exc_info.value.error_code == "CLAIM_FREEZE_REQUIRES_USER_EVENT"
