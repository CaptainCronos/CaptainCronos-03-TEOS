"""Public Application API facade, contracts, orchestration, and diagnostics."""

from __future__ import annotations

from dataclasses import FrozenInstanceError
from datetime import datetime, timezone
from pathlib import Path

import pytest

from src.api import (
    API_VERSION,
    ENGINE_VERSION,
    SUPPORTED_CONTRACT_VERSION,
    ApplicationServices,
    BuildRequest,
    CompileRequest,
    DiagnosticSeverity,
    DoctorRequest,
    GenerateRequest,
    InspectRequest,
    ListPluginsRequest,
    OperationStatus,
    PipelineStage,
    RenderRequest,
    ScheduleRequest,
    TEOSApplication,
    ValidateRequest,
)
from src.api.contracts import (
    CompilationService,
    GenerationService,
    PluginService,
    RenderingService,
    RepositoryService,
    SchedulingService,
    ValidationService,
)
from src.application.services import default_services
from src.cli.commands import CommandName, CommandRequest
from src.repository.exceptions import SchemaValidationError
from tests.test_cli import application as cli_fixture
from tests.test_scheduler import compiled_fixture


GENERATED_AT = datetime(2026, 7, 25, 12, tzinfo=timezone.utc)


class FixtureLoader:
    """Expose one real immutable repository through the loader interface."""

    def __init__(self, failure: Exception | None = None) -> None:
        self.repository = compiled_fixture()[0].source
        self.failure = failure
        self.calls: list[str] = []

    def locate(self, location: str | Path) -> tuple[Path, ...]:
        self.calls.append("load")
        return (Path(location).resolve() / "fixture.json",)

    def load(self, location: str | Path):
        self.calls.append("validate")
        if self.failure is not None:
            raise self.failure
        return self.repository


def fixture_application(
    tmp_path: Path, *, failure: Exception | None = None
) -> tuple[TEOSApplication, FixtureLoader]:
    """Create a facade around real engines and a fixture repository."""
    loader = FixtureLoader(failure)
    application = TEOSApplication(
        services=default_services(loader=loader),  # type: ignore[arg-type]
        clock=lambda: GENERATED_AT,
    )
    return application, loader


def request_values(tmp_path: Path) -> dict[str, object]:
    return {
        "repository_path": tmp_path,
        "output_directory": tmp_path / "output",
    }


def test_requests_responses_and_diagnostics_are_immutable(
    tmp_path: Path,
) -> None:
    """Public input and output values cannot acquire execution state."""
    request = BuildRequest(
        **request_values(tmp_path),
        plugin_configuration={
            "z": [2, {"nested": True}],
            "a": 1,
        },  # type: ignore[arg-type]
    )
    application, _ = fixture_application(tmp_path)
    response = application.build(request)

    assert request.plugin_configuration == (
        ("a", 1),
        ("z", (2, (("nested", True),))),
    )
    assert response.success
    assert response.generated_files[0].path.is_file()
    with pytest.raises(FrozenInstanceError):
        request.renderer = "html"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        response.status = OperationStatus.EXECUTION_FAILURE  # type: ignore[misc]


@pytest.mark.parametrize(
    ("request_type", "method", "terminal"),
    (
        (ValidateRequest, "validate_repository", PipelineStage.VALIDATE),
        (CompileRequest, "compile_repository", PipelineStage.COMPILE),
        (ScheduleRequest, "schedule_curriculum", PipelineStage.SCHEDULE),
        (RenderRequest, "render_schedule", PipelineStage.RENDER),
        (GenerateRequest, "generate_documents", PipelineStage.GENERATE),
        (BuildRequest, "build", PipelineStage.GENERATE),
    ),
)
def test_facade_executes_only_the_required_deterministic_prefix(
    tmp_path: Path, request_type, method: str, terminal: PipelineStage
) -> None:
    """Facade operations share one fixed ordered pipeline."""
    application, _ = fixture_application(tmp_path)
    values = request_values(tmp_path)
    request = (
        request_type(repository_path=tmp_path)
        if request_type is ValidateRequest
        else request_type(**values)
    )

    response = getattr(application, method)(request)

    assert response.success
    assert response.stages[-1].stage is terminal
    assert tuple(stage.stage for stage in response.stages) == (
        PipelineStage.LOAD,
        PipelineStage.VALIDATE,
        PipelineStage.COMPILE,
        PipelineStage.SCHEDULE,
        PipelineStage.RENDER,
        PipelineStage.GENERATE,
    )[: len(response.stages)]


