"""Engineering bidirectional traceability and V&V records (03B, sections 5/8/9).

The traceability matrix supports the ENG2 and ENG5 coverage gates; V&V
records separate Verification ("built right") from Validation ("right
product") and require real receipts before a PASS may be recorded
(03B, section 9.2).
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

from synaisthesis.domain.enums import StrictStrEnum
from synaisthesis.domain.errors import DomainError
from synaisthesis.domain.event import canonicalize
from synaisthesis.domain.requirements import VerificationMethod


def _canonical_payload(value: Any) -> dict[str, Any]:
    payload = canonicalize(value)
    if not isinstance(payload, dict):
        raise TypeError("traceability payload must canonicalize to an object")
    return payload


class TraceableElementType(StrictStrEnum):
    """Element kinds in a traceability edge (03B, sections 5.3/8.3)."""

    REQUIREMENT = "REQUIREMENT"
    DESIGN = "DESIGN"
    TASK = "TASK"
    TEST = "TEST"
    CONOPS = "CONOPS"
    CLAIM = "CLAIM"
    EVIDENCE = "EVIDENCE"


class TraceRelation(StrictStrEnum):
    """Relation labels for trace edges (06 engineering_trace_edges.relation)."""

    TRACES_TO = "TRACES_TO"
    VERIFIES = "VERIFIES"
    VALIDATES = "VALIDATES"
    EVIDENCES = "EVIDENCES"
    DEPENDS_ON = "DEPENDS_ON"


@dataclass(frozen=True, slots=True)
class TraceabilityEdge:
    """One directed trace edge (06, engineering_trace_edges)."""

    edge_id: str
    project_id: str
    from_type: TraceableElementType
    from_id: str
    relation: TraceRelation
    to_type: TraceableElementType
    to_id: str
    baseline_version: int
    evidence_artifact_id: str | None = None

    def __post_init__(self) -> None:
        if not self.edge_id.strip() or not self.from_id.strip() or not self.to_id.strip():
            raise DomainError(
                "trace edge requires ids",
                error_code="TRACEABILITY_INVALID",
            )
        if self.relation is TraceRelation.EVIDENCES and not self.evidence_artifact_id:
            raise DomainError(
                f"trace edge {self.edge_id!r} 的 EVIDENCES 关系必须绑定证据",
                error_code="TRACEABILITY_INVALID",
            )

    def to_event_payload(self) -> dict[str, Any]:
        return _canonical_payload(asdict(self))


@dataclass(frozen=True, slots=True)
class RequirementsTraceabilityMatrix:
    """ENG2/ENG5 bidirectional traceability matrix (03B, sections 5.3/8.3)."""

    matrix_id: str
    project_id: str
    baseline_version: int
    edges: tuple[TraceabilityEdge, ...]

    def __post_init__(self) -> None:
        seen: set[str] = set()
        for edge in self.edges:
            if edge.edge_id in seen:
                raise DomainError(
                    f"duplicate trace edge {edge.edge_id!r}",
                    error_code="TRACEABILITY_INVALID",
                )
            seen.add(edge.edge_id)

    def to_event_payload(self) -> dict[str, Any]:
        return _canonical_payload(asdict(self))

    def edges_from(
        self,
        *,
        from_type: TraceableElementType,
        from_id: str,
        relation: TraceRelation | None = None,
        to_type: TraceableElementType | None = None,
    ) -> tuple[TraceabilityEdge, ...]:
        return tuple(
            edge
            for edge in self.edges
            if edge.from_type is from_type
            and edge.from_id == from_id
            and (relation is None or edge.relation is relation)
            and (to_type is None or edge.to_type is to_type)
        )

    def edges_to(
        self,
        *,
        to_type: TraceableElementType,
        to_id: str,
        relation: TraceRelation | None = None,
        from_type: TraceableElementType | None = None,
    ) -> tuple[TraceabilityEdge, ...]:
        return tuple(
            edge
            for edge in self.edges
            if edge.to_type is to_type
            and edge.to_id == to_id
            and (relation is None or edge.relation is relation)
            and (from_type is None or edge.from_type is from_type)
        )


def traceability_coverage(
    matrix: RequirementsTraceabilityMatrix,
    *,
    requirements: tuple[str, ...],
    design_elements: tuple[str, ...],
    tasks: tuple[str, ...],
    tests: tuple[str, ...],
) -> dict[str, float]:
    """Return the fraction of requirements traced to design/task/test.

    Coverage is 1.0 only when every requirement has at least one outgoing edge
    to the target element kind (03B, section 8.3).
    """
    traced_to_design = sum(
        1
        for requirement in requirements
        if matrix.edges_from(
            from_type=TraceableElementType.REQUIREMENT,
            from_id=requirement,
            to_type=TraceableElementType.DESIGN,
        )
    )
    traced_to_task = sum(
        1
        for requirement in requirements
        if matrix.edges_from(
            from_type=TraceableElementType.REQUIREMENT,
            from_id=requirement,
            to_type=TraceableElementType.TASK,
        )
    )
    traced_to_test = sum(
        1
        for requirement in requirements
        if matrix.edges_from(
            from_type=TraceableElementType.REQUIREMENT,
            from_id=requirement,
            to_type=TraceableElementType.TEST,
        )
    )
    return {
        "requirements_traced_to_design": (
            traced_to_design / len(requirements) if requirements else 0.0
        ),
        "requirements_traced_to_task": (
            traced_to_task / len(requirements) if requirements else 0.0
        ),
        "requirements_traced_to_test": (
            traced_to_test / len(requirements) if requirements else 0.0
        ),
        "design_elements_reachable": (
            sum(
                1
                for design in design_elements
                if matrix.edges_to(to_type=TraceableElementType.DESIGN, to_id=design)
            )
            / len(design_elements)
            if design_elements
            else 0.0
        ),
        "tasks_reachable": (
            sum(
                1
                for task in tasks
                if matrix.edges_to(to_type=TraceableElementType.TASK, to_id=task)
            )
            / len(tasks)
            if tasks
            else 0.0
        ),
        "tests_reachable": (
            sum(
                1
                for test in tests
                if matrix.edges_to(to_type=TraceableElementType.TEST, to_id=test)
            )
            / len(tests)
            if tests
            else 0.0
        ),
    }


# ---------------------------------------------------------------------------
# ENG6 — V&V records (03B, section 9)
# ---------------------------------------------------------------------------


class VerificationReportStatus(StrictStrEnum):
    """Verification outcome (03B, section 9.3)."""

    PASS = "PASS"
    FAIL = "FAIL"
    BLOCKED = "BLOCKED"


class ValidationReportStatus(StrictStrEnum):
    """Validation outcome (03B, section 9.3)."""

    PASS = "PASS"
    FAIL = "FAIL"
    BLOCKED = "BLOCKED"


@dataclass(frozen=True, slots=True)
class VerificationPlan:
    """One requirement's planned verification (03B, section 9.2)."""

    plan_id: str
    requirement_id: str
    method: VerificationMethod
    acceptance_criteria_ref: str
    planned_receipt_kind: str

    def __post_init__(self) -> None:
        if not self.plan_id.strip() or not self.requirement_id.strip():
            raise DomainError(
                "verification plan requires ids",
                error_code="VERIFICATION_PLAN_INVALID",
            )

    def to_event_payload(self) -> dict[str, Any]:
        return _canonical_payload(asdict(self))


