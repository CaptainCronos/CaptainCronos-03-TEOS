"""Small structured logger for deterministic CLI diagnostics."""

from __future__ import annotations

from dataclasses import dataclass
from enum import IntEnum
from typing import TextIO

from .exceptions import OutputError


class LogLevel(IntEnum):
    """Ordered CLI logging thresholds."""

    DEBUG = 10
    INFO = 20
    WARNING = 30
    ERROR = 40


@dataclass(frozen=True, slots=True)
class LogRecord:
    """One immutable structured logging event."""

    level: LogLevel
    event: str
    message: str
    fields: tuple[tuple[str, object], ...] = ()


class StructuredLogger:
    """Write stable key-value log records to a text stream."""

    def __init__(self, stream: TextIO, threshold: LogLevel) -> None:
        self._stream = stream
        self.threshold = threshold

    def emit(
        self,
        level: LogLevel,
        event: str,
        message: str,
        **fields: object,
    ) -> None:
        """Write a record when it meets the configured threshold."""
        record = LogRecord(
            level, event, message, tuple(sorted(fields.items()))
        )
        if record.level < self.threshold:
            return
        values = [
            f"level={record.level.name.lower()}",
            f"event={record.event}",
            f"message={record.message!r}",
        ]
        values.extend(f"{key}={value!r}" for key, value in record.fields)
        try:
            self._stream.write(" ".join(values) + "\n")
            self._stream.flush()
        except OSError as error:
            raise OutputError(f"could not write log record: {error}") from error

    def debug(self, event: str, message: str, **fields: object) -> None:
        """Emit a debug record."""
        self.emit(LogLevel.DEBUG, event, message, **fields)

    def info(self, event: str, message: str, **fields: object) -> None:
        """Emit an information record."""
        self.emit(LogLevel.INFO, event, message, **fields)

    def warning(self, event: str, message: str, **fields: object) -> None:
        """Emit a warning record."""
        self.emit(LogLevel.WARNING, event, message, **fields)

    def error(self, event: str, message: str, **fields: object) -> None:
        """Emit an error record."""
        self.emit(LogLevel.ERROR, event, message, **fields)


def logging_threshold(level: str, *, verbose: bool, debug: bool) -> LogLevel:
    """Resolve explicit level and convenience flags to one threshold."""
    if debug:
        return LogLevel.DEBUG
    if verbose and level in {"warning", "error"}:
        return LogLevel.INFO
    return LogLevel[level.upper()]
