"""Application service that coordinates existing TEOS pipeline components."""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path, PurePosixPath
from time import perf_counter
from typing import Any, TypeVar
from uuid import UUID

from src.compiler import CompiledRepository
from src.generators import GeneratedFile
from src.models import AcademicCalendar, InstitutionProfile
from src.models.lifecycle import ArtifactType, OutputFormat
from src.rendering import (
    InstitutionBranding,
    RenderOptions,
    RenderedArtifact,
    RenderingContext,
    Template,
    TemplateRegion,
)
from src.repository import Repository
from src.scheduler import ScheduledRepository, SchedulingContext

from .commands import CommandName, CommandRequest
from .configuration import CliConfiguration
from .context import CliContext
from .exceptions import CliError, CommandError, ConfigurationError, PipelineError
from .progress import ProgressEvent, ProgressState


TEOS_VERSION = "1.1.0"
Result = TypeVar("Result")


class CliApplication:
    """Dispatch commands and execute only the required pipeline prefix."""

    def __init__(self, context: CliContext) -> None:
        self.context = context

    @property
    def configuration(self) -> CliConfiguration:
        """Return the immutable invocation configuration."""
        return self.context.configuration

    def execute(self, request: CommandRequest) -> None:
        """Execute one command and present its result."""
        handlers: dict[CommandName, Callable[[CommandRequest], None]] = {
            CommandName.VALIDATE: self._validate,
            CommandName.COMPILE: self._compile,
            CommandName.SCHEDULE: self._schedule,
            CommandName.RENDER: self._render,
            CommandName.GENERATE: self._generate,
            CommandName.BUILD: self._generate,
            CommandName.INFO: self._info,
            CommandName.VERSION: self._version,
            CommandName.DOCTOR: self._doctor,
            CommandName.LIST: self._list,
        }
        try:
            handler = handlers[request.name]
        except KeyError as error:
            raise CommandError(f"unsupported command: {request.name}") from error
        handler(request)

    def _stage(self, name: str, operation: Callable[[], Result]) -> Result:
        self.context.progress.report(
            ProgressEvent(name, ProgressState.STARTED)
        )
        self.context.logger.debug(
            "pipeline.stage.started", "stage started", stage=name
        )
        started = perf_counter()
        try:
            result = operation()
        except PipelineError:
            raise
        except CliError as error:
            self.context.progress.report(
                ProgressEvent(name, ProgressState.FAILED, str(error))
            )
            self.context.logger.error(
                "pipeline.stage.failed",
                "stage failed",
                stage=name,
                cause=type(error).__name__,
            )
            raise
        except Exception as error:
            self.context.progress.report(
                ProgressEvent(name, ProgressState.FAILED, str(error))
            )
            self.context.logger.error(
                "pipeline.stage.failed",
                "stage failed",
                stage=name,
                cause=type(error).__name__,
            )
            raise PipelineError(name, error) from error
        fields: dict[str, object] = {"stage": name}
        if self.configuration.timing:
            fields["elapsed_seconds"] = round(perf_counter() - started, 6)
        self.context.logger.info(
            "pipeline.stage.completed", "stage completed", **fields
        )
        self.context.progress.report(
            ProgressEvent(name, ProgressState.COMPLETED)
        )
        return result

    def _repository(self) -> Repository:
        loader = self.context.services.repository_loader
        self._stage(
            "repository loading",
            lambda: loader.locate(self.configuration.repository),
        )
        return self._stage(
            "validation",
            lambda: loader.load(self.configuration.repository),
        )

    def _compiled(self) -> CompiledRepository:
        repository = self._repository()
        return self._stage(
            "compilation",
            lambda: self.context.services.compiler.compile(repository),
        )

    def _scheduled(self) -> ScheduledRepository:
        compiled = self._compiled()

        def schedule() -> ScheduledRepository:
            profile = self._select_object(
                compiled.source,
                InstitutionProfile,
                self.configuration.institution_profile,
                self.configuration.institution_profile_version,
                "institution profile",
            )
            calendar = self._select_object(
                compiled.source,
                AcademicCalendar,
                self.configuration.academic_calendar,
                self.configuration.academic_calendar_version,
                "academic calendar",
            )
            return self.context.services.scheduler.schedule_repository(
                compiled, (SchedulingContext(profile, calendar),)
            )

        return self._stage("scheduling", schedule)

    def _rendered(
        self,
    ) -> tuple[RenderedArtifact, Template, RenderingContext]:
        scheduled = self._scheduled()

        def render() -> tuple[RenderedArtifact, Template, RenderingContext]:
            renderer = self.context.services.renderers.select(
                self.configuration.renderer
            )
            output_format = OutputFormat(self.configuration.renderer)
            template = Template(
                identifier="teos-cli-schedule",
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
                        f"course-schedule{renderer.file_extension}"
                    ),
                    self.context.clock(),
                ),
                branding=InstitutionBranding(profile.display_name()),
            )
            return renderer.render(scheduled, template, context), template, context

        return self._stage("rendering", render)

    def _generated(self) -> GeneratedFile:
        if self.configuration.generator != self.configuration.renderer:
            raise ConfigurationError(
                "renderer and generator selections must match for generation"
            )
        artifact, template, rendering_context = self._rendered()
        return self._stage(
            "generation",
            lambda: self.context.services.generators.select(
                self.configuration.generator
            ).generate(
                artifact,
                self.configuration.output_directory,
                template=template,
                context=rendering_context,
                asset_root=(
                    self.configuration.repository
                    if self.configuration.repository.is_dir()
                    else self.configuration.repository.parent
                ),
            ),
        )

    @staticmethod
    def _select_object(
        repository: Repository,
        object_type: type[Result],
        identifier: str | None,
        version: str | None,
        label: str,
    ) -> Result:
        if identifier is not None:
            try:
                value = repository.registry.lookup(UUID(identifier), version)
            except (KeyError, ValueError) as error:
                raise ConfigurationError(
                    f"could not select {label}: {identifier}"
                ) from error
            if not isinstance(value, object_type):
                raise ConfigurationError(
                    f"selected {label} has type {type(value).__name__}"
                )
            return value
        candidates = repository.registry.by_type(object_type)
        if len(candidates) != 1:
            raise ConfigurationError(
                f"{label} must be specified when the repository contains "
                f"{len(candidates)} candidates"
            )
        value = candidates[0]
        if not isinstance(value, object_type):
            raise ConfigurationError(f"invalid {label} registry entry")
        return value

    def _complete(self) -> None:
        self.context.progress.report(
            ProgressEvent("completion", ProgressState.COMPLETED)
        )

    def _validate(self, request: CommandRequest) -> None:
        repository = self._repository()
        self._complete()
        self.context.output.result(
            "repository valid",
            objects=len(repository),
            sources=len(repository.sources),
        )

    def _compile(self, request: CommandRequest) -> None:
        compiled = self._compiled()
        self._complete()
        self.context.output.result(
            "repository compiled",
            objects=len(compiled.dependency_order),
            edges=len(compiled.graph.edges),
        )

    def _schedule(self, request: CommandRequest) -> None:
        scheduled = self._scheduled()
        schedule = scheduled.institution_schedules[0]
        self._complete()
        self.context.output.result(
            "repository scheduled",
            sessions=len(schedule.sessions),
            unscheduled=len(schedule.unscheduled_sessions),
        )

    def _render(self, request: CommandRequest) -> None:
        artifact, _, _ = self._rendered()
        self._complete()
        self.context.output.result(
            "schedule rendered",
            artifact=str(artifact.identifier),
            format=artifact.output_format.value,
            filename=artifact.output_filename.as_posix(),
        )

    def _generate(self, request: CommandRequest) -> None:
        generated = self._generated()
        self._complete()
        self.context.output.result(
            "document generated",
            path=generated.path,
            bytes=generated.size_bytes,
            checksum=generated.checksum,
        )

    def _info(self, request: CommandRequest) -> None:
        self.context.output.result(
            "TEOS CLI",
            version=TEOS_VERSION,
            repository=self.configuration.repository,
            output=self.configuration.output_directory,
            renderer=self.configuration.renderer,
            generator=self.configuration.generator,
        )

    def _version(self, request: CommandRequest) -> None:
        self.context.output.result(f"teos {TEOS_VERSION}")

    def _doctor(self, request: CommandRequest) -> None:
        repository = self.configuration.repository
        schema = Path("schemas")
        failures = []
        if not repository.exists():
            failures.append(f"repository not found: {repository}")
        if not schema.is_dir():
            failures.append(f"schema directory not found: {schema}")
        if failures:
            raise CommandError("; ".join(failures))
        self.context.output.result(
            "TEOS environment ready",
            generators=len(tuple(self.context.services.generators)),
            renderers=len(tuple(self.context.services.renderers)),
        )

    def _list(self, request: CommandRequest) -> None:
        target = request.target or "all"
        fields: dict[str, Any] = {}
        if target in {"all", "renderers"}:
            fields["renderers"] = tuple(
                renderer.name for renderer in self.context.services.renderers
            )
        if target in {"all", "generators"}:
            fields["generators"] = tuple(
                generator.name for generator in self.context.services.generators
            )
        self.context.output.result("available components", **fields)
