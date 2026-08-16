"""Real Python sandbox verifier (blueprint 19 §5 M8.2, 08 §3 CONTAINER).

Runs untrusted Python inside a Docker container under the M8.2 fail-closed
policy: no network, no host mounts, read-only root, resource limits and a
timeout.  Every run produces a content-bound receipt (exit code, output,
image id, elapsed time, policy hash, code hash); timeouts kill the container
so no orphan survives.
"""

from __future__ import annotations

import os
import subprocess
import time
import uuid
from dataclasses import dataclass

from synaisthesis.domain.errors import DomainError
from synaisthesis.domain.event import sha256_hex
from synaisthesis.integrations.docker.policy import DockerSandboxPolicy

DOCKER_BINARY_CANDIDATES: tuple[str, ...] = (
    "/mnt/c/Program Files/Docker/Docker/resources/bin/docker.exe",
    "docker",
    "docker.exe",
)

GRACE_SECONDS = 10


def find_docker_binary() -> str | None:
    configured = os.environ.get("SYNAISTHESIS_DOCKER_BINARY")
    candidates = (
        (configured,) + DOCKER_BINARY_CANDIDATES if configured else DOCKER_BINARY_CANDIDATES
    )
    for candidate in candidates:
        if not candidate:
            continue
        try:
            probe = subprocess.run(
                [candidate, "info", "--format", "{{.ServerVersion}}"],
                capture_output=True,
                text=True,
                timeout=30,
                check=False,
            )
        except (OSError, subprocess.SubprocessError):
            continue
        if probe.returncode == 0 and probe.stdout.strip():
            return candidate
    return None


def docker_image_id(binary: str, image: str) -> str:
    probe = subprocess.run(
        [binary, "image", "inspect", "--format", "{{.Id}}", image],
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )
    if probe.returncode != 0:
        raise DomainError(
            f"无法解析镜像 {image!r} 的 Id",
            error_code="SANDBOX_IMAGE_UNKNOWN",
        )
    return probe.stdout.strip()


@dataclass(frozen=True, slots=True)
class PythonSandboxReceipt:
    """One real sandboxed execution with a content-bound receipt."""

    exit_code: int
    stdout: str
    stderr: str
    image_id: str
    elapsed_ms: int
    timed_out: bool
    policy_hash: str
    code_hash: str
    container_name: str
    receipt_hash: str | None = None

    def __post_init__(self) -> None:
        expected = self._content_hash()
        if self.receipt_hash is not None and self.receipt_hash != expected:
            raise DomainError(
                "receipt_hash does not match the sandbox receipt content",
                error_code="RECEIPT_HASH_MISMATCH",
            )
        object.__setattr__(self, "receipt_hash", expected)

    def _content_hash(self) -> str:
        return sha256_hex(
            {
                "exit_code": self.exit_code,
                "stdout": self.stdout,
                "stderr": self.stderr,
                "image_id": self.image_id,
                "elapsed_ms": self.elapsed_ms,
                "timed_out": self.timed_out,
                "policy_hash": self.policy_hash,
                "code_hash": self.code_hash,
                "container_name": self.container_name,
            }
        )


def run_python_in_sandbox(
    code: str,
    *,
    policy: DockerSandboxPolicy | None = None,
    docker_binary: str | None = None,
) -> PythonSandboxReceipt:
    """Run untrusted Python in Docker; timeout kills the container (M8.2)."""
    policy = policy or DockerSandboxPolicy()
    binary = docker_binary or find_docker_binary()
    if binary is None:
        raise DomainError(
            "未找到可用的 Docker 客户端/守护进程；真实沙箱不可用",
            error_code="TOOL_UNAVAILABLE",
        )
    try:
        image_id = docker_image_id(binary, policy.image)
    except OSError as exc:
        raise DomainError(
            f"Docker 客户端不可执行：{binary!r}",
            error_code="TOOL_UNAVAILABLE",
        ) from exc
    container_name = f"synaisthesis-sandbox-{uuid.uuid4().hex[:12]}"
    started = time.monotonic()
    timed_out = False
    try:
        proc = subprocess.run(
            [binary, *policy.docker_run_args(container_name)],
            input=code,
            capture_output=True,
            text=True,
            timeout=policy.timeout_seconds + GRACE_SECONDS,
            check=False,
        )
    except OSError as exc:
        raise DomainError(
            f"Docker 客户端不可执行：{binary!r}",
            error_code="TOOL_UNAVAILABLE",
        ) from exc
    except subprocess.TimeoutExpired:
        timed_out = True
        subprocess.run(
            [binary, "rm", "-f", container_name],
            capture_output=True,
            text=True,
            timeout=30,
            check=False,
        )
        proc = None
    elapsed_ms = int((time.monotonic() - started) * 1000)
    return PythonSandboxReceipt(
        exit_code=proc.returncode if proc is not None else -1,
        stdout=proc.stdout if proc is not None else "",
        stderr=proc.stderr if proc is not None else "timeout: container killed",
        image_id=image_id,
        elapsed_ms=elapsed_ms,
        timed_out=timed_out,
        policy_hash=policy.policy_hash(),
        code_hash=sha256_hex({"code": code}),
        container_name=container_name,
    )


__all__ = [
    "DOCKER_BINARY_CANDIDATES",
    "PythonSandboxReceipt",
    "docker_image_id",
    "find_docker_binary",
    "run_python_in_sandbox",
]
