"""Descriptor-only PDF renderer implementation."""

from src.models.lifecycle import OutputFormat

from .renderer import Renderer


class PdfRenderer(Renderer):
    """Describe a future PDF output without generating document bytes."""

    name = "pdf"
    output_format = OutputFormat.PDF
    content_type = "application/pdf"
    file_extension = ".pdf"
