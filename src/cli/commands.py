"""Immutable command vocabulary passed from parsing to application dispatch."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class CommandName(StrEnum):
    """Commands supported by the TEOS command-line interface."""

    VALIDATE = "validate"
    COMPILE = "compile"
    SCHEDULE = "schedule"
    RENDER = "render"
    GENERATE = "generate"
    BUILD = "build"
    INFO = "info"
    VERSION = "version"
    DOCTOR = "doctor"
    LIST = "list"


@dataclass(frozen=True, slots=True)
class CommandRequest:
    """One parsed command and its command-specific immutable arguments."""

    name: CommandName
    target: str | None = None
