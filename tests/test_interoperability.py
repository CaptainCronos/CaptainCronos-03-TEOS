"""Import/export translation, compatibility, registry, and plugin tests."""

from __future__ import annotations

import csv
import io
import json
from dataclasses import FrozenInstanceError
from hashlib import sha256
from pathlib import Path

import pytest
import yaml

from src.api import (
    ArtifactResult,
    Diagnostic,
    DiagnosticCode,
    DiagnosticCollection,
    DiagnosticSeverity as ApiDiagnosticSeverity,
    Operation,
    OperationResult,
    OperationStatus,
    ValidationResponse,
    ValidateRequest,
)
from src.interoperability import (
    CapabilityKind,
    CompatibilityError,
    ConversionOptions,
    DiagnosticKind,
    DiagnosticSeverity,
    ExportContext,
    ExportError,
    FormatCapability,
    FormatError,
    FormatOptions,
    ImportContext,
    ImportError,
    ImportExportError,
    InteroperabilityManager,
    InteroperabilityRegistry,
    JsonExporter,
    JsonImporter,
    TranslationError,
)
from src.plugins import EXPORTER, IMPORTER, ExtensionRegistry


def import_envelopes(tmp_path: Path) -> dict[str, str]:
    """Return equivalent valid documents in every built-in import format."""
    request = {"repository_path": str(tmp_path), "timing": True}
    envelope = {
        "format_version": "1.0",
        "operation": "validate_repository",
        "request": request,
    }
    return {
        "json": json.dumps(envelope),
        "yaml": yaml.safe_dump(envelope),
        "markdown": "---\n"
        + yaml.safe_dump(envelope).rstrip()
        + "\n---\n\n# Validate\n",
        "csv": (
            "format_version,operation,repository_path,timing\n"
            f"1.0,validate_repository,{tmp_path},true\n"
        ),
    }


def response(tmp_path: Path) -> ValidationResponse:
    """Create a representative immutable public response."""
    diagnostic = Diagnostic(
        DiagnosticCode("teos.test.warning"),
        ApiDiagnosticSeverity.WARNING,
        "test warning",
        "validate",
    )
    return ValidationResponse(
        Operation.VALIDATE_REPOSITORY,
        OperationStatus.SUCCESS_WITH_WARNINGS,
        OperationResult(
            OperationStatus.SUCCESS_WITH_WARNINGS,
            (("sources", 2), ("objects", 7)),
        ),
        DiagnosticCollection((diagnostic,)),
        0.125,
    )


@pytest.mark.parametrize("format_name", ("csv", "markdown", "json", "yaml"))
def test_builtin_imports_translate_to_immutable_public_requests(
    tmp_path: Path, format_name: str
) -> None:
    """Every built-in importer produces the same public request contract."""
    manager = InteroperabilityManager()

    result = manager.import_data(
        format_name, import_envelopes(tmp_path)[format_name]
    )

    assert result.success
    assert result.operation is Operation.VALIDATE_REPOSITORY
    assert result.request == ValidateRequest(
        repository_path=tmp_path, timing=True
    )
    assert result.source.size_bytes > 0
    with pytest.raises(FrozenInstanceError):
        result.format_version = "2.0"  # type: ignore[misc]


@pytest.mark.parametrize("format_name", ("csv", "markdown", "json", "yaml"))
def test_builtin_exports_are_deterministic_and_complete(
    tmp_path: Path, format_name: str
) -> None:
    """Every built-in exporter retains public status and result information."""
    manager = InteroperabilityManager()
    first = manager.export_data(format_name, response(tmp_path))
    second = manager.export_data(format_name, response(tmp_path))

    assert first.content == second.content
    assert "validate_repository" in first.content
    assert "success_with_warnings" in first.content
    assert "objects" in first.content
    assert first.format_version == "1.0"


def test_json_yaml_and_csv_exports_are_machine_readable(tmp_path: Path) -> None:
    """Structured exporters produce valid representations with stable values."""
    manager = InteroperabilityManager()
    api_response = response(tmp_path)

    json_document = json.loads(
        manager.export_data("json", api_response).content
    )
    yaml_document = yaml.safe_load(
        manager.export_data("yaml", api_response).content
    )
    csv_rows = list(
        csv.DictReader(
            io.StringIO(manager.export_data("csv", api_response).content)
        )
    )

    assert json_document["result"]["values"]["objects"] == 7
    assert yaml_document["diagnostics"][0]["message"] == "test warning"
    assert json.loads(csv_rows[0]["result"])["values"]["sources"] == 2


