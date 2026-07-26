"""Immutable responses returned by public application operations."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .diagnostics import (
    Diagnostic,
    DiagnosticCollection,
    DiagnosticSeverity,
)
from .results import (
    GeneratedFileResult,
    OperationResult,
    PipelineResult,
    PluginResult,
)
from .status import Operation, OperationStatus


@dataclass(frozen=True, slots=True)
class SourceInformation:
    """Stable source paths associated with an application response."""

    repository: Path | None = None
    documents: tuple[Path, ...] = ()

    def __post_init__(self) -> None:
        if self.repository is not None:
            object.__setattr__(self, "repository", Path(self.repository))
        object.__setattr__(
            self, "documents", tuple(Path(item) for item in self.documents)
        )


@dataclass(frozen=True, slots=True)
class OperationResponse:
    """Common immutable response envelope."""

    operation: Operation | str
    status: OperationStatus
    result: OperationResult | None = None
    diagnostics: DiagnosticCollection = DiagnosticCollection()
    elapsed_seconds: float | None = None
    source: SourceInformation = SourceInformation()

    @property
    def success(self) -> bool:
        """Return whether the requested operation completed."""
        return self.status.succeeded

    @property
    def warnings(self) -> tuple[Diagnostic, ...]:
        """Return warning diagnostics."""
        return self.diagnostics.by_severity(DiagnosticSeverity.WARNING)

    @property
    def errors(self) -> tuple[Diagnostic, ...]:
        """Return error and fatal diagnostics."""
        return self.diagnostics.by_severity(
            DiagnosticSeverity.ERROR, DiagnosticSeverity.FATAL
        )

    @property
    def stages(self):
        """Return pipeline stages when the response carries a pipeline result."""
        if isinstance(self.result, PipelineResult):
            return self.result.stages
        return ()


@dataclass(frozen=True, slots=True)
class ValidationResponse(OperationResponse):
    """Response from repository validation."""


@dataclass(frozen=True, slots=True)
class CompilationResponse(OperationResponse):
    """Response from repository compilation."""


@dataclass(frozen=True, slots=True)
class SchedulingResponse(OperationResponse):
    """Response from curriculum scheduling."""


@dataclass(frozen=True, slots=True)
class RenderingResponse(OperationResponse):
    """Response from schedule rendering."""


@dataclass(frozen=True, slots=True)
class GenerationResponse(OperationResponse):
    """Response from document generation."""

    @property
    def generated_files(self) -> tuple[GeneratedFileResult, ...]:
        if isinstance(self.result, PipelineResult):
            return self.result.generated_files
        return ()


@dataclass(frozen=True, slots=True)
class BuildResponse(GenerationResponse):
    """Response from a canonical complete build."""


@dataclass(frozen=True, slots=True)
class InspectionResponse(OperationResponse):
    """Response from repository inspection."""


@dataclass(frozen=True, slots=True)
class DoctorResponse(OperationResponse):
    """Response from application readiness checks."""


@dataclass(frozen=True, slots=True)
class PluginListResponse(OperationResponse):
    """Response from plugin discovery."""

    plugins: tuple[PluginResult, ...] = ()