@dataclass(frozen=True, slots=True)
class ValidationPlan:
    """ConOps-based validation plan (03B, section 9.2)."""

    plan_id: str
    conops_scenario_refs: tuple[str, ...]
    pre_registered_success_metrics: tuple[str, ...]
    representative_user_refs: tuple[str, ...]

    def __post_init__(self) -> None:
        if not self.conops_scenario_refs or not self.pre_registered_success_metrics:
            raise DomainError(
                f"validation plan {self.plan_id!r} 必须绑定场景与预注册成功指标",
                error_code="VALIDATION_PLAN_INVALID",
            )

    def to_event_payload(self) -> dict[str, Any]:
        return _canonical_payload(asdict(self))


@dataclass(frozen=True, slots=True)
class VerificationReport:
    """ENG6 verification report with real tool receipt (03B, section 9.3)."""

    report_id: str
    plan_id: str
    receipt_id: str | None
    tool: str
    version: str
    environment: str
    random_seed: str | None
    status: VerificationReportStatus
    corrective_actions: tuple[str, ...] = ()
    residual_risk: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if self.status is VerificationReportStatus.PASS and not self.receipt_id:
            raise DomainError(
                f"verification report {self.report_id!r} 声称 PASS 但没有真实回执",
                error_code="EVIDENCE_RECEIPT_REQUIRED",
            )

    def to_event_payload(self) -> dict[str, Any]:
        return _canonical_payload(asdict(self))


@dataclass(frozen=True, slots=True)
class ValidationReport:
    """ENG6 validation report; PASS requires a real receipt (03B, section 9.3)."""

    report_id: str
    plan_id: str
    scenario_refs: tuple[str, ...]
    receipt_id: str | None
    results: tuple[str, ...]
    status: ValidationReportStatus
    corrective_actions: tuple[str, ...] = ()
    residual_risk: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if self.status is ValidationReportStatus.PASS and not self.receipt_id:
            raise DomainError(
                f"validation report {self.report_id!r} 声称 PASS 但没有真实回执",
                error_code="EVIDENCE_RECEIPT_REQUIRED",
            )

    def to_event_payload(self) -> dict[str, Any]:
        return _canonical_payload(asdict(self))


def verification_report_blockers(report: VerificationReport) -> tuple[str, ...]:
    """A unit-test PASS may not stand in for application validity (03B, 9.2)."""
    if report.status is VerificationReportStatus.PASS and not report.receipt_id:
        return ("Verification PASS 必须绑定真实工具回执",)
    return ()


def validation_report_blockers(report: ValidationReport) -> tuple[str, ...]:
    if report.status is ValidationReportStatus.PASS and not report.receipt_id:
        return ("Validation PASS 必须绑定真实回执",)
    return ()


__all__ = [
    "RequirementsTraceabilityMatrix",
    "TraceRelation",
    "TraceabilityEdge",
    "TraceableElementType",
    "ValidationPlan",
    "ValidationReport",
    "ValidationReportStatus",
    "VerificationPlan",
    "VerificationReport",
    "VerificationReportStatus",
    "traceability_coverage",
    "validation_report_blockers",
    "verification_report_blockers",
]
