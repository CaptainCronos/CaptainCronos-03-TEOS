"""Immutable public contracts for interoperability translation."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path
from typing import Any, Iterable, Iterator, Mapping

from src.api import ApplicationRequest, Operation, OperationResponse


FRAMEWORK_VERSION = "1.0.0"
SUPPORTED_FRAMEWORK_CONTRACT_VERSION = "1.0"
DEFAULT_FORMAT_VERSION = "1.0"


def freeze_value(value: Any) -> Any:
    """Recursively convert containers to deterministic immutable values."""
    if isinstance(value, Mapping):
        return tuple(
            (str(key), freeze_value(child))
            for key, child in sorted(value.items(), key=lambda item: str(item[0]))
        )
    if isinstance(value, (list, tuple)):
        return tuple(freeze_value(child) for child in value)
    if isinstance(value, set):
        return tuple(sorted((freeze_value(child) for child in value), key=repr))
    return value


class CapabilityKind(StrEnum):
    """Direction implemented by an interoperability capability."""

    IMPORTER = "importer"
    EXPORTER = "exporter"


class DiagnosticKind(StrEnum):
    """Stable translation diagnostic categories."""

    UNSUPPORTED_FIELD = "unsupported_field"
    DATA_TRUNCATION = "data_truncation"
    UNKNOWN_VALUE = "unknown_value"
    MISSING_MANDATORY_FIELD = "missing_mandatory_field"
    VERSION_MISMATCH = "version_mismatch"
    UNSUPPORTED_FEATURE = "unsupported_feature"


class DiagnosticSeverity(StrEnum):
    """Translation diagnostic impact."""

    INFORMATION = "information"
    WARNING = "warning"
    ERROR = "error"


@dataclass(frozen=True, slots=True)
class TranslationDiagnostic:
    """One immutable observation produced during translation."""

    kind: DiagnosticKind
    severity: DiagnosticSeverity
    message: str
    source: Path | None = None
    field_path: tuple[str | int, ...] = ()
    line: int | None = None
    column: int | None = None

    def __post_init__(self) -> None:
        if not self.message:
            raise ValueError("diagnostic message cannot be empty")
        if self.source is not None:
            object.__setattr__(self, "source", Path(self.source))
        object.__setattr__(self, "field_path", tuple(self.field_path))
        if self.line is not None and self.line < 1:
            raise ValueError("diagnostic line must be positive")
        if self.column is not None and self.column < 1:
            raise ValueError("diagnostic column must be positive")


@dataclass(frozen=True, slots=True)
class TranslationDiagnostics:
    """Ordered immutable collection of translation diagnostics."""

    items: tuple[TranslationDiagnostic, ...] = ()

    def __init__(self, items: Iterable[TranslationDiagnostic] = ()) -> None:
        object.__setattr__(self, "items", tuple(items))

    def __iter__(self) -> Iterator[TranslationDiagnostic]:
        return iter(self.items)

    def __len__(self) -> int:
        return len(self.items)

    @property
    def has_errors(self) -> bool:
        """Return whether any diagnostic prevents translation."""
        return any(item.severity is DiagnosticSeverity.ERROR for item in self)


@dataclass(frozen=True, slots=True)
class FormatOptions:
    """Representation settings shared by built-in formats."""

    encoding: str = "utf-8"
    newline: str = "\n"
    delimiter: str = ","
    indent: int = 2
    sort_keys: bool = True
    values: tuple[tuple[str, Any], ...] = ()

    def __post_init__(self) -> None:
        if not self.encoding:
            raise ValueError("encoding cannot be empty")
        if self.newline not in {"\n", "\r\n"}:
            raise ValueError("newline must be LF or CRLF")
        if len(self.delimiter) != 1 or self.delimiter in {"\r", "\n"}:
            raise ValueError("delimiter must be one non-newline character")
        if self.indent < 1:
            raise ValueError("indent must be positive")
        object.__setattr__(self, "values", tuple(freeze_value(self.values)))

    def get(self, name: str, default: Any = None) -> Any:
        """Return one format-specific option."""
        return dict(self.values).get(name, default)


@dataclass(frozen=True, slots=True)
class ConversionOptions:
    """Semantic translation settings."""

    strict: bool = True
    include_diagnostics: bool = True
    values: tuple[tuple[str, Any], ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "values", tuple(freeze_value(self.values)))

    def get(self, name: str, default: Any = None) -> Any:
        """Return one conversion-specific option."""
        return dict(self.values).get(name, default)


@dataclass(frozen=True, slots=True)
class FormatCapability:
    """One importer or exporter registration contract."""

    name: str
    kind: CapabilityKind
    versions: tuple[str, ...] = (DEFAULT_FORMAT_VERSION,)
    extensions: tuple[str, ...] = ()
    media_types: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        normalized = self.name.strip().lower()
        if not normalized or not normalized.replace("-", "").isalnum():
            raise ValueError(f"invalid format capability name: {self.name!r}")
        versions = tuple(sorted(set(self.versions)))
        if not versions or any(not version for version in versions):
            raise ValueError("at least one non-empty format version is required")
        extensions = tuple(
            sorted(
                {
                    item.lower() if item.startswith(".") else "." + item.lower()
                    for item in self.extensions
                }
            )
        )
        media_types = tuple(sorted({item.lower() for item in self.media_types}))
        object.__setattr__(self, "name", normalized)
        object.__setattr__(self, "versions", versions)
        object.__setattr__(self, "extensions", extensions)
        object.__setattr__(self, "media_types", media_types)

    def supports(self, version: str) -> bool:
        """Return whether the exact external format version is implemented."""
        return version in self.versions


@dataclass(frozen=True, slots=True)
class SourceAttribution:
    """Stable provenance for imported source bytes."""

    location: Path | None
    checksum: str
    size_bytes: int

    def __post_init__(self) -> None:
        if self.location is not None:
            object.__setattr__(self, "location", Path(self.location))


@dataclass(frozen=True, slots=True)
class ImportResult:
    """Result of translating an external document to one public request."""

    format_name: str
    format_version: str
    operation: Operation | None
    request: ApplicationRequest | None
    source: SourceAttribution
    diagnostics: TranslationDiagnostics = TranslationDiagnostics()

    @property
    def success(self) -> bool:
        """Return whether a request was produced without error diagnostics."""
        return self.request is not None and not self.diagnostics.has_errors


@dataclass(frozen=True, slots=True)
class ImportExecution:
    """Imported request paired with its immutable public API response."""

    imported: ImportResult
    response: OperationResponse


@dataclass(frozen=True, slots=True)
class ExportResult:
    """Deterministic external representation of a public API response."""

    format_name: str
    format_version: str
    media_type: str
    content: str
    encoding: str = "utf-8"
    diagnostics: TranslationDiagnostics = TranslationDiagnostics()

    @property
    def bytes(self) -> bytes:
        """Return encoded bytes for persistence or transport."""
        return self.content.encode(self.encoding)
