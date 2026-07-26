"""Immutable input-only requests accepted by the public application facade."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

from .exceptions import ApplicationConfigurationError


def _freeze_value(value: Any) -> Any:
    if isinstance(value, Mapping):
        return tuple(
            (str(key), _freeze_value(child))
            for key, child in sorted(
                value.items(), key=lambda item: str(item[0])
            )
        )
    if isinstance(value, (list, tuple)):
        return tuple(_freeze_value(child) for child in value)
    if isinstance(value, set):
        return tuple(sorted((_freeze_value(child) for child in value), key=repr))
    return value


def _freeze_mapping(
    value: Mapping[str, Any] | tuple[tuple[str, Any], ...],
) -> tuple[tuple[str, Any], ...]:
    return tuple(_freeze_value(value))


@dataclass(frozen=True, slots=True)
class ApplicationRequest:
    """Configuration shared by every public application request."""

    timing: bool = False
    diagnostic_verbosity: str = "normal"
    contract_version: str | None = None

    def __post_init__(self) -> None:
        if self.diagnostic_verbosity not in {"quiet", "normal", "verbose"}:
            raise ApplicationConfigurationError(
                "diagnostic verbosity must be quiet, normal, or verbose"
            )


@dataclass(frozen=True, slots=True)
class RepositoryRequest(ApplicationRequest):
    """Inputs shared by operations rooted in a TEOS repository."""

    repository_path: Path = Path(".")

    def __post_init__(self) -> None:
        ApplicationRequest.__post_init__(self)
        object.__setattr__(self, "repository_path", Path(self.repository_path))


@dataclass(frozen=True, slots=True)
class PipelineRequest(RepositoryRequest):
    """Inputs shared by compilation-through-generation operations."""

    institution_profile_id: str | None = None
    institution_profile_version: str | None = None
    academic_calendar_id: str | None = None
    academic_calendar_version: str | None = None
    renderer: str = "markdown"
    generator: str = "markdown"
    output_directory: Path = Path("output")
    plugin_configuration: tuple[tuple[str, Any], ...] = ()

    def __post_init__(self) -> None:
        RepositoryRequest.__post_init__(self)
        object.__setattr__(self, "renderer", self.renderer.lower())
        object.__setattr__(self, "generator", self.generator.lower())
        object.__setattr__(
            self, "output_directory", Path(self.output_directory)
        )
        object.__setattr__(
            self,
            "plugin_configuration",
            _freeze_mapping(self.plugin_configuration),
        )


@dataclass(frozen=True, slots=True)
class ValidateRequest(RepositoryRequest):
    """Request authoritative repository loading and validation."""


@dataclass(frozen=True, slots=True)
class CompileRequest(PipelineRequest):
    """Request repository compilation."""


@dataclass(frozen=True, slots=True)
class ScheduleRequest(PipelineRequest):
    """Request deterministic curriculum scheduling."""


@dataclass(frozen=True, slots=True)
class RenderRequest(PipelineRequest):
    """Request schedule rendering without physical generation."""


@dataclass(frozen=True, slots=True)
class GenerateRequest(PipelineRequest):
    """Request the complete pipeline through document generation."""


@dataclass(frozen=True, slots=True)
class BuildRequest(PipelineRequest):
    """Request the canonical complete application build."""


@dataclass(frozen=True, slots=True)
class InspectRequest(RepositoryRequest):
    """Request a stable repository inventory."""


DEFAULT_SCHEMA_PATH = Path(__file__).resolve().parents[2] / "schemas"


@dataclass(frozen=True, slots=True)
class DoctorRequest(ApplicationRequest):
    """Request read-only application readiness checks."""

    repository_path: Path = Path(".")
    schema_path: Path = DEFAULT_SCHEMA_PATH

    def __post_init__(self) -> None:
        ApplicationRequest.__post_init__(self)
        object.__setattr__(self, "repository_path", Path(self.repository_path))
        object.__setattr__(self, "schema_path", Path(self.schema_path))


@dataclass(frozen=True, slots=True)
class ListPluginsRequest(ApplicationRequest):
    """Request deterministic plugin discovery without activation."""
