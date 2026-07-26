"""Deterministic single-record CSV response exporter."""

from __future__ import annotations

import csv
import io
import json

from ..contracts import (
    CapabilityKind,
    ExportResult,
    FormatCapability,
)
from ..export_context import ExportContext
from ..exporter import Exporter, ExportSource, response_document


class CsvExporter(Exporter):
    """Serialize one public response as a flat CSV summary."""

    capability = FormatCapability(
        "csv",
        CapabilityKind.EXPORTER,
        extensions=(".csv",),
        media_types=("text/csv",),
    )
    _FIELDS = (
        "format_version",
        "kind",
        "operation",
        "status",
        "success",
        "result",
        "diagnostics",
        "elapsed_seconds",
        "source",
        "plugins",
    )

    def export(
        self, response: ExportSource, context: ExportContext
    ) -> ExportResult:
        """Export one public response as one header and one data row."""
        document = response_document(response, context)
        row = {
            name: (
                json.dumps(
                    document[name],
                    ensure_ascii=False,
                    sort_keys=True,
                    separators=(",", ":"),
                )
                if isinstance(document.get(name), (dict, list))
                else document.get(name, "")
            )
            for name in self._FIELDS
        }
        output = io.StringIO(newline="")
        writer = csv.DictWriter(
            output,
            fieldnames=self._FIELDS,
            delimiter=context.format_options.delimiter,
            lineterminator=context.format_options.newline,
        )
        writer.writeheader()
        writer.writerow(row)
        return ExportResult(
            self.name,
            context.format_version,
            self.capability.media_types[0],
            output.getvalue(),
            context.format_options.encoding,
        )
