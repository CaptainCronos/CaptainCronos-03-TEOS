"""Deterministic JSON response exporter."""

from __future__ import annotations

import json

from ..contracts import (
    CapabilityKind,
    ExportResult,
    FormatCapability,
)
from ..export_context import ExportContext
from ..exporter import Exporter, ExportSource, response_document


class JsonExporter(Exporter):
    """Serialize a public API response as canonical readable JSON."""

    capability = FormatCapability(
        "json",
        CapabilityKind.EXPORTER,
        extensions=(".json",),
        media_types=("application/json",),
    )

    def export(
        self, response: ExportSource, context: ExportContext
    ) -> ExportResult:
        """Export one public response."""
        content = json.dumps(
            response_document(response, context),
            ensure_ascii=False,
            indent=context.format_options.indent,
            sort_keys=context.format_options.sort_keys,
        )
        content = content.replace("\n", context.format_options.newline)
        content += context.format_options.newline
        return ExportResult(
            self.name,
            context.format_version,
            self.capability.media_types[0],
            content,
            context.format_options.encoding,
        )
