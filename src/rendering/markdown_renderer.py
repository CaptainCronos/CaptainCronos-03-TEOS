"""Descriptor-only Markdown renderer implementation."""

from src.models.lifecycle import OutputFormat

from .renderer import Renderer


class MarkdownRenderer(Renderer):
    """Describe a future Markdown output without generating a document."""

    name = "markdown"
    output_format = OutputFormat.MARKDOWN
    content_type = "text/markdown; charset=utf-8"
    file_extension = ".md"
