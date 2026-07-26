"""Deterministic YAML response exporter."""

from __future__ import annotations

import yaml

from ..contracts import (
    CapabilityKind,
    ExportResult,
    FormatCapability,
)
from ..export_context import ExportContext
from ..exporter import Exporter, ExportSource, response_document


class YamlExporter(Exporter):
    """Serialize a public API response as safe YAML."""

    capability = FormatCapability(
        "yaml",
        CapabilityKind.EXPORTER,
        extensions=(".yaml", ".yml"),
        media_types=("application/yaml", "text/yaml"),
    )

    def export(
        self, response: ExportSource, context: ExportContext
    ) -> ExportResult:
        """Export one public response."""
        content = yaml.safe_dump(
            response_document(response, context),
            allow_unicode=True,
            default_flow_style=False,
            sort_keys=context.format_options.sort_keys,
            indent=context.format_options.indent,
            line_break=context.format_options.newline,
        )
        return ExportResult(
            self.name,
            context.format_version,
            self.capability.media_types[0],
            content,
            context.format_options.encoding,
        )
