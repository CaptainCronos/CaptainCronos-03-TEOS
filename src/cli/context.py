"""Runtime dependencies and I/O context for CLI orchestration."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime, timezone

from src.compiler import CurriculumCompiler
from src.generators import GeneratorRegistry
from src.rendering import RendererRegistry
from src.repository.loader import RepositoryLoader
from src.scheduler import Scheduler

from .configuration import CliConfiguration
from .logging import StructuredLogger
from .output import OutputWriter
from .progress import ProgressReporter


@dataclass(frozen=True, slots=True)
class PipelineServices:
    """Injectable existing-engine services used by the CLI application."""

    repository_loader: RepositoryLoader = field(
        default_factory=RepositoryLoader
    )
    compiler: CurriculumCompiler = field(default_factory=CurriculumCompiler)
    scheduler: Scheduler = field(default_factory=Scheduler)
    renderers: RendererRegistry = field(
        default_factory=RendererRegistry.with_defaults
    )
    generators: GeneratorRegistry = field(
        default_factory=GeneratorRegistry.with_defaults
    )


def utc_now() -> datetime:
    """Return the current aware UTC time for artifact request metadata."""
    return datetime.now(timezone.utc)


@dataclass(frozen=True, slots=True)
class CliContext:
    """Complete runtime context for one CLI application invocation."""

    configuration: CliConfiguration
    logger: StructuredLogger
    progress: ProgressReporter
    output: OutputWriter
    services: PipelineServices = field(default_factory=PipelineServices)
    clock: Callable[[], datetime] = utc_now
