"""Instruction Delta grading between Codex and the platform (05A, sections 9-12).

Every mutation carries two channels: channel A (the verbatim InstructionCapsule)
and channel B (the structured command). The platform derives its own
interpretation and compares it with the Codex CommandProposal; a Codex
interpretation can never override the verbatim instruction.
"""

from __future__ import annotations

from dataclasses import dataclass

from synaisthesis.domain.enums import StrictStrEnum

#: Fields that must never be silently normalized (05A, section 12).
NO_SILENT_NORMALIZATION_FIELDS: tuple[str, ...] = (
    "loop_rounds",
    "max_cost",
    "max_model_calls",
    "target_project",
    "target_claim",
    "target_revision",
    "prohibitions",
    "autonomy_level",
    "allow_modify_frozen_claim",
    "allow_codex_worker",
    "allow_network",
    "allow_execute_code",
    "stop_conditions",
)

#: Parameter-drift fields (05A, section 11, F3).
_PARAMETER_FIELDS: tuple[str, ...] = (
    "target_project",
    "target_claim",
    "target_revision",
    "loop_rounds",
    "max_cost",
    "max_model_calls",
    "stop_conditions",
    "requested_tools",
    "expected_outputs",
)

#: Permission/budget escalation fields (05A, section 11, F5).
_ESCALATION_FIELDS: tuple[str, ...] = (
    "allow_modify_frozen_claim",
    "allow_codex_worker",
    "allow_network",
    "allow_execute_code",
)


class InstructionDelta(StrictStrEnum):
    """Instruction Delta grades F0-F5 (05A, section 11)."""

    F0_EXACT = "F0"
    F1_PRESENTATIONAL_ONLY = "F1"
    F2_INFERRED_DEFAULT = "F2"
    F3_PARAMETER_DRIFT = "F3"
    F4_SEMANTIC_DRIFT = "F4"
    F5_UNAUTHORIZED_ACTION = "F5"


@dataclass(frozen=True, slots=True)
class StructuredCommand:
    """Structured channel B fields (05A, section 9) plus the section 12 protected fields."""

    operation: str
    target_project: str | None = None
    target_claim: str | None = None
    target_revision: str | None = None
    loop_rounds: int | None = None
    max_cost: float | None = None
    max_model_calls: int | None = None
    autonomy_level: str | None = None
    read_only: bool = False
    allow_modify_frozen_claim: bool = False
    allow_codex_worker: bool = False
    allow_network: bool = False
    allow_execute_code: bool = False
    prohibitions: tuple[str, ...] = ()
    stop_conditions: tuple[str, ...] = ()
    requested_tools: tuple[str, ...] = ()
    expected_outputs: tuple[str, ...] = ()
    constraints: tuple[str, ...] = ()
    unresolved_references: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class CommandProposal(StructuredCommand):
    """Codex's structured interpretation; only a candidate, never the source of truth."""


@dataclass(frozen=True, slots=True)
class PlatformInterpretation(StructuredCommand):
    """The platform's own structured interpretation derived from the InstructionCapsule."""


@dataclass(frozen=True, slots=True)
class DeltaAssessment:
    """Result of comparing a CommandProposal against the PlatformInterpretation."""

    grade: InstructionDelta
    differences: tuple[str, ...]

    @property
    def blocking(self) -> bool:
        """True when a mutation must be blocked (F3 or worse)."""
        return self.grade in {
            InstructionDelta.F3_PARAMETER_DRIFT,
            InstructionDelta.F4_SEMANTIC_DRIFT,
            InstructionDelta.F5_UNAUTHORIZED_ACTION,
        }


def _autonomy_rank(value: str | None) -> int:
    if value is None:
        return 0
    return {
        "A0": 0,
        "A1": 1,
        "A2": 2,
        "A3": 3,
    }.get(value, 0)


def grade_instruction_delta(
    proposal: CommandProposal, interpretation: PlatformInterpretation
) -> DeltaAssessment:
    """Classify the drift between the Codex proposal and the platform interpretation.

    Deterministic mapping (05A, section 11): exact match is F0; parameter/budget/
    target/tool/output/stop changes are F3; omission of a prohibition, turning a
    read-only request into a mutation, or a semantic/permission change is F4;
    permission or autonomy escalation is F5 (unauthorized action).
    """
    differences: list[str] = []
    grade = InstructionDelta.F0_EXACT

    # Read-only request turned into a mutation is semantic drift, not a default.
    if proposal.read_only and not interpretation.read_only:
        differences.append("read_only: 只读请求被改为 mutation")
        grade = InstructionDelta.F4_SEMANTIC_DRIFT

    # Permission / autonomy escalation is an unauthorized action.
    for field in _ESCALATION_FIELDS:
        proposed = bool(getattr(proposal, field))
        interpreted = bool(getattr(interpretation, field))
        if interpreted and not proposed:
            differences.append(f"{field}: Codex 提升了未授权的权限")
            grade = InstructionDelta.F5_UNAUTHORIZED_ACTION
    if _autonomy_rank(interpretation.autonomy_level) > _autonomy_rank(proposal.autonomy_level):
        differences.append(
            f"autonomy_level: {proposal.autonomy_level!r} -> {interpretation.autonomy_level!r}"
        )
        grade = InstructionDelta.F5_UNAUTHORIZED_ACTION

    # A prohibition present in the proposal but dropped is semantic drift.
    missing_prohibitions = set(proposal.prohibitions) - set(interpretation.prohibitions)
    if missing_prohibitions:
        differences.append("prohibitions: 遗漏否定约束 " + ", ".join(sorted(missing_prohibitions)))
        grade = InstructionDelta.F4_SEMANTIC_DRIFT

    # Operation drift beyond the read-only case is semantic drift.
    if proposal.operation != interpretation.operation and not (
        proposal.read_only and not interpretation.read_only
    ):
        differences.append(f"operation: {proposal.operation!r} -> {interpretation.operation!r}")
        grade = InstructionDelta.F4_SEMANTIC_DRIFT

    # Parameter drift on the protected fields.
    for field in _PARAMETER_FIELDS:
        proposed = getattr(proposal, field)
        interpreted = getattr(interpretation, field)
        if proposed != interpreted:
            differences.append(f"{field}: {proposed!r} -> {interpreted!r}")
            if grade.value < InstructionDelta.F3_PARAMETER_DRIFT.value:
                grade = InstructionDelta.F3_PARAMETER_DRIFT

    # Non-protected differences are inferred defaults, never blocking on their own.
    if not differences:
        if _non_protected_differs(proposal, interpretation):
            return DeltaAssessment(InstructionDelta.F2_INFERRED_DEFAULT, ())
        return DeltaAssessment(InstructionDelta.F0_EXACT, ())
    return DeltaAssessment(grade, tuple(differences))


def _non_protected_differs(proposal: StructuredCommand, interpretation: StructuredCommand) -> bool:
    for field in ("constraints", "unresolved_references"):
        if getattr(proposal, field) != getattr(interpretation, field):
            return True
    return False


def has_unresolved_references(command: StructuredCommand) -> bool:
    """True when the structured command still has unresolved deictic references."""
    return bool(command.unresolved_references)
