"""M8.3 external tests against the real Lean 4 compiler.

Skipped when no Lean binary is available — an explicit environment blocker,
never a Fake substitution.  Only a real exit-0 Lean run is E4-eligible.
"""

from __future__ import annotations

import pytest

from synaisthesis.domain.errors import DomainError
from synaisthesis.verifiers.lean.adapter import (
    LeanResult,
    assert_proof_loop_statement_unchanged,
    find_lean_binary,
    lean_evidence_ok,
    lean_version,
    run_lean,
    statement_hash_of_source,
)
from synaisthesis.verifiers.registry import VerifierRegistry

GOOD_SOURCE = """theorem add_zero (n : Nat) : n + 0 = n := by
  simp
"""
BAD_SOURCE = """theorem bad (n : Nat) : n = 1 := by
  simp
"""

pytestmark = pytest.mark.skipif(
    find_lean_binary() is None,
    reason="no runnable Lean binary (SYNAISTHESIS_LEAN_BINARY or ~/.elan missing)",
)


def test_real_lean_binary_and_version():
    binary = find_lean_binary()
    assert binary is not None
    version = lean_version(binary)
    assert "Lean (version" in version
    assert "4.32" in version


def test_valid_theorem_is_e4_eligible():
    result = run_lean(GOOD_SOURCE)
    assert result.exit_code == 0
    assert lean_evidence_ok(result) is True
    assert result.receipt_hash is not None and len(result.receipt_hash) == 64
    assert result.tool_version


def test_invalid_proof_is_not_evidence():
    result = run_lean(BAD_SOURCE)
    assert result.exit_code != 0
    assert "error" in result.stderr or "error" in result.stdout
    assert lean_evidence_ok(result) is False


def test_statement_hash_and_proof_loop_guard():
    source = "theorem t : 2 + 2 = 4 := by\n  norm_num\n"
    expected = statement_hash_of_source(source)
    assert len(expected) == 64
    # unchanged statement passes the guard
    assert_proof_loop_statement_unchanged(current_source=source, expected_statement_hash=expected)
    # changed statement exits the loop
    changed = "theorem t : 2 + 2 = 5 := by\n  norm_num\n"
    with pytest.raises(DomainError) as exc_info:
        assert_proof_loop_statement_unchanged(
            current_source=changed, expected_statement_hash=expected
        )
    assert exc_info.value.error_code == "PROOF_LOOP_STATEMENT_CHANGED"


def test_receipt_is_content_bound_and_deterministic():
    first = run_lean(GOOD_SOURCE)
    second = run_lean(GOOD_SOURCE)
    assert first.receipt_hash == second.receipt_hash
    assert first.source_hash == second.source_hash
    different = run_lean(GOOD_SOURCE.replace("simp", "rfl"))
    assert first.receipt_hash != different.receipt_hash


def test_registry_registers_lean():
    registry = VerifierRegistry()
    registry.register(
        "lean", lambda text: run_lean(text), version=lean_version(find_lean_binary() or "lean")
    )
    assert "lean" in registry.supported()
    result = registry.run("lean", GOOD_SOURCE)
    assert isinstance(result, LeanResult)
    assert result.exit_code == 0


def test_unavailable_lean_is_structured_blocker():
    with pytest.raises(DomainError) as exc_info:
        run_lean(GOOD_SOURCE, binary="/nonexistent/lean")
    assert exc_info.value.error_code == "TOOL_UNAVAILABLE"
