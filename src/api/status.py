"""Stable operation identifiers and completion states for the public API."""

from enum import StrEnum


class Operation(StrEnum):
    """Operations supported by the synchronous application facade."""

    VALIDATE_REPOSITORY = "validate_repository"
    COMPILE_REPOSITORY = "compile_repository"
    SCHEDULE_CURRICULUM = "schedule_curriculum"
    RENDER_SCHEDULE = "render_schedule"
    GENERATE_DOCUMENTS = "generate_documents"
    BUILD = "build"
    INSPECT_REPOSITORY = "inspect_repository"
    LIST_PLUGINS = "list_plugins"
    DOCTOR = "doctor"


class OperationStatus(StrEnum):
    """Stable outcome categories independent of internal exceptions."""

    SUCCESS = "success"
    SUCCESS_WITH_WARNINGS = "success_with_warnings"
    PARTIAL = "partial"
    VALIDATION_FAILURE = "validation_failure"
    EXECUTION_FAILURE = "execution_failure"
    CONFIGURATION_FAILURE = "configuration_failure"
    UNSUPPORTED_OPERATION = "unsupported_operation"

    @property
    def succeeded(self) -> bool:
        """Return whether the operation produced its requested result."""
        return self in {self.SUCCESS, self.SUCCESS_WITH_WARNINGS}


class PipelineStage(StrEnum):
    """Deterministic application pipeline stage identifiers."""

    LOAD = "load"
    VALIDATE = "validate"
    COMPILE = "compile"
    SCHEDULE = "schedule"
    RENDER = "render"
    GENERATE = "generate"

