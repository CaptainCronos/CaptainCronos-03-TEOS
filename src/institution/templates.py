"""Immutable template selection configuration without rendering behavior."""

from dataclasses import dataclass
from enum import StrEnum
from pathlib import PurePosixPath

from .exceptions import TemplateConfigurationError


class TemplateKind(StrEnum):
    """Supported institution-selectable document template families."""

    LESSON_PLAN = "lesson-plan"
    ASSESSMENT = "assessment"
    QUIZ = "quiz"
    WORKSHEET = "worksheet"
    CERTIFICATE = "certificate"
    REPORT = "report"
    ATTENDANCE_SHEET = "attendance-sheet"
    GRADING_EXPORT = "grading-export"


@dataclass(frozen=True, slots=True)
class TemplateSelection:
    """One versioned external template choice."""

    identifier: str
    kind: TemplateKind
    path: PurePosixPath
    version: str
    format: str
    audience: str | None = None
    is_default: bool = False

    def __post_init__(self) -> None:
        if not self.identifier or not self.version or not self.format:
            raise ValueError("template identifier, version, and format are required")
        if self.path.is_absolute() or ".." in self.path.parts:
            raise ValueError("template path must be a safe relative path")


@dataclass(frozen=True, slots=True)
class TemplateProfile:
    """Deterministic template catalog and selection policy."""

    selections: tuple[TemplateSelection, ...] = ()

    def select(
        self, kind: TemplateKind, *, audience: str | None = None
    ) -> TemplateSelection:
        """Select an exact audience template or the unique default."""
        exact = tuple(
            item
            for item in self.selections
            if item.kind is kind and item.audience == audience
        )
        if len(exact) == 1:
            return exact[0]
        defaults = tuple(
            item
            for item in self.selections
            if item.kind is kind and item.is_default
        )
        if len(defaults) == 1:
            return defaults[0]
        raise TemplateConfigurationError(
            f"no unambiguous template for {kind.value!r}"
        )
