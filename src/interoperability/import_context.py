"""Immutable configuration supplied to importers."""

from dataclasses import dataclass
from pathlib import Path

from .contracts import (
    DEFAULT_FORMAT_VERSION,
    ConversionOptions,
    FormatOptions,
)


@dataclass(frozen=True, slots=True)
class ImportContext:
    """Input-only context for one import translation."""

    format_version: str = DEFAULT_FORMAT_VERSION
    source: Path | None = None
    format_options: FormatOptions = FormatOptions()
    conversion_options: ConversionOptions = ConversionOptions()

    def __post_init__(self) -> None:
        if not self.format_version:
            raise ValueError("format version cannot be empty")
        if self.source is not None:
            object.__setattr__(self, "source", Path(self.source))
