"""Domain model primitives for Synaisthesis.

This layer is framework-free and must stay free of web, database, MCP and LLM
dependencies. See tests/unit/domain/test_primitives.py for the enforced
layering invariant.
"""

from synaisthesis.domain.enums import (
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
from synaisthesis.domain.policies import IdempotencyContext, check_expected_version

__all__ = [
    "ConflictError",
    "DomainError",
    "DomainEvent",
    "EvidenceStrength",
    "EvidenceType",
    "IdempotencyContext",
    "IndependenceStatus",
    "InvalidEnumValueError",
    "ProgressKind",
    "ProjectLifecycleStatus",
    "ProvenanceType",
    "StageGateStatus",
    "StageId",
    "StrictStrEnum",
    "check_expected_version",
]
