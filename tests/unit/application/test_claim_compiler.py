"""M4.1 unit tests for the Claim Compiler."""

from __future__ import annotations

from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config

from synaisthesis.agents.schemas import ClaimCandidate
from synaisthesis.application.claim_compiler_service import (
    classify_claim,
    compile_claims,
    is_mixed_statement,
    save_compiled_claims,
    split_propositions,
)
from synaisthesis.domain.claim import Claim, ClaimClass, ClaimVerifier
from synaisthesis.domain.errors import DomainError
from synaisthesis.domain.event import sha256_hex
from synaisthesis.storage.database import init_database
from synaisthesis.storage.repositories.claim_repository import (
    claim_from_state,
    claim_state_dict,
    load_claim,
    save_claim,
)

REPO_ROOT = Path(__file__).resolve().parents[3]
MIGRATIONS_DIR = REPO_ROOT / "src" / "synaisthesis" / "storage" / "migrations"


def _fresh_database(tmp_path: Path):
    db_url = f"sqlite:///{tmp_path / 'claims.db'}"
    cfg = Config()
    cfg.set_main_option("script_location", str(MIGRATIONS_DIR))
    cfg.set_main_option("sqlalchemy.url", db_url)
    command.upgrade(cfg, "head")
    _, session_factory = init_database(db_url)
    return session_factory


def _atomic_candidate(**overrides) -> ClaimCandidate:
    params = {
        "statement": "tr(AB)=tr(BA)",
        "object_domain": "有限域上的 n×n 矩阵",
        "quantifiers": ["∀ A", "∀ B"],
        "claim_class": ClaimClass.FORMAL,
        "verifier": ClaimVerifier.LEAN,
        "falsification_witness": "∃ A,B: tr(AB)≠tr(BA)",
    }
    params.update(overrides)
    return ClaimCandidate(**params)


def _atomic_claim(**overrides) -> Claim:
    return compile_claims([_atomic_candidate(**overrides)], project_id="p-1")[0]


# ---------------------------------------------------------------------------
# Proposition splitting / classification
# ---------------------------------------------------------------------------


def test_split_propositions_splits_top_level_and_or():
    assert split_propositions("a and b or c") == ("a", "b", "c")
    assert split_propositions("A 且 B") == ("A", "B")
    assert split_propositions("A 以及 B 并且 C") == ("A", "B", "C")


def test_split_propositions_respects_brackets():
    assert split_propositions("f(x and y)=0") == ("f(x and y)=0",)
    assert split_propositions("单一命题") == ("单一命题",)


def test_is_mixed_statement_and_classify():
    assert is_mixed_statement("a and b")
    assert not is_mixed_statement("单一命题")
    assert classify_claim("a and b", ClaimClass.FORMAL) is ClaimClass.MIXED
    assert classify_claim("单一命题", ClaimClass.FORMAL) is ClaimClass.FORMAL


# ---------------------------------------------------------------------------
# compile_claims: MIXED split
# ---------------------------------------------------------------------------


def test_mixed_claim_splits_into_atomic_claims():
    candidate = ClaimCandidate(
        statement="tr(AB)=tr(BA) and det(A)det(B)=det(AB)",
        object_domain="有限域上的 n×n 矩阵",
        quantifiers=["∀ A", "∀ B"],
        claim_class=ClaimClass.MIXED,
        verifier=ClaimVerifier.LEAN,
        atomic_parts=[
            _atomic_candidate(
                statement="tr(AB)=tr(BA)",
                falsification_witness="∃ A,B: tr(AB)≠tr(BA)",
            ),
            _atomic_candidate(
                statement="det(A)det(B)=det(AB)",
                falsification_witness="∃ A,B: det(A)det(B)≠det(AB)",
            ),
        ],
    )
    claims = compile_claims([candidate], project_id="p-1")
    assert len(claims) == 2
    for claim in claims:
        assert claim.is_atomic
        assert claim.object_domain
        assert claim.quantifiers
        assert claim.falsification_witness
        assert claim.verifier is ClaimVerifier.LEAN
    assert [claim.natural_language_statement for claim in claims] == [
        "tr(AB)=tr(BA)",
        "det(A)det(B)=det(AB)",
    ]
    assert claims[0].parent_claim_id == claims[1].parent_claim_id
    assert claims[0].claim_key != claims[1].claim_key


def test_atomic_claim_compiles():
    claim = _atomic_claim()
    assert claim.is_atomic
    assert claim.claim_class is ClaimClass.FORMAL
    assert claim.verifier is ClaimVerifier.LEAN
    assert claim.artifact_hash == sha256_hex(claim.content_payload())


def test_none_verifier_requires_explicit_unverified():
    claim = _atomic_claim(verifier=ClaimVerifier.NONE, unverified=True)
    assert claim.verifier is ClaimVerifier.NONE
    assert claim.unverified is True


