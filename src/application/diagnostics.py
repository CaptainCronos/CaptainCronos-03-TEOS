"""Private translation from engine failures to stable public diagnostics."""

from __future__ import annotations

from pathlib import Path

from src.api.diagnostics import (
    Diagnostic,
    DiagnosticCode,
    DiagnosticLocation,
    DiagnosticSeverity,
)
from src.api.exceptions import (
    ApplicationCompatibilityError,
    ApplicationConfigurationError,
)
from src.api.status import OperationStatus, PipelineStage
from src.repository.exceptions import RepositoryError


def translate_exception(
    error: Exception, stage: PipelineStage | str
) -> tuple[OperationStatus, Diagnostic]:
    """Translate an internal exception without publishing a traceback."""
    stage_name = stage.value if isinstance(stage, PipelineStage) else stage
    location = None
    severity = DiagnosticSeverity.FATAL
    if isinstance(error, RepositoryError):
        location = DiagnosticLocation(
            source=error.source,
            object_identifier=(
                str(error.details.get("identifier"))
                if error.details.get("identifier") is not None
                else None
            ),
            field_path=error.path,
        )
        return (
            OperationStatus.VALIDATION_FAILURE,
            Diagnostic(
                DiagnosticCode(
                    f"teos.{stage_name}.{type(error).__name__}"
                ),
                severity,
                error.message,
                stage_name,
                location,
            ),
        )
    if isinstance(
        error, (ApplicationConfigurationError, ApplicationCompatibilityError)
    ):
        status = OperationStatus.CONFIGURATION_FAILURE
        prefix = "configuration"
    else:
        status = OperationStatus.EXECUTION_FAILURE
        prefix = "execution"
        source = getattr(error, "source", None)
        path = getattr(error, "path", ())
        identifier = getattr(error, "object_identifier", None)
        if source is not None or path or identifier is not None:
            location = DiagnosticLocation(
                Path(source) if source is not None else None,
                str(identifier) if identifier is not None else None,
                tuple(path),
            )
    return (
        status,
        Diagnostic(
            DiagnosticCode(
                f"teos.{stage_name}.{prefix}.{type(error).__name__}"
            ),
            severity,
            str(error) or type(error).__name__,
            stage_name,
            location,
        ),
    )

