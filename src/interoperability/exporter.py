"""Base exporter contract and stable public-response projection."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import fields, is_dataclass
from datetime import date, datetime
from enum import Enum
from pathlib import Path
from typing import Any, Mapping

from src.api import (
    ArtifactResult,
    GeneratedFileResult,
    OperationResponse,
    OperationResult,
    PipelineResult,
)

from .contracts import ExportResult, FormatCapability
from .export_context import ExportContext


ExportSource = OperationResponse | ArtifactResult | GeneratedFileResult


class Exporter(ABC):
    """Common interface implemented by every response exporter."""

    capability: FormatCapability

    @property
    def name(self) -> str:
        """Return the stable registry name."""
        return self.capability.name

    @abstractmethod
    def export(
        self, response: ExportSource, context: ExportContext
    ) -> ExportResult:
        """Translate one public API response or artifact to external text."""


def to_primitive(value: Any) -> Any:
    """Project public immutable values into deterministic scalar containers."""
    if isinstance(value, Enum):
        return value.value
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if isinstance(value, Mapping):
        return {
            str(key): to_primitive(child)
            for key, child in sorted(value.items(), key=lambda item: str(item[0]))
        }
    if isinstance(value, (tuple, list)):
        return [to_primitive(child) for child in value]
    if is_dataclass(value):
        return {
            item.name: to_primitive(getattr(value, item.name))
            for item in fields(value)
        }
    raise TypeError(f"unsupported public response value: {type(value).__name__}")


def _result_projection(result: OperationResult | None) -> Any:
    if result is None:
        return None
    projection: dict[str, Any] = {
        "status": result.status.value,
        "values": {
            name: to_primitive(value)
            for name, value in sorted(result.values, key=lambda item: item[0])
        },
    }
    if isinstance(result, PipelineResult):
        projection["stages"] = [
            {
                "stage": stage.stage.value,
                "status": stage.status.value,
                "values": {
                    name: to_primitive(value)
                    for name, value in sorted(
                        stage.values, key=lambda item: item[0]
                    )
                },
                "diagnostics": to_primitive(stage.diagnostics.items),
                "elapsed_seconds": stage.elapsed_seconds,
            }
            for stage in result.stages
        ]
        projection["artifacts"] = to_primitive(result.artifacts)
        projection["generated_files"] = to_primitive(result.generated_files)
    return projection


def response_document(
    response: ExportSource,
    context: ExportContext,
) -> dict[str, Any]:
    """Create the canonical external projection of a public API value."""
    if isinstance(response, ArtifactResult):
        return {
            "format_version": context.format_version,
            "kind": "artifact",
            "operation": None,
            "status": None,
            "success": True,
            "result": to_primitive(response),
            "elapsed_seconds": None,
            "source": None,
            "diagnostics": [],
        }
    if isinstance(response, GeneratedFileResult):
        return {
            "format_version": context.format_version,
            "kind": "generated_file",
            "operation": None,
            "status": None,
            "success": True,
            "result": to_primitive(response),
            "elapsed_seconds": None,
            "source": None,
            "diagnostics": [],
        }
    document = {
        "format_version": context.format_version,
        "kind": "response",
        "operation": to_primitive(response.operation),
        "status": response.status.value,
        "success": response.success,
        "result": _result_projection(response.result),
        "elapsed_seconds": response.elapsed_seconds,
        "source": to_primitive(response.source),
    }
    if context.conversion_options.include_diagnostics:
        document["diagnostics"] = to_primitive(response.diagnostics.items)
    if hasattr(response, "plugins"):
        document["plugins"] = to_primitive(response.plugins)
    return document
