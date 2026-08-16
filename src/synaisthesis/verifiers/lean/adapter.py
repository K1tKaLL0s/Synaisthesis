"""Real Lean compiler adapter (blueprint 19 §5 M8.3, 10 §tool verification).

Only a real Lean invocation that exits 0 may ever be recorded as
E4-eligible evidence.  The adapter runs the Lean 4 binary on a source file,
captures diagnostics, records the tool version and a content-bound receipt,
and guards the proof loop: if the theorem/lemma statement hash changed, the
loop must exit with PROOF_LOOP_STATEMENT_CHANGED instead of reusing old
results.
"""

from __future__ import annotations

import os
import re
import subprocess
import tempfile
import time
from dataclasses import dataclass
from pathlib import Path

from synaisthesis.domain.errors import DomainError
from synaisthesis.domain.event import sha256_hex

LEAN_BINARY_CANDIDATES: tuple[str, ...] = (
    str(Path.home() / ".elan" / "bin" / "lean"),
    "lean",
)

_DECL_RE = re.compile(r"^\s*(theorem|lemma|example)\b")


def find_lean_binary() -> str | None:
    configured = os.environ.get("SYNAISTHESIS_LEAN_BINARY")
    candidates = (configured,) + LEAN_BINARY_CANDIDATES if configured else LEAN_BINARY_CANDIDATES
    for candidate in candidates:
        if not candidate:
            continue
        try:
            probe = subprocess.run(
                [candidate, "--version"],
                capture_output=True,
                text=True,
                timeout=15,
                check=False,
            )
        except (OSError, subprocess.SubprocessError):
            continue
        if probe.returncode == 0:
            return candidate
    return None


def lean_version(binary: str) -> str:
    probe = subprocess.run(
        [binary, "--version"],
        capture_output=True,
        text=True,
        timeout=15,
        check=False,
    )
    return probe.stdout.strip() or probe.stderr.strip() or "unknown"


def statement_hash_of_source(source: str) -> str:
    """Hash of the declared theorem/lemma/example statements (proof-loop guard).

    The full declaration lines are hashed so a changed statement (including
    its type) produces a different hash.
    """
    statements = tuple(line.strip() for line in source.splitlines() if _DECL_RE.match(line))
    return sha256_hex({"statements": list(statements)})


@dataclass(frozen=True, slots=True)
class LeanResult:
    """One real Lean invocation with a content-bound receipt."""

    exit_code: int
    stdout: str
    stderr: str
    tool: str
    tool_version: str
    source_hash: str
    output_hash: str
    statement_hash: str
    elapsed_ms: int
    receipt_hash: str | None = None

    def __post_init__(self) -> None:
        expected = self._content_hash()
        if self.receipt_hash is not None and self.receipt_hash != expected:
            raise DomainError(
                "receipt_hash does not match the Lean receipt content",
                error_code="RECEIPT_HASH_MISMATCH",
            )
        object.__setattr__(self, "receipt_hash", expected)

    def _content_hash(self) -> str:
        return sha256_hex(
            {
                "exit_code": self.exit_code,
                "stdout": self.stdout,
                "stderr": self.stderr,
                "tool": self.tool,
                "tool_version": self.tool_version,
                "source_hash": self.source_hash,
                "output_hash": self.output_hash,
                "statement_hash": self.statement_hash,
            }
        )


def run_lean(
    source: str,
    *,
    binary: str | None = None,
    timeout_ms: int = 120_000,
) -> LeanResult:
    """Compile one Lean source with the real compiler; never evaluates more."""
    resolved = binary or find_lean_binary()
    if resolved is None:
        raise DomainError(
            "未找到可运行的 Lean 二进制；真实适配器不可用",
            error_code="TOOL_UNAVAILABLE",
        )
    started = time.monotonic()
    path = ""
    try:
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".lean", encoding="utf-8", delete=False
        ) as handle:
            handle.write(source)
            path = handle.name
        try:
            proc = subprocess.run(
                [resolved, path],
                capture_output=True,
                text=True,
                timeout=timeout_ms / 1000,
                check=False,
            )
            stdout: str = proc.stdout.replace(path, "<source>")
            stderr: str = proc.stderr.replace(path, "<source>")
        finally:
            Path(path).unlink(missing_ok=True)
    except OSError as exc:
        raise DomainError(
            f"Lean 二进制不可执行：{resolved!r}",
            error_code="TOOL_UNAVAILABLE",
        ) from exc
    except subprocess.TimeoutExpired as exc:
        raw_stdout = exc.stdout or b""
        if isinstance(raw_stdout, bytes):
            output = raw_stdout.decode("utf-8", errors="replace").replace(
                path, "<source>"
            )
        else:
            output = raw_stdout.replace(path, "<source>")
        return LeanResult(
            exit_code=-1,
            stdout=output,
            stderr="timeout",
            tool=resolved,
            tool_version=lean_version(resolved),
            source_hash=sha256_hex({"source": source}),
            output_hash=sha256_hex({"stdout": output, "stderr": "timeout"}),
            statement_hash=statement_hash_of_source(source),
            elapsed_ms=int((time.monotonic() - started) * 1000),
        )
    elapsed_ms = int((time.monotonic() - started) * 1000)
    return LeanResult(
        exit_code=proc.returncode,
        stdout=stdout,
        stderr=stderr,
        tool=resolved,
        tool_version=lean_version(resolved),
        source_hash=sha256_hex({"source": source}),
        output_hash=sha256_hex({"stdout": proc.stdout, "stderr": proc.stderr}),
        statement_hash=statement_hash_of_source(source),
        elapsed_ms=elapsed_ms,
    )


def assert_proof_loop_statement_unchanged(
    *,
    current_source: str,
    expected_statement_hash: str,
) -> None:
    """Exit the proof loop when the frozen statement hash changed (M8.3)."""
    current = statement_hash_of_source(current_source)
    if current != expected_statement_hash:
        raise DomainError(
            "statement hash 已变化，必须退出 Proof Loop 并重新审查定理",
            error_code="PROOF_LOOP_STATEMENT_CHANGED",
        )


def lean_evidence_ok(result: LeanResult) -> bool:
    """Only a real exit-0 Lean run may be recorded as E4-eligible evidence."""
    return result.exit_code == 0


__all__ = [
    "LEAN_BINARY_CANDIDATES",
    "LeanResult",
    "assert_proof_loop_statement_unchanged",
    "find_lean_binary",
    "lean_evidence_ok",
    "lean_version",
    "run_lean",
    "statement_hash_of_source",
]
