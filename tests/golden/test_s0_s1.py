"""M2.1 golden tests: S0 raw preservation and S1 user-confirmation contracts.

Golden inputs come from the incubator contracts (blueprint 03, S0/S1). Each
test pins the expected schema and the expected forbidden behavior.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from pydantic import ValidationError
from sqlalchemy import select

from synaisthesis.agents.schemas import NaturalLanguageSpec, SeedRecord
from synaisthesis.application.incubation_service import (
    EVENT_SEED_CAPTURED,
    EVENT_SPEC_CONFIRMED,
    EVENT_SPEC_PROPOSED,
    SEED_AGGREGATE_TYPE,
    SPEC_AGGREGATE_TYPE,
    capture_seed,
    confirm_natural_language_spec,
    evaluate_stage_gate,
    load_natural_language_spec,
    load_seed,
    propose_natural_language_spec,
    validate_stage_output,
)
from synaisthesis.domain.enums import ProvenanceType, StageGateStatus, StageId
from synaisthesis.domain.errors import DomainError
from synaisthesis.domain.event import DomainEvent
from synaisthesis.domain.stage import (
    S0_STAGE_CONTRACT,
    S1_STAGE_CONTRACT,
    validate_natural_language_spec,
    validate_seed_record,
)
from synaisthesis.storage.artifact_store import ArtifactRecord
from synaisthesis.storage.database import init_database
from synaisthesis.storage.hashing import sha256_bytes
from synaisthesis.storage.repositories.event_repository import (
    DomainEventRecord,
    append_domain_event,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
MIGRATIONS_DIR = REPO_ROOT / "src" / "synaisthesis" / "storage" / "migrations"
PROMPTS_DIR = REPO_ROOT / "src" / "synaisthesis" / "prompts" / "incubator"

GOLDEN_SEED_RAW = (
    "当我把两个矩阵的乘积取迹时，迹对乘积顺序的交换似乎是自由的，但转置会打破这种对称性。"
)

GOLDEN_SEED = SeedRecord(
    raw_input=GOLDEN_SEED_RAW,
    source_type="user_message",
    user_intent_guess="想研究迹交换与转置之间的关系",
    observation="tr(AB)=tr(BA) 对乘积交换自由",
    interpretation="用户可能观察到迹的循环性质",
    observation_interpretation_separated=True,
    key_ambiguity="转置是否保持该对称性尚不明确",
)

GOLDEN_S1 = NaturalLanguageSpec(
    core_definition="迹是方阵对角元之和，tr(AB)=tr(BA) 对可相乘的方阵成立。",
    positive_examples=["tr(AB)=tr(BA)", "tr(ABC)=tr(BCA)"],
    non_examples=["det(AB)=det(A)det(B) 不涉及交换对称"],
    boundary_conditions=[
        "A 与 B 必须可相乘且乘积为方阵",
        "仅对迹成立，对一般矩阵函数不成立",
    ],
    object_candidates=["方阵", "迹", "转置"],
    ambiguous_terms=["交换对称", "循环不变"],
    explicit_non_goals=["不研究行列式的类似性质"],
    expected_functions=["证明循环性质", "给出转置反例"],
    target_applications=["线性代数教学", "量子态密度矩阵"],
    intended_users=["研究者", "学生"],
    operational_constraints=["限定有限维实/复方阵"],
    success_metrics=["给出形式化证明", "覆盖边界反例"],
)


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


def _capture_golden_seed(session_factory, artifact_root: Path):
    with session_factory() as session:
        seed, raw_hash = capture_seed(
            session,
            project_id="p-1",
            record=GOLDEN_SEED,
            artifact_root=artifact_root,
            seed_id="seed-golden",
        )
        session.commit()
    return seed, raw_hash


# ---------------------------------------------------------------------------
# S0: raw input preserved with a re-computable hash
# ---------------------------------------------------------------------------


def test_s0_golden_preserves_raw_input_and_hash(tmp_path):
    _, session_factory = _fresh_database(tmp_path)
    artifact_root = tmp_path / "artifacts"

    seed, raw_hash = _capture_golden_seed(session_factory, artifact_root)

    assert seed.raw_input == GOLDEN_SEED_RAW
    assert raw_hash == sha256_bytes(GOLDEN_SEED_RAW.encode("utf-8"))

    with session_factory() as session:
        reloaded = load_seed(session, "seed-golden", artifact_root=artifact_root)
        events = (
            session.execute(
                select(DomainEventRecord).where(DomainEventRecord.aggregate_id == "seed-golden")
            )
            .scalars()
            .all()
        )

    assert reloaded.raw_input == GOLDEN_SEED_RAW
    assert reloaded == GOLDEN_SEED
    assert len(events) == 1
    assert events[0].event_type == EVENT_SEED_CAPTURED
    assert events[0].aggregate_type == SEED_AGGREGATE_TYPE


def test_s0_tampered_payload_blocks_load(tmp_path):
    _, session_factory = _fresh_database(tmp_path)
    artifact_root = tmp_path / "artifacts"
    _capture_golden_seed(session_factory, artifact_root)

    with session_factory() as session:
        event = session.execute(
            select(DomainEventRecord).where(DomainEventRecord.aggregate_id == "seed-golden")
        ).scalar_one()
        artifact = session.get(ArtifactRecord, event.event_payload_artifact_id)
        assert artifact is not None
        payload_file = artifact_root / artifact.relative_path
    payload_file.write_bytes(b"tampered")

    with session_factory() as session, pytest.raises(DomainError) as exc_info:
        load_seed(session, "seed-golden", artifact_root=artifact_root)
    assert exc_info.value.error_code == "ARTIFACT_HASH_MISMATCH"


def test_s0_raw_hash_mismatch_detected(tmp_path):
    _, session_factory = _fresh_database(tmp_path)
    artifact_root = tmp_path / "artifacts"

    bad_payload = {
        "seed": GOLDEN_SEED.model_dump() | {"raw_input": "被改写的原文"},
        "raw_hash": sha256_bytes(GOLDEN_SEED_RAW.encode("utf-8")),
    }
    event = DomainEvent(
        aggregate_type=SEED_AGGREGATE_TYPE,
        aggregate_id="seed-bad",
        event_type=EVENT_SEED_CAPTURED,
        payload=bad_payload,
        sequence=1,
    )
    with session_factory() as session:
        append_domain_event(session, event, project_id="p-1", artifact_root=artifact_root)
        session.commit()

    with session_factory() as session, pytest.raises(DomainError) as exc_info:
        load_seed(session, "seed-bad", artifact_root=artifact_root)
    assert exc_info.value.error_code == "RAW_HASH_MISMATCH"


def test_s0_validator_separates_observation_and_interpretation():
    assert validate_seed_record(GOLDEN_SEED) == ()
    assert validate_stage_output(StageId.S0, GOLDEN_SEED) == ()

    blended = GOLDEN_SEED.model_copy(
        update={
            "observation": "同一句话",
            "interpretation": "同一句话",
            "observation_interpretation_separated": False,
        }
    )
    issues = validate_seed_record(blended)
    assert any("分栏" in issue for issue in issues)
    assert any("混同" in issue for issue in issues)


def test_s0_schema_rejects_multiple_key_ambiguities_and_unknown_fields():
    # Intentionally schema-invalid inputs prove the Schema layer rejects them.
    with pytest.raises(ValidationError):
        SeedRecord(
            **GOLDEN_SEED.model_dump() | {"key_ambiguity": ["歧义一", "歧义二"]}  # type: ignore[arg-type]
        )
    with pytest.raises(ValidationError):
        SeedRecord(
            **GOLDEN_SEED.model_dump() | {"silently_added": "x"}  # type: ignore[arg-type]
        )


# ---------------------------------------------------------------------------
# S1: all required fields present; only real user events can confirm
# ---------------------------------------------------------------------------


def test_s1_golden_full_fields_validate_clean():
    assert validate_natural_language_spec(GOLDEN_S1) == ()
    assert validate_stage_output(StageId.S1, GOLDEN_S1) == ()


def test_s1_validator_requires_positive_non_and_boundary():
    for field, label in (
        ("positive_examples", "正例"),
        ("non_examples", "非例"),
        ("boundary_conditions", "边界"),
    ):
        missing = GOLDEN_S1.model_copy(update={field: []})
        issues = validate_natural_language_spec(missing)
        assert any(label in issue for issue in issues), field


def test_s1_schema_rejects_missing_required_field():
    payload = GOLDEN_S1.model_dump()
    del payload["core_definition"]
    with pytest.raises(ValidationError):
        NaturalLanguageSpec(**payload)


def test_s1_gate_partial_until_real_user_confirmation(tmp_path):
    _, session_factory = _fresh_database(tmp_path)
    artifact_root = tmp_path / "artifacts"

    with session_factory() as session:
        proposed = propose_natural_language_spec(
            session,
            project_id="p-1",
            spec=GOLDEN_S1,
            artifact_root=artifact_root,
            spec_id="spec-1",
        )
        session.commit()

    with session_factory() as session:
        reloaded = load_natural_language_spec(session, "spec-1", artifact_root=artifact_root)
    assert reloaded.user_confirmed is False
    assert reloaded.assistant_proposed is True

    assert (
        evaluate_stage_gate(StageId.S1, output=proposed, confirmed=False) is StageGateStatus.PARTIAL
    )
    assert evaluate_stage_gate(StageId.S1, output=None) is StageGateStatus.NOT_TESTED
    assert (
        evaluate_stage_gate(StageId.S1, output=GOLDEN_SEED, confirmed=False)
        is StageGateStatus.BLOCKED
    )

    with session_factory() as session:
        confirmed = confirm_natural_language_spec(
            session,
            spec_id="spec-1",
            actor=ProvenanceType.USER_DECISION,
            user_event_id="uev-1",
            artifact_root=artifact_root,
        )
        session.commit()

    assert confirmed.user_confirmed is True
    assert evaluate_stage_gate(StageId.S1, output=confirmed, confirmed=True) is StageGateStatus.PASS


def test_s1_model_actor_cannot_confirm(tmp_path):
    _, session_factory = _fresh_database(tmp_path)
    artifact_root = tmp_path / "artifacts"

    with session_factory() as session:
        propose_natural_language_spec(
            session,
            project_id="p-1",
            spec=GOLDEN_S1,
            artifact_root=artifact_root,
            spec_id="spec-2",
        )
        session.commit()

    for actor in (ProvenanceType.ASSISTANT_PROPOSAL, ProvenanceType.EXTERNAL_MODEL_IMPORT):
        with session_factory() as session, pytest.raises(DomainError) as exc_info:
            confirm_natural_language_spec(
                session,
                spec_id="spec-2",
                actor=actor,
                user_event_id=f"model-{actor.value}",
                artifact_root=artifact_root,
            )
        assert exc_info.value.error_code == "CONFIRMATION_REQUIRES_USER_EVENT"

    with session_factory() as session:
        reloaded = load_natural_language_spec(session, "spec-2", artifact_root=artifact_root)
        events = (
            session.execute(
                select(DomainEventRecord).where(DomainEventRecord.aggregate_id == "spec-2")
            )
            .scalars()
            .all()
        )
    assert reloaded.user_confirmed is False
    assert [e.event_type for e in events] == [EVENT_SPEC_PROPOSED]


def test_s1_confirmation_records_user_provenance(tmp_path):
    _, session_factory = _fresh_database(tmp_path)
    artifact_root = tmp_path / "artifacts"

    with session_factory() as session:
        propose_natural_language_spec(
            session,
            project_id="p-1",
            spec=GOLDEN_S1,
            artifact_root=artifact_root,
            spec_id="spec-3",
        )
        confirm_natural_language_spec(
            session,
            spec_id="spec-3",
            actor=ProvenanceType.USER_DECISION,
            user_event_id="uev-42",
            artifact_root=artifact_root,
        )
        session.commit()

    with session_factory() as session:
        reloaded = load_natural_language_spec(session, "spec-3", artifact_root=artifact_root)
        events = (
            session.execute(
                select(DomainEventRecord)
                .where(DomainEventRecord.aggregate_id == "spec-3")
                .order_by(DomainEventRecord.id)
            )
            .scalars()
            .all()
        )
        confirmed_event = events[-1]
        artifact = session.get(ArtifactRecord, confirmed_event.event_payload_artifact_id)
        assert artifact is not None
        payload_file = (artifact_root / artifact.relative_path).read_text(encoding="utf-8")

    assert reloaded.user_confirmed is True
    assert confirmed_event.event_type == EVENT_SPEC_CONFIRMED
    assert confirmed_event.aggregate_type == SPEC_AGGREGATE_TYPE
    assert "USER_DECISION" in payload_file
    assert "uev-42" in payload_file


def test_s1_propose_rejects_invalid_or_preconfirmed(tmp_path):
    _, session_factory = _fresh_database(tmp_path)
    artifact_root = tmp_path / "artifacts"

    with session_factory() as session:
        with pytest.raises(DomainError) as exc_info:
            propose_natural_language_spec(
                session,
                project_id="p-1",
                spec=GOLDEN_S1.model_copy(update={"non_examples": []}),
                artifact_root=artifact_root,
                spec_id="spec-bad",
            )
        assert exc_info.value.error_code == "STAGE_OUTPUT_INVALID"

        with pytest.raises(DomainError) as exc_info:
            propose_natural_language_spec(
                session,
                project_id="p-1",
                spec=GOLDEN_S1.model_copy(update={"user_confirmed": True}),
                artifact_root=artifact_root,
                spec_id="spec-preconfirmed",
            )
        assert exc_info.value.error_code == "CONFIRMATION_REQUIRES_USER_EVENT"


# ---------------------------------------------------------------------------
# Prompt assets and stage contracts
# ---------------------------------------------------------------------------


def test_prompt_assets_have_required_sections():
    s0 = (PROMPTS_DIR / "s0_capture_seed.md").read_text(encoding="utf-8")
    assert "prompt_key: s0_capture_seed" in s0
    assert "version: 1.0.0" in s0
    assert "禁止行为" in s0
    assert "raw_input" in s0

    s1 = (PROMPTS_DIR / "s1_natural_language_spec.md").read_text(encoding="utf-8")
    assert "prompt_key: s1_natural_language_spec" in s1
    assert "version: 1.0.0" in s1
    assert "禁止行为" in s1
    assert "core_definition" in s1
    assert "positive_examples" in s1


def test_stage_contracts_match_blueprint():
    assert S0_STAGE_CONTRACT.stage_id is StageId.S0
    assert S0_STAGE_CONTRACT.output_artifact_type == "SeedRecord"
    assert "raw_input" in S0_STAGE_CONTRACT.required_fields
    assert "无强制确认" in S0_STAGE_CONTRACT.human_gate_policy

    assert S1_STAGE_CONTRACT.stage_id is StageId.S1
    assert S1_STAGE_CONTRACT.output_artifact_type == "NaturalLanguageSpec"
    assert "user_confirmed" in S1_STAGE_CONTRACT.required_fields
    assert "用户明确确认" in S1_STAGE_CONTRACT.pass_criteria
    assert "模型不能代替用户确认" in S1_STAGE_CONTRACT.human_gate_policy
    assert S1_STAGE_CONTRACT.allowed_next_stages == (StageId.S2,)
    assert S1_STAGE_CONTRACT.rollback_targets == (StageId.S0,)
