"""Presentation of CLI results and diagnostics."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping, TextIO

from .exceptions import OutputError


def _json_value(value: Any) -> Any:
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, tuple):
        return [_json_value(item) for item in value]
    if isinstance(value, dict):
        return {key: _json_value(item) for key, item in value.items()}
    return value


class OutputWriter:
    """Write successful results to stdout and diagnostics to stderr."""

    def __init__(
        self, stdout: TextIO, stderr: TextIO, *, json_output: bool = False
    ) -> None:
        self._stdout = stdout
        self._stderr = stderr
        self.json_output = json_output

    def result(self, message: str, **fields: object) -> None:
        """Present one successful command result."""
        if self.json_output:
            payload = {"message": message, **fields}
            text = json.dumps(
                _json_value(payload), sort_keys=True, separators=(",", ":")
            )
        else:
            suffix = " ".join(
                f"{key}={value}" for key, value in sorted(fields.items())
            )
            text = f"{message}{' ' + suffix if suffix else ''}"
        self._write(self._stdout, text + "\n")

    def diagnostic(
        self,
        message: str,
        *,
        details: Mapping[str, object] | None = None,
    ) -> None:
        """Present one failure diagnostic."""
        if self.json_output:
            payload = {"error": message, "details": dict(details or {})}
            text = json.dumps(
                _json_value(payload), sort_keys=True, separators=(",", ":")
            )
        else:
            suffix = " ".join(
                f"{key}={value}"
                for key, value in sorted((details or {}).items())
            )
            text = f"error: {message}{' ' + suffix if suffix else ''}"
        self._write(self._stderr, text + "\n")

    @staticmethod
    def _write(stream: TextIO, value: str) -> None:
        try:
            stream.write(value)
            stream.flush()
        except OSError as error:
            raise OutputError(f"could not write CLI output: {error}") from error
