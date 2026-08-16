"""Real Z3 adapter (blueprint 19 §5 M8.1, 10 §tool verification).

Only real solver invocations produce SAT/UNSAT/UNKNOWN verdicts; there is no
Fake path.  The adapter shells out to the Z3 binary over stdin (`-in`),
separates the three verdicts, records a content-bound receipt (input hash,
output hash, tool version, exit code) and independently re-verifies SAT
witnesses by re-checking the formula under the model's scalar assignments.
"""

from __future__ import annotations

import os
import re
import subprocess
import time
from dataclasses import dataclass

from synaisthesis.domain.enums import StrictStrEnum
from synaisthesis.domain.errors import DomainError
from synaisthesis.domain.event import sha256_hex

Z3_VERSION_CMD = "--version"
DEFAULT_TIMEOUT_MS = 30_000

Z3_BINARY_CANDIDATES: tuple[str, ...] = (
    "/mnt/n/CodexData/toolchains/formal/z3/5.0.0/z3-5.0.0-x64-win/bin/z3.exe",
    "z3",
    "z3.exe",
)

_MODEL_FUN_RE = re.compile(r"\(define-fun\s+([^\s()]+)\s*\(\)\s+([^\s()]+)\s+([^)]*)\)")
_SCALAR_TYPES = frozenset({"Int", "Real", "Bool"})


class Z3Verdict(StrictStrEnum):
    """The three separated solver verdicts (M8.1)."""

    SAT = "SAT"
    UNSAT = "UNSAT"
    UNKNOWN = "UNKNOWN"


def find_z3_binary() -> str | None:
    """Locate a runnable Z3 binary (env override wins)."""
    configured = os.environ.get("SYNAISTHESIS_Z3_BINARY")
    candidates = (configured,) + Z3_BINARY_CANDIDATES if configured else Z3_BINARY_CANDIDATES
    for candidate in candidates:
        if not candidate:
            continue
        try:
            probe = subprocess.run(
                [candidate, Z3_VERSION_CMD],
                capture_output=True,
                text=True,
                timeout=10,
                check=False,
            )
        except (OSError, subprocess.SubprocessError):
            continue
        if probe.returncode == 0:
            return candidate
    return None


def z3_version(binary: str) -> str:
    probe = subprocess.run(
        [binary, Z3_VERSION_CMD],
        capture_output=True,
        text=True,
        timeout=10,
        check=False,
    )
    return probe.stdout.strip() or probe.stderr.strip() or "unknown"


@dataclass(frozen=True, slots=True)
class Z3Result:
    """One real solver invocation with a content-bound receipt."""

    verdict: Z3Verdict
    model_text: str | None
    stdout: str
    exit_code: int
    tool: str
    tool_version: str
    input_hash: str
    output_hash: str
    elapsed_ms: int
    witness_verified: bool | None
    witness_blockers: tuple[str, ...] = ()

    @property
    def receipt(self) -> str:
        return sha256_hex(
            {
                "tool": self.tool,
                "tool_version": self.tool_version,
                "input_hash": self.input_hash,
                "output_hash": self.output_hash,
                "verdict": self.verdict.value,
                "exit_code": self.exit_code,
            }
        )


def _strip_solver_directives(smt2_text: str) -> str:
    return "\n".join(
        line
        for line in smt2_text.splitlines()
        if "(get-model)" not in line and "(check-sat)" not in line
    )


def parse_sat_model(model_text: str) -> dict[str, tuple[str, str]]:
    """Parse scalar define-fun assignments: {name: (type, value)}."""
    assignments: dict[str, tuple[str, str]] = {}
    for match in _MODEL_FUN_RE.finditer(model_text):
        name, type_name, raw_value = match.group(1), match.group(2), match.group(3)
        assignments[name] = (type_name, raw_value.strip().replace("\n", " "))
    return assignments


