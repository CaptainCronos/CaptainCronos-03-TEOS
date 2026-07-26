"""Immutable bundle of public service contracts used by the facade."""

from __future__ import annotations

from dataclasses import dataclass

from .contracts import (
    CompilationService,
    GenerationService,
    PluginService,
    RenderingService,
    RepositoryService,
    SchedulingService,
    ValidationService,
)


@dataclass(frozen=True, slots=True)
class ApplicationServices:
    """Complete injectable service set for one application facade."""

    repository: RepositoryService
    validation: ValidationService
    compilation: CompilationService
    scheduling: SchedulingService
    rendering: RenderingService
    generation: GenerationService
    plugins: PluginService

