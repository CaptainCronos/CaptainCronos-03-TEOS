"""Stable exception hierarchy for explicit public API misuse."""


class ApplicationError(Exception):
    """Base class for documented application-boundary failures."""


class ApplicationConfigurationError(ApplicationError):
    """Application or request configuration is invalid."""


class ApplicationOperationError(ApplicationError):
    """A requested application operation cannot be performed."""


class ApplicationPipelineError(ApplicationOperationError):
    """A pipeline stage failed while coordinating engine services."""

    def __init__(self, stage: str, cause: Exception) -> None:
        self.stage = stage
        self.cause = cause
        super().__init__(f"{stage} failed: {cause}")


class ApplicationCompatibilityError(ApplicationConfigurationError):
    """A requested public contract version is not supported."""


class ApplicationServiceError(ApplicationOperationError):
    """An injected or default application service failed unexpectedly."""


class UnsupportedApplicationOperationError(ApplicationOperationError):
    """The installed API does not implement the requested operation."""

