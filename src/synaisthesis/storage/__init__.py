"""Persistence layer for Synaisthesis (blueprint 12, storage/)."""

from synaisthesis.storage.artifact_store import save_artifact
from synaisthesis.storage.database import init_database
from synaisthesis.storage.hashing import verify_artifact_hash
from synaisthesis.storage.repositories.event_repository import append_domain_event

__all__ = ["append_domain_event", "init_database", "save_artifact", "verify_artifact_hash"]
