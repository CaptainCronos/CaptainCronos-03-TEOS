"""Immutable public result descriptors that hide engine implementations."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

from .diagnostics import DiagnosticCollection
from .status import OperationStatus, PipelineStage


def _freeze_value(value: Any) -> Any:
    if isinstance(value, dict):
        return tuple(
            (str(key), _freeze_value(child))
            for key, child in sorted(
                value.items(), key=lambda item: str(item[0])
            )
        )
    if isinstance(value, (list, tuple)):
        return tuple(_freeze_value(child) for child in value)
    if isinstance(value, set):
        return tuple(sorted((_freeze_value(child) for child in value), key=repr))
    return value


@dataclass(frozen=True, slots=True)
class OperationResult:
    """Stable summary for a completed application operation."""

    status: OperationStatus
    values: tuple[tuple[str, Any], ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "values", tuple(_freeze_value(self.values)))

    def get(self, name: str, default: Any = None) -> Any:
        """Return one named summary value."""
        return dict(self.values).get(name, default)


@dataclass(frozen=True, slots=True)
class StageResult:
    """Public summary of one attempted pipeline stage."""

    stage: PipelineStage
    status: OperationStatus
    values: tuple[tuple[str, Any], ...] = ()
    diagnostics: DiagnosticCollection = DiagnosticCollection()
    elapsed_seconds: float | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "values", tuple(_freeze_value(self.values)))

    @property
    def success(self) -> bool:
        """Return whether this stage completed successfully."""
        return self.status.succeeded

    def get(self, name: str, default: Any = None) -> Any:
        """Return one named stage summary value."""
        return dict(self.values).get(name, default)


@dataclass(frozen=True, slots=True)
class ArtifactResult:
    """Stable descriptor for one rendered artifact."""

    identifier: str
    renderer: str
    output_format: str
    content_type: str
    filename: str
    source_fingerprint: str


@dataclass(frozen=True, slots=True)
class GeneratedFileResult:
    """Stable descriptor for one generated physical file."""

    path: Path
    filename: str
    mime_type: str
    checksum: str
    size_bytes: int
    generation_timestamp: datetime

    def __post_init__(self) -> None:
        object.__setattr__(self, "path", Path(self.path))


@dataclass(frozen=True, slots=True)
class PluginResult:
    """Public metadata descriptor for one discovered plugin."""

    identifier: str
    version: str
    name: str
    capabilities: tuple[str, ...]
    source: str


@dataclass(frozen=True, slots=True)
class PipelineResult(OperationResult):
    """Ordered summaries and artifacts retained from a pipeline execution."""

    stages: tuple[StageResult, ...] = ()
    artifacts: tuple[ArtifactResult, ...] = ()
    generated_files: tuple[GeneratedFileResult, ...] = ()
