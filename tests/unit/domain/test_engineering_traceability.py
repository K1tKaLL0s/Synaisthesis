"""M2.8 domain tests for traceability, requirements, architecture and publication."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from synaisthesis.domain.architecture import (
    ArchitectureBaseline,
    ArchitectureComponent,
    ArchitectureDecisionRecord,
    ArchitectureDiagram,
    ArchitectureReviewBinding,
    DataContractSet,
    DeploymentAndOperationsDesign,
    InterfaceContractSet,
    StateAndFailureModel,
    ThreatModel,
    architecture_review_blockers,
)
from synaisthesis.domain.engineering import (
    EngineeringChangeKind,
    EngineeringDeliveryStatus,
    EngineeringStageId,
    engineering_regression_check,
)
from synaisthesis.domain.errors import DomainError
from synaisthesis.domain.publication import (
    AUTHOR_INPUT_NEEDS,
    AUTHOR_INPUT_PROVIDED,
    ClaimEvidenceEntry,
    ClaimEvidenceMatrix,
    ClaimStatus,
    EngineeringEvidenceTier,
    EngineeringManuscriptAuditStatus,
    EngineeringMasterManuscript,
    EngineeringPaperType,
    VenueComplianceEntry,
    VenueComplianceMatrix,
    VenueComplianceStatus,
    compliance_blockers,
    manuscript_claim_blockers,
    master_manuscript_blockers,
    paper_type_allowed_by_evidence,
)
from synaisthesis.domain.requirements import (
    AcceptanceCriteriaCatalog,
    AcceptanceCriterion,
    DecisionStatus,
    EngineeringRequirement,
    QualityAttributeScenario,
    QualityAttributeScenarioSet,
    RequirementPriority,
    RequirementsBaseline,
    RequirementStatus,
    RequirementType,
    SecurityPrivacyComplianceObligation,
    SecurityPrivacyComplianceObligationSet,
    UnresolvedDecision,
    UnresolvedDecisionRegister,
    VerificationMethod,
    acceptance_catalog_blockers,
    has_measurable_acceptance,
    requirements_baseline_blockers,
    unresolved_decision_blockers,
)
from synaisthesis.domain.traceability import (
    RequirementsTraceabilityMatrix,
    TraceabilityEdge,
    TraceableElementType,
    TraceRelation,
    ValidationPlan,
    ValidationReport,
    ValidationReportStatus,
    VerificationPlan,
    VerificationReport,
    VerificationReportStatus,
    traceability_coverage,
)

NOW = datetime(2026, 8, 17, 2, 0, 0, tzinfo=UTC)
SPEC_HASH = "s" * 64
CONOPS_HASH = "c" * 64


# ---------------------------------------------------------------------------
# ENG2 requirements (03B section 5)
# ---------------------------------------------------------------------------


def _req(
    req_id: str = "R1",
    *,
    statement: str = "系统在 1 秒内返回结果",
    threshold: str | None = "1",
    priority: RequirementPriority = RequirementPriority.CRITICAL,
    source_refs: tuple[str, ...] = ("intent-1",),
    status: RequirementStatus = RequirementStatus.ACTIVE,
    conflict_refs: tuple[str, ...] = (),
    acceptance: str = "latency <= 1s",
) -> EngineeringRequirement:
    return EngineeringRequirement(
        requirement_id=req_id,
        type=RequirementType.QUALITY,
        statement=statement,
        source_refs=source_refs,
        priority=priority,
        rationale="why",
        precondition="ready",
        inputs=(),
        expected_behavior_output="result",
        measurement_method="latency",
        unit="s",
        threshold=threshold,
        tolerance=None,
        verification_method=VerificationMethod.TEST,
        acceptance_criterion=acceptance,
        owner="team",
        dependency_refs=(),
        conflict_refs=conflict_refs,
        status=status,
    )


def test_vague_requirement_without_threshold_is_rejected():
    with pytest.raises(DomainError) as exc_info:
        _req(statement="系统响应要快速", threshold=None)
    assert exc_info.value.error_code == "REQUIREMENT_UNRESOLVED_THRESHOLD"


def test_unresolved_threshold_requires_empty_threshold():
    with pytest.raises(DomainError) as exc_info:
        _req(status=RequirementStatus.UNRESOLVED_THRESHOLD, threshold="1")
    assert exc_info.value.error_code == "REQUIREMENT_INVALID"


def test_measurable_acceptance_helper():
    assert has_measurable_acceptance(threshold="100", acceptance_criterion="x")
    assert has_measurable_acceptance(threshold="true", acceptance_criterion="x")
    assert has_measurable_acceptance(threshold=None, acceptance_criterion="true")
    assert not has_measurable_acceptance(threshold=None, acceptance_criterion="低延迟")


def _baseline(*requirements: EngineeringRequirement, **overrides) -> RequirementsBaseline:
    params = {
        "baseline_id": "rb-1",
        "version": 1,
        "project_id": "p-1",
        "conops_id": "co-1",
        "input_spec_hash": SPEC_HASH,
        "conops_hash": CONOPS_HASH,
        "source_refs_required": ("intent-1",),
        "requirements": requirements,
    }
    params.update(overrides)
    return RequirementsBaseline(**params)


def test_baseline_blocks_incomplete_source_coverage():
    baseline = _baseline(
        _req(source_refs=("intent-2",)),
        source_refs_required=("intent-1", "intent-2"),
    )
    blockers = requirements_baseline_blockers(baseline)
    assert any("source_coverage" in blocker for blocker in blockers)


def test_baseline_blocks_critical_without_measurable_acceptance():
    baseline = _baseline(
        _req(
            statement="系统返回结果",
            threshold=None,
            acceptance="低延迟",
        )
    )
    blockers = requirements_baseline_blockers(baseline)
    assert any(
        "critical_requirement_with_numeric_or_boolean_acceptance" in blocker for blocker in blockers
    )


def test_baseline_blocks_critical_conflicts_and_unresolved_thresholds():
    baseline = _baseline(
        _req(conflict_refs=("R2",)),
        _req(req_id="R2"),
    )
    blockers = requirements_baseline_blockers(baseline)
    assert any("unresolved_critical_conflicts" in blocker for blocker in blockers)

    baseline = _baseline(
        _req(status=RequirementStatus.UNRESOLVED_THRESHOLD, threshold=None, acceptance="x")
    )
    blockers = requirements_baseline_blockers(baseline)
    assert any("unresolved_critical_thresholds" in blocker for blocker in blockers)


def test_baseline_passes_when_complete():
    baseline = _baseline(_req())
    assert requirements_baseline_blockers(baseline) == ()


def test_acceptance_catalog_requires_every_requirement():
    catalog = AcceptanceCriteriaCatalog(
        catalog_id="ac-1",
        project_id="p-1",
        baseline_id="rb-1",
        criteria=(
            AcceptanceCriterion(
                criterion_id="ac-1",
                requirement_id="R1",
                acceptance_criterion="latency <= 1s",
                verification_method=VerificationMethod.TEST,
                measurement_method="latency",
                unit="s",
                threshold="1",
                tolerance=None,
            ),
        ),
    )
    baseline = _baseline(_req(), _req(req_id="R2"))
    blockers = acceptance_catalog_blockers(catalog, baseline)
    assert any("R2" in blocker for blocker in blockers)
    full = AcceptanceCriteriaCatalog(
        catalog_id="ac-2",
        project_id="p-1",
        baseline_id="rb-1",
        criteria=(
            AcceptanceCriterion(
                criterion_id="ac-1",
                requirement_id="R1",
                acceptance_criterion="latency <= 1s",
                verification_method=VerificationMethod.TEST,
                measurement_method="latency",
                unit="s",
                threshold="1",
                tolerance=None,
            ),
            AcceptanceCriterion(
                criterion_id="ac-2",
                requirement_id="R2",
                acceptance_criterion="latency <= 2s",
                verification_method=VerificationMethod.TEST,
                measurement_method="latency",
                unit="s",
                threshold="2",
                tolerance=None,
            ),
        ),
    )
    assert acceptance_catalog_blockers(full, baseline) == ()


def test_quality_scenario_requires_threshold_and_evidence():
    with pytest.raises(DomainError) as exc_info:
        QualityAttributeScenario(
            scenario_id="qs-1",
            quality_characteristic="Performance",
            statement="响应快",
            project_threshold="",
            evidence_refs=(),
        )
    assert exc_info.value.error_code == "QUALITY_SCENARIO_INVALID"
    scenario_set = QualityAttributeScenarioSet(
        set_id="qs-1",
        project_id="p-1",
        scenarios=(
            QualityAttributeScenario(
                scenario_id="qs-1",
                quality_characteristic="Performance",
                statement="p95 <= 2s",
                project_threshold="2s",
                evidence_refs=("benchmark-1",),
            ),
        ),
    )
    assert scenario_set.set_id == "qs-1"


def test_ai_obligation_requires_all_ai_fields():
    with pytest.raises(DomainError) as exc_info:
        SecurityPrivacyComplianceObligation(
            obligation_id="ob-1",
            framework="AI",
            responsibility="oversight",
            artifact="report",
            verification="inspection",
            ai_data_source="dataset-1",
            ai_provider_boundary="provider-1",
            ai_known_failures="hallucination",
            ai_human_oversight=None,
            ai_drift=None,
            ai_misuse_scenarios=None,
        )
    assert exc_info.value.error_code == "OBLIGATION_INVALID"
    obligation_set = SecurityPrivacyComplianceObligationSet(
        set_id="sp-1",
        project_id="p-1",
        obligations=(
            SecurityPrivacyComplianceObligation(
                obligation_id="ob-1",
                framework="AI",
                responsibility="oversight",
                artifact="report",
                verification="inspection",
                ai_data_source="dataset-1",
                ai_provider_boundary="provider-1",
                ai_known_failures="hallucination",
                ai_human_oversight="human-in-the-loop",
                ai_drift="monthly check",
                ai_misuse_scenarios="prompt injection",
            ),
        ),
    )
    assert obligation_set.set_id == "sp-1"


def test_unresolved_decision_register_blocks_critical_open():
    register = UnresolvedDecisionRegister(
        register_id="ud-1",
        project_id="p-1",
        decisions=(
            UnresolvedDecision(
                decision_id="d-1",
                description="数据库选择",
                owner="architect",
                critical=True,
            ),
        ),
    )
    assert unresolved_decision_blockers(register)
    resolved = UnresolvedDecisionRegister(
        register_id="ud-2",
        project_id="p-1",
        decisions=(
            UnresolvedDecision(
                decision_id="d-1",
                description="数据库选择",
                owner="architect",
                critical=True,
                status=DecisionStatus.RESOLVED,
            ),
        ),
    )
    assert unresolved_decision_blockers(resolved) == ()


# ---------------------------------------------------------------------------
# Traceability (03B sections 5.3/8.3)
# ---------------------------------------------------------------------------


def _edge(
    edge_id: str,
    from_id: str,
    to_type: TraceableElementType,
    to_id: str,
    relation: TraceRelation = TraceRelation.TRACES_TO,
) -> TraceabilityEdge:
    return TraceabilityEdge(
        edge_id=edge_id,
        project_id="p-1",
        from_type=TraceableElementType.REQUIREMENT,
        from_id=from_id,
        relation=relation,
        to_type=to_type,
        to_id=to_id,
        baseline_version=1,
    )


def test_traceability_coverage_math():
    matrix = RequirementsTraceabilityMatrix(
        matrix_id="tm-1",
        project_id="p-1",
        baseline_version=1,
        edges=(
            _edge("e1", "R1", TraceableElementType.DESIGN, "d-1"),
            _edge("e2", "R1", TraceableElementType.TASK, "t-1"),
            _edge("e3", "R1", TraceableElementType.TEST, "test-1"),
            _edge("e4", "R2", TraceableElementType.DESIGN, "d-2"),
        ),
    )
    coverage = traceability_coverage(
        matrix,
        requirements=("R1", "R2"),
        design_elements=("d-1", "d-2", "d-3"),
        tasks=("t-1",),
        tests=("test-1",),
    )
    assert coverage["requirements_traced_to_design"] == 1.0
    assert coverage["requirements_traced_to_task"] == 0.5
    assert coverage["requirements_traced_to_test"] == 0.5
    assert coverage["design_elements_reachable"] == pytest.approx(2 / 3)
    assert coverage["tasks_reachable"] == 1.0


def test_evidence_relation_requires_receipt():
    with pytest.raises(DomainError) as exc_info:
        TraceabilityEdge(
            edge_id="e1",
            project_id="p-1",
            from_type=TraceableElementType.CLAIM,
            from_id="claim-1",
            relation=TraceRelation.EVIDENCES,
            to_type=TraceableElementType.EVIDENCE,
            to_id="receipt-1",
            baseline_version=1,
            evidence_artifact_id=None,
        )
    assert exc_info.value.error_code == "TRACEABILITY_INVALID"


# ---------------------------------------------------------------------------
# ENG4 architecture and diagrams (03B section 7)
# ---------------------------------------------------------------------------


def _diagram(**overrides) -> ArchitectureDiagram:
    params = {
        "diagram_id": "dg-1",
        "title": "system context",
        "version": 1,
        "input_hash": "i" * 64,
        "legend": "boxes are components",
        "node_edge_semantics": "solid=call",
        "stable_id_mapping": {"n1": "comp-1"},
        "node_component_ids": ("n1",),
        "source_path": "diagrams/context.mmd",
        "source_hash": "s" * 64,
        "rendered_svg_path": "diagrams/context.svg",
        "rendered_svg_hash": "v" * 64,
        "render_receipt": "receipt-1",
    }
    params.update(overrides)
    return ArchitectureDiagram(**params)


def test_diagram_requires_stable_component_ids():
    with pytest.raises(DomainError) as exc_info:
        _diagram(stable_id_mapping={}, node_component_ids=("comp-1",))
    assert exc_info.value.error_code == "DIAGRAM_INVALID"


def test_diagram_requires_rendered_hash_and_receipt():
    with pytest.raises(DomainError) as exc_info:
        _diagram(rendered_svg_hash="", render_receipt="receipt-1")
    assert exc_info.value.error_code == "DIAGRAM_INVALID"


def test_diagram_rejects_broken_links():
    with pytest.raises(DomainError) as exc_info:
        _diagram(broken_link_refs=("n9",))
    assert exc_info.value.error_code == "DIAGRAM_BROKEN_LINKS"


def _arch_baseline(**overrides) -> ArchitectureBaseline:
    params = {
        "baseline_id": "ab-1",
        "version": 1,
        "project_id": "p-1",
        "requirements_baseline_id": "rb-1",
        "requirements_hash": "r" * 64,
        "trade_study_id": "ts-1",
        "trade_study_hash": "t" * 64,
        "components": (
            ArchitectureComponent(
                component_id="comp-1", name="core", responsibilities=("compute",)
            ),
        ),
        "views": {"system_context": "single box"},
        "interface_contracts": (
            InterfaceContractSet(
                interface_id="if-1", schema_ref="openapi.yaml", version_policy="semver"
            ),
        ),
        "data_contracts": (
            DataContractSet(contract_id="dc-1", schema_ref="x.json", lifecycle="immutable"),
        ),
        "state_and_failure_model": StateAndFailureModel(
            model_id="sf-1",
            states=("idle", "running"),
            errors=("timeout",),
            recovery_actions=("retry",),
            idempotency_boundary="event id",
            concurrency_boundary="per project",
        ),
        "threat_model": ThreatModel(
            model_id="th-1",
            trust_boundaries=("local",),
            threats=("tampering",),
            security_controls=("hash verify",),
        ),
        "deployment_and_operations": DeploymentAndOperationsDesign(
            design_id="do-1",
            topology="single node",
            environment="wsl",
            operations_boundary="cli",
            observability_audit_backup_recovery="logs",
            retirement="archive",
        ),
        "adrs": (
            ArchitectureDecisionRecord(
                adr_id="adr-1",
                title="event sourcing",
                status="ACCEPTED",
                decision="events",
                alternatives_considered=("tables",),
                rationale="replay",
                affected_component_ids=("comp-1",),
                irreversible=True,
            ),
        ),
        "diagrams": (_diagram(),),
    }
    params.update(overrides)
    return ArchitectureBaseline(**params)


def test_architecture_review_blockers_for_unmapped_node_and_missing_adr():
    baseline = _arch_baseline(
        diagrams=(_diagram(stable_id_mapping={"n1": "ghost-1"}),),
        adrs=(),
    )
    blockers = architecture_review_blockers(baseline)
    assert any("ghost-1" in blocker for blocker in blockers)
    assert any("ADR" in blocker for blocker in blockers)


def test_architecture_review_passes_and_binding_matches():
    baseline = _arch_baseline()
    assert architecture_review_blockers(baseline) == ()
    binding = ArchitectureReviewBinding(
        requirements_hash=baseline.requirements_hash,
        trade_study_hash=baseline.trade_study_hash,
        architecture_hash=baseline.artifact_hash or "",
    )
    assert binding.matches(baseline)
    stale = ArchitectureReviewBinding(
        requirements_hash="0" * 64,
        trade_study_hash=baseline.trade_study_hash,
        architecture_hash=baseline.artifact_hash or "",
    )
    assert not stale.matches(baseline)


# ---------------------------------------------------------------------------
# ENG6 V&V (03B section 9)
# ---------------------------------------------------------------------------


def test_verification_report_pass_requires_real_receipt():
    with pytest.raises(DomainError) as exc_info:
        VerificationReport(
            report_id="vr-1",
            plan_id="vp-1",
            receipt_id=None,
            tool="pytest",
            version="8",
            environment="wsl",
            random_seed=None,
            status=VerificationReportStatus.PASS,
        )
    assert exc_info.value.error_code == "EVIDENCE_RECEIPT_REQUIRED"
    plan = VerificationPlan(
        plan_id="vp-1",
        requirement_id="R1",
        method=VerificationMethod.TEST,
        acceptance_criteria_ref="ac-1",
        planned_receipt_kind="pytest receipt",
    )
    assert plan.plan_id == "vp-1"


def test_validation_plan_and_report():
    plan = ValidationPlan(
        plan_id="vap-1",
        conops_scenario_refs=("sc-1",),
        pre_registered_success_metrics=("p50 latency < 1s",),
        representative_user_refs=("u-1",),
    )
    assert plan.plan_id == "vap-1"
    with pytest.raises(DomainError) as exc_info:
        ValidationPlan(
            plan_id="vap-2",
            conops_scenario_refs=(),
            pre_registered_success_metrics=(),
            representative_user_refs=(),
        )
    assert exc_info.value.error_code == "VALIDATION_PLAN_INVALID"
    with pytest.raises(DomainError) as exc_info:
        ValidationReport(
            report_id="var-1",
            plan_id="vap-1",
            scenario_refs=("sc-1",),
            receipt_id=None,
            results=("ok",),
            status=ValidationReportStatus.PASS,
        )
    assert exc_info.value.error_code == "EVIDENCE_RECEIPT_REQUIRED"


# ---------------------------------------------------------------------------
# ENG8/ENG9 publication (03B sections 11-12)
# ---------------------------------------------------------------------------


def test_paper_type_allowed_by_evidence():
    assert paper_type_allowed_by_evidence(
        EngineeringPaperType.DESIGN_ARTICLE, EngineeringEvidenceTier.BLUEPRINT_ONLY
    )
    assert not paper_type_allowed_by_evidence(
        EngineeringPaperType.SYSTEMS_ARTICLE, EngineeringEvidenceTier.BLUEPRINT_ONLY
    )
    assert paper_type_allowed_by_evidence(
        EngineeringPaperType.SYSTEMS_ARTICLE,
        EngineeringEvidenceTier.PROTOTYPE_ENGINEERING_VERIFIED,
    )
    assert paper_type_allowed_by_evidence(
        EngineeringPaperType.FULL_ENGINEERING_RESEARCH_ARTICLE,
        EngineeringEvidenceTier.PROTOTYPE_VV_VERIFIED,
    )
    assert paper_type_allowed_by_evidence(
        EngineeringPaperType.RESEARCH_SOFTWARE_ARTICLE,
        EngineeringEvidenceTier.MATURE_OPEN_SOURCE,
    )


def test_claim_supported_requires_receipt():
    with pytest.raises(DomainError) as exc_info:
        ClaimEvidenceEntry(
            claim_id="claim-1",
            statement="系统已验证",
            source_requirement_id="R1",
            design_element_id="d-1",
            evidence_receipt_id=None,
            figure_table_ref=None,
            citation_ref=None,
            status=ClaimStatus.SUPPORTED,
        )
    assert exc_info.value.error_code == "MANUSCRIPT_CLAIM_UNSUPPORTED"


def test_manuscript_claim_blockers_detect_unsupported_completion_claims():
    matrix = ClaimEvidenceMatrix(
        matrix_id="cem-1",
        project_id="p-1",
        entries=(
            ClaimEvidenceEntry(
                claim_id="claim-1",
                statement="结果表明系统延迟优于基线",
                source_requirement_id="R1",
                design_element_id="d-1",
                evidence_receipt_id=None,
                figure_table_ref=None,
                citation_ref=None,
            ),
            ClaimEvidenceEntry(
                claim_id="claim-2",
                statement="蓝图覆盖所有关键需求",
                source_requirement_id="R1",
                design_element_id="d-1",
                evidence_receipt_id="receipt-1",
                figure_table_ref="fig-1",
                citation_ref="ref-1",
            ),
        ),
    )
    blockers = manuscript_claim_blockers(matrix, ("claim-1", "claim-2"))
    assert any("claim-1" in blocker for blocker in blockers)
    supported = matrix.entry("claim-2")
    assert supported is not None and supported.evidence_receipt_id == "receipt-1"


def _manuscript(**overrides) -> EngineeringMasterManuscript:
    params = {
        "manuscript_id": "ms-1",
        "version": 1,
        "project_id": "p-1",
        "paper_type": EngineeringPaperType.DESIGN_ARTICLE,
        "evidence_tier": EngineeringEvidenceTier.BLUEPRINT_ONLY,
        "title": "A design",
        "abstract": "abstract",
        "keywords": ("design",),
        "statement_of_need": "need",
        "related_work_neighbors": ("n1",),
        "requirements_conops_design": "section",
        "method_architecture": "section",
        "vv_methods": "section",
        "results": "no results",
        "comparison_with_baseline": "none",
        "threats_limitations": "limits",
        "application_extension": "none",
        "security_privacy_ethics": "none",
        "data_availability": "none",
        "reproducibility_instructions": "steps",
        "conclusion": "conclusion",
        "references": ("r1",),
        "author_contributions": AUTHOR_INPUT_NEEDS,
        "ai_use_disclosure": AUTHOR_INPUT_NEEDS,
        "funding": AUTHOR_INPUT_NEEDS,
        "conflicts": AUTHOR_INPUT_NEEDS,
        "acknowledgements": AUTHOR_INPUT_NEEDS,
        "author_input_status": {
            field: AUTHOR_INPUT_NEEDS
            for field in (
                "author_contributions",
                "ai_use_disclosure",
                "funding",
                "conflicts",
                "acknowledgements",
            )
        },
        "claim_ids": ("claim-2",),
    }
    params.update(overrides)
    return EngineeringMasterManuscript(**params)


def test_manuscript_rejects_fabricated_author_input():
    with pytest.raises(DomainError) as exc_info:
        _manuscript(
            author_contributions="设计并实现",
            author_input_status={"author_contributions": AUTHOR_INPUT_NEEDS},
        )
    assert exc_info.value.error_code == "MANUSCRIPT_AUTHOR_INPUT_INVALID"
    provided = _manuscript(
        author_contributions="设计并实现",
        author_input_status={
            "author_contributions": AUTHOR_INPUT_PROVIDED,
            "ai_use_disclosure": AUTHOR_INPUT_NEEDS,
            "funding": AUTHOR_INPUT_NEEDS,
            "conflicts": AUTHOR_INPUT_NEEDS,
            "acknowledgements": AUTHOR_INPUT_NEEDS,
        },
    )
    assert provided.master_hash is not None and len(provided.master_hash) == 64


def test_manuscript_rejects_paper_type_beyond_evidence_tier():
    with pytest.raises(DomainError) as exc_info:
        _manuscript(paper_type=EngineeringPaperType.SYSTEMS_ARTICLE)
    assert exc_info.value.error_code == "MANUSCRIPT_PAPER_TYPE_INVALID"


def test_master_manuscript_blockers_require_clean_audit():
    matrix = ClaimEvidenceMatrix(
        matrix_id="cem-1",
        project_id="p-1",
        entries=(
            ClaimEvidenceEntry(
                claim_id="claim-2",
                statement="蓝图覆盖所有关键需求",
                source_requirement_id="R1",
                design_element_id="d-1",
                evidence_receipt_id="receipt-1",
                figure_table_ref="fig-1",
                citation_ref="ref-1",
            ),
        ),
    )
    manuscript = _manuscript()
    blockers = master_manuscript_blockers(manuscript, matrix)
    assert any("审计" in blocker for blocker in blockers)
    audited = _manuscript(audit_status=EngineeringManuscriptAuditStatus.AUDITED_CLEAN)
    assert master_manuscript_blockers(audited, matrix) == ()


def test_compliance_matrix_statuses():
    with pytest.raises(DomainError) as exc_info:
        VenueComplianceEntry(
            requirement_id="template",
            status=VenueComplianceStatus.PASS,
            evidence_ref=None,
        )
    assert exc_info.value.error_code == "COMPLIANCE_MATRIX_INVALID"
    matrix = VenueComplianceMatrix(
        matrix_id="cm-1",
        project_id="p-1",
        profile_id="ENG_IEEE_TSE",
        entries=(
            VenueComplianceEntry(
                requirement_id="template",
                status=VenueComplianceStatus.PASS,
                evidence_ref="section 3",
            ),
            VenueComplianceEntry(
                requirement_id="ethics",
                status=VenueComplianceStatus.FAIL,
                evidence_ref=None,
            ),
            VenueComplianceEntry(
                requirement_id="guide",
                status=VenueComplianceStatus.STALE_GUIDANCE,
                evidence_ref=None,
            ),
        ),
    )
    blockers = compliance_blockers(matrix)
    assert any("FAIL" in blocker for blocker in blockers)
    assert any("STALE_GUIDANCE" in blocker for blocker in blockers)
    clean = VenueComplianceMatrix(
        matrix_id="cm-2",
        project_id="p-1",
        profile_id="ENG_ARXIV_PREPRINT",
        entries=(
            VenueComplianceEntry(
                requirement_id="template",
                status=VenueComplianceStatus.PASS,
                evidence_ref="section 3",
            ),
            VenueComplianceEntry(
                requirement_id="preprint",
                status=VenueComplianceStatus.NOT_APPLICABLE,
                evidence_ref=None,
            ),
        ),
    )
    assert compliance_blockers(clean) == ()


# ---------------------------------------------------------------------------
# Regression (03B section 14) — traceability-facing cases
# ---------------------------------------------------------------------------


def test_regression_for_upstream_changes():
    result = engineering_regression_check((EngineeringChangeKind.S1_S4_CORE_SEMANTICS,))
    assert result.requires_reentry
    assert result.earliest_rollback_stage is None
    assert result.status is EngineeringDeliveryStatus.NEEDS_REGRESSION

    result = engineering_regression_check((EngineeringChangeKind.STAKEHOLDER_OR_CONOPS,))
    assert result.earliest_rollback_stage is EngineeringStageId.ENG1

    result = engineering_regression_check((EngineeringChangeKind.EVIDENCE_REVOCATION_OR_LICENSE,))
    assert result.earliest_rollback_stage is EngineeringStageId.ENG6
