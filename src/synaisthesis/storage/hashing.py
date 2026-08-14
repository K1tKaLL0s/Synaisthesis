"""Artifact hashing (blueprint 12, storage/hashing.py)."""

from __future__ import annotations

import hashlib
from pathlib import Path


def sha256_bytes(data: bytes) -> str:
    """Return the SHA-256 hex digest of raw bytes."""
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    """Return the SHA-256 hex digest of a file's raw bytes."""
    return hashlib.sha256(path.read_bytes()).hexdigest()


def verify_artifact_hash(path: Path, expected_sha256: str) -> bool:
    """Return True when the file exists and its SHA-256 matches the expected.

    Missing or tampered files are detected and reported as False.
    """
    if not path.exists():
        return False
    return sha256_file(path) == expected_sha256
