"""M2.4A golden tests for the mandatory engineering-route Human Gate."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, inspect

from synaisthesis.application.qualification_service import (
    assess_formalization_feasibility_from_matrices,
    open_formalization_feasibility_gate,
    resolve_engineering_route_decision,
    resolve_formalization_feasibility_decision,
)
from synaisthesis.domain.enums import (
    EngineeringRouteDecision,
    FormalizationFeasibilityDecision,
    GateStatus,
    PredicateVerdict,
    ProvenanceType,
    QualificationGateType,
)
from synaisthesis.domain.errors import DomainError
from synaisthesis.domain.qualification import (
    EngineeringFitPredicates,
    FeasibilityPredicate,
    FeasibilityPredicateMatrix,
    TheoryFitPredicates,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
MIGRATIONS_DIR = REPO_ROOT / "src" / "synaisthesis" / "storage" / "migrations"
PROMPTS_DIR = REPO_ROOT / "src" / "synaisthesis" / "prompts" / "formalization"

NOW = datetime(2026, 8, 16, 18, 30, 0, tzinfo=UTC)


def _pred(predicate_id: str, verdict: PredicateVerdict) -> FeasibilityPredicate:
    return FeasibilityPredicate(
        predicate_id=predicate_id,
        verdict=verdict,
        evidence_refs=(f"S1.{predicate_id.lower()}", "RQ1.neighbor[0]"),
    )


def _matrix(theory_verdict: PredicateVerdict, engineering_verdict: PredicateVerdict):
    return FeasibilityPredicateMatrix(
        theory=TheoryFitPredicates(
            tfo=_pred("TFO", theory_verdict),
            tfr=_pred("TFR", theory_verdict),
            tfc=_pred("TFC", theory_verdict),
            tfw=_pred("TFW", theory_verdict),
            tfp=_pred("TFP", theory_verdict),
        ),
        engineering=EngineeringFitPredicates(
            efs=_pred("EFS", engineering_verdict),
            efi=_pred("EFI", engineering_verdict),
            efa=_pred("EFA", engineering_verdict),
            efm=_pred("EFM", engineering_verdict),
            eff=_pred("EFF", engineering_verdict),
        ),
    )


def _assessment(
    theory_verdict: PredicateVerdict,
    engineering_verdict: PredicateVerdict,
    *,
    assessment_id: str = "fa-golden",
    input_spec_hash: str = "a" * 64,
):
    return assess_formalization_feasibility_from_matrices(
        assessment_id=assessment_id,
        version=1,
        research_spec_id="rs-1",
        input_spec_hash=input_spec_hash,
        neighbor_evidence_set_id="ps-1",
        assessor_session_ids=("session-early", "session-engineering"),
        early_matrix=_matrix(theory_verdict, engineering_verdict),
        engineering_matrix=_matrix(theory_verdict, engineering_verdict),
        public_explanation=("feasibility materials evaluated",),
    )


def test_theory_true_does_not_open_gate():
    assessment = _assessment(PredicateVerdict.PASS, PredicateVerdict.PASS)
    assert open_formalization_feasibility_gate(assessment=assessment, gate_id="g-1") is None
    assessment = _assessment(PredicateVerdict.PASS, PredicateVerdict.FAIL)
    assert open_formalization_feasibility_gate(assessment=assessment, gate_id="g-1") is None


def test_theory_false_engineering_true_opens_only_engineering_route_gate():
    assessment = _assessment(PredicateVerdict.FAIL, PredicateVerdict.PASS)
    gate = open_formalization_feasibility_gate(assessment=assessment, gate_id="g-1")
    assert gate is not None
    assert gate.gate_type is QualificationGateType.ENGINEERING_ROUTE_DECISION
    assert gate.status is GateStatus.OPEN
    assert gate.binding.artifact_hash == assessment.artifact_hash
    assert gate.binding.input_spec_hash == assessment.input_spec_hash


def test_model_actor_cannot_select_engineering_route():
    assessment = _assessment(PredicateVerdict.FAIL, PredicateVerdict.PASS)
    gate = open_formalization_feasibility_gate(assessment=assessment, gate_id="g-1")
    assert gate is not None
    for actor in (ProvenanceType.ASSISTANT_PROPOSAL, ProvenanceType.EXTERNAL_MODEL_IMPORT):
        with pytest.raises(DomainError) as exc_info:
            resolve_engineering_route_decision(
                gate=gate,
                decision=EngineeringRouteDecision.TRY_ENGINEERING_PROJECT.value,
                actor=actor,
                user_event_id=f"model-{actor.value}",
                current_input_spec_hash=assessment.input_spec_hash,
                at=NOW,
                selection_id="ers-model",
            )
        assert exc_info.value.error_code == "CONFIRMATION_REQUIRES_USER_EVENT"


def test_user_try_engineering_project_creates_selection():
    assessment = _assessment(PredicateVerdict.FAIL, PredicateVerdict.PASS)
    gate = open_formalization_feasibility_gate(assessment=assessment, gate_id="g-1")
    assert gate is not None
    resolved, selection = resolve_engineering_route_decision(
        gate=gate,
        decision=EngineeringRouteDecision.TRY_ENGINEERING_PROJECT.value,
        actor=ProvenanceType.USER_DECISION,
        user_event_id="uev-1",
        current_input_spec_hash=assessment.input_spec_hash,
        at=NOW,
        selection_id="ers-1",
    )
    assert resolved.status is GateStatus.RESOLVED
    assert resolved.decision == "TRY_ENGINEERING_PROJECT"
    assert selection is not None
    assert selection.decision is EngineeringRouteDecision.TRY_ENGINEERING_PROJECT
    assert selection.bound_assessment_hash == assessment.artifact_hash
    assert selection.input_spec_hash == assessment.input_spec_hash


def test_other_engineering_route_decisions_do_not_create_selection():
    assessment = _assessment(PredicateVerdict.FAIL, PredicateVerdict.PASS)
    gate = open_formalization_feasibility_gate(assessment=assessment, gate_id="g-1")
    assert gate is not None
    resolved, selection = resolve_engineering_route_decision(
        gate=gate,
        decision=EngineeringRouteDecision.PAUSE.value,
        actor=ProvenanceType.USER_DECISION,
        user_event_id="uev-pause",
        current_input_spec_hash=assessment.input_spec_hash,
        at=NOW,
    )
    assert resolved.status is GateStatus.RESOLVED
    assert resolved.decision == "PAUSE"
    assert selection is None


def test_neither_fit_or_unknown_opens_formalization_feasibility_decision():
    for theory_verdict, engineering_verdict in (
        (PredicateVerdict.FAIL, PredicateVerdict.FAIL),
        (PredicateVerdict.UNKNOWN, PredicateVerdict.PASS),
        (PredicateVerdict.PASS, PredicateVerdict.UNKNOWN),
    ):
        assessment = _assessment(theory_verdict, engineering_verdict)
        gate = open_formalization_feasibility_gate(assessment=assessment, gate_id="g-feas")
        assert gate is not None
        assert gate.gate_type is QualificationGateType.FORMALIZATION_FEASIBILITY_DECISION
        resolved = resolve_formalization_feasibility_decision(
            gate=gate,
            decision=FormalizationFeasibilityDecision.RESEARCH_MORE.value,
            actor=ProvenanceType.USER_DECISION,
            user_event_id="uev-research",
            current_input_spec_hash=assessment.input_spec_hash,
            at=NOW,
        )
        assert resolved.status is GateStatus.RESOLVED


def test_stale_spec_hash_invalidates_old_gate_decision():
    assessment = _assessment(PredicateVerdict.FAIL, PredicateVerdict.PASS)
    gate = open_formalization_feasibility_gate(assessment=assessment, gate_id="g-1")
    assert gate is not None
    with pytest.raises(DomainError) as exc_info:
        resolve_engineering_route_decision(
            gate=gate,
            decision=EngineeringRouteDecision.TRY_ENGINEERING_PROJECT.value,
            actor=ProvenanceType.USER_DECISION,
            user_event_id="uev-stale",
            current_input_spec_hash="b" * 64,
            at=NOW,
            selection_id="ers-stale",
        )
    assert exc_info.value.error_code == "STALE_FEASIBILITY_BINDING"


def test_prompt_assets_have_required_sections():
    for filename, prompt_key in (
        ("feasibility_early_formalizer.md", "feasibility_early_formalizer"),
        ("feasibility_engineering_assessor.md", "feasibility_engineering_assessor"),
    ):
        content = (PROMPTS_DIR / filename).read_text(encoding="utf-8")
        assert f"prompt_key: {prompt_key}" in content
        assert "version: 1.0.0" in content
        assert "禁止行为" in content
        assert "TFO" in content and "EFS" in content


def _alembic_config(db_url: str) -> Config:
    cfg = Config()
    cfg.set_main_option("script_location", str(MIGRATIONS_DIR))
    cfg.set_main_option("sqlalchemy.url", db_url)
    return cfg


def test_migration_0003_role_sessions_upgrade_and_downgrade(tmp_path):
    db_url = f"sqlite:///{tmp_path / 'feasibility.db'}"
    cfg = _alembic_config(db_url)
    command.upgrade(cfg, "0003")
    inspector = inspect(create_engine(db_url))
    columns = {column["name"] for column in inspector.get_columns("role_sessions")}
    assert {
        "id",
        "run_id",
        "round_id",
        "role",
        "model_profile_id",
        "visibility_policy_id",
        "isolated_context_hash",
        "session_status",
    } <= columns
    command.downgrade(cfg, "0002")
    inspector = inspect(create_engine(db_url))
    assert "role_sessions" not in set(inspector.get_table_names())
