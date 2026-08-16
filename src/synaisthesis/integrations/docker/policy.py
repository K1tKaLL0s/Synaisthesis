"""Docker sandbox policy (blueprint 08 section 3 CONTAINER, 19 §5 M8.2).

The policy is the only place sandbox parameters live; it is hash-bound into
every receipt.  M8.2 defaults are fail-closed: no network, no host mounts,
read-only root filesystem, resource limits and a timeout.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

from synaisthesis.domain.event import sha256_hex

DEFAULT_IMAGE = "ghcr.io/astral-sh/uv:python3.13-bookworm-slim"


@dataclass(frozen=True, slots=True)
class DockerSandboxPolicy:
    """Immutable sandbox parameters (M8.2)."""

    image: str = DEFAULT_IMAGE
    network_mode: str = "none"
    memory_limit: str = "256m"
    cpu_limit: float = 1.0
    pids_limit: int = 64
    timeout_seconds: int = 30
    read_only_rootfs: bool = True
    allowed_env: tuple[str, ...] = ()
    mounts: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if self.network_mode != "none":
            raise ValueError("M8.2 沙箱必须 network=none")
        if self.mounts:
            raise ValueError("M8.2 沙箱禁止 host mounts（无 secret 边界）")
        if self.timeout_seconds < 1:
            raise ValueError("timeout_seconds must be >= 1")

    def policy_hash(self) -> str:
        return sha256_hex(asdict(self))

    def docker_run_args(self, container_name: str) -> tuple[str, ...]:
        """Deterministic docker run flags for this policy."""
        args: list[str] = [
            "run",
            "--rm",
            "--name",
            container_name,
            "-i",
            "--network",
            self.network_mode,
            "-m",
            self.memory_limit,
            "--cpus",
            str(self.cpu_limit),
            "--pids-limit",
            str(self.pids_limit),
        ]
        if self.read_only_rootfs:
            args.append("--read-only")
        for key in self.allowed_env:
            args.extend(["--env", key])
        args.append(self.image)
        args.extend(["python3", "-"])
        return tuple(args)

    def to_event_payload(self) -> dict[str, Any]:
        return dict(asdict(self))


__all__ = [
    "DEFAULT_IMAGE",
    "DockerSandboxPolicy",
]
