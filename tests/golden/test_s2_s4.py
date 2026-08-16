"""M2.2 golden tests: S2-S4 contracts and NATURAL_LANGUAGE_DESIGN_READY.

Golden inputs come from the incubator contracts (blueprint 03, S2/S3/S4) and
from the M2.2 acceptance clauses in blueprint 19 section 5.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from pydantic import ValidationError
from sqlalchemy import select

from synaisthesis.agents.schemas import (
    MechanismSketch,
    NaturalLanguageSpec,
    PriorWorkMap,
    ResearchScopeSpec,
    SeedRecord,
)
from synaisthesis.application.incubation_service import (
    EVENT_RESEARCH_SPEC_BOUND,
    EVENT_SCOPE_CONFIRMED,
    EVENT_SCOPE_PROPOSED,
    RESEARCH_SPEC_AGGREGATE_TYPE,
    SCOPE_AGGREGATE_TYPE,
    capture_seed,
    confirm_natural_language_spec,
    confirm_research_scope_spec,
    derive_natural_language_design_ready,
    evaluate_natural_language_design_ready,
    evaluate_natural_language_design_ready_from_events,
    evaluate_stage_gate,
    load_mechanism_sketch,
    load_natural_language_spec,
    load_prior_work_map,
    load_research_scope_spec,
    propose_mechanism_sketch,
    propose_natural_language_spec,
    propose_prior_work_map,
    propose_research_scope_spec,
    validate_stage_output,
)
from synaisthesis.application.project_service import create_project
from synaisthesis.domain.enums import (
    ProjectLifecycleStatus,
    ProvenanceType,
    StageGateStatus,
    StageId,
)
from synaisthesis.domain.errors import DomainError
from synaisthesis.domain.event import DomainEvent, sha256_hex
from synaisthesis.domain.research_spec import ResearchSpec
from synaisthesis.domain.stage import (
    S2_STAGE_CONTRACT,
    S3_STAGE_CONTRACT,
    S4_STAGE_CONTRACT,
    validate_mechanism_sketch,
    validate_prior_work_map,
    validate_research_scope_spec,
)
from synaisthesis.storage.artifact_store import ArtifactRecord
from synaisthesis.storage.database import init_database
from synaisthesis.storage.repositories.event_repository import (
    DomainEventRecord,
    append_domain_event,
)
from synaisthesis.storage.repositories.project_repository import load_project

REPO_ROOT = Path(__file__).resolve().parents[2]
MIGRATIONS_DIR = REPO_ROOT / "src" / "synaisthesis" / "storage" / "migrations"
PROMPTS_DIR = REPO_ROOT / "src" / "synaisthesis" / "prompts" / "incubator"

GOLDEN_SEED = SeedRecord(
    raw_input="当我把两个矩阵的乘积取迹时，迹对乘积顺序的交换似乎是自由的，但转置会打破这种对称性。",
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
    ambiguous_terms=[],
    explicit_non_goals=["不研究行列式的类似性质"],
    expected_functions=["证明循环性质", "给出转置反例"],
    target_applications=["线性代数教学", "量子态密度矩阵"],
    intended_users=["研究者", "学生"],
    operational_constraints=["限定有限维实/复方阵"],
    success_metrics=["给出形式化证明", "覆盖边界反例"],
)

GOLDEN_S2 = MechanismSketch(
    inputs=["方阵 A", "方阵 B"],
    state_change="取乘积 AB 与 BA 的迹",
    outputs=["tr(AB)", "tr(BA)"],
    invariants=["tr(AB)=tr(BA)"],
    failure_conditions=["A、B 不可相乘时无定义"],
    causal_claims=["循环置换使迹不变"],
    merely_descriptive_relations=["乘积交换与迹不变在样本中相关"],
    uncertainty_register=["转置是否打破该对称性未定"],
)

GOLDEN_S3 = PriorWorkMap(
    search_queries={
        "academic": ["trace cyclic property matrix proof"],
        "engineering": ["numpy trace invariance numerical linear algebra"],
    },
    sources=["arXiv:math/0000000", "GitHub:numpy/numpy"],
    nearest_theories=["矩阵迹理论"],
    same_object_different_method=["用指标缩并研究方阵迹"],
    same_method_different_object=["用循环性质研究其他矩阵函数"],
    conflicts=["某教材称迹交换仅对正整数幂成立"],
    terminology_candidates=["cyclic trace property", "trace invariance"],
    retrieval_scope="有限维实/复方阵的迹与循环性质",
    unsearched_areas=["专利库"],
    literature_hits=["迹的循环性质标准教材条目"],
    mature_engineering_projects=["NumPy"],
    engineering_maturity_evidence=["NumPy 发布与维护记录"],
    function_application_neighbors=["np.trace"],
    metadata_verified=True,
)

GOLDEN_S4 = ResearchScopeSpec(
    main_question="迹的循环不变性在什么边界条件下保持？",
    object_domain="有限维实/复方阵",
    non_goals=["不研究行列式的类似性质"],
    nearest_neighbor_difference="与已有教材相比，本方向明确转置反例边界",
    central_claims=["tr(AB)=tr(BA)", "转置会打破该对称性"],
    evidence_requirements=["给出方阵可相乘时的证明", "给出具体转置反例"],
    failure_learning_plan="若边界反例不成立，则收窄对象域并回 S1/S3",
    engineering_relevance="数值线性代数中迹的快速计算与验证",
    stop_conditions=["无法给出任何非平凡反例", "中心主张全部被推翻"],
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


def _persist_complete_pipeline(
    session_factory,
    artifact_root: Path,
    *,
    project_id: str = "p-1",
    confirm_s4: bool = True,
):
    """Persist S0-S4 for the golden trace example; S1 is always user-confirmed."""
    with session_factory() as session:
        capture_seed(
            session,
            project_id=project_id,
            record=GOLDEN_SEED,
            artifact_root=artifact_root,
            seed_id="seed-1",
        )
        propose_natural_language_spec(
            session,
            project_id=project_id,
            spec=GOLDEN_S1,
            artifact_root=artifact_root,
            spec_id="spec-1",
        )
        confirm_natural_language_spec(
            session,
            spec_id="spec-1",
            actor=ProvenanceType.USER_DECISION,
            user_event_id="uev-s1",
            artifact_root=artifact_root,
        )
        propose_mechanism_sketch(
            session,
            project_id=project_id,
            sketch=GOLDEN_S2,
            artifact_root=artifact_root,
            sketch_id="sketch-1",
        )
        propose_prior_work_map(
            session,
            project_id=project_id,
            prior_work=GOLDEN_S3,
            artifact_root=artifact_root,
            prior_work_id="prior-1",
        )
        propose_research_scope_spec(
            session,
            project_id=project_id,
            scope=GOLDEN_S4,
            artifact_root=artifact_root,
            scope_id="scope-1",
        )
        if confirm_s4:
            confirm_research_scope_spec(
                session,
                scope_id="scope-1",
                s1_spec_id="spec-1",
                actor=ProvenanceType.USER_DECISION,
                user_event_id="uev-s4",
                artifact_root=artifact_root,
                research_spec_id="rs-1",
            )
        session.commit()


# ---------------------------------------------------------------------------
# S2 — MechanismSketch
# ---------------------------------------------------------------------------


def test_s2_golden_schema_validator_and_gate():
    assert validate_mechanism_sketch(GOLDEN_S2) == ()
    assert validate_stage_output(StageId.S2, GOLDEN_S2) == ()
    assert evaluate_stage_gate(StageId.S2, output=GOLDEN_S2) is StageGateStatus.PASS
    assert evaluate_stage_gate(StageId.S2, output=None) is StageGateStatus.NOT_TESTED
    assert evaluate_stage_gate(StageId.S2, output=GOLDEN_S3) is StageGateStatus.BLOCKED


def test_s2_validator_requires_mechanism_contract():
    cases = (
        ("inputs", [], "inputs"),
        ("state_change", "", "state_change"),
        ("outputs", [], "outputs"),
        ("invariants", [], "不变量"),
        ("failure_conditions", [], "失败条件"),
    )
    for field, value, label in cases:
        issues = validate_mechanism_sketch(GOLDEN_S2.model_copy(update={field: value}))
        assert any(label in issue for issue in issues), field

    blended = GOLDEN_S2.model_copy(
        update={
            "causal_claims": ["同一关系"],
            "merely_descriptive_relations": ["同一关系"],
        }
    )
    issues = validate_mechanism_sketch(blended)
    assert any("同一关系不得同时" in issue for issue in issues)


def test_s2_schema_rejects_missing_and_unknown_fields():
    payload = GOLDEN_S2.model_dump()
    del payload["state_change"]
    with pytest.raises(ValidationError):
        MechanismSketch(**payload)  # type: ignore[arg-type]
    with pytest.raises(ValidationError):
        MechanismSketch(
            **GOLDEN_S2.model_dump() | {"invented": "x"}  # type: ignore[arg-type]
        )


# ---------------------------------------------------------------------------
# S3 — PriorWorkMap
# ---------------------------------------------------------------------------


def test_s3_golden_schema_validator_and_gate():
    assert validate_prior_work_map(GOLDEN_S3) == ()
    assert validate_stage_output(StageId.S3, GOLDEN_S3) == ()
    assert evaluate_stage_gate(StageId.S3, output=GOLDEN_S3) is StageGateStatus.PASS
    assert evaluate_stage_gate(StageId.S3, output=None) is StageGateStatus.NOT_TESTED
    assert evaluate_stage_gate(StageId.S3, output=GOLDEN_S2) is StageGateStatus.BLOCKED


def test_s3_validator_requires_dual_query_seeds_and_traceability():
    academic_missing = GOLDEN_S3.model_copy(
        update={"search_queries": {"academic": [], "engineering": ["e"]}}
    )
    assert any(
        "search_queries.academic" in issue for issue in validate_prior_work_map(academic_missing)
    )
    engineering_missing = GOLDEN_S3.model_copy(
        update={"search_queries": {"academic": ["a"], "engineering": []}}
    )
    assert any(
        "search_queries.engineering" in issue
        for issue in validate_prior_work_map(engineering_missing)
    )

    assert any(
        "metadata_verified" in issue
        for issue in validate_prior_work_map(
            GOLDEN_S3.model_copy(update={"metadata_verified": False})
        )
    )
    no_neighbors = GOLDEN_S3.model_copy(
        update={
            "nearest_theories": [],
            "same_object_different_method": [],
            "same_method_different_object": [],
            "function_application_neighbors": [],
        }
    )
    assert any("最近邻类别" in issue for issue in validate_prior_work_map(no_neighbors))
    assert any(
        "sources" in issue
        for issue in validate_prior_work_map(GOLDEN_S3.model_copy(update={"sources": []}))
    )
    no_hits_or_unsearched = GOLDEN_S3.model_copy(
        update={"literature_hits": [], "unsearched_areas": []}
    )
    assert any(
        "unsearched_areas" in issue for issue in validate_prior_work_map(no_hits_or_unsearched)
    )


def test_s3_schema_rejects_missing_and_unknown_fields():
    payload = GOLDEN_S3.model_dump()
    del payload["metadata_verified"]
    with pytest.raises(ValidationError):
        PriorWorkMap(**payload)  # type: ignore[arg-type]
    with pytest.raises(ValidationError):
        PriorWorkMap(
            **GOLDEN_S3.model_dump() | {"novelty": "绝对原创"}  # type: ignore[arg-type]
        )


# ---------------------------------------------------------------------------
# S4 — ResearchScopeSpec
# ---------------------------------------------------------------------------


def test_s4_golden_schema_validator_and_gate():
    assert validate_research_scope_spec(GOLDEN_S4) == ()
    assert validate_stage_output(StageId.S4, GOLDEN_S4) == ()
    # S4 stage PASS is independent of scope confirmation; the completion gate is not.
    assert evaluate_stage_gate(StageId.S4, output=GOLDEN_S4) is StageGateStatus.PASS
    assert evaluate_stage_gate(StageId.S4, output=None) is StageGateStatus.NOT_TESTED
    assert evaluate_stage_gate(StageId.S4, output=GOLDEN_S3) is StageGateStatus.BLOCKED


def test_s4_validator_requires_scope_contract():
    for field in (
        "main_question",
        "object_domain",
        "nearest_neighbor_difference",
        "failure_learning_plan",
        "engineering_relevance",
    ):
        issues = validate_research_scope_spec(GOLDEN_S4.model_copy(update={field: ""}))
        assert any(field in issue for issue in issues), field

    assert any(
        "non_goals" in issue
        for issue in validate_research_scope_spec(GOLDEN_S4.model_copy(update={"non_goals": []}))
    )
    assert any(
        "stop_conditions" in issue
        for issue in validate_research_scope_spec(
            GOLDEN_S4.model_copy(update={"stop_conditions": []})
        )
    )
    mismatched = GOLDEN_S4.model_copy(update={"evidence_requirements": ["只有一条证据需求"]})
    assert any("数量一致" in issue for issue in validate_research_scope_spec(mismatched))


# ---------------------------------------------------------------------------
# Persistence and user confirmation
# ---------------------------------------------------------------------------


def test_s2_s3_s4_propose_and_load_roundtrip(tmp_path):
    _, session_factory = _fresh_database(tmp_path)
    artifact_root = tmp_path / "artifacts"

    with session_factory() as session:
        propose_mechanism_sketch(
            session,
            project_id="p-1",
            sketch=GOLDEN_S2,
            artifact_root=artifact_root,
            sketch_id="sketch-1",
        )
        propose_prior_work_map(
            session,
            project_id="p-1",
            prior_work=GOLDEN_S3,
            artifact_root=artifact_root,
            prior_work_id="prior-1",
        )
        propose_research_scope_spec(
            session,
            project_id="p-1",
            scope=GOLDEN_S4,
            artifact_root=artifact_root,
            scope_id="scope-1",
        )
        session.commit()

    with session_factory() as session:
        assert load_mechanism_sketch(session, "sketch-1", artifact_root=artifact_root) == GOLDEN_S2
        assert load_prior_work_map(session, "prior-1", artifact_root=artifact_root) == GOLDEN_S3
        assert (
            load_research_scope_spec(session, "scope-1", artifact_root=artifact_root) == GOLDEN_S4
        )


def test_s4_preconfirmed_and_model_actor_are_rejected(tmp_path):
    _, session_factory = _fresh_database(tmp_path)
    artifact_root = tmp_path / "artifacts"

    with session_factory() as session:
        with pytest.raises(DomainError) as exc_info:
            propose_research_scope_spec(
                session,
                project_id="p-1",
                scope=GOLDEN_S4.model_copy(update={"user_confirmed_scope": True}),
                artifact_root=artifact_root,
                scope_id="scope-bad",
            )
        assert exc_info.value.error_code == "CONFIRMATION_REQUIRES_USER_EVENT"

        propose_research_scope_spec(
            session,
            project_id="p-1",
            scope=GOLDEN_S4,
            artifact_root=artifact_root,
            scope_id="scope-1",
        )
        for actor in (ProvenanceType.ASSISTANT_PROPOSAL, ProvenanceType.EXTERNAL_MODEL_IMPORT):
            with pytest.raises(DomainError) as exc_info:
                confirm_research_scope_spec(
                    session,
                    scope_id="scope-1",
                    s1_spec_id="spec-missing",
                    actor=actor,
                    user_event_id="model-event",
                    artifact_root=artifact_root,
                )
            assert exc_info.value.error_code == "CONFIRMATION_REQUIRES_USER_EVENT"
        session.commit()

    with session_factory() as session:
        reloaded = load_research_scope_spec(session, "scope-1", artifact_root=artifact_root)
        events = (
            session.execute(
                select(DomainEventRecord).where(DomainEventRecord.aggregate_id == "scope-1")
            )
            .scalars()
            .all()
        )
    assert reloaded.user_confirmed_scope is False
    assert [e.event_type for e in events] == [EVENT_SCOPE_PROPOSED]


def test_s4_confirmation_requires_user_confirmed_s1(tmp_path):
    _, session_factory = _fresh_database(tmp_path)
    artifact_root = tmp_path / "artifacts"

    with session_factory() as session:
        propose_natural_language_spec(
            session,
            project_id="p-1",
            spec=GOLDEN_S1,
            artifact_root=artifact_root,
            spec_id="spec-1",
        )
        propose_research_scope_spec(
            session,
            project_id="p-1",
            scope=GOLDEN_S4,
            artifact_root=artifact_root,
            scope_id="scope-1",
        )
        with pytest.raises(DomainError) as exc_info:
            confirm_research_scope_spec(
                session,
                scope_id="scope-1",
                s1_spec_id="spec-1",
                actor=ProvenanceType.USER_DECISION,
                user_event_id="uev-s4",
                artifact_root=artifact_root,
            )
        assert exc_info.value.error_code == "CONFIRMATION_REQUIRES_USER_EVENT"
        session.commit()

    with session_factory() as session:
        scope = load_research_scope_spec(session, "scope-1", artifact_root=artifact_root)
        binding_events = (
            session.execute(
                select(DomainEventRecord).where(
                    DomainEventRecord.aggregate_type == RESEARCH_SPEC_AGGREGATE_TYPE
                )
            )
            .scalars()
            .all()
        )
    assert scope.user_confirmed_scope is False
    assert binding_events == []


def test_s4_confirmation_binds_s1_s4_hashes(tmp_path):
    _, session_factory = _fresh_database(tmp_path)
    artifact_root = tmp_path / "artifacts"
    _persist_complete_pipeline(session_factory, artifact_root)

    with session_factory() as session:
        spec = load_natural_language_spec(session, "spec-1", artifact_root=artifact_root)
        scope = load_research_scope_spec(session, "scope-1", artifact_root=artifact_root)
        expected_s1_hash = sha256_hex(
            spec.model_dump(exclude={"assistant_proposed", "user_confirmed"})
        )
        expected_scope_hash = sha256_hex(scope.model_dump(exclude={"user_confirmed_scope"}))
        expected_content_hash = ResearchSpec(
            project_id="p-1",
            version=1,
            s1_natural_language_spec=spec.model_dump(
                exclude={"assistant_proposed", "user_confirmed"}
            ),
            s4_scope_spec=scope.model_dump(exclude={"user_confirmed_scope"}),
            user_confirmed=True,
        ).content_hash

        scope_event = session.execute(
            select(DomainEventRecord).where(
                DomainEventRecord.aggregate_id == "scope-1",
                DomainEventRecord.event_type == EVENT_SCOPE_CONFIRMED,
            )
        ).scalar_one()
        binding_event = session.execute(
            select(DomainEventRecord).where(
                DomainEventRecord.aggregate_id == "rs-1",
                DomainEventRecord.event_type == EVENT_RESEARCH_SPEC_BOUND,
            )
        ).scalar_one()
        scope_artifact = session.get(ArtifactRecord, scope_event.event_payload_artifact_id)
        binding_artifact = session.get(ArtifactRecord, binding_event.event_payload_artifact_id)
        assert scope_artifact is not None and binding_artifact is not None
        scope_payload = (artifact_root / scope_artifact.relative_path).read_text(encoding="utf-8")
        binding_payload = (artifact_root / binding_artifact.relative_path).read_text(
            encoding="utf-8"
        )

    assert scope.user_confirmed_scope is True
    assert "USER_DECISION" in scope_payload
    assert "uev-s4" in scope_payload
    assert expected_s1_hash in scope_payload
    assert expected_scope_hash in scope_payload
    assert expected_s1_hash in binding_payload
    assert expected_scope_hash in binding_payload
    assert expected_content_hash in binding_payload


def test_s4_tampered_confirmation_hash_blocks_replay(tmp_path):
    _, session_factory = _fresh_database(tmp_path)
    artifact_root = tmp_path / "artifacts"

    with session_factory() as session:
        propose_research_scope_spec(
            session,
            project_id="p-1",
            scope=GOLDEN_S4,
            artifact_root=artifact_root,
            scope_id="scope-1",
        )
        event = DomainEvent(
            aggregate_type=SCOPE_AGGREGATE_TYPE,
            aggregate_id="scope-1",
            event_type=EVENT_SCOPE_CONFIRMED,
            payload={
                "scope_id": "scope-1",
                "actor": ProvenanceType.USER_DECISION.value,
                "user_event_id": "uev-bad",
                "confirmed_at": "2026-08-16T00:00:00+00:00",
                "scope_hash": "0" * 64,
                "s1_spec_id": "spec-1",
                "s1_hash": "1" * 64,
            },
            sequence=2,
        )
        append_domain_event(session, event, project_id="p-1", artifact_root=artifact_root)
        session.commit()

    with session_factory() as session, pytest.raises(DomainError) as exc_info:
        load_research_scope_spec(session, "scope-1", artifact_root=artifact_root)
    assert exc_info.value.error_code == "CONTENT_HASH_MISMATCH"


# ---------------------------------------------------------------------------
# NATURAL_LANGUAGE_DESIGN_READY
# ---------------------------------------------------------------------------


def test_design_gate_from_events_requires_binding_then_passes(tmp_path):
    _, session_factory = _fresh_database(tmp_path)
    artifact_root = tmp_path / "artifacts"
    _persist_complete_pipeline(session_factory, artifact_root, confirm_s4=False)

    with session_factory() as session:
        status, issues = evaluate_natural_language_design_ready_from_events(
            session,
            seed_id="seed-1",
            spec_id="spec-1",
            mechanism_id="sketch-1",
            prior_work_id="prior-1",
            scope_id="scope-1",
            artifact_root=artifact_root,
        )
    assert status is StageGateStatus.BLOCKED
    assert any("hash 未绑定" in issue for issue in issues)

    with session_factory() as session:
        confirm_research_scope_spec(
            session,
            scope_id="scope-1",
            s1_spec_id="spec-1",
            actor=ProvenanceType.USER_DECISION,
            user_event_id="uev-s4",
            artifact_root=artifact_root,
            research_spec_id="rs-1",
        )
        session.commit()

    with session_factory() as session:
        status, issues = evaluate_natural_language_design_ready_from_events(
            session,
            seed_id="seed-1",
            spec_id="spec-1",
            mechanism_id="sketch-1",
            prior_work_id="prior-1",
            scope_id="scope-1",
            artifact_root=artifact_root,
        )
    assert status is StageGateStatus.PASS
    assert issues == ()


def test_design_gate_partial_when_critical_fields_or_ambiguities_remain():
    confirmed_s1 = GOLDEN_S1.model_copy(update={"user_confirmed": True})
    confirmed_s4 = GOLDEN_S4.model_copy(update={"user_confirmed_scope": True})
    s4_hash = sha256_hex(confirmed_s4.model_dump(exclude={"user_confirmed_scope"}))

    partial_s1 = confirmed_s1.model_copy(update={"target_applications": []})
    status, issues = evaluate_natural_language_design_ready(
        seed=GOLDEN_SEED,
        spec=partial_s1,
        mechanism=GOLDEN_S2,
        prior_work=GOLDEN_S3,
        scope=confirmed_s4,
        s1_hash=sha256_hex(partial_s1.model_dump(exclude={"assistant_proposed", "user_confirmed"})),
        s4_hash=s4_hash,
    )
    assert status is StageGateStatus.PARTIAL
    assert any("target_applications" in issue for issue in issues)

    ambiguous_s1 = confirmed_s1.model_copy(update={"ambiguous_terms": ["未解决歧义"]})
    status, issues = evaluate_natural_language_design_ready(
        seed=GOLDEN_SEED,
        spec=ambiguous_s1,
        mechanism=GOLDEN_S2,
        prior_work=GOLDEN_S3,
        scope=confirmed_s4,
        s1_hash=sha256_hex(
            ambiguous_s1.model_dump(exclude={"assistant_proposed", "user_confirmed"})
        ),
        s4_hash=s4_hash,
    )
    assert status is StageGateStatus.PARTIAL
    assert any("Critical 歧义" in issue for issue in issues)


def test_derive_persists_project_lifecycle_once(tmp_path):
    _, session_factory = _fresh_database(tmp_path)
    artifact_root = tmp_path / "artifacts"

    with session_factory() as session:
        create_project(
            session,
            name="M2.2 golden",
            description="trace scope",
            artifact_root=artifact_root,
            project_id="p-1",
        )
        session.commit()

    _persist_complete_pipeline(session_factory, artifact_root)

    with session_factory() as session:
        status, issues = derive_natural_language_design_ready(
            session,
            project_id="p-1",
            seed_id="seed-1",
            spec_id="spec-1",
            mechanism_id="sketch-1",
            prior_work_id="prior-1",
            scope_id="scope-1",
            artifact_root=artifact_root,
        )
        session.commit()
    assert status is StageGateStatus.PASS
    assert issues == ()

    with session_factory() as session:
        project = load_project(session, "p-1", artifact_root=artifact_root)
        project_events = (
            session.execute(
                select(DomainEventRecord).where(
                    DomainEventRecord.aggregate_type == "Project",
                    DomainEventRecord.aggregate_id == "p-1",
                )
            )
            .scalars()
            .all()
        )
    assert project is not None
    assert project.lifecycle_status is ProjectLifecycleStatus.NATURAL_LANGUAGE_DESIGN_READY
    assert [event.event_type for event in project_events] == [
        "ProjectCreated",
        "ProjectLifecycleChanged",
    ]

    with session_factory() as session:
        status, _ = derive_natural_language_design_ready(
            session,
            project_id="p-1",
            seed_id="seed-1",
            spec_id="spec-1",
            mechanism_id="sketch-1",
            prior_work_id="prior-1",
            scope_id="scope-1",
            artifact_root=artifact_root,
        )
        session.commit()
        project = load_project(session, "p-1", artifact_root=artifact_root)
        project_events = (
            session.execute(
                select(DomainEventRecord).where(
                    DomainEventRecord.aggregate_type == "Project",
                    DomainEventRecord.aggregate_id == "p-1",
                )
            )
            .scalars()
            .all()
        )
    assert status is StageGateStatus.PASS
    assert project.lifecycle_status is ProjectLifecycleStatus.NATURAL_LANGUAGE_DESIGN_READY
    assert len(project_events) == 2


# ---------------------------------------------------------------------------
# Prompt assets and stage contracts
# ---------------------------------------------------------------------------


def test_prompt_assets_have_required_sections():
    expected_fields = {
        "s2_mechanism_sketch.md": ("prompt_key: s2_mechanism_sketch", "inputs", "state_change"),
        "s3_prior_work_map.md": (
            "prompt_key: s3_prior_work_map",
            "academic",
            "engineering",
        ),
        "s4_research_scope_spec.md": (
            "prompt_key: s4_research_scope_spec",
            "main_question",
            "user_confirmed_scope",
        ),
    }
    for filename, needles in expected_fields.items():
        content = (PROMPTS_DIR / filename).read_text(encoding="utf-8")
        assert "version: 1.0.0" in content
        assert "禁止行为" in content
        for needle in needles:
            assert needle in content


def test_stage_contracts_match_blueprint():
    assert S2_STAGE_CONTRACT.stage_id is StageId.S2
    assert S2_STAGE_CONTRACT.output_artifact_type == "MechanismSketch"
    assert "invariants" in S2_STAGE_CONTRACT.required_fields
    assert S2_STAGE_CONTRACT.allowed_next_stages == (StageId.S3,)
    assert any("不把相关性" in item for item in S2_STAGE_CONTRACT.pass_criteria)

    assert S3_STAGE_CONTRACT.stage_id is StageId.S3
    assert S3_STAGE_CONTRACT.output_artifact_type == "PriorWorkMap"
    assert "search_queries" in S3_STAGE_CONTRACT.required_fields
    assert "metadata_verified" in S3_STAGE_CONTRACT.required_fields
    assert S3_STAGE_CONTRACT.allowed_next_stages == (StageId.S4,)
    assert any("外部源验证" in item for item in S3_STAGE_CONTRACT.pass_criteria)

    assert S4_STAGE_CONTRACT.stage_id is StageId.S4
    assert S4_STAGE_CONTRACT.output_artifact_type == "ResearchScopeSpec"
    assert "user_confirmed_scope" in S4_STAGE_CONTRACT.required_fields
    assert S4_STAGE_CONTRACT.allowed_next_stages == ()
    assert S4_STAGE_CONTRACT.rollback_targets == (StageId.S1, StageId.S3)
    assert any("中心主张有证据需求" in item for item in S4_STAGE_CONTRACT.pass_criteria)
