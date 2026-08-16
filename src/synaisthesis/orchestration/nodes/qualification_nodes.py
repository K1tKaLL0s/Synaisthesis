"""Route-aware RQ0-RQ4 qualification orchestration nodes (19 §5 M13.3).

The pipeline is pure: it returns every stage artifact and a next target
(S5 / ENG0) or an open user Gate.  Persistence belongs to the downstream
stage services (incubation S5 / engineering ENG0), which re-validate the
qualification preconditions against their own artifacts.
"""

from __future__ import annotations

from synaisthesis.application.qualification_service import (
    QualificationRun,
    qualification_export_payload,
    run_qualification_pipeline,
)


def qualification_pipeline_node(*args, **kwargs) -> QualificationRun:
    """Execute one route-aware RQ0→RQ4 run (no persistence here)."""
    return run_qualification_pipeline(*args, **kwargs)


__all__ = [
    "QualificationRun",
    "qualification_export_payload",
    "qualification_pipeline_node",
]