def test_exporters_consume_public_artifact_descriptors() -> None:
    """A public immutable artifact can be exported without engine access."""
    artifact = ArtifactResult(
        "schedule-1",
        "markdown",
        "markdown",
        "text/markdown",
        "schedule.md",
        "abc123",
    )

    document = json.loads(
        InteroperabilityManager().export_data("json", artifact).content
    )

    assert document["kind"] == "artifact"
    assert document["result"]["identifier"] == "schedule-1"
    assert document["result"]["source_fingerprint"] == "abc123"


def test_markdown_import_requires_front_matter() -> None:
    """Markdown prose alone cannot silently become an API request."""
    manager = InteroperabilityManager()

    with pytest.raises(FormatError, match="front matter"):
        manager.import_data("markdown", "# Unversioned request")


@pytest.mark.parametrize(
    ("format_name", "content"),
    (
        ("json", "{"),
        ("yaml", "request: ["),
        ("csv", "format_version,operation\n"),
    ),
)
def test_invalid_format_syntax_is_rejected(
    format_name: str, content: str
) -> None:
    """Malformed built-in representations raise stable format failures."""
    with pytest.raises(FormatError):
        InteroperabilityManager().import_data(format_name, content)


def test_translation_diagnostics_cover_unknown_and_missing_fields() -> None:
    """Representable translation failures return ordered machine diagnostics."""
    manager = InteroperabilityManager()
    document = json.dumps(
        {
            "format_version": "1.0",
            "request": {"future_field": True},
            "future_envelope": "value",
        }
    )

    result = manager.import_data("json", document)

    assert not result.success
    assert [item.kind for item in result.diagnostics] == [
        DiagnosticKind.UNSUPPORTED_FIELD,
        DiagnosticKind.MISSING_MANDATORY_FIELD,
    ]
    assert all(
        item.severity is DiagnosticSeverity.ERROR
        for item in result.diagnostics
    )


def test_permissive_translation_omits_unknown_request_fields(
    tmp_path: Path,
) -> None:
    """Permissive mode preserves a warning while constructing the request."""
    document = json.dumps(
        {
            "format_version": "1.0",
            "operation": "validate_repository",
            "request": {
                "repository_path": str(tmp_path),
                "future_field": True,
            },
        }
    )
    context = ImportContext(
        conversion_options=ConversionOptions(strict=False)
    )

    result = InteroperabilityManager().import_data(
        "json", document, context
    )

    assert result.success
    assert result.request == ValidateRequest(repository_path=tmp_path)
    assert result.diagnostics.items[0].kind is DiagnosticKind.UNSUPPORTED_FIELD
    assert (
        result.diagnostics.items[0].severity
        is DiagnosticSeverity.WARNING
    )


def test_version_compatibility_is_exact_and_checked_before_decode() -> None:
    """Unsupported capability versions never reach a translator."""
    manager = InteroperabilityManager()

    with pytest.raises(CompatibilityError, match="does not support"):
        manager.import_data(
            "json",
            "not json",
            ImportContext(format_version="2.0"),
        )
    with pytest.raises(CompatibilityError, match="unsupported"):
        manager.export_data("xml", response(Path(".")))


def test_document_version_mismatch_is_diagnostic() -> None:
    """A document cannot silently select another compatible representation."""
    result = InteroperabilityManager().import_data(
        "json",
        json.dumps(
            {
                "format_version": "0.9",
                "operation": "validate_repository",
                "request": {},
            }
        ),
    )

    assert not result.success
    assert result.diagnostics.items[0].kind is DiagnosticKind.VERSION_MISMATCH


def test_registry_is_deterministic_rejects_duplicates_and_discovers(
    tmp_path: Path,
) -> None:
    """Capability registration and extension lookup have stable semantics."""
    registry = InteroperabilityRegistry()
    registry.register_importer(JsonImporter())
    registry.register_exporter(JsonExporter())

    assert [
        (item.capability.kind, item.capability.name)
        for item in registry.registrations()
    ] == [
        (CapabilityKind.EXPORTER, "json"),
        (CapabilityKind.IMPORTER, "json"),
    ]
    assert (
        registry.discover(
            CapabilityKind.IMPORTER,
            path=tmp_path / "request.json",
            version="1.0",
        ).capability.name
        == "json"
    )
    with pytest.raises(CompatibilityError, match="already registered"):
        registry.register_importer(JsonImporter())


