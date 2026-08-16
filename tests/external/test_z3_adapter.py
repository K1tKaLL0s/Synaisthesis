"""M8.1 external tests against the real Z3 adapter (no Fake path).

These tests invoke the real Z3 binary (N-drive toolchain via WSL interop or
$SYNAISTHESIS_Z3_BINARY).  They are skipped when no Z3 binary is available —
an explicit environment blocker, never a Fake substitution.
"""

from __future__ import annotations

import pytest

from synaisthesis.domain.errors import DomainError
from synaisthesis.verifiers.registry import VerifierRegistry, z3_evidence_ok
from synaisthesis.verifiers.z3.adapter import (
    Z3Result,
    Z3Verdict,
    find_z3_binary,
    run_z3_smt2,
    verify_sat_witness,
    z3_version,
)

SAT_SCRIPT = "(declare-const x Int)\n(assert (> x 0))\n(check-sat)\n(get-model)\n"
UNSAT_SCRIPT = "(declare-const x Int)\n(assert (= x 0))\n(assert (= x 1))\n(check-sat)\n"
UNKNOWN_SCRIPT = (
    "(set-option :timeout 1)\n"
    "(declare-const p Int)\n"
    "(declare-const q Int)\n"
    "(assert (and (> p 1) (> q 1)))\n"
    "(assert (= (* p q) 104729))\n"
    "(check-sat)\n"
)

pytestmark = pytest.mark.skipif(
    find_z3_binary() is None,
    reason="no runnable Z3 binary (SYNAISTHESIS_Z3_BINARY or toolchain missing)",
)


def test_real_z3_binary_and_version():
    binary = find_z3_binary()
    assert binary is not None
    assert "Z3" in z3_version(binary)


def test_sat_verdict_with_reverified_witness():
    result = run_z3_smt2(SAT_SCRIPT)
    assert result.verdict is Z3Verdict.SAT
    assert result.model_text is not None
    assert result.witness_verified is True
    assert z3_evidence_ok(result) is True
    assert len(result.receipt) == 64


def test_unsat_verdict():
    result = run_z3_smt2(UNSAT_SCRIPT)
    assert result.verdict is Z3Verdict.UNSAT
    assert z3_evidence_ok(result) is True


def test_unknown_verdict_is_never_pass():
    result = run_z3_smt2(UNKNOWN_SCRIPT)
    assert result.verdict is Z3Verdict.UNKNOWN
    assert z3_evidence_ok(result) is False


def test_tampered_witness_fails_reverification():
    result = run_z3_smt2(SAT_SCRIPT)
    assert result.model_text is not None
    tampered = result.model_text.replace("1)", "0)")
    verified, blockers = verify_sat_witness(SAT_SCRIPT, tampered)
    assert verified is False
    assert blockers


def test_input_is_never_executed_as_code():
    # Python/OS payloads inside the SMT2 text are inert data: the adapter only
    # passes the text to Z3 and parses its verdict lines.
    hostile = SAT_SCRIPT + '; __import__("os").system("touch /tmp/pwned")\n'
    result = run_z3_smt2(hostile)
    assert result.verdict is Z3Verdict.SAT
    import pathlib

    assert not pathlib.Path("/tmp/pwned").exists()


def test_receipt_is_content_bound_and_deterministic():
    first = run_z3_smt2(UNSAT_SCRIPT)
    second = run_z3_smt2(UNSAT_SCRIPT)
    assert first.receipt == second.receipt
    assert first.input_hash == second.input_hash
    assert first.output_hash == second.output_hash
    different = run_z3_smt2(UNSAT_SCRIPT.replace("= x 1", "= x 2"))
    assert first.receipt != different.receipt


def test_registry_registers_and_runs_real_adapter():
    registry = VerifierRegistry()
    registry.register("z3", lambda text: run_z3_smt2(text), version="5.0.0")
    assert "z3" in registry.supported()
    result = registry.run("z3", UNSAT_SCRIPT)
    assert isinstance(result, Z3Result)
    assert result.verdict is Z3Verdict.UNSAT
    with pytest.raises(DomainError) as exc_info:
        registry.run("missing", UNSAT_SCRIPT)
    assert exc_info.value.error_code == "VERIFIER_UNKNOWN"


def test_unavailable_binary_is_a_structured_blocker():
    from synaisthesis.verifiers.z3.adapter import run_z3_smt2 as run

    with pytest.raises(DomainError) as exc_info:
        run(UNSAT_SCRIPT, binary="/nonexistent/z3-binary")
    assert exc_info.value.error_code == "TOOL_UNAVAILABLE"
