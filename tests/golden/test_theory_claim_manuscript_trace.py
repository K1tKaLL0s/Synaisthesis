"""M9.2 golden tests: theory claim/manuscript tracing (03C sections 5-6)."""

from __future__ import annotations

import pytest

from synaisthesis.agents.theory_manuscript_auditor import audit_theory_manuscript
from synaisthesis.domain.errors import DomainError
from synaisthesis.domain.publication import (
    TheoryEvidenceTier,
    TheoryManuscriptAuditStatus,
)
from synaisthesis.publication.theory_master_manuscript import (
    MathematicalManuscriptClaim,
    ProofDependencyGraph,
    ProofStatus,
    TheoryClaimKind,
    TheoryMasterManuscript,
    claim_statement_hash,
)


def _claim(
    claim_id: str,
    *,
    kind: TheoryClaimKind = TheoryClaimKind.THEOREM,
    proof_status: ProofStatus = ProofStatus.COMPLETE,
    statement: str = "∀ A B ∈ M_n，tr(AB)=tr(BA)",
    object_domain: str = "有限矩阵 M_n",
    quantifiers: tuple[str, ...] = ("forall A", "forall B"),
    assumptions: tuple[str, ...] = ("A,B 为方阵",),
    conclusion: str = "tr(AB)=tr(BA)",
    citations: tuple[str, ...] = ("ref-cyclic",),
) -> MathematicalManuscriptClaim:
    return MathematicalManuscriptClaim(
        manuscript_claim_id=claim_id,
        kind=kind,
        display_statement=statement,
        normalized_statement_hash=claim_statement_hash(
            display_statement=statement,
            object_domain=object_domain,
            quantifiers=quantifiers,
            assumptions=assumptions,
            conclusion=conclusion,
        ),
        source_claim_contract_id=f"cc-{claim_id}",
        object_domain=object_domain,
        quantifiers=quantifiers,
        assumptions=assumptions,
        conclusion=conclusion,
        proof_status=proof_status,
        proof_artifact_ids=("proof-1",),
        tool_receipt_ids=("lean-1",)
        if kind
        in {
            TheoryClaimKind.THEOREM,
            TheoryClaimKind.LEMMA,
            TheoryClaimKind.PROPOSITION,
            TheoryClaimKind.COROLLARY,
        }
        else (),
        semantic_status="ALIGNED",
        citation_refs=citations,
        limitations=("浮点实现未覆盖",),
        manuscript_locations=("sec:main",),
    )


def _manuscript(**overrides) -> TheoryMasterManuscript:
    lemma = _claim(
        "lem-1",
        kind=TheoryClaimKind.LEMMA,
        statement="∀ A B，tr(AB)=tr(BA) 中 A,B 可交换乘法次序",
        conclusion="tr(AB)=tr(BA)",
    )
    theorem = _claim("thm-1")
    params = {
        "manuscript_id": "tms-1",
        "version": 1,
        "project_id": "p-1",
        "evidence_tier": TheoryEvidenceTier.PROVED_AND_SEMANTICALLY_ACCEPTED,
        "title": "Cyclic trace invariance",
        "abstract": "abstract",
        "msc": "15A15",
        "keywords": ("trace",),
        "introduction": "intro",
        "related_work": "related",
        "notation_and_preliminaries": "notation",
        "definitions_and_assumptions": "defs",
        "main_results": "tr(AB)=tr(BA)",
        "proof_architecture": "lemma then theorem",
        "proofs_status": "all complete",
        "examples_counterexamples": "counterexample: non-square",
        "verification_methods_scope": "Lean 4",
        "limitations_unresolved_obligations": "floating point not covered",
        "implications_applications": "numerical libraries",
        "availability": "lean sources",
        "structured_author_fields": {
            "author_contributions": "NEEDS_AUTHOR_INPUT",
            "funding": "NEEDS_AUTHOR_INPUT",
        },
        "references": ("ref-cyclic",),
        "claims": (lemma, theorem),
        "dependency_graph": ProofDependencyGraph(
            nodes=("thm-1", "lem-1"),
            edges=(("thm-1", "lem-1"),),
        ),
    }
    params.update(overrides)
    return TheoryMasterManuscript(**params)


def test_golden_manuscript_hashes_are_traceable():
    manuscript = _manuscript()
    hashes = manuscript.statement_hashes()
    assert set(hashes) == {"lem-1", "thm-1"}
    for claim in manuscript.claims:
        recomputed = claim_statement_hash(
            display_statement=claim.display_statement,
            object_domain=claim.object_domain,
            quantifiers=claim.quantifiers,
            assumptions=claim.assumptions,
            conclusion=claim.conclusion,
        )
        assert claim.normalized_statement_hash == recomputed
    assert manuscript.master_hash and len(manuscript.master_hash) == 64


def test_incomplete_theorem_must_be_demoted():
    with pytest.raises(DomainError) as exc_info:
        _manuscript(
            claims=(_claim("thm-1", proof_status=ProofStatus.INCOMPLETE),),
            dependency_graph=ProofDependencyGraph(nodes=("thm-1",), edges=()),
        )
    assert exc_info.value.error_code == "CLAIM_PROOF_INCOMPLETE"


def test_claim_without_citations_is_rejected():
    with pytest.raises(DomainError) as exc_info:
        _claim("thm-1", citations=())
    assert exc_info.value.error_code == "CLAIM_CITATION_MISSING"


def test_proof_graph_rejects_undeclared_cycle():
    with pytest.raises(DomainError) as exc_info:
        ProofDependencyGraph(
            nodes=("a", "b"),
            edges=(("a", "b"), ("b", "a")),
        )
    assert exc_info.value.error_code == "PROOF_GRAPH_INVALID"
    # declared recursion is allowed
    graph = ProofDependencyGraph(
        nodes=("a", "b"),
        edges=(("a", "b"), ("b", "a")),
        declared_recursive_pairs=(("a", "b"), ("b", "a")),
    )
    assert graph.nodes == ("a", "b")


def test_audit_finds_dangling_graph_and_hidden_obligations():
    manuscript = _manuscript(
        dependency_graph=ProofDependencyGraph(nodes=("thm-1", "ghost"), edges=()),
        limitations_unresolved_obligations="",
    )
    findings, status = audit_theory_manuscript(
        manuscript,
        auditor_session_id="auditor-1",
        draft_generator_session_ids=("generator-1",),
    )
    assert status is TheoryManuscriptAuditStatus.AUDITED_WITH_FINDINGS
    descriptions = [finding.description for finding in findings]
    assert any("ghost" in description for description in descriptions)
    assert any("未解决义务" in description for description in descriptions)


def test_audit_clean_and_independence():
    manuscript = _manuscript()
    findings, status = audit_theory_manuscript(
        manuscript,
        auditor_session_id="auditor-1",
        draft_generator_session_ids=("generator-1",),
    )
    assert status is TheoryManuscriptAuditStatus.AUDITED_CLEAN
    assert findings == []
    with pytest.raises(DomainError) as exc_info:
        audit_theory_manuscript(
            manuscript,
            auditor_session_id="generator-1",
            draft_generator_session_ids=("generator-1",),
        )
    assert exc_info.value.error_code == "AUDITOR_NOT_INDEPENDENT"
