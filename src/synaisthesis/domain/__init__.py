"""Domain model primitives for Synaisthesis.

This layer is framework-free and must stay free of web, database, MCP and LLM
dependencies. See tests/unit/domain/test_primitives.py for the enforced
layering invariant.
"""

from synaisthesis.domain.engineering import EngineeringStageId
from synaisthesis.domain.enums import (
    EvidenceStatus,
    EvidenceStrength,
    EvidenceType,
    IndependenceStatus,
    ProgressKind,
    ProjectLifecycleStatus,
    ProvenanceType,
    StageGateStatus,
    StageId,
    StrictStrEnum,
)
from synaisthesis.domain.errors import ConflictError, DomainError, InvalidEnumValueError
from synaisthesis.domain.event import DomainEvent
from synaisthesis.domain.evidence import Evidence
from synaisthesis.domain.gate import EngineeringGate, EngineeringGateBinding
from synaisthesis.domain.policies import IdempotencyContext, check_expected_version
from synaisthesis.domain.project import Project
from synaisthesis.domain.publication import EngineeringMasterManuscript
from synaisthesis.domain.requirements import EngineeringRequirement
from synaisthesis.domain.research_spec import ResearchSpec
from synaisthesis.domain.revision import Revision
from synaisthesis.domain.stage import StageRun
from synaisthesis.domain.traceability import RequirementsTraceabilityMatrix

__all__ = [
    "ConflictError",
    "DomainError",
    "DomainEvent",
    "EngineeringGate",
    "EngineeringGateBinding",
    "EngineeringMasterManuscript",
    "EngineeringRequirement",
    "EngineeringStageId",
    "Evidence",
    "EvidenceStatus",
    "EvidenceStrength",
    "EvidenceType",
    "IdempotencyContext",
    "IndependenceStatus",
    "InvalidEnumValueError",
    "ProgressKind",
    "Project",
    "ProjectLifecycleStatus",
    "ProvenanceType",
    "RequirementsTraceabilityMatrix",
    "ResearchSpec",
    "Revision",
    "StageGateStatus",
    "StageId",
    "StageRun",
    "StrictStrEnum",
    "check_expected_version",
]
