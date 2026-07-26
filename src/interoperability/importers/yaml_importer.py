"""YAML request-envelope importer."""

from __future__ import annotations

from typing import Any, Mapping

import yaml

from ..contracts import CapabilityKind, FormatCapability
from ..exceptions import FormatError
from ..import_context import ImportContext
from ..importer import Importer


class YamlImporter(Importer):
    """Translate a safe YAML envelope to a public API request."""

    capability = FormatCapability(
        "yaml",
        CapabilityKind.IMPORTER,
        extensions=(".yaml", ".yml"),
        media_types=("application/yaml", "text/yaml"),
    )

    def decode(self, data: bytes, context: ImportContext) -> Mapping[str, Any]:
        """Decode one safe YAML mapping."""
        try:
            document = yaml.safe_load(
                data.decode(context.format_options.encoding)
            )
        except (UnicodeDecodeError, yaml.YAMLError) as error:
            raise FormatError(f"invalid YAML import: {error}") from error
        if not isinstance(document, Mapping):
            raise FormatError("YAML import must contain one mapping")
        return document
