"""Private reusable deterministic application pipeline coordinator."""

from __future__ import annotations

from pathlib import Path
from time import perf_counter

from src.api.diagnostics import DiagnosticCollection
from src.api.requests import PipelineRequest
from src.api.results import (
    ArtifactResult,
    GeneratedFileResult,
    PipelineResult,
    StageResult,
)
from src.api.services import ApplicationServices
from src.api.status import OperationStatus, PipelineStage
from src.compiler import CompiledRepository
from src.generators import GeneratedFile
from src.rendering import RenderedArtifact
from src.repository import Repository
from src.scheduler import ScheduledRepository

from .context import PipelineContext
from .diagnostics import translate_exception
from .operation import PipelineExecution, StageExecution
from .services import RenderingProduct


_STAGE_ORDER = (
    PipelineStage.LOAD,
    PipelineStage.VALIDATE,
    PipelineStage.COMPILE,
    PipelineStage.SCHEDULE,
    PipelineStage.RENDER,
    PipelineStage.GENERATE,
)


class PipelineService:
    """Execute only the required prefix of the application pipeline."""

    def __init__(self, services: ApplicationServices) -> None:
        self.services = services

    def execute(
        self, context: PipelineContext, request: PipelineRequest
    ) -> PipelineExecution:
        """Run ordered stages and stop after the first fatal failure."""
        executions: list[StageExecution] = []
        previous: object | None = None
        failure_status: OperationStatus | None = None
        terminal_index = _STAGE_ORDER.index(context.terminal_stage)
        for stage in _STAGE_ORDER[: terminal_index + 1]:
            started = perf_counter()
            try:
                value = self._execute_stage(
                    stage, previous, request, context
                )
                values = _stage_values(stage, value)
                elapsed = (
                    round(perf_counter() - started, 6)
                    if context.operation.options.timing
                    else None
                )
                executions.append(
                    StageExecution(
                        StageResult(
                            stage,
                            OperationStatus.SUCCESS,
                            values,
                            elapsed_seconds=elapsed,
                        ),
                        value,
                    )
                )
                previous = value
            except Exception as error:
                failure_status, diagnostic = translate_exception(error, stage)
                elapsed = (
                    round(perf_counter() - started, 6)
                    if context.operation.options.timing
                    else None
                )
                executions.append(
                    StageExecution(
                        StageResult(
                            stage,
                            failure_status,
                            diagnostics=DiagnosticCollection((diagnostic,)),
                            elapsed_seconds=elapsed,
                        )
                    )
                )
                break
        return PipelineExecution(tuple(executions), failure_status)

    def _execute_stage(
        self,
        stage: PipelineStage,
        previous: object | None,
        request: PipelineRequest,
        context: PipelineContext,
    ) -> object:
        if stage is PipelineStage.LOAD:
            return self.services.repository.locate(request.repository_path)
        if stage is PipelineStage.VALIDATE:
            return self.services.validation.validate(request.repository_path)
        if stage is PipelineStage.COMPILE:
            return self.services.compilation.compile(previous)
        if stage is PipelineStage.SCHEDULE:
            return self.services.scheduling.schedule(
                previous,
                institution_profile_id=request.institution_profile_id,
                institution_profile_version=request.institution_profile_version,
                academic_calendar_id=request.academic_calendar_id,
                academic_calendar_version=request.academic_calendar_version,
            )
        if stage is PipelineStage.RENDER:
            return self.services.rendering.render(
                previous,
                renderer=request.renderer,
                generated_at=context.operation.generated_at,
            )
        return self.services.generation.generate(
            previous,
            generator=request.generator,
            output_directory=request.output_directory,
            asset_root=(
                request.repository_path
                if request.repository_path.is_dir()
                else request.repository_path.parent
            ),
        )

    @staticmethod
    def public_result(execution: PipelineExecution) -> PipelineResult:
        """Project private execution state into a stable public result."""
        stages = tuple(item.result for item in execution.stages)
        diagnostics = tuple(
            diagnostic
            for stage in stages
            for diagnostic in stage.diagnostics
        )
        successful = tuple(stage for stage in stages if stage.success)
        if execution.failure_status is None:
            status = (
                OperationStatus.SUCCESS_WITH_WARNINGS
                if any(
                    diagnostic.severity.value == "warning"
                    for diagnostic in diagnostics
                )
                else OperationStatus.SUCCESS
            )
        elif successful:
            status = OperationStatus.PARTIAL
        else:
            status = execution.failure_status
        artifacts = tuple(
            _artifact_result(item.value)
            for item in execution.stages
            if item.result.stage is PipelineStage.RENDER
            and item.result.success
            and isinstance(item.value, RenderingProduct)
        )
        generated = tuple(
            _generated_file_result(item.value)
            for item in execution.stages
            if item.result.stage is PipelineStage.GENERATE
            and item.result.success
            and isinstance(item.value, GeneratedFile)
        )
        return PipelineResult(
            status=status,
            values=(
                ("completed_stages", len(successful)),
                ("requested_stages", len(stages)),
            ),
            stages=stages,
            artifacts=artifacts,
            generated_files=generated,
        )


def _stage_values(
    stage: PipelineStage, value: object
) -> tuple[tuple[str, object], ...]:
    if stage is PipelineStage.LOAD:
        return (("sources", len(tuple(value))),)
    if stage is PipelineStage.VALIDATE and isinstance(value, Repository):
        return (("objects", len(value)), ("sources", len(value.sources)))
    if stage is PipelineStage.COMPILE and isinstance(
        value, CompiledRepository
    ):
        return (
            ("objects", len(value.dependency_order)),
            ("edges", len(value.graph.edges)),
        )
    if stage is PipelineStage.SCHEDULE and isinstance(
        value, ScheduledRepository
    ):
        sessions = sum(
            len(item.sessions) for item in value.institution_schedules
        )
        unscheduled = sum(
            len(item.unscheduled_sessions)
            for item in value.institution_schedules
        )
        return (("sessions", sessions), ("unscheduled", unscheduled))
    if stage is PipelineStage.RENDER and isinstance(value, RenderingProduct):
        artifact = value.artifact
        return (
            ("artifact", str(artifact.identifier)),
            ("format", artifact.output_format.value),
            ("filename", artifact.output_filename.as_posix()),
        )
    if stage is PipelineStage.GENERATE and isinstance(value, GeneratedFile):
        return (
            ("path", value.path),
            ("bytes", value.size_bytes),
            ("checksum", value.checksum),
        )
    return ()


def _artifact_result(product: RenderingProduct) -> ArtifactResult:
    artifact = product.artifact
    return ArtifactResult(
        str(artifact.identifier),
        artifact.renderer,
        artifact.output_format.value,
        artifact.content_type,
        artifact.output_filename.as_posix(),
        artifact.source_fingerprint,
    )


def _generated_file_result(value: GeneratedFile) -> GeneratedFileResult:
    return GeneratedFileResult(
        Path(value.path),
        value.filename,
        value.mime_type,
        value.checksum,
        value.size_bytes,
        value.generation_timestamp,
    )

