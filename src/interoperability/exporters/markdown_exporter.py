"""Human-readable Markdown public-response exporter."""

from __future__ import annotations

import yaml

from ..contracts import (
    CapabilityKind,
    ExportResult,
    FormatCapability,
)
from ..export_context import ExportContext
from ..exporter import Exporter, ExportSource, response_document


class MarkdownExporter(Exporter):
    """Serialize a public response as deterministic Markdown with metadata."""

    capability = FormatCapability(
        "markdown",
        CapabilityKind.EXPORTER,
        extensions=(".md", ".markdown"),
        media_types=("text/markdown",),
    )

    def export(
        self, response: ExportSource, context: ExportContext
    ) -> ExportResult:
        """Export one response with YAML metadata and a concise summary."""
        document = response_document(response, context)
        metadata = yaml.safe_dump(
            document,
            allow_unicode=True,
            default_flow_style=False,
            sort_keys=context.format_options.sort_keys,
            indent=context.format_options.indent,
            line_break=context.format_options.newline,
        ).rstrip("\r\n")
        newline = context.format_options.newline
        operation = document["operation"] or document["kind"]
        title = str(operation).replace("_", " ").title()
        status = document["status"] or "not_applicable"
        content = newline.join(
            (
                "---",
                metadata,
                "---",
                "",
                f"# {title}",
                "",
                f"- Status: `{status}`",
                f"- Success: `{str(document['success']).lower()}`",
                "",
            )
        )
        return ExportResult(
            self.name,
            context.format_version,
            self.capability.media_types[0],
            content,
            context.format_options.encoding,
        )
