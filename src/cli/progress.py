"""User-facing pipeline progress events independent of structured logs."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Protocol, TextIO

from .exceptions import OutputError


class ProgressState(StrEnum):
    """Lifecycle states emitted for CLI pipeline stages."""

    STARTED = "started"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass(frozen=True, slots=True)
class ProgressEvent:
    """One immutable stage progress notification."""

    stage: str
    state: ProgressState
    detail: str | None = None


class ProgressReporter(Protocol):
    """Observer interface for pipeline progress."""

    def report(self, event: ProgressEvent) -> None:
        """Observe one pipeline event."""


class TextProgressReporter:
    """Write concise human-readable progress to a stream."""

    def __init__(self, stream: TextIO, *, enabled: bool = True) -> None:
        self._stream = stream
        self.enabled = enabled

    def report(self, event: ProgressEvent) -> None:
        """Write one progress line when reporting is enabled."""
        if not self.enabled:
            return
        suffix = f": {event.detail}" if event.detail else ""
        try:
            self._stream.write(
                f"[{event.state.value}] {event.stage}{suffix}\n"
            )
            self._stream.flush()
        except OSError as error:
            raise OutputError(
                f"could not write progress: {error}"
            ) from error


class NullProgressReporter:
    """Ignore progress while preserving the reporter interface."""

    def report(self, event: ProgressEvent) -> None:
        """Discard one event."""
