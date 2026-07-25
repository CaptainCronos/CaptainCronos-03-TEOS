"""Descriptor-only HTML renderer implementation."""

from src.models.lifecycle import OutputFormat

from .renderer import Renderer


class HtmlRenderer(Renderer):
    """Describe a future HTML output without generating a page."""

    name = "html"
    output_format = OutputFormat.HTML
    content_type = "text/html; charset=utf-8"
    file_extension = ".html"
