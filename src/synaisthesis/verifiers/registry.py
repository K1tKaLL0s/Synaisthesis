"""Verifier registry (blueprint 19 §5 M8.x, 10 §tool verification; M8.1).

Every registered verifier is a real tool adapter; evidence policy is strict:
a SAT/UNSAT verdict may only become evidence when the adapter produced it and
its witness (for SAT) re-verified.  UNKNOWN is never PASS.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from synaisthesis.domain.errors import DomainError
from synaisthesis.verifiers.z3.adapter import Z3Result, Z3Verdict


class VerifierRegistry:
    """Maps stable verifier ids to real tool adapters."""

    def __init__(self) -> None:
        self._adapters: dict[str, tuple[str, Callable[[str], Any]]] = {}

    def register(
        self,
        verifier_id: str,
        adapter: Callable[[str], Any],
        *,
        version: str,
    ) -> None:
        if not verifier_id.strip():
            raise DomainError(
                "verifier id must be non-empty",
                error_code="VERIFIER_INVALID",
            )
        self._adapters[verifier_id] = (version, adapter)

    def supported(self) -> tuple[str, ...]:
        return tuple(sorted(self._adapters))

    def run(self, verifier_id: str, input_text: str) -> Any:
        entry = self._adapters.get(verifier_id)
        if entry is None:
            raise DomainError(
                f"unknown verifier {verifier_id!r}",
                error_code="VERIFIER_UNKNOWN",
            )
        _version, adapter = entry
        return adapter(input_text)


def z3_evidence_ok(result: Z3Result) -> bool:
    """A Z3 result may become evidence only when verdict and witness hold.

    SAT requires a re-verified witness; UNSAT is self-witnessing; UNKNOWN is
    never PASS (M8.1 stop condition: UNKNOWN 变 PASS 是违规).
    """
    if result.verdict is Z3Verdict.UNKNOWN:
        return False
    if result.verdict is Z3Verdict.SAT:
        return result.witness_verified is True
    return True


__all__ = [
    "VerifierRegistry",
    "z3_evidence_ok",
]
