"""Theory master manuscript domain (03C sections 5-6; M9.2).

The TheoryMasterManuscript carries structured mathematical claims, a proof
dependency graph, theorem/claim -> statement/proof/evidence/citation tracing
and explicit limitations.  THEOREM/LEMMA/PROPOSITION/COROLLARY kinds may only
appear with a non-INCOMPLETE proof status; anything else must be demoted to
CONJECTURE or an explicit conditional statement (03C section 5.2).
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime
from typing import Any

from synaisthesis.domain.enums import StrictStrEnum
from synaisthesis.domain.errors import DomainError
from synaisthesis.domain.event import canonicalize, sha256_hex
from synaisthesis.domain.publication import (
    TheoryEvidenceTier,
    TheoryManuscriptAuditStatus,
)


class TheoryClaimKind(StrictStrEnum):
    """Mathematical manuscript claim kinds (03C, section 5.2)."""

    DEFINITION = "DEFINITION"
    ASSUMPTION = "ASSUMPTION"
    LEMMA = "LEMMA"
    PROPOSITION = "PROPOSITION"
    THEOREM = "THEOREM"
    COROLLARY = "COROLLARY"
    CONJECTURE = "CONJECTURE"
    COUNTEREXAMPLE = "COUNTEREXAMPLE"
    APPLICATION_CLAIM = "APPLICATION_CLAIM"


class ProofStatus(StrictStrEnum):
    """Proof status of one mathematical claim (03C, section 5.2)."""

    COMPLETE = "COMPLETE"
    INCOMPLETE = "INCOMPLETE"


def _canonical_payload(value: Any) -> dict[str, Any]:
    payload = canonicalize(value)
    if not isinstance(payload, dict):
        raise TypeError("theory manuscript payload must canonicalize to an object")
    return payload


def claim_statement_hash(
    *,
    display_statement: str,
    object_domain: str,
    quantifiers: tuple[str, ...],
    assumptions: tuple[str, ...],
    conclusion: str,
) -> str:
    """Normalized statement hash; adaptation may never change it (03C, 7.2)."""
    return sha256_hex(
        {
            "display_statement": display_statement,
            "object_domain": object_domain,
            "quantifiers": list(quantifiers),
            "assumptions": list(assumptions),
            "conclusion": conclusion,
        }
    )


@dataclass(frozen=True, slots=True)
class MathematicalManuscriptClaim:
    """One mathematical claim in the master manuscript (03C, section 5.2)."""

    manuscript_claim_id: str
    kind: TheoryClaimKind
    display_statement: str
    normalized_statement_hash: str
    source_claim_contract_id: str
    object_domain: str
    quantifiers: tuple[str, ...]
    assumptions: tuple[str, ...]
    conclusion: str
    proof_status: ProofStatus
    proof_artifact_ids: tuple[str, ...]
    tool_receipt_ids: tuple[str, ...]
    semantic_status: str
    citation_refs: tuple[str, ...]
    limitations: tuple[str, ...]
    manuscript_locations: tuple[str, ...]

    def __post_init__(self) -> None:
        expected = claim_statement_hash(
            display_statement=self.display_statement,
            object_domain=self.object_domain,
            quantifiers=self.quantifiers,
            assumptions=self.assumptions,
            conclusion=self.conclusion,
        )
        if self.normalized_statement_hash != expected:
            raise DomainError(
                f"claim {self.manuscript_claim_id!r} 的 normalized_statement_hash 与表述内容不符",
                error_code="ARTIFACT_HASH_MISMATCH",
            )
        if (
            self.kind
            in {
                TheoryClaimKind.THEOREM,
                TheoryClaimKind.LEMMA,
                TheoryClaimKind.PROPOSITION,
                TheoryClaimKind.COROLLARY,
            }
            and self.proof_status is ProofStatus.INCOMPLETE
        ):
            raise DomainError(
                f"claim {self.manuscript_claim_id!r} 的 {self.kind.value} 证明未完成；"
                "必须降级为 CONJECTURE/OPEN_PROBLEM 或显式条件陈述",
                error_code="CLAIM_PROOF_INCOMPLETE",
            )
        if not self.citation_refs:
            raise DomainError(
                f"claim {self.manuscript_claim_id!r} 必须带 citation_refs（禁止捏造/缺失引用）",
                error_code="CLAIM_CITATION_MISSING",
            )

    def to_event_payload(self) -> dict[str, Any]:
        return _canonical_payload(asdict(self))


@dataclass(frozen=True, slots=True)
class ProofDependencyGraph:
    """G_proof = (V, E); no undeclared cycles (03C, section 5.3)."""

    nodes: tuple[str, ...]
    edges: tuple[tuple[str, str], ...]
    declared_recursive_pairs: tuple[tuple[str, str], ...] = ()

    def __post_init__(self) -> None:
        node_set = set(self.nodes)
        for source, target in self.edges:
            if source not in node_set or target not in node_set:
                raise DomainError(
                    f"proof edge ({source}, {target}) 引用未声明节点",
                    error_code="PROOF_GRAPH_INVALID",
                )
        declared = set(self.declared_recursive_pairs)
        # DFS cycle check ignoring declared recursive pairs
        visited: set[str] = set()
        active: set[str] = set()

        def visit(node: str) -> bool:
            if node in active:
                return True
            if node in visited:
                return False
            active.add(node)
            for source, target in self.edges:
                if source != node:
                    continue
                if (source, target) in declared:
                    continue
                if visit(target):
                    return True
            active.discard(node)
            visited.add(node)
            return False

        for node in self.nodes:
            if visit(node):
                raise DomainError(
                    "proof dependency graph 存在未声明循环",
                    error_code="PROOF_GRAPH_INVALID",
                )

    def to_event_payload(self) -> dict[str, Any]:
        return _canonical_payload(asdict(self))


@dataclass(frozen=True, slots=True)
class TheoryMasterManuscript:
    """TP1 output (03C, section 5.1)."""

    manuscript_id: str
    version: int
    project_id: str
    evidence_tier: TheoryEvidenceTier
    title: str
    abstract: str
    msc: str
    keywords: tuple[str, ...]
    introduction: str
    related_work: str
    notation_and_preliminaries: str
    definitions_and_assumptions: str
    main_results: str
    proof_architecture: str
    proofs_status: str
    examples_counterexamples: str
    verification_methods_scope: str
    limitations_unresolved_obligations: str
    implications_applications: str
    availability: str
    structured_author_fields: dict[str, str]
    references: tuple[str, ...]
    claims: tuple[MathematicalManuscriptClaim, ...]
    dependency_graph: ProofDependencyGraph
    master_hash: str | None = None
    audit_status: TheoryManuscriptAuditStatus = TheoryManuscriptAuditStatus.NOT_AUDITED
    status: str = "DRAFT"
    created_at: datetime | None = None

    def __post_init__(self) -> None:
        if not self.title.strip() or not self.abstract.strip():
            raise DomainError(
                "theory master manuscript requires title and abstract",
                error_code="THEORY_MANUSCRIPT_INVALID",
            )
        for field_name, value in self.structured_author_fields.items():
            if field_name.endswith(":user_provided"):
                continue
            if (
                value
                and value != "NEEDS_AUTHOR_INPUT"
                and not (self.structured_author_fields.get(field_name + ":user_provided"))
            ):
                raise DomainError(
                    f"作者字段 {field_name!r} 非空但未标记用户提供",
                    error_code="MANUSCRIPT_AUTHOR_INPUT_INVALID",
                )
        expected = sha256_hex(self.content_payload())
        if self.master_hash is not None and self.master_hash != expected:
            raise DomainError(
                "master_hash does not match the manuscript content",
                error_code="ARTIFACT_HASH_MISMATCH",
            )
        object.__setattr__(self, "master_hash", expected)

    def content_payload(self) -> dict[str, Any]:
        payload = asdict(self)
        for key in ("master_hash", "audit_status", "status", "created_at"):
            payload.pop(key, None)
        return _canonical_payload(payload)

    def to_event_payload(self) -> dict[str, Any]:
        return _canonical_payload(asdict(self))

    def statement_hashes(self) -> dict[str, str]:
        return {claim.manuscript_claim_id: claim.normalized_statement_hash for claim in self.claims}


__all__ = [
    "MathematicalManuscriptClaim",
    "ProofDependencyGraph",
    "ProofStatus",
    "TheoryClaimKind",
    "TheoryMasterManuscript",
    "claim_statement_hash",
]
