"""Deterministic GitHub-compatible Markdown generation."""

from __future__ import annotations

import base64
from pathlib import Path

from src.models.lifecycle import OutputFormat
from src.rendering import RenderedArtifact, RenderingContext, Template

from ..generator import Generator
from ..output import DocumentOutput


def _cell(value: str) -> str:
    return value.replace("\\", "\\\\").replace("|", "\\|").replace("\n", "<br>")


class MarkdownGenerator(Generator):
    """Encode rendered artifacts as standalone UTF-8 Markdown."""

    name = "markdown"
    output_format = OutputFormat.MARKDOWN
    mime_type = "text/markdown; charset=utf-8"
    file_extension = ".md"

    def _encode(
        self,
        artifact: RenderedArtifact,
        output: DocumentOutput,
        *,
        template: Template | None,
        context: RenderingContext | None,
        asset_root: Path,
    ) -> bytes:
        lines = [f"# {output.title}", "", output.subtitle, ""]
        logo = self.logo_asset(context)
        if logo is not None:
            payload = base64.b64encode(
                self.load_asset(logo, asset_root)
            ).decode("ascii")
            lines.extend(
                [
                    f"![{logo.description or 'Logo'}]"
                    f"(data:{logo.content_type};base64,{payload})",
                    "",
                ]
            )
        lines.extend(
            [
                "## Navigation",
                "",
                *(
                    f"- [{section.heading}](#"
                    f"{section.heading.lower().replace(' ', '-').replace(':', '')})"
                    for section in output.sections
                ),
                "",
            ]
        )
        for section in output.sections:
            lines.extend([f"## {section.heading}", ""])
            for paragraph in section.paragraphs:
                lines.extend([paragraph, ""])
            for item in section.items:
                lines.append(f"- {item}")
            if section.items:
                lines.append("")
            for table in section.tables:
                lines.append("| " + " | ".join(map(_cell, table.headers)) + " |")
                lines.append("| " + " | ".join("---" for _ in table.headers) + " |")
                lines.extend(
                    "| " + " | ".join(map(_cell, row)) + " |"
                    for row in table.rows
                )
                lines.append("")
        return ("\n".join(lines).rstrip() + "\n").encode("utf-8")
