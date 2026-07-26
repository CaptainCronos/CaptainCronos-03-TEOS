"""Immutable operational configuration and deterministic precedence loading."""

from __future__ import annotations

import json
import os
from collections.abc import Sequence
from dataclasses import dataclass, fields
from pathlib import Path
from typing import Any, Mapping

from .exceptions import ConfigurationError


_CONFIGURATION_KEYS = frozenset(
    {
        "repository",
        "output_directory",
        "renderer",
        "generator",
        "institution_profile",
        "institution_profile_version",
        "academic_calendar",
        "academic_calendar_version",
        "logging_level",
        "verbose",
        "debug",
        "timing",
        "progress",
        "json_output",
    }
)

_ENVIRONMENT_KEYS = {
    "TEOS_REPOSITORY": "repository",
    "TEOS_OUTPUT_DIRECTORY": "output_directory",
    "TEOS_RENDERER": "renderer",
    "TEOS_GENERATOR": "generator",
    "TEOS_INSTITUTION_PROFILE": "institution_profile",
    "TEOS_INSTITUTION_PROFILE_VERSION": "institution_profile_version",
    "TEOS_ACADEMIC_CALENDAR": "academic_calendar",
    "TEOS_ACADEMIC_CALENDAR_VERSION": "academic_calendar_version",
    "TEOS_LOG_LEVEL": "logging_level",
    "TEOS_VERBOSE": "verbose",
    "TEOS_DEBUG": "debug",
    "TEOS_TIMING": "timing",
    "TEOS_PROGRESS": "progress",
    "TEOS_JSON": "json_output",
}

_BOOLEAN_KEYS = frozenset(
    {"verbose", "debug", "timing", "progress", "json_output"}
)
_FORMATS = frozenset({"docx", "pdf", "html", "markdown"})
_LEVELS = frozenset({"debug", "info", "warning", "error"})


def _freeze_extension(value: Any) -> Any:
    if isinstance(value, Mapping):
        return tuple(
            (str(key), _freeze_extension(child))
            for key, child in sorted(value.items(), key=lambda item: str(item[0]))
        )
    if isinstance(value, Sequence) and not isinstance(
        value, (str, bytes, bytearray)
    ):
        return tuple(_freeze_extension(child) for child in value)
    return value


@dataclass(frozen=True, slots=True)
class CliConfiguration:
    """Complete immutable operational configuration for one invocation."""

    repository: Path = Path(".")
    output_directory: Path = Path("output")
    renderer: str = "markdown"
    generator: str = "markdown"
    institution_profile: str | None = None
    institution_profile_version: str | None = None
    academic_calendar: str | None = None
    academic_calendar_version: str | None = None
    logging_level: str = "info"
    verbose: bool = False
    debug: bool = False
    timing: bool = False
    progress: bool = True
    json_output: bool = False
    extensions: tuple[tuple[str, Any], ...] = ()

    def __post_init__(self) -> None:
        """Normalize paths and validate CLI-owned enumerations."""
        object.__setattr__(self, "repository", Path(self.repository))
        object.__setattr__(
            self, "output_directory", Path(self.output_directory)
        )
        object.__setattr__(self, "renderer", self.renderer.lower())
        object.__setattr__(self, "generator", self.generator.lower())
        object.__setattr__(self, "logging_level", self.logging_level.lower())
        if self.renderer not in _FORMATS:
            raise ConfigurationError(
                f"unsupported renderer selection: {self.renderer}"
            )
        if self.generator not in _FORMATS:
            raise ConfigurationError(
                f"unsupported generator selection: {self.generator}"
            )
        if self.logging_level not in _LEVELS:
            raise ConfigurationError(
                f"unsupported logging level: {self.logging_level}"
            )


def _boolean(value: Any, name: str) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        normalized = value.strip().lower()
        if normalized in {"1", "true", "yes", "on"}:
            return True
        if normalized in {"0", "false", "no", "off"}:
            return False
    raise ConfigurationError(f"{name} must be a boolean")


def _read_file(path: str | Path | None) -> dict[str, Any]:
    if path is None:
        return {}
    source = Path(path)
    try:
        value = json.loads(source.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise ConfigurationError(
            f"could not load configuration {source}: {error}"
        ) from error
    if not isinstance(value, dict):
        raise ConfigurationError("configuration file must contain an object")
    return value


def load_configuration(
    path: str | Path | None = None,
    *,
    overrides: Mapping[str, Any] | None = None,
    environ: Mapping[str, str] | None = None,
) -> CliConfiguration:
    """Load configuration using defaults, file, environment, then overrides."""
    document = _read_file(path)
    values = {
        key: value
        for key, value in document.items()
        if key in _CONFIGURATION_KEYS
    }
    extensions = tuple(
        sorted(
            (
                (key, value)
                for key, value in document.items()
                if key not in _CONFIGURATION_KEYS
            ),
            key=lambda item: item[0],
        )
    )
    extensions = tuple(
        (key, _freeze_extension(value)) for key, value in extensions
    )
    environment = os.environ if environ is None else environ
    for environment_key, configuration_key in _ENVIRONMENT_KEYS.items():
        if environment_key in environment:
            values[configuration_key] = environment[environment_key]
    for key, value in (overrides or {}).items():
        if value is not None:
            values[key] = value
    for key in _BOOLEAN_KEYS:
        if key in values:
            values[key] = _boolean(values[key], key)
    valid_fields = {field.name for field in fields(CliConfiguration)}
    unexpected = sorted(set(values) - valid_fields)
    if unexpected:
        raise ConfigurationError(
            f"unknown configuration override: {unexpected[0]}"
        )
    try:
        return CliConfiguration(**values, extensions=extensions)
    except TypeError as error:
        raise ConfigurationError(str(error)) from error
