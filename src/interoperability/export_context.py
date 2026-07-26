"""Immutable configuration supplied to exporters."""

from dataclasses import dataclass

from .contracts import (
    DEFAULT_FORMAT_VERSION,
    ConversionOptions,
    FormatOptions,
)


@dataclass(frozen=True, slots=True)
class ExportContext:
    """Input-only context for one export translation."""

    format_version: str = DEFAULT_FORMAT_VERSION
    format_options: FormatOptions = FormatOptions()
    conversion_options: ConversionOptions = ConversionOptions()

    def __post_init__(self) -> None:
        if not self.format_version:
            raise ValueError("format version cannot be empty")
