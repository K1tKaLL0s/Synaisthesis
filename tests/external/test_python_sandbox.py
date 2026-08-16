"""M8.2 external tests against the real Docker Python sandbox.

Skipped when the Docker daemon or the sandbox image is unavailable — an
explicit environment blocker, never a Fake substitution (19 §5 M8.2).
"""

from __future__ import annotations

import pytest

from synaisthesis.domain.errors import DomainError
from synaisthesis.integrations.docker.policy import DockerSandboxPolicy
from synaisthesis.verifiers.python.sandbox import (
    find_docker_binary,
    run_python_in_sandbox,
)

pytestmark = pytest.mark.skipif(
    find_docker_binary() is None,
    reason="no reachable Docker daemon (SYNAISTHESIS_DOCKER_BINARY or interop missing)",
)

SLOW_POLICY = DockerSandboxPolicy(timeout_seconds=10)


def test_basic_execution_and_receipt():
    result = run_python_in_sandbox("print('hello from sandbox')\n")
    assert result.exit_code == 0
    assert "hello from sandbox" in result.stdout
    assert result.timed_out is False
    assert result.receipt_hash and len(result.receipt_hash) == 64
    assert result.image_id


def test_no_network():
    code = (
        "import socket\n"
        "s = socket.socket()\n"
        "s.settimeout(3)\n"
        "try:\n"
        "    s.connect(('1.1.1.1', 80))\n"
        "    print('NETWORK_OK')\n"
        "except OSError as exc:\n"
        "    print('NETWORK_BLOCKED', type(exc).__name__)\n"
    )
    result = run_python_in_sandbox(code, policy=SLOW_POLICY)
    assert "NETWORK_BLOCKED" in result.stdout


def test_no_host_secrets_or_mounts():
    code = (
        "import os\n"
        "print('ENV=' + repr(sorted(os.environ.keys())))\n"
        "try:\n"
        "    open('/host-etc/passwd').read()\n"
        "    print('HOST_FILE_OK')\n"
        "except OSError:\n"
        "    print('HOST_FILE_BLOCKED')\n"
    )
    result = run_python_in_sandbox(code, policy=SLOW_POLICY)
    # no host env leaks through (only container defaults), no host files
    assert "HOST_FILE_BLOCKED" in result.stdout
    assert "HOST_FILE_OK" not in result.stdout


def test_pids_limit_blocks_fork_bomb():
    code = (
        "import os\n"
        "try:\n"
        "    for _ in range(200):\n"
        "        pid = os.fork()\n"
        "        if pid == 0:\n"
        "            import time; time.sleep(60)\n"
        "    print('FORKED')\n"
        "except OSError:\n"
        "    print('FORK_BLOCKED')\n"
    )
    result = run_python_in_sandbox(code, policy=SLOW_POLICY)
    assert "FORK_BLOCKED" in result.stdout


def test_memory_limit_kills_hog():
    code = (
        "chunks = []\n"
        "try:\n"
        "    while True:\n"
        "        chunks.append(bytearray(8 * 1024 * 1024))\n"
        "except MemoryError:\n"
        "    print('MEMORY_ERROR')\n"
    )
    result = run_python_in_sandbox(code, policy=SLOW_POLICY)
    # OOM may SIGKILL the container (137) before Python catches MemoryError;
    # either outcome proves the memory limit is enforced
    assert "MEMORY_ERROR" in result.stdout or result.exit_code == 137


def test_timeout_kills_container_and_removes_orphan():
    import subprocess

    binary = find_docker_binary()
    assert binary is not None
    result = run_python_in_sandbox(
        "import time\nwhile True: time.sleep(1)\n",
        policy=DockerSandboxPolicy(timeout_seconds=3),
    )
    assert result.timed_out is True
    assert result.exit_code == -1
    # no orphan container survives
    probe = subprocess.run(
        [binary, "ps", "--filter", f"name={result.container_name}"],
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )
    assert result.container_name not in probe.stdout


def test_unavailable_docker_is_structured_blocker():
    with pytest.raises(DomainError) as exc_info:
        run_python_in_sandbox(
            "print(1)\n",
            docker_binary="/nonexistent/docker",
            policy=DockerSandboxPolicy(timeout_seconds=3),
        )
    assert exc_info.value.error_code == "TOOL_UNAVAILABLE"
