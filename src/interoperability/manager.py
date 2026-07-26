"""Public coordinator for import, API execution, and export translation."""

from __future__ import annotations

from hashlib import sha256
from pathlib import Path

from src.api import (
    TEOSApplication,
)
from src.plugins import ExtensionRegistry

from .contracts import (
    CapabilityKind,
    ExportResult,
    ImportExecution,
    ImportResult,
    SourceAttribution,
)
from .export_context import ExportContext
from .exporter import ExportSource
from .exporters import (
    CsvExporter,
    JsonExporter,
    MarkdownExporter,
    YamlExporter,
)
from .import_context import ImportContext
from .importers import (
    CsvImporter,
    JsonImporter,
    MarkdownImporter,
    YamlImporter,
)
from .registry import FormatRegistration, InteroperabilityRegistry


class InteroperabilityManager:
    """Coordinate translators exclusively through the public application API."""

    def __init__(
        self,
        *,
        application: TEOSApplication | None = None,
        registry: InteroperabilityRegistry | None = None,
        register_builtins: bool = True,
        plugin_extensions: ExtensionRegistry | None = None,
    ) -> None:
        self.application = application or TEOSApplication()
        self.registry = registry or InteroperabilityRegistry()
        if register_builtins:
            self._register_builtins()
        if plugin_extensions is not None:
            self.registry.register_plugin_extensions(plugin_extensions)

    def import_data(
        self,
        format_name: str,
        source: str | bytes | Path,
        context: ImportContext | None = None,
    ) -> ImportResult:
        """Translate external data to one immutable public API request."""
        selected = context or ImportContext()
        data, location = self._source_bytes(
            source, selected.format_options.encoding
        )
        if selected.source is not None:
            location = selected.source
        attribution = SourceAttribution(
            location, sha256(data).hexdigest(), len(data)
        )
        importer = self.registry.importer(
            format_name, selected.format_version
        )
        return importer.import_data(data, selected, attribution)

    def import_discovered(
        self,
        source: Path,
        context: ImportContext | None = None,
        *,
        media_type: str | None = None,
    ) -> ImportResult:
        """Discover an importer from path/media type and translate its source."""
        selected = context or ImportContext(source=source)
        registration = self.registry.discover(
            CapabilityKind.IMPORTER,
            path=source,
            media_type=media_type,
            version=selected.format_version,
        )
        return self.import_data(
            registration.capability.name, source, selected
        )

    def execute_import(
        self,
        format_name: str,
        source: str | bytes | Path,
        context: ImportContext | None = None,
    ) -> ImportExecution:
        """Import then execute via ``TEOSApplication.execute`` only."""
        imported = self.import_data(format_name, source, context)
        if not imported.success:
            from .exceptions import TranslationError

            raise TranslationError(
                "import diagnostics prevented public API execution"
            )
        assert imported.operation is not None
        assert imported.request is not None
        response = self.application.execute(
            imported.operation, imported.request
        )
        return ImportExecution(imported, response)

    def export_data(
        self,
        format_name: str,
        response: ExportSource,
        context: ExportContext | None = None,
    ) -> ExportResult:
        """Translate one immutable public API response to external text."""
        selected = context or ExportContext()
        exporter = self.registry.exporter(
            format_name, selected.format_version
        )
        return exporter.export(response, selected)

    def export_discovered(
        self,
        path: str | Path,
        response: ExportSource,
        context: ExportContext | None = None,
        *,
        media_type: str | None = None,
    ) -> ExportResult:
        """Discover an exporter from a target path/media type."""
        selected = context or ExportContext()
        registration = self.registry.discover(
            CapabilityKind.EXPORTER,
            path=path,
            media_type=media_type,
            version=selected.format_version,
        )
        return self.export_data(
            registration.capability.name, response, selected
        )

    def register_plugin_extensions(
        self, extensions: ExtensionRegistry
    ) -> tuple[FormatRegistration, ...]:
        """Register active plugin importers and exporters."""
        return self.registry.register_plugin_extensions(extensions)

    def _register_builtins(self) -> None:
        for importer in (
            CsvImporter(),
            JsonImporter(),
            MarkdownImporter(),
            YamlImporter(),
        ):
            self.registry.register_importer(importer)
        for exporter in (
            CsvExporter(),
            JsonExporter(),
            MarkdownExporter(),
            YamlExporter(),
        ):
            self.registry.register_exporter(exporter)

    @staticmethod
    def _source_bytes(
        source: str | bytes | Path, encoding: str
    ) -> tuple[bytes, Path | None]:
        if isinstance(source, Path):
            return source.read_bytes(), source
        if isinstance(source, bytes):
            return source, None
        return source.encode(encoding), None
