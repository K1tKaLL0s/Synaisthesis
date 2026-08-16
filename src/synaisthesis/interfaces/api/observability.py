"""Web observability API handler (19 §5 M14).

The frozen API schema lives at configs/api/observability_schema.json.  The
handler returns the store-verbatim payload; the static page renderers in
interfaces/web only display fields from this payload.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from sqlalchemy.orm import Session

from synaisthesis.application.observability_service import (
    OBSERVABILITY_SCHEMA_VERSION,
    project_observability_payload,
)
from synaisthesis.domain.errors import DomainError


def handle_observability_get(
    session: Session,
    *,
    project_id: str,
    artifact_root: Path,
) -> dict[str, Any]:
    """GET /api/observability?project_id=... -> frozen-schema payload."""
    return project_observability_payload(
        session, project_id=project_id, artifact_root=artifact_root
    )


def validate_observability_payload(payload: dict[str, Any]) -> None:
    """Structural check against the frozen schema (no jsonschema dependency)."""
    if payload.get("schema_version") != OBSERVABILITY_SCHEMA_VERSION:
        raise DomainError(
            f"observability payload schema_version 必须是 {OBSERVABILITY_SCHEMA_VERSION}",
            error_code="OBSERVABILITY_SCHEMA_MISMATCH",
        )
    if payload.get("rendered_from_store") is not True:
        raise DomainError(
            "observability payload 必须显式声明 rendered_from_store=true",
            error_code="OBSERVABILITY_SCHEMA_MISMATCH",
        )
    if not isinstance(payload.get("project_id"), str) or not payload["project_id"]:
        raise DomainError(
            "observability payload 缺少 project_id",
            error_code="OBSERVABILITY_SCHEMA_MISMATCH",
        )
    pages = payload.get("pages")
    if not isinstance(pages, list):
        raise DomainError(
            "observability payload 缺少 pages",
            error_code="OBSERVABILITY_SCHEMA_MISMATCH",
        )
    for page in pages:
        if not isinstance(page, dict):
            raise DomainError(
                "observability page 必须是对象",
                error_code="OBSERVABILITY_SCHEMA_MISMATCH",
            )
        for key in (
            "page_id",
            "title",
            "status",
            "route",
            "inputs",
            "artifacts",
            "gates",
            "rendered_from_store",
        ):
            if key not in page:
                raise DomainError(
                    f"observability page 缺少字段 {key!r}",
                    error_code="OBSERVABILITY_SCHEMA_MISMATCH",
                )
        if page.get("status") not in {"NOT_STARTED", "IN_PROGRESS", "READY"}:
            raise DomainError(
                "observability page status 非法",
                error_code="OBSERVABILITY_SCHEMA_MISMATCH",
            )
        if page.get("rendered_from_store") is not True:
            raise DomainError(
                "observability page 必须声明 rendered_from_store=true",
                error_code="OBSERVABILITY_SCHEMA_MISMATCH",
            )
        if not isinstance(page.get("route"), (str, type(None))):
            raise DomainError(
                "observability page route 必须是字符串或 null",
                error_code="OBSERVABILITY_SCHEMA_MISMATCH",
            )


__all__ = ["handle_observability_get", "validate_observability_payload"]