def test_failure_stops_pipeline_preserves_partial_stages_and_location(
    tmp_path: Path,
) -> None:
    """Validation failure returns load success and a located fatal diagnostic."""
    source = tmp_path / "broken.json"
    failure = SchemaValidationError(
        "invalid title", source=source, path=("title",)
    )
    application, loader = fixture_application(tmp_path, failure=failure)

    response = application.build(BuildRequest(**request_values(tmp_path)))

    assert response.status is OperationStatus.VALIDATION_FAILURE
    assert response.result.status is OperationStatus.PARTIAL
    assert [stage.stage for stage in response.stages] == [
        PipelineStage.LOAD,
        PipelineStage.VALIDATE,
    ]
    assert loader.calls == ["load", "validate"]
    diagnostic = response.errors[0]
    assert diagnostic.severity is DiagnosticSeverity.FATAL
    assert diagnostic.location.source == source
    assert diagnostic.location.field_path == ("title",)


def test_compatibility_failure_runs_no_services(tmp_path: Path) -> None:
    """Unsupported contract versions fail before source discovery."""
    application, loader = fixture_application(tmp_path)

    response = application.validate_repository(
        ValidateRequest(repository_path=tmp_path, contract_version="2.0")
    )

    assert response.status is OperationStatus.CONFIGURATION_FAILURE
    assert loader.calls == []
    assert "unsupported contract version" in response.errors[0].message


def test_invalid_component_selection_is_configuration_failure(
    tmp_path: Path,
) -> None:
    """Public configuration mistakes are distinct from engine failures."""
    application, _ = fixture_application(tmp_path)

    response = application.render_schedule(
        RenderRequest(**request_values(tmp_path), renderer="unknown")
    )

    assert response.status is OperationStatus.CONFIGURATION_FAILURE
    assert response.stages[-1].stage is PipelineStage.RENDER
    assert "unsupported renderer selection" in response.errors[0].message


def test_unsupported_operation_returns_stable_failure(tmp_path: Path) -> None:
    """Future operation names do not raise arbitrary dispatch exceptions."""
    application, loader = fixture_application(tmp_path)

    response = application.execute("future_operation", ValidateRequest())

    assert response.status is OperationStatus.UNSUPPORTED_OPERATION
    assert not response.success
    assert response.operation == "future_operation"
    assert response.errors[0].code.value == "teos.operation.unsupported"
    assert loader.calls == []


def test_inspection_doctor_plugins_and_versions(tmp_path: Path) -> None:
    """Non-pipeline operations publish stable summaries and version values."""
    application, _ = fixture_application(tmp_path)

    inspection = application.inspect_repository(
        InspectRequest(repository_path=tmp_path)
    )
    doctor = application.doctor(
        DoctorRequest(repository_path=tmp_path, schema_path=Path("schemas"))
    )
    plugins = application.list_plugins(ListPluginsRequest())

    assert inspection.success
    assert inspection.result.get("objects") > 0
    assert doctor.success
    assert plugins.success
    assert application.api_version == API_VERSION == "1.0.0"
    assert application.engine_version == ENGINE_VERSION == "1.1.0"
    assert application.supported_contract_version == SUPPORTED_CONTRACT_VERSION
    assert SUPPORTED_CONTRACT_VERSION == "1.0"


@pytest.mark.smoke
def test_default_doctor_schema_path_is_independent_of_working_directory(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Packaged schema readiness does not depend on the invocation directory."""
    monkeypatch.chdir(tmp_path)

    request = DoctorRequest()

    assert request.schema_path.is_dir()
    assert tuple(request.schema_path.glob("*.schema.json"))


def test_default_services_implement_every_public_contract() -> None:
    """Published protocols accept the default application adapters."""
    services = default_services()

    assert isinstance(services.repository, RepositoryService)
    assert isinstance(services.validation, ValidationService)
    assert isinstance(services.compilation, CompilationService)
    assert isinstance(services.scheduling, SchedulingService)
    assert isinstance(services.rendering, RenderingService)
    assert isinstance(services.generation, GenerationService)
    assert isinstance(services.plugins, PluginService)
    assert isinstance(services, ApplicationServices)


def test_public_contract_modules_do_not_import_private_application_values() -> None:
    """Plugin-facing contract annotations remain opaque and public."""
    import src.api.contracts.compilation as compilation_contract

    assert "src.application" not in compilation_contract.__dict__
    assert CompilationService.__module__.startswith("src.api.contracts")


def test_cli_delegates_pipeline_commands_to_public_facade(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The terminal adapter invokes an API operation instead of engine stages."""
    calls: list[str] = []

    class RecordingApplication(TEOSApplication):
        def build(self, request: BuildRequest):
            calls.append("build")
            return super().build(request)

    monkeypatch.setattr(
        "src.cli.application.TEOSApplication", RecordingApplication
    )
    cli, _, _, _ = cli_fixture(tmp_path)

    cli.execute(CommandRequest(CommandName.BUILD))

    assert calls == ["build"]
