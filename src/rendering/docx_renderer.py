"""Descriptor-only DOCX renderer implementation."""

from src.models.lifecycle import OutputFormat

from .renderer import Renderer


class DocxRenderer(Renderer):
    """Describe a future DOCX output without generating document bytes."""

    name = "docx"
    output_format = OutputFormat.DOCX
    content_type = (
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    )
    file_extension = ".docx"