def verify_sat_witness(smt2_text: str, model_text: str) -> tuple[bool, tuple[str, ...]]:
    """Independently re-check the formula under the model assignments.

    Only scalar assignments (Int/Real/Bool) are re-checked; any other model
    type yields a blocker instead of a false pass.
    """
    assignments = parse_sat_model(model_text)
    if not assignments:
        return False, ("模型为空或无法解析",)
    blockers: list[str] = []
    lines = [_strip_solver_directives(smt2_text)]
    for name, (type_name, value) in assignments.items():
        if type_name not in _SCALAR_TYPES:
            blockers.append(f"模型变量 {name} 类型 {type_name} 暂不支持独立重验")
            continue
        lines.append(f"(assert (= {name} {value}))")
    if blockers:
        return False, tuple(blockers)
    lines.append("(check-sat)")
    recheck = "\n".join(lines) + "\n"
    result = run_z3_smt2(recheck)
    if result.verdict is not Z3Verdict.SAT:
        return False, (f"witness 重验结果 {result.verdict.value}，模型无效",)
    return True, ()


def run_z3_smt2(
    smt2_text: str,
    *,
    binary: str | None = None,
    timeout_ms: int = DEFAULT_TIMEOUT_MS,
) -> Z3Result:
    """Run one real Z3 invocation; never evaluates the input as code."""
    resolved = binary or find_z3_binary()
    if resolved is None:
        raise DomainError(
            "未找到可运行的 Z3 二进制；真实适配器不可用",
            error_code="TOOL_UNAVAILABLE",
        )
    started = time.monotonic()
    try:
        proc = subprocess.run(
            [resolved, "-in"],
            input=smt2_text,
            capture_output=True,
            text=True,
            timeout=timeout_ms / 1000,
            check=False,
        )
    except FileNotFoundError as exc:
        raise DomainError(
            f"Z3 二进制不可执行：{resolved!r}",
            error_code="TOOL_UNAVAILABLE",
        ) from exc
    except subprocess.TimeoutExpired as exc:
        if isinstance(exc.stdout, bytes):
            output = exc.stdout.decode("utf-8", errors="replace")
        else:
            output = exc.stdout or ""
        return Z3Result(
            verdict=Z3Verdict.UNKNOWN,
            model_text=None,
            stdout=output,
            exit_code=-1,
            tool=resolved,
            tool_version=z3_version(resolved),
            input_hash=sha256_hex({"smt2": smt2_text}),
            output_hash=sha256_hex({"stdout": output}),
            elapsed_ms=int((time.monotonic() - started) * 1000),
            witness_verified=None,
            witness_blockers=("timeout",),
        )
    elapsed_ms = int((time.monotonic() - started) * 1000)
    stdout = proc.stdout
    lines = [line.strip() for line in stdout.splitlines() if line.strip()]
    if not lines:
        raise DomainError(
            f"Z3 无输出（exit={proc.returncode}）",
            error_code="TOOL_EXECUTION_FAILED",
        )
    first = lines[0]
    model_text: str | None = None
    if first == "sat":
        verdict = Z3Verdict.SAT
        model_text = "\n".join(lines[1:])
    elif first == "unsat":
        verdict = Z3Verdict.UNSAT
    elif first == "unknown":
        verdict = Z3Verdict.UNKNOWN
    else:
        raise DomainError(
            f"Z3 输出无法解析：{first!r}",
            error_code="TOOL_OUTPUT_UNPARSEABLE",
        )
    witness_verified: bool | None = None
    witness_blockers: tuple[str, ...] = ()
    if verdict is Z3Verdict.SAT and model_text:
        witness_verified, witness_blockers = verify_sat_witness(smt2_text, model_text)
    return Z3Result(
        verdict=verdict,
        model_text=model_text,
        stdout=stdout,
        exit_code=proc.returncode,
        tool=resolved,
        tool_version=z3_version(resolved),
        input_hash=sha256_hex({"smt2": smt2_text}),
        output_hash=sha256_hex({"stdout": stdout}),
        elapsed_ms=elapsed_ms,
        witness_verified=witness_verified,
        witness_blockers=witness_blockers,
    )


__all__ = [
    "DEFAULT_TIMEOUT_MS",
    "Z3Result",
    "Z3Verdict",
    "Z3_BINARY_CANDIDATES",
    "find_z3_binary",
    "parse_sat_model",
    "run_z3_smt2",
    "verify_sat_witness",
    "z3_version",
]
