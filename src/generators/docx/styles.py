"""DOCX style and page-layout helpers."""

from __future__ import annotations


def apply_document_styles(document, template, context) -> None:
    """Apply approved typography, theme colors, and physical page settings."""
    from docx.enum.section import WD_ORIENT
    from docx.shared import Mm, Pt

    typography = (
        template.formatting.typography
        if template is not None
        else (context.theme.typography if context is not None else None)
    )
    if typography is not None:
        normal = document.styles["Normal"]
        normal.font.name = typography.body_family
        normal.font.size = Pt(typography.body_size_points)
        for name in ("Title", "Heading 1", "Heading 2"):
            document.styles[name].font.name = typography.heading_family
    if context is None:
        return
    settings = context.page_settings
    for section in document.sections:
        section.top_margin = Mm(settings.margin_top_mm)
        section.right_margin = Mm(settings.margin_right_mm)
        section.bottom_margin = Mm(settings.margin_bottom_mm)
        section.left_margin = Mm(settings.margin_left_mm)
        if settings.orientation == "landscape":
            section.orientation = WD_ORIENT.LANDSCAPE
            section.page_width, section.page_height = (
                section.page_height,
                section.page_width,
            )
