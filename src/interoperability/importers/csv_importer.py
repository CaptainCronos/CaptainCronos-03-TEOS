"""Single-record CSV request importer."""

from __future__ import annotations

import csv
import io
import json
from typing import Any, Mapping

from ..contracts import CapabilityKind, FormatCapability
from ..exceptions import FormatError
from ..import_context import ImportContext
from ..importer import Importer, request_envelope_from_flat_record


class CsvImporter(Importer):
    """Translate one flat CSV record to a public API request."""

    capability = FormatCapability(
        "csv",
        CapabilityKind.IMPORTER,
        extensions=(".csv",),
        media_types=("text/csv",),
    )

    def decode(self, data: bytes, context: ImportContext) -> Mapping[str, Any]:
        """Decode exactly one header-based CSV record."""
        try:
            text = data.decode(context.format_options.encoding)
            reader = csv.DictReader(
                io.StringIO(text, newline=""),
                delimiter=context.format_options.delimiter,
                strict=True,
            )
            rows = list(reader)
        except (UnicodeDecodeError, csv.Error) as error:
            raise FormatError(f"invalid CSV import: {error}") from error
        if reader.fieldnames is None:
            raise FormatError("CSV import requires a header row")
        if None in reader.fieldnames:
            raise FormatError("CSV import contains an empty header")
        if len(rows) != 1:
            raise FormatError("CSV import requires exactly one request row")
        if None in rows[0]:
            raise FormatError("CSV row has more values than header fields")
        record: dict[str, Any] = dict(rows[0])
        for name, value in tuple(record.items()):
            stripped = value.strip() if isinstance(value, str) else value
            if (
                isinstance(stripped, str)
                and stripped
                and stripped[0] in "[{"
            ):
                try:
                    record[name] = json.loads(stripped)
                except json.JSONDecodeError as error:
                    raise FormatError(
                        f"CSV field {name!r} contains invalid JSON: {error}"
                    ) from error
            else:
                record[name] = stripped
        return request_envelope_from_flat_record(record)