def test_path_discovery_and_source_attribution(tmp_path: Path) -> None:
    """Automatic discovery preserves exact path and source-byte checksum."""
    source = tmp_path / "request.json"
    content = json.dumps(
        {
            "format_version": "1.0",
            "operation": "inspect_repository",
            "request": {"repository_path": str(tmp_path)},
        }
    ).encode()
    source.write_bytes(content)

    result = InteroperabilityManager().import_discovered(source)

    assert result.success
    assert result.source.location == source
    assert result.source.checksum == sha256(content).hexdigest()


class PluginJsonImporter(JsonImporter):
    """Plugin fixture using the real importer contract."""

    capability = FormatCapability(
        "plugin-json",
        CapabilityKind.IMPORTER,
        extensions=(".pjson",),
    )


class PluginJsonExporter(JsonExporter):
    """Plugin fixture using the real exporter contract."""

    capability = FormatCapability(
        "plugin-json",
        CapabilityKind.EXPORTER,
        extensions=(".pjson",),
        media_types=("application/vnd.example+json",),
    )


def test_plugin_extensions_register_through_existing_categories(
    tmp_path: Path,
) -> None:
    """Active plugin registrations become regular format capabilities."""
    extensions = ExtensionRegistry()
    registrar = extensions.registrar(
        "org.example.interop", (IMPORTER, EXPORTER)
    )
    registrar.register(IMPORTER, PluginJsonImporter())
    registrar.register(EXPORTER, PluginJsonExporter())

    manager = InteroperabilityManager(plugin_extensions=extensions)
    imported = manager.import_data(
        "plugin-json", import_envelopes(tmp_path)["json"]
    )
    exported = manager.export_data(
        "plugin-json", response(tmp_path)
    )

    assert imported.success
    assert json.loads(exported.content)["operation"] == "validate_repository"
    owners = {
        item.owner
        for item in manager.registry.registrations()
        if item.capability.name == "plugin-json"
    }
    assert owners == {"org.example.interop"}


def test_manager_executes_only_through_public_application_facade(
    tmp_path: Path,
) -> None:
    """Translated requests are dispatched through the injected public facade."""

    class RecordingApplication:
        def __init__(self) -> None:
            self.calls = []

        def execute(self, operation, request):
            self.calls.append((operation, request))
            return response(tmp_path)

    application = RecordingApplication()
    manager = InteroperabilityManager(
        application=application  # type: ignore[arg-type]
    )

    execution = manager.execute_import(
        "json", import_envelopes(tmp_path)["json"]
    )

    assert application.calls == [
        (
            Operation.VALIDATE_REPOSITORY,
            ValidateRequest(repository_path=tmp_path, timing=True),
        )
    ]
    assert execution.response.success


def test_failed_import_is_not_submitted_to_application() -> None:
    """Error diagnostics prevent facade execution."""
    manager = InteroperabilityManager()

    with pytest.raises(TranslationError):
        manager.execute_import(
            "json",
            json.dumps({"format_version": "1.0", "request": {}}),
        )


def test_context_options_are_immutable_and_control_output(
    tmp_path: Path,
) -> None:
    """Frozen contexts carry deterministic representation settings."""
    options = FormatOptions(newline="\r\n", delimiter=";", indent=4)
    context = ExportContext(
        format_options=options,
        conversion_options=ConversionOptions(include_diagnostics=False),
    )

    exported = InteroperabilityManager().export_data(
        "csv", response(tmp_path), context
    )

    assert "\r\n" in exported.content
    assert ";" in exported.content.splitlines()[0]
    assert "test warning" not in exported.content
    assert exported.encoding == "utf-8"
    assert exported.bytes == exported.content.encode("utf-8")
    with pytest.raises(FrozenInstanceError):
        context.format_version = "2.0"  # type: ignore[misc]


def test_exception_hierarchy_separates_translation_directions() -> None:
    """Direction failures share one documented interoperability root."""
    assert issubclass(ImportError, ImportExportError)
    assert issubclass(ExportError, ImportExportError)
    assert issubclass(FormatError, ImportExportError)
    assert issubclass(CompatibilityError, ImportExportError)
    assert issubclass(TranslationError, ImportExportError)
