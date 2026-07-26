"""Markdown request importer using explicit YAML front matter."""

from __future__ import annotations

from typing import Any, Mapping

import yaml

from ..contracts import CapabilityKind, FormatCapability
from ..exceptions import FormatError
from ..import_context import ImportContext
from ..importer import Importer


class MarkdownImporter(Importer):
    """Translate Markdown YAML front matter to a public API request."""

    capability = FormatCapability(
        "markdown",
        CapabilityKind.IMPORTER,
        extensions=(".md", ".markdown"),
        media_types=("text/markdown",),
    )

    def decode(self, data: bytes, context: ImportContext) -> Mapping[str, Any]:
        """Decode a YAML front-matter envelope and ignore the prose body."""
        try:
            text = data.decode(context.format_options.encoding)
        except UnicodeDecodeError as error:
            raise FormatError(f"invalid Markdown encoding: {error}") from error
        lines = text.splitlines()
        if not lines or lines[0].strip() != "---":
            raise FormatError("Markdown import requires YAML front matter")
        try:
            closing = next(
                index
                for index, line in enumerate(lines[1:], start=1)
                if line.strip() == "---"
            )
        except StopIteration as error:
            raise FormatError("Markdown YAML front matter is not closed") from error
        try:
            document = yaml.safe_load("\n".join(lines[1:closing]))
        except yaml.YAMLError as error:
            raise FormatError(f"invalid Markdown front matter: {error}") from error
        if not isinstance(document, Mapping):
            raise FormatError("Markdown front matter must contain one mapping")
        return document
