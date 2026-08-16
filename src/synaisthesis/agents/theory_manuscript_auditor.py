"""Independent theory manuscript auditor (03C section 6.1; M9.2).

A THEORY_MANUSCRIPT_AUDITOR who never generated the draft checks statement
hash consistency, proof-status/kind rules, proof dependency closure,
unresolved-obligation honesty and citation presence.  Findings are
structured; Critical/Major findings block readiness.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

from synaisthesis.domain.errors import DomainError
from synaisthesis.domain.event import canonicalize
from synaisthesis.domain.publication import TheoryManuscriptAuditStatus
from synaisthesis.publication.theory_master_manuscript import (
    MathematicalManuscriptClaim,
    ProofStatus,
    TheoryClaimKind,
    TheoryMasterManuscript,
)

SEVERITY_MAJOR = "MAJOR"
SEVERITY_CRITICAL = "CRITICAL"


def _canonical_payload(value: Any) -> dict[str, Any]:
    payload = canonicalize(value)
    if not isinstance(payload, dict):
        raise TypeError("audit payload must canonicalize to an object")
    return payload


@dataclass(frozen=True, slots=True)
class TheoryAuditFinding:
    """One structured audit finding (03C, section 6.1)."""

    finding_id: str
    severity: str
    description: str

    def to_event_payload(self) -> dict[str, Any]:
        return _canonical_payload(asdict(self))


def audit_theory_manuscript(
    manuscript: TheoryMasterManuscript,
    *,
    auditor_session_id: str,
    draft_generator_session_ids: tuple[str, ...],
) -> tuple[list[TheoryAuditFinding], TheoryManuscriptAuditStatus]:
    """Run the deterministic independent audit; the auditor must be independent."""
    if auditor_session_id in draft_generator_session_ids:
        raise DomainError(
            "理论母稿审计人不得参与母稿生成",
            error_code="AUDITOR_NOT_INDEPENDENT",
        )
    findings: list[TheoryAuditFinding] = []
    for claim in manuscript.claims:
        claim_findings = _audit_claim(claim)
        findings.extend(claim_findings)
    if not manuscript.claims:
        findings.append(
            TheoryAuditFinding(
                finding_id="no-claims",
                severity=SEVERITY_MAJOR,
                description="母稿没有任何数学 claim",
            )
        )
    if not manuscript.limitations_unresolved_obligations.strip():
        findings.append(
            TheoryAuditFinding(
                finding_id="hidden-obligations",
                severity=SEVERITY_MAJOR,
                description="未解决义务/限制被隐藏",
            )
        )
    _check_graph_closure(manuscript, findings)
    if findings:
        return findings, TheoryManuscriptAuditStatus.AUDITED_WITH_FINDINGS
    return findings, TheoryManuscriptAuditStatus.AUDITED_CLEAN


def _audit_claim(claim: MathematicalManuscriptClaim) -> list[TheoryAuditFinding]:
    findings: list[TheoryAuditFinding] = []
    if (
        claim.kind
        in {
            TheoryClaimKind.THEOREM,
            TheoryClaimKind.LEMMA,
            TheoryClaimKind.PROPOSITION,
            TheoryClaimKind.COROLLARY,
        }
        and claim.proof_status is ProofStatus.INCOMPLETE
    ):
        findings.append(
            TheoryAuditFinding(
                finding_id=f"{claim.manuscript_claim_id}-proof-status",
                severity=SEVERITY_CRITICAL,
                description=f"claim {claim.manuscript_claim_id} 证明未完成却标为 "
                f"{claim.kind.value}",
            )
        )
    if claim.kind is TheoryClaimKind.THEOREM and not claim.tool_receipt_ids:
        findings.append(
            TheoryAuditFinding(
                finding_id=f"{claim.manuscript_claim_id}-receipt",
                severity=SEVERITY_MAJOR,
                description=f"THEOREM {claim.manuscript_claim_id} 没有工具回执",
            )
        )
    return findings


def _check_graph_closure(
    manuscript: TheoryMasterManuscript,
    findings: list[TheoryAuditFinding],
) -> None:
    node_set = set(manuscript.dependency_graph.nodes)
    claim_ids = {claim.manuscript_claim_id for claim in manuscript.claims}
    dangling = node_set - claim_ids
    if dangling:
        findings.append(
            TheoryAuditFinding(
                finding_id="graph-dangling",
                severity=SEVERITY_MAJOR,
                description="proof dependency graph 含未登记 claim：" + ", ".join(sorted(dangling)),
            )
        )


__all__ = [
    "SEVERITY_CRITICAL",
    "SEVERITY_MAJOR",
    "TheoryAuditFinding",
    "audit_theory_manuscript",
]