# ---------------------------------------------------------------------------
# Rejections: cannot form an unambiguous atomic proposition
# ---------------------------------------------------------------------------


def test_atomic_claim_missing_quantifiers_rejected():
    with pytest.raises(DomainError) as exc_info:
        _atomic_claim(quantifiers=[])
    assert exc_info.value.error_code == "CLAIM_NOT_ATOMIC"


def test_atomic_claim_empty_falsification_witness_rejected():
    with pytest.raises(DomainError) as exc_info:
        _atomic_claim(falsification_witness="   ")
    assert exc_info.value.error_code == "CLAIM_NOT_ATOMIC"


def test_none_verifier_without_declaration_rejected():
    with pytest.raises(DomainError) as exc_info:
        _atomic_claim(verifier=ClaimVerifier.NONE, unverified=False)
    assert exc_info.value.error_code == "CLAIM_VERIFIER_MISSING"


def test_compound_statement_not_declared_mixed_rejected():
    with pytest.raises(DomainError) as exc_info:
        compile_claims(
            [_atomic_candidate(statement="a and b", claim_class=ClaimClass.FORMAL)],
            project_id="p-1",
        )
    assert exc_info.value.error_code == "CLAIM_MIXED"


def test_mixed_claim_without_atomic_parts_rejected():
    with pytest.raises(DomainError) as exc_info:
        compile_claims(
            [
                ClaimCandidate(
                    statement="a and b",
                    object_domain="D",
                    quantifiers=["∀ x"],
                    claim_class=ClaimClass.MIXED,
                )
            ],
            project_id="p-1",
        )
    assert exc_info.value.error_code == "CLAIM_MIXED"


def test_atomic_declaration_on_compound_statement_rejected():
    with pytest.raises(DomainError) as exc_info:
        compile_claims(
            [
                _atomic_candidate(
                    statement="a and b",
                    claim_class=ClaimClass.MIXED,
                    atomic=True,
                )
            ],
            project_id="p-1",
        )
    assert exc_info.value.error_code == "CLAIM_NOT_ATOMIC"


# ---------------------------------------------------------------------------
# Persistence round-trip and tamper detection
# ---------------------------------------------------------------------------


def test_claim_round_trip(tmp_path):
    session_factory = _fresh_database(tmp_path)
    artifact_root = tmp_path / "artifacts"
    claim = _atomic_claim()
    with session_factory() as session:
        save_claim(session, claim, project_id="p-1", artifact_root=artifact_root)
        session.commit()
    with session_factory() as session:
        reloaded = load_claim(session, claim.claim_id, artifact_root=artifact_root)
    assert reloaded == claim
    assert reloaded.artifact_hash == claim.artifact_hash


def test_save_compiled_claims_persists_all(tmp_path):
    session_factory = _fresh_database(tmp_path)
    artifact_root = tmp_path / "artifacts"
    candidate = ClaimCandidate(
        statement="a and b",
        object_domain="D",
        quantifiers=["∀ x"],
        claim_class=ClaimClass.MIXED,
        atomic_parts=[
            _atomic_candidate(statement="a", falsification_witness="¬a"),
            _atomic_candidate(statement="b", falsification_witness="¬b"),
        ],
    )
    claims = compile_claims([candidate], project_id="p-1")
    with session_factory() as session:
        save_compiled_claims(session, project_id="p-1", claims=claims, artifact_root=artifact_root)
        session.commit()
    with session_factory() as session:
        reloaded = [
            load_claim(session, claim.claim_id, artifact_root=artifact_root) for claim in claims
        ]
    assert reloaded == list(claims)


def test_content_hash_tamper_detected():
    claim = _atomic_claim()
    state = claim_state_dict(claim)
    state["natural_language_statement"] = "被篡改的命题"
    with pytest.raises(DomainError) as exc_info:
        claim_from_state(state)
    assert exc_info.value.error_code == "ARTIFACT_HASH_MISMATCH"


def test_payload_artifact_tamper_detected_on_load(tmp_path):
    session_factory = _fresh_database(tmp_path)
    artifact_root = tmp_path / "artifacts"
    claim = _atomic_claim()
    with session_factory() as session:
        save_claim(session, claim, project_id="p-1", artifact_root=artifact_root)
        session.commit()
    payload_files = list((artifact_root / "events" / claim.claim_id).glob("*.json"))
    assert payload_files
    payload_files[0].write_text('{"tampered": true}', encoding="utf-8")
    with session_factory() as session, pytest.raises(DomainError) as exc_info:
        load_claim(session, claim.claim_id, artifact_root=artifact_root)
    assert exc_info.value.error_code == "ARTIFACT_HASH_MISMATCH"
