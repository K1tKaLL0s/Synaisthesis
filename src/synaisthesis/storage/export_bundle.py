"""Deterministic engineering delivery export bundle (03B, section 13.2; M2.10).

The bundle keeps a manifest recording every file's role, source artifact,
version, byte size, checksum and generation method, plus a SHA-256 checksum
file.  Rebuilding the bundle must reproduce identical manifest entries for
identical inputs (03B, section 16.24).
"""

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping
from dataclasses import asdict, dataclass
from typing import Any

from synaisthesis.domain.event import canonicalize

MANIFEST_ROLE_EXECUTIVE_SUMMARY = "executive_summary"
MANIFEST_ROLE_BLUEPRINT = "blueprint"
MANIFEST_ROLE_WORK_UNIT = "work_unit"
MANIFEST_ROLE_TRACEABILITY = "traceability"
MANIFEST_ROLE_DIAGRAM_SOURCE = "diagram_source"
MANIFEST_ROLE_DIAGRAM_RENDERED = "diagram_rendered"
MANIFEST_ROLE_CHECKSUMS = "checksums"
MANIFEST_ROLE_MANIFEST = "manifest"


def _sha256_bytes(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def _canonical_payload(value: Any) -> dict[str, Any]:
    payload = canonicalize(value)
    if not isinstance(payload, dict):
        raise TypeError("export payload must canonicalize to an object")
    return payload


@dataclass(frozen=True, slots=True)
class ExportBundleItem:
    """One file entry in the delivery manifest (03B, section 13.2)."""

    path: str
    role: str
    source_artifact: str
    version: int
    size_bytes: int
    sha256: str
    generation_method: str


@dataclass(frozen=True, slots=True)
class ExportBundle:
    """An immutable export bundle with manifest and checksums."""

    bundle_id: str
    project_id: str
    items: tuple[ExportBundleItem, ...]
    manifest_yaml: str
    checksums_txt: str
    bundle_hash: str

    @classmethod
    def create(
        cls,
        *,
        bundle_id: str,
        project_id: str,
        files: Mapping[str, bytes],
        generation_method: str = "deterministic-builder",
    ) -> ExportBundle:
        """Build the bundle deterministically from path -> bytes inputs."""
        ordered = sorted(files.items())
        items = tuple(
            ExportBundleItem(
                path=path,
                role=_role_for_path(path),
                source_artifact=path,
                version=1,
                size_bytes=len(content),
                sha256=_sha256_bytes(content),
                generation_method=generation_method,
            )
            for path, content in ordered
        )
        checksums_txt = "".join(f"{item.sha256}  {item.path}\n" for item in items)
        manifest_lines = [
            "manifest:",
            f"  bundle_id: {bundle_id}",
            f"  project_id: {project_id}",
            f"  generation_method: {generation_method}",
            "files:",
        ]
        for item in items:
            manifest_lines.extend(
                [
                    f"  - path: {item.path}",
                    f"    role: {item.role}",
                    f"    source_artifact: {item.source_artifact}",
                    f"    version: {item.version}",
                    f"    size_bytes: {item.size_bytes}",
                    f"    sha256: {item.sha256}",
                    f"    generation_method: {item.generation_method}",
                ]
            )
        manifest_yaml = "\n".join(manifest_lines) + "\n"
        bundle_hash = _sha256_bytes(manifest_yaml.encode("utf-8") + checksums_txt.encode("utf-8"))
        return cls(
            bundle_id=bundle_id,
            project_id=project_id,
            items=items,
            manifest_yaml=manifest_yaml,
            checksums_txt=checksums_txt,
            bundle_hash=bundle_hash,
        )

    def to_event_payload(self) -> dict[str, Any]:
        return _canonical_payload(
            {
                "bundle_id": self.bundle_id,
                "project_id": self.project_id,
                "items": [asdict(item) for item in self.items],
                "manifest_yaml": self.manifest_yaml,
                "checksums_txt": self.checksums_txt,
                "bundle_hash": self.bundle_hash,
            }
        )


def _role_for_path(path: str) -> str:
    lowered = path.lower()
    if lowered.endswith((".md",)) and "summary" in lowered:
        return MANIFEST_ROLE_EXECUTIVE_SUMMARY
    if lowered.endswith(".svg") or lowered.endswith(".png"):
        return MANIFEST_ROLE_DIAGRAM_RENDERED
    if lowered.startswith(("diagrams/",)) or "diagram" in lowered:
        return MANIFEST_ROLE_DIAGRAM_SOURCE
    if "work_unit" in lowered or "work_units" in lowered:
        return MANIFEST_ROLE_WORK_UNIT
    if "trace" in lowered:
        return MANIFEST_ROLE_TRACEABILITY
    return MANIFEST_ROLE_BLUEPRINT


def verify_export_bundle(bundle: ExportBundle, files: Mapping[str, bytes]) -> tuple[str, ...]:
    """Recompute sizes/checksums; a single mismatch fails the bundle (03B, 13.2)."""
    blockers: list[str] = []
    provided = dict(files)
    for item in bundle.items:
        content = provided.get(item.path)
        if content is None:
            blockers.append(f"{item.path} 缺失")
            continue
        if len(content) != item.size_bytes:
            blockers.append(f"{item.path} size 不符")
        if _sha256_bytes(content) != item.sha256:
            blockers.append(f"{item.path} checksum 不符")
    if not blockers:
        expected_hash = _sha256_bytes(
            bundle.manifest_yaml.encode("utf-8") + bundle.checksums_txt.encode("utf-8")
        )
        if bundle.bundle_hash != expected_hash:
            blockers.append("bundle_hash 与 manifest/checksums 不符")
    return tuple(blockers)


def export_bundle_manifest_json(bundle: ExportBundle) -> str:
    """Return the manifest as canonical JSON (for tests and tooling)."""
    return json.dumps(canonicalize(bundle.to_event_payload()), sort_keys=True, ensure_ascii=False)


__all__ = [
    "MANIFEST_ROLE_BLUEPRINT",
    "MANIFEST_ROLE_CHECKSUMS",
    "MANIFEST_ROLE_DIAGRAM_RENDERED",
    "MANIFEST_ROLE_DIAGRAM_SOURCE",
    "MANIFEST_ROLE_EXECUTIVE_SUMMARY",
    "MANIFEST_ROLE_MANIFEST",
    "MANIFEST_ROLE_TRACEABILITY",
    "MANIFEST_ROLE_WORK_UNIT",
    "ExportBundle",
    "ExportBundleItem",
    "export_bundle_manifest_json",
    "verify_export_bundle",
]
