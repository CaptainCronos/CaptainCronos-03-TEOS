"""CLI adapter over the stable TEOS Public Application API."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from src.api import (
    ENGINE_VERSION,
    BuildRequest,
    CompileRequest,
    DoctorRequest,
    GenerateRequest,
    OperationResponse,
    PipelineResult,
    RenderRequest,
    ScheduleRequest,
    TEOSApplication,
    ValidateRequest,
)
from src.api.services import ApplicationServices

from .commands import CommandName, CommandRequest
from .configuration import CliConfiguration
from .context import CliContext
from .exceptions import CommandError, PipelineError
from .progress import ProgressEvent, ProgressState


TEOS_VERSION = ENGINE_VERSION
_CLI_STAGE_NAMES = {
    "load": "repository loading",
    "validate": "validation",
    "compile": "compilation",
    "schedule": "scheduling",
    "render": "rendering",
    "generate": "generation",
}


class _RecordingService:
    """CLI-only contract decorator retaining causes for legacy exit handling."""

    def __init__(
        self, delegate: object, causes: dict[str, Exception], stage: str
    ) -> None:
        self._delegate = delegate
        self._causes = causes
        self._stage = stage

    def __getattr__(self, name: str):
        value = getattr(self._delegate, name)
        if not callable(value):
            return value

        def invoke(*args, **kwargs):
            try:
                return value(*args, **kwargs)
            except Exception as error:
                self._causes[self._stage] = error
                raise

        return invoke


class CliApplication:
    """Parse-free terminal adapter that delegates operations to the API."""

    def __init__(self, context: CliContext) -> None:
        self.context = context
        self._causes: dict[str, Exception] = {}
        services = context.services.application_services()
        recorded = ApplicationServices(
            repository=_RecordingService(
                services.repository, self._causes, "load"
            ),
            validation=_RecordingService(
                services.validation, self._causes, "validate"
            ),
            compilation=_RecordingService(
                services.compilation, self._causes, "compile"
            ),
            scheduling=_RecordingService(
                services.scheduling, self._causes, "schedule"
            ),
            rendering=_RecordingService(
                services.rendering, self._causes, "render"
            ),
            generation=_RecordingService(
                services.generation, self._causes, "generate"
            ),
            plugins=services.plugins,
        )
        self.api = TEOSApplication(
            services=recorded,
            clock=context.clock,
        )

    @property
    def configuration(self) -> CliConfiguration:
        """Return the immutable invocation configuration."""
        return self.context.configuration

    def execute(self, request: CommandRequest) -> None:
        """Execute one command through the API and present its result."""
        handlers: dict[CommandName, Callable[[CommandRequest], None]] = {
            CommandName.VALIDATE: self._validate,
            CommandName.COMPILE: self._compile,
            CommandName.SCHEDULE: self._schedule,
            CommandName.RENDER: self._render,
            CommandName.GENERATE: self._generate,
            CommandName.BUILD: self._build,
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

    def _request_values(self) -> dict[str, Any]:
        configuration = self.configuration
        return {
            "repository_path": configuration.repository,
            "institution_profile_id": configuration.institution_profile,
            "institution_profile_version": (
                configuration.institution_profile_version
            ),
            "academic_calendar_id": configuration.academic_calendar,
            "academic_calendar_version": (
                configuration.academic_calendar_version
            ),
            "renderer": configuration.renderer,
            "generator": configuration.generator,
            "output_directory": configuration.output_directory,
            "timing": configuration.timing,
        }

    def _consume(self, response: OperationResponse) -> PipelineResult:
        result = response.result
        if not isinstance(result, PipelineResult):
            raise CommandError("application operation returned no pipeline result")
        failed_stage = None
        for stage in result.stages:
            name = _CLI_STAGE_NAMES[stage.stage.value]
            self.context.progress.report(
                ProgressEvent(name, ProgressState.STARTED)
            )
            if stage.success:
                fields: dict[str, object] = {"stage": name}
                if stage.elapsed_seconds is not None:
                    fields["elapsed_seconds"] = stage.elapsed_seconds
                self.context.logger.info(
                    "pipeline.stage.completed", "stage completed", **fields
                )
                self.context.progress.report(
                    ProgressEvent(name, ProgressState.COMPLETED)
                )
            else:
                message = (
                    stage.diagnostics.items[0].message
                    if stage.diagnostics.items
                    else "application stage failed"
                )
                failed_stage = (stage.stage.value, name, message)
                self.context.logger.error(
                    "pipeline.stage.failed",
                    "stage failed",
                    stage=name,
                )
                self.context.progress.report(
                    ProgressEvent(name, ProgressState.FAILED, message)
                )
        if not response.success:
            if failed_stage is None:
                internal_name = response.operation.value
                name = internal_name
                message = (
                    response.errors[0].message
                    if response.errors
                    else "application operation failed"
                )
            else:
                internal_name, name, message = failed_stage
            cause = self._causes.get(internal_name, CommandError(message))
            raise PipelineError(name, cause)
        self.context.progress.report(
            ProgressEvent("completion", ProgressState.COMPLETED)
        )
        return result

    @staticmethod
    def _last_values(result: PipelineResult) -> dict[str, Any]:
        return dict(result.stages[-1].values)

    def _validate(self, request: CommandRequest) -> None:
        values = self._request_values()
        response = self.api.validate_repository(
            ValidateRequest(
                repository_path=values["repository_path"],
                timing=values["timing"],
            )
        )
        result = self._consume(response)
        fields = self._last_values(result)
        self.context.output.result("repository valid", **fields)

    def _compile(self, request: CommandRequest) -> None:
        response = self.api.compile_repository(
            CompileRequest(**self._request_values())
        )
        result = self._consume(response)
        self.context.output.result(
            "repository compiled", **self._last_values(result)
        )

    def _schedule(self, request: CommandRequest) -> None:
        response = self.api.schedule_curriculum(
            ScheduleRequest(**self._request_values())
        )
        result = self._consume(response)
        self.context.output.result(
            "repository scheduled", **self._last_values(result)
        )

    def _render(self, request: CommandRequest) -> None:
        response = self.api.render_schedule(
            RenderRequest(**self._request_values())
        )
        result = self._consume(response)
        self.context.output.result(
            "schedule rendered", **self._last_values(result)
        )

    def _generate(self, request: CommandRequest) -> None:
        response = self.api.generate_documents(
            GenerateRequest(**self._request_values())
        )
        result = self._consume(response)
        self.context.output.result(
            "document generated", **self._last_values(result)
        )

    def _build(self, request: CommandRequest) -> None:
        response = self.api.build(BuildRequest(**self._request_values()))
        result = self._consume(response)
        self.context.output.result(
            "document generated", **self._last_values(result)
        )

    def _info(self, request: CommandRequest) -> None:
        self.context.output.result(
            "TEOS CLI",
            version=self.api.engine_version,
            api_version=self.api.api_version,
            repository=self.configuration.repository,
            output=self.configuration.output_directory,
            renderer=self.configuration.renderer,
            generator=self.configuration.generator,
        )

    def _version(self, request: CommandRequest) -> None:
        self.context.output.result(f"teos {self.api.engine_version}")

    def _doctor(self, request: CommandRequest) -> None:
        response = self.api.doctor(
            DoctorRequest(
                repository_path=self.configuration.repository,
                timing=self.configuration.timing,
            )
        )
        if not response.success:
            message = "; ".join(
                diagnostic.message for diagnostic in response.errors
            )
            raise CommandError(message or "TEOS environment check failed")
        values = dict(response.result.values) if response.result else {}
        self.context.output.result("TEOS environment ready", **values)

    def _list(self, request: CommandRequest) -> None:
        target = request.target or "all"
        fields: dict[str, Any] = {}
        services = self.context.services.application_services()
        if target in {"all", "renderers"}:
            fields["renderers"] = services.rendering.available_renderers()
        if target in {"all", "generators"}:
            fields["generators"] = services.generation.available_generators()
        self.context.output.result("available components", **fields)
