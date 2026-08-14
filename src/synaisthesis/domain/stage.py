"""StageRun aggregate (blueprint 06, section 1, incubation_stage_runs table)."""

from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import datetime

from synaisthesis.domain.enums import StageGateStatus, StageId
from synaisthesis.domain.errors import ConflictError


@dataclass(frozen=True, slots=True)
class StageRun:
    """An immutable record of one incubator stage execution."""

    id: str
    project_id: str
    stage_id: StageId
    started_at: datetime
    input_artifact_ids: tuple[str, ...] = ()
    output_artifact_id: str | None = None
    status: StageGateStatus = StageGateStatus.NOT_TESTED
    prompt_version: str | None = None
    model_invocation_ids: tuple[str, ...] = ()
    ended_at: datetime | None = None

    @property
    def is_finished(self) -> bool:
        return self.ended_at is not None

    def complete(
        self,
        *,
        status: StageGateStatus,
        output_artifact_id: str,
        ended_at: datetime,
    ) -> StageRun:
        """Return a finished copy of this run."""
        if self.ended_at is not None:
            raise ConflictError(f"stage run {self.id} is already finished")
        return replace(
            self,
            status=status,
            output_artifact_id=output_artifact_id,
            ended_at=ended_at,
        )
