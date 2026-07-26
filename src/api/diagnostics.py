"""Immutable machine-readable diagnostics published by the application API."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path
from typing import Iterable, Iterator


class DiagnosticSeverity(StrEnum):
    """Severity levels in increasing order of operational impact."""

    INFORMATION = "information"
    WARNING = "warning"
    ERROR = "error"
    FATAL = "fatal"


@dataclass(frozen=True, slots=True)
class DiagnosticCode:
    """Namespaced machine-readable diagnostic identifier."""

    value: str

    def __post_init__(self) -> None:
        if not self.value or any(character.isspace() for character in self.value):
            raise ValueError("diagnostic code must be a non-empty token")

    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True, slots=True)
class DiagnosticLocation:
    """Optional source, object, and field location for one diagnostic."""

    source: Path | None = None
    object_identifier: str | None = None
    field_path: tuple[str | int, ...] = ()

    def __post_init__(self) -> None:
        if self.source is not None:
            object.__setattr__(self, "source", Path(self.source))
        object.__setattr__(self, "field_path", tuple(self.field_path))


@dataclass(frozen=True, slots=True)
class Diagnostic:
    """One stable application observation or failure."""

    code: DiagnosticCode
    severity: DiagnosticSeverity
    message: str
    stage: str | None = None
    location: DiagnosticLocation | None = None

    def __post_init__(self) -> None:
        if not self.message:
            raise ValueError("diagnostic message cannot be empty")


@dataclass(frozen=True, slots=True)
class DiagnosticCollection:
    """Ordered immutable diagnostic collection with severity views."""

    items: tuple[Diagnostic, ...] = ()

    def __init__(self, items: Iterable[Diagnostic] = ()) -> None:
        object.__setattr__(self, "items", tuple(items))

    def __iter__(self) -> Iterator[Diagnostic]:
        return iter(self.items)

    def __len__(self) -> int:
        return len(self.items)

    def by_severity(
        self, *severities: DiagnosticSeverity
    ) -> tuple[Diagnostic, ...]:
        """Return diagnostics matching the selected severities."""
        selected = frozenset(severities)
        return tuple(item for item in self.items if item.severity in selected)

