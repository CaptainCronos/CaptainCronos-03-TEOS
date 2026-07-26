"""JSON request-envelope importer."""

from __future__ import annotations

import json
from typing import Any, Mapping

from ..contracts import CapabilityKind, FormatCapability
from ..exceptions import FormatError
from ..import_context import ImportContext
from ..importer import Importer


class JsonImporter(Importer):
    """Translate a JSON envelope to a public API request."""

    capability = FormatCapability(
        "json",
        CapabilityKind.IMPORTER,
        extensions=(".json",),
        media_types=("application/json",),
    )

    def decode(self, data: bytes, context: ImportContext) -> Mapping[str, Any]:
        """Decode one JSON object."""
        try:
            document = json.loads(data.decode(context.format_options.encoding))
        except (UnicodeDecodeError, json.JSONDecodeError) as error:
            raise FormatError(f"invalid JSON import: {error}") from error
        if not isinstance(document, Mapping):
            raise FormatError("JSON import must contain one object")
        return document
