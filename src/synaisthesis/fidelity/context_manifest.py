"""ContextManifest: resolving deictic references like "this file" (05A, section 13).

Saving the raw prompt is not enough; every context reference must resolve to a
concrete artifact. A mutation whose manifest still has unresolved references, or
whose artifact hashes cannot be re-verified, fails closed with MISSING_CONTEXT.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

from synaisthesis.domain.errors import DomainError
from synaisthesis.domain.event import canonicalize, sha256_hex


@dataclass(frozen=True, slots=True)
class ContextManifest:
    """Resolved context references for one instruction (05A, section 13)."""

    context_manifest_id: str
    workspace_root: str = ""
    git_commit_or_worktree: str | None = None
    selected_file_refs: tuple[str, ...] = ()
    selected_line_ranges: tuple[tuple[str, int, int], ...] = ()
    attached_artifact_refs: tuple[str, ...] = ()
    active_research_spec_id: str | None = None
    active_claim_contract_id: str | None = None
    cited_instruction_ids: tuple[str, ...] = ()
    artifact_hashes: tuple[tuple[str, str], ...] = ()
    unresolved_deictic_references: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not self.context_manifest_id.strip():
            raise DomainError(
                "context manifest requires context_manifest_id",
                error_code="CONTEXT_MANIFEST_INVALID",
            )

    def has_unresolved_references(self) -> bool:
        return bool(self.unresolved_deictic_references)

    def content_payload(self) -> dict[str, Any]:
        payload = canonicalize(asdict(self))
        if not isinstance(payload, dict):
            raise TypeError("context manifest payload must canonicalize to an object")
        return payload

    def content_hash(self) -> str:
        return sha256_hex(self.content_payload())
