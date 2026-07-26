"""Default thin adapters over completed TEOS architectural components."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path, PurePosixPath
from typing import cast
from uuid import UUID

from src.api.exceptions import ApplicationConfigurationError
from src.api.results import PluginResult
from src.api.services import ApplicationServices
from src.compiler import CompiledRepository, CurriculumCompiler
from src.generators import GeneratorRegistry, UnsupportedGeneratorError
from src.models import AcademicCalendar, InstitutionProfile
from src.models.lifecycle import ArtifactType, OutputFormat
from src.plugins import PluginDiscovery
from src.rendering import (
    InstitutionBranding,
    RenderOptions,
    RenderedArtifact,
    RendererRegistry,
    RenderingContext,
    Template,
    TemplateRegion,
    UnsupportedRendererError,
)
from src.repository import Repository
from src.repository.loader import RepositoryLoader
from src.scheduler import ScheduledRepository, Scheduler, SchedulingContext


@dataclass(frozen=True, slots=True)
class RenderingProduct:
    """Private values required to continue from rendering to generation."""

    artifact: RenderedArtifact
    template: Template
    context: RenderingContext


@dataclass(frozen=True, slots=True)
class RepositoryApplicationService:
    """Adapt deterministic source discovery."""

    loader: RepositoryLoader

    def locate(self, location: str | Path) -> tuple[Path, ...]:
        return self.loader.locate(location)


@dataclass(frozen=True, slots=True)
class ValidationApplicationService:
    """Adapt authoritative loader validation."""

    loader: RepositoryLoader

    def validate(self, location: str | Path) -> object:
        return self.loader.load(location)


@dataclass(frozen=True, slots=True)
class CompilationApplicationService:
    """Adapt the curriculum compiler."""

    compiler: CurriculumCompiler

    def compile(self, repository: object) -> object:
        if not isinstance(repository, Repository):
            raise ApplicationConfigurationError(
                "compilation requires a validated repository"
            )
        return self.compiler.compile(repository)


def _select_object(
    repository: Repository,
    object_type: type[object],
    identifier: str | None,
    version: str | None,
    label: str,
) -> object:
    if identifier is not None:
        try:
            value = repository.registry.lookup(UUID(identifier), version)
        except (KeyError, ValueError) as error:
            raise ApplicationConfigurationError(
                f"could not select {label}: {identifier}"
            ) from error
        if not isinstance(value, object_type):
            raise ApplicationConfigurationError(
                f"selected {label} has type {type(value).__name__}"
            )
        return value
    candidates = repository.registry.by_type(object_type)
    if len(candidates) != 1:
        raise ApplicationConfigurationError(
            f"{label} must be specified when the repository contains "
            f"{len(candidates)} candidates"
        )
    return candidates[0]


@dataclass(frozen=True, slots=True)
class SchedulingApplicationService:
    """Adapt context selection and the deterministic scheduler."""

    scheduler: Scheduler

    def schedule(
        self,
        compiled: object,
        *,
        institution_profile_id: str | None,
        institution_profile_version: str | None,
        academic_calendar_id: str | None,
        academic_calendar_version: str | None,
    ) -> object:
        if not isinstance(compiled, CompiledRepository):
            raise ApplicationConfigurationError(
                "scheduling requires compiled curriculum"
            )
        profile = cast(
            InstitutionProfile,
            _select_object(
                compiled.source,
                InstitutionProfile,
                institution_profile_id,
                institution_profile_version,
                "institution profile",
            ),
        )
        calendar = cast(
            AcademicCalendar,
            _select_object(
                compiled.source,
                AcademicCalendar,
                academic_calendar_id,
                academic_calendar_version,
                "academic calendar",
            ),
        )
        return self.scheduler.schedule_repository(
            compiled, (SchedulingContext(profile, calendar),)
        )


@dataclass(frozen=True, slots=True)
class RenderingApplicationService:
    """Adapt renderer selection and the default schedule presentation."""

    renderers: RendererRegistry

    def render(
        self, scheduled: object, *, renderer: str, generated_at: datetime
    ) -> object:
        if not isinstance(scheduled, ScheduledRepository):
            raise ApplicationConfigurationError(
                "rendering requires a scheduled repository"
            )
        try:
            selected = self.renderers.select(renderer)
            output_format = OutputFormat(renderer)
        except (UnsupportedRendererError, ValueError) as error:
            raise ApplicationConfigurationError(
                f"unsupported renderer selection: {renderer}"
            ) from error
        template = Template(
            identifier="teos-api-schedule",
            version="1.0.0",
            artifact_type=ArtifactType.SCHEDULE,
            supported_formats=(output_format,),
            regions=(
                TemplateRegion("title", "heading"),
                TemplateRegion("schedule", "table"),
            ),
        )
        profile = scheduled.institution_schedules[0].institution_profile
        context = RenderingContext(
            options=RenderOptions(
                PurePosixPath(
                    f"course-schedule{selected.file_extension}"
                ),
                generated_at,
            ),
            branding=InstitutionBranding(profile.display_name()),
        )
        return RenderingProduct(
            selected.render(scheduled, template, context), template, context
        )

    def available_renderers(self) -> tuple[str, ...]:
        return tuple(renderer.name for renderer in self.renderers)


@dataclass(frozen=True, slots=True)
class GenerationApplicationService:
    """Adapt generator selection and physical artifact generation."""

    generators: GeneratorRegistry

    def generate(
        self,
        rendered: object,
        *,
        generator: str,
        output_directory: str | Path,
        asset_root: str | Path,
    ) -> object:
        if not isinstance(rendered, RenderingProduct):
            raise ApplicationConfigurationError(
                "generation requires a rendering product"
            )
        if generator != rendered.artifact.output_format.value:
            raise ApplicationConfigurationError(
                "renderer and generator selections must match for generation"
            )
        try:
            selected = self.generators.select(generator)
        except UnsupportedGeneratorError as error:
            raise ApplicationConfigurationError(
                f"unsupported generator selection: {generator}"
            ) from error
        return selected.generate(
            rendered.artifact,
            output_directory,
            template=rendered.template,
            context=rendered.context,
            asset_root=asset_root,
        )

    def available_generators(self) -> tuple[str, ...]:
        return tuple(generator.name for generator in self.generators)


@dataclass(frozen=True, slots=True)
class PluginApplicationService:
    """Adapt side-effect-free plugin metadata discovery."""

    discovery: PluginDiscovery

    def list_plugins(self) -> tuple[PluginResult, ...]:
        return tuple(
            PluginResult(
                candidate.metadata.identifier,
                str(candidate.metadata.version),
                candidate.metadata.name,
                candidate.metadata.capabilities,
                candidate.source,
            )
            for candidate in self.discovery.discover()
        )


def default_services(
    *,
    loader: RepositoryLoader | None = None,
    compiler: CurriculumCompiler | None = None,
    scheduler: Scheduler | None = None,
    renderers: RendererRegistry | None = None,
    generators: GeneratorRegistry | None = None,
    discovery: PluginDiscovery | None = None,
) -> ApplicationServices:
    """Create the complete default public service bundle."""
    selected_loader = loader or RepositoryLoader()
    return ApplicationServices(
        repository=RepositoryApplicationService(selected_loader),
        validation=ValidationApplicationService(selected_loader),
        compilation=CompilationApplicationService(
            compiler or CurriculumCompiler()
        ),
        scheduling=SchedulingApplicationService(scheduler or Scheduler()),
        rendering=RenderingApplicationService(
            renderers or RendererRegistry.with_defaults()
        ),
        generation=GenerationApplicationService(
            generators or GeneratorRegistry.with_defaults()
        ),
        plugins=PluginApplicationService(discovery or PluginDiscovery()),
    )
