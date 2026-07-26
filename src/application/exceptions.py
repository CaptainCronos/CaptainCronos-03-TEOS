"""Private aliases and helpers for application-level exception translation."""

from src.api.exceptions import (
    ApplicationCompatibilityError,
    ApplicationConfigurationError,
    ApplicationError,
    ApplicationOperationError,
    ApplicationPipelineError,
    ApplicationServiceError,
    UnsupportedApplicationOperationError,
)

__all__ = [
    "ApplicationCompatibilityError",
    "ApplicationConfigurationError",
    "ApplicationError",
    "ApplicationOperationError",
    "ApplicationPipelineError",
    "ApplicationServiceError",
    "UnsupportedApplicationOperationError",
]

