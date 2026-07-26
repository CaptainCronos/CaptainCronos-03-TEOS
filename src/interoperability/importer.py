"""Base importer contract and public-request translation helpers."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import fields
from pathlib import Path
from typing import Any, Mapping

from src.api import (
    BuildRequest,
    CompileRequest,
    DoctorRequest,
    GenerateRequest,
    InspectRequest,
    ListPluginsRequest,
    Operation,
    PipelineRequest,
    RenderRequest,
    ScheduleRequest,
    ValidateRequest,
)

from .contracts import (
    DiagnosticKind,
    DiagnosticSeverity,
    FormatCapability,
    ImportResult,
    SourceAttribution,
    TranslationDiagnostic,
    TranslationDiagnostics,
)
from .import_context import ImportContext


_REQUEST_TYPES = {
    Operation.VALIDATE_REPOSITORY: ValidateRequest,
    Operation.COMPILE_REPOSITORY: CompileRequest,
    Operation.SCHEDULE_CURRICULUM: ScheduleRequest,
    Operation.RENDER_SCHEDULE: RenderRequest,
    Operation.GENERATE_DOCUMENTS: GenerateRequest,
    Operation.BUILD: BuildRequest,
    Operation.INSPECT_REPOSITORY: InspectRequest,
    Operation.LIST_PLUGINS: ListPluginsRequest,
    Operation.DOCTOR: DoctorRequest,
}
_PATH_FIELDS = {"repository_path", "schema_path", "output_directory"}
_BOOLEAN_FIELDS = {"timing"}
_ENVELOPE_FIELDS = {"format_version", "operation", "request"}


class Importer(ABC):
    """Common interface implemented by every import translator."""

    capability: FormatCapability

    @property
    def name(self) -> str:
        """Return the stable registry name."""
        return self.capability.name

    @abstractmethod
    def decode(self, data: bytes, context: ImportContext) -> Mapping[str, Any]:
        """Decode external bytes into the canonical import envelope."""

    def import_data(
        self,
        data: bytes,
        context: ImportContext,
        source: SourceAttribution,
    ) -> ImportResult:
        """Decode and translate one external representation."""
        document = self.decode(data, context)
        return self.translate(document, context, source)

    def translate(
        self,
        document: Mapping[str, Any],
        context: ImportContext,
        source: SourceAttribution,
    ) -> ImportResult:
        """Translate a decoded envelope to an immutable public request."""
        diagnostics: list[TranslationDiagnostic] = []
        unknown_envelope = sorted(set(document) - _ENVELOPE_FIELDS)
        self._unknown_fields(
            unknown_envelope, (), context, source, diagnostics
        )

        raw_version = document.get("format_version")
        if raw_version is None:
            diagnostics.append(
                self._diagnostic(
                    DiagnosticKind.MISSING_MANDATORY_FIELD,
                    DiagnosticSeverity.ERROR,
                    "missing mandatory field: format_version",
                    source,
                    ("format_version",),
                )
            )
            version = context.format_version
        else:
            version = str(raw_version)
            if version != context.format_version:
                diagnostics.append(
                    self._diagnostic(
                        DiagnosticKind.VERSION_MISMATCH,
                        DiagnosticSeverity.ERROR,
                        f"document format version {version!r} does not match "
                        f"requested version {context.format_version!r}",
                        source,
                        ("format_version",),
                    )
                )

        raw_operation = document.get("operation")
        operation: Operation | None = None
        if raw_operation is None:
            diagnostics.append(
                self._diagnostic(
                    DiagnosticKind.MISSING_MANDATORY_FIELD,
                    DiagnosticSeverity.ERROR,
                    "missing mandatory field: operation",
                    source,
                    ("operation",),
                )
            )
        else:
            try:
                operation = Operation(str(raw_operation))
            except ValueError:
                diagnostics.append(
                    self._diagnostic(
                        DiagnosticKind.UNKNOWN_VALUE,
                        DiagnosticSeverity.ERROR,
                        f"unknown public API operation: {raw_operation!r}",
                        source,
                        ("operation",),
                    )
                )

        raw_request = document.get("request")
        if raw_request is None:
            diagnostics.append(
                self._diagnostic(
                    DiagnosticKind.MISSING_MANDATORY_FIELD,
                    DiagnosticSeverity.ERROR,
                    "missing mandatory field: request",
                    source,
                    ("request",),
                )
            )
            request_values: dict[str, Any] = {}
        elif not isinstance(raw_request, Mapping):
            diagnostics.append(
                self._diagnostic(
                    DiagnosticKind.UNKNOWN_VALUE,
                    DiagnosticSeverity.ERROR,
                    "request must be an object",
                    source,
                    ("request",),
                )
            )
            request_values = {}
        else:
            request_values = dict(raw_request)

        request = None
        if operation is not None:
            request_type = _REQUEST_TYPES[operation]
            supported = {item.name for item in fields(request_type) if item.init}
            unknown_request = sorted(set(request_values) - supported)
            self._unknown_fields(
                unknown_request, ("request",), context, source, diagnostics
            )
            if unknown_request:
                request_values = {
                    key: value
                    for key, value in request_values.items()
                    if key in supported
                }
            if not any(
                item.severity is DiagnosticSeverity.ERROR
                for item in diagnostics
            ):
                try:
                    request = request_type(
                        **self._coerce_request_values(request_values)
                    )
                except (TypeError, ValueError) as error:
                    diagnostics.append(
                        self._diagnostic(
                            DiagnosticKind.UNKNOWN_VALUE,
                            DiagnosticSeverity.ERROR,
                            f"invalid request value: {error}",
                            source,
                            ("request",),
                        )
                    )

        return ImportResult(
            self.name,
            version,
            operation,
            request,
            source,
            TranslationDiagnostics(diagnostics),
        )

    @staticmethod
    def _coerce_request_values(values: Mapping[str, Any]) -> dict[str, Any]:
        coerced = dict(values)
        for name in _PATH_FIELDS.intersection(coerced):
            coerced[name] = Path(coerced[name])
        for name in _BOOLEAN_FIELDS.intersection(coerced):
            value = coerced[name]
            if isinstance(value, str):
                normalized = value.strip().lower()
                if normalized not in {"true", "false"}:
                    raise ValueError(f"{name} must be true or false")
                coerced[name] = normalized == "true"
        return coerced

    def _unknown_fields(
        self,
        names: list[str],
        prefix: tuple[str, ...],
        context: ImportContext,
        source: SourceAttribution,
        diagnostics: list[TranslationDiagnostic],
    ) -> None:
        severity = (
            DiagnosticSeverity.ERROR
            if context.conversion_options.strict
            else DiagnosticSeverity.WARNING
        )
        for name in names:
            diagnostics.append(
                TranslationDiagnostic(
                    DiagnosticKind.UNSUPPORTED_FIELD,
                    severity,
                    f"unsupported field: {name}",
                    source.location,
                    prefix + (name,),
                )
            )

    @staticmethod
    def _diagnostic(
        kind: DiagnosticKind,
        severity: DiagnosticSeverity,
        message: str,
        source: SourceAttribution,
        path: tuple[str | int, ...],
    ) -> TranslationDiagnostic:
        return TranslationDiagnostic(
            kind, severity, message, source.location, path
        )


def request_envelope_from_flat_record(
    record: Mapping[str, Any],
) -> dict[str, Any]:
    """Convert one flat CSV record to the canonical request envelope."""
    request = {
        key: value
        for key, value in record.items()
        if key not in {"format_version", "operation"}
        and value != ""
        and value is not None
    }
    return {
        "format_version": record.get("format_version"),
        "operation": record.get("operation"),
        "request": request,
    }


def is_pipeline_operation(operation: Operation) -> bool:
    """Return whether an operation uses pipeline request fields."""
    return issubclass(_REQUEST_TYPES[operation], PipelineRequest)
