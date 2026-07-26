"""Private operation records retaining opaque engine values between stages."""

from __future__ import annotations

from dataclasses import dataclass

from src.api.results import StageResult


@dataclass(frozen=True, slots=True)
class StageExecution:
    """One public stage summary paired with its private engine output."""

    result: StageResult
    value: object | None = None


@dataclass(frozen=True, slots=True)
class PipelineExecution:
    """Private complete pipeline execution state."""

    stages: tuple[StageExecution, ...]
    failure_status: object | None = None

    @property
    def value(self) -> object | None:
        """Return the last successful private stage value."""
        for stage in reversed(self.stages):
            if stage.result.success:
                return stage.value
        return None

