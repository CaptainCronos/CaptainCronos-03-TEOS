"""Primary synchronous facade for the stable TEOS application API."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from time import perf_counter
from typing import TypeVar

from src.application.configuration import (
    API_VERSION,
    ENGINE_VERSION,
    SUPPORTED_CONTRACT_VERSION,
    ApplicationConfiguration,
)
from src.application.context import (
    ApplicationContext,
    ExecutionOptions,
    OperationContext,
    PipelineContext,
)
from src.application.diagnostics import translate_exception
from src.application.pipeline import PipelineService
from src.application.services import default_services

from .diagnostics import (
    Diagnostic,
    DiagnosticCode,
    DiagnosticCollection,
    DiagnosticLocation,
    DiagnosticSeverity,
)
from .exceptions import ApplicationCompatibilityError
from .requests import (
    BuildRequest,
    CompileRequest,
    DoctorRequest,
    GenerateRequest,
    InspectRequest,
    ListPluginsRequest,
    PipelineRequest,
    RenderRequest,
    ScheduleRequest,
    ValidateRequest,
)
from .responses import (
    BuildResponse,
    CompilationResponse,
    DoctorResponse,
    GenerationResponse,
    InspectionResponse,
    OperationResponse,
    PluginListResponse,
    RenderingResponse,
    SchedulingResponse,
    SourceInformation,
    ValidationResponse,
)
from .results import OperationResult, PipelineResult
from .services import ApplicationServices
from .status import Operation, OperationStatus, PipelineStage


ResponseType = TypeVar("ResponseType", bound=OperationResponse)


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


class TEOSApplication:
    """Stable synchronous entry point for TEOS application operations."""

    def __init__(
        self,
        *,
        services: ApplicationServices | None = None,
        clock=_utc_now,
    ) -> None:
        self._context = ApplicationContext(
            ApplicationConfiguration(), services or default_services(), clock
        )
        self._pipeline = PipelineService(self._context.services)

    @property
    def api_version(self) -> str:
        """Return the installed public API version."""
        return API_VERSION

    @property
    def engine_version(self) -> str:
        """Return the coordinated TEOS engine version."""
        return ENGINE_VERSION

    @property
    def supported_contract_version(self) -> str:
        """Return the one supported service contract version."""
        return SUPPORTED_CONTRACT_VERSION

    def execute(
        self, operation: Operation | str, request
    ) -> OperationResponse:
        """Dispatch a public operation or return an unsupported response."""
        try:
            selected = Operation(operation)
        except (TypeError, ValueError):
            diagnostic = Diagnostic(
                DiagnosticCode("teos.operation.unsupported"),
                DiagnosticSeverity.ERROR,
                f"unsupported operation: {operation}",
                "dispatch",
            )
            return OperationResponse(
                str(operation),
                OperationStatus.UNSUPPORTED_OPERATION,
                OperationResult(OperationStatus.UNSUPPORTED_OPERATION),
                DiagnosticCollection((diagnostic,)),
            )
        handlers = {
            Operation.VALIDATE_REPOSITORY: self.validate_repository,
            Operation.COMPILE_REPOSITORY: self.compile_repository,
            Operation.SCHEDULE_CURRICULUM: self.schedule_curriculum,
            Operation.RENDER_SCHEDULE: self.render_schedule,
            Operation.GENERATE_DOCUMENTS: self.generate_documents,
            Operation.BUILD: self.build,
            Operation.INSPECT_REPOSITORY: self.inspect_repository,
            Operation.LIST_PLUGINS: self.list_plugins,
            Operation.DOCTOR: self.doctor,
        }
        try:
            return handlers[selected](request)
        except (AttributeError, TypeError, ValueError) as error:
            status, diagnostic = translate_exception(error, "dispatch")
            return OperationResponse(
                selected,
                status,
                diagnostics=DiagnosticCollection((diagnostic,)),
            )

    def validate_repository(
        self, request: ValidateRequest
    ) -> ValidationResponse:
        """Load and authoritatively validate a repository."""
        return self._run_pipeline(
            Operation.VALIDATE_REPOSITORY,
            request,
            PipelineStage.VALIDATE,
            ValidationResponse,
        )

    def compile_repository(
        self, request: CompileRequest
    ) -> CompilationResponse:
        """Compile one validated repository."""
        return self._run_pipeline(
            Operation.COMPILE_REPOSITORY,
            request,
            PipelineStage.COMPILE,
            CompilationResponse,
        )

    def schedule_curriculum(
        self, request: ScheduleRequest
    ) -> SchedulingResponse:
        """Compile and schedule repository curriculum."""
        return self._run_pipeline(
            Operation.SCHEDULE_CURRICULUM,
            request,
            PipelineStage.SCHEDULE,
            SchedulingResponse,
        )

    def render_schedule(self, request: RenderRequest) -> RenderingResponse:
        """Run the required pipeline through side-effect-free rendering."""
        return self._run_pipeline(
            Operation.RENDER_SCHEDULE,
            request,
            PipelineStage.RENDER,
            RenderingResponse,
        )

    def generate_documents(
        self, request: GenerateRequest
    ) -> GenerationResponse:
        """Run the complete pipeline through physical generation."""
        return self._run_pipeline(
            Operation.GENERATE_DOCUMENTS,
            request,
            PipelineStage.GENERATE,
            GenerationResponse,
        )

    def build(self, request: BuildRequest) -> BuildResponse:
        """Run the canonical complete TEOS build."""
        return self._run_pipeline(
            Operation.BUILD,
            request,
            PipelineStage.GENERATE,
            BuildResponse,
        )

    def inspect_repository(
        self, request: InspectRequest
    ) -> InspectionResponse:
        """Return a stable inventory without publishing repository objects."""
        pipeline_request = PipelineRequest(
            timing=request.timing,
            diagnostic_verbosity=request.diagnostic_verbosity,
            contract_version=request.contract_version,
            repository_path=request.repository_path,
        )
        response = self._run_pipeline(
            Operation.INSPECT_REPOSITORY,
            pipeline_request,
            PipelineStage.VALIDATE,
            InspectionResponse,
        )
        if not response.success or not isinstance(
            response.result, PipelineResult
        ):
            return response
        validation = response.result.stages[-1]
        result = OperationResult(
            response.status,
            (
                ("objects", validation.get("objects", 0)),
                ("sources", validation.get("sources", 0)),
            ),
        )
        return InspectionResponse(
            response.operation,
            response.status,
            result,
            response.diagnostics,
            response.elapsed_seconds,
            response.source,
        )

    def list_plugins(
        self, request: ListPluginsRequest | None = None
    ) -> PluginListResponse:
        """Discover plugin metadata without importing or activating plugins."""
        selected = request or ListPluginsRequest()
        started = perf_counter()
        try:
            self._check_compatibility(selected.contract_version)
            plugins = self._context.services.plugins.list_plugins()
            elapsed = (
                round(perf_counter() - started, 6)
                if selected.timing
                else None
            )
            return PluginListResponse(
                Operation.LIST_PLUGINS,
                OperationStatus.SUCCESS,
                OperationResult(
                    OperationStatus.SUCCESS, (("plugins", len(plugins)),)
                ),
                elapsed_seconds=elapsed,
                plugins=plugins,
            )
        except Exception as error:
            status, diagnostic = translate_exception(error, "plugins")
            return PluginListResponse(
                Operation.LIST_PLUGINS,
                status,
                diagnostics=DiagnosticCollection((diagnostic,)),
            )

    def doctor(self, request: DoctorRequest | None = None) -> DoctorResponse:
        """Perform local read-only readiness checks."""
        selected = request or DoctorRequest()
        started = perf_counter()
        diagnostics: list[Diagnostic] = []
        try:
            self._check_compatibility(selected.contract_version)
            checks = (
                ("repository", selected.repository_path),
                ("schemas", selected.schema_path),
            )
            for label, path in checks:
                if not path.exists():
                    diagnostics.append(
                        Diagnostic(
                            DiagnosticCode(f"teos.doctor.missing_{label}"),
                            DiagnosticSeverity.ERROR,
                            f"{label} location not found: {path}",
                            "doctor",
                            DiagnosticLocation(source=path),
                        )
                    )
            status = (
                OperationStatus.SUCCESS
                if not diagnostics
                else OperationStatus.CONFIGURATION_FAILURE
            )
            values = (
                (
                    "generators",
                    len(
                        self._context.services.generation.available_generators()
                    ),
                ),
                (
                    "renderers",
                    len(
                        self._context.services.rendering.available_renderers()
                    ),
                ),
            )
            elapsed = (
                round(perf_counter() - started, 6)
                if selected.timing
                else None
            )
            return DoctorResponse(
                Operation.DOCTOR,
                status,
                OperationResult(status, values),
                DiagnosticCollection(diagnostics),
                elapsed,
            )
        except Exception as error:
            status, diagnostic = translate_exception(error, "doctor")
            return DoctorResponse(
                Operation.DOCTOR,
                status,
                diagnostics=DiagnosticCollection((diagnostic,)),
            )

    def _run_pipeline(
        self,
        operation: Operation,
        request: PipelineRequest | ValidateRequest,
        terminal_stage: PipelineStage,
        response_type: type[ResponseType],
    ) -> ResponseType:
        started = perf_counter()
        pipeline_request = (
            request
            if isinstance(request, PipelineRequest)
            else PipelineRequest(
                timing=request.timing,
                diagnostic_verbosity=request.diagnostic_verbosity,
                contract_version=request.contract_version,
                repository_path=request.repository_path,
            )
        )
        try:
            self._check_compatibility(request.contract_version)
        except Exception as error:
            status, diagnostic = translate_exception(error, "compatibility")
            return response_type(
                operation,
                status,
                diagnostics=DiagnosticCollection((diagnostic,)),
                source=SourceInformation(pipeline_request.repository_path),
            )
        operation_context = OperationContext(
            operation,
            request,
            ExecutionOptions(
                request.timing, request.diagnostic_verbosity
            ),
            self._context.clock(),
        )
        execution = self._pipeline.execute(
            PipelineContext(operation_context, terminal_stage),
            pipeline_request,
        )
        result = self._pipeline.public_result(execution)
        diagnostics = DiagnosticCollection(
            diagnostic
            for stage in result.stages
            for diagnostic in stage.diagnostics
        )
        response_status = (
            execution.failure_status
            if execution.failure_status is not None
            else result.status
        )
        sources: tuple[Path, ...] = ()
        if execution.stages and execution.stages[0].result.success:
            sources = tuple(execution.stages[0].value or ())
        elapsed = (
            round(perf_counter() - started, 6) if request.timing else None
        )
        return response_type(
            operation,
            response_status,
            result,
            diagnostics,
            elapsed,
            SourceInformation(pipeline_request.repository_path, sources),
        )

    @staticmethod
    def _check_compatibility(requested: str | None) -> None:
        if requested is not None and requested != SUPPORTED_CONTRACT_VERSION:
            raise ApplicationCompatibilityError(
                f"unsupported contract version {requested!r}; "
                f"expected {SUPPORTED_CONTRACT_VERSION!r}"
            )
