"""Private immutable execution contexts for application orchestration."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime

from src.api.requests import ApplicationRequest
from src.api.services import ApplicationServices
from src.api.status import Operation, PipelineStage

from .configuration import ApplicationConfiguration


@dataclass(frozen=True, slots=True)
class ExecutionOptions:
    """Cross-stage execution controls derived from a public request."""

    timing: bool = False
    diagnostic_verbosity: str = "normal"


@dataclass(frozen=True, slots=True)
class ApplicationContext:
    """Long-lived dependencies for one facade instance."""

    configuration: ApplicationConfiguration
    services: ApplicationServices
    clock: Callable[[], datetime]


@dataclass(frozen=True, slots=True)
class OperationContext:
    """Complete immutable input for one facade operation."""

    operation: Operation
    request: ApplicationRequest
    options: ExecutionOptions
    generated_at: datetime


@dataclass(frozen=True, slots=True)
class PipelineContext:
    """Immutable pipeline selection for one operation."""

    operation: OperationContext
    terminal_stage: PipelineStage

