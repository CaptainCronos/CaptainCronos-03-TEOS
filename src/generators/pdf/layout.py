"""ReportLab page layout, header, footer, and pagination helpers."""

from __future__ import annotations


def page_geometry(context):
    """Return ReportLab page size and margins from immutable page settings."""
    from reportlab.lib.pagesizes import A4, LEGAL, LETTER, landscape
    from reportlab.lib.units import mm

    if context is None:
        return LETTER, (25.4 * mm,) * 4
    sizes = {"letter": LETTER, "a4": A4, "legal": LEGAL}
    page_size = sizes.get(context.page_settings.size.lower(), LETTER)
    if context.page_settings.orientation == "landscape":
        page_size = landscape(page_size)
    settings = context.page_settings
    margins = (
        settings.margin_left_mm * mm,
        settings.margin_right_mm * mm,
        settings.margin_top_mm * mm,
        settings.margin_bottom_mm * mm,
    )
    return page_size, margins


def page_decorator(
    title: str,
    institution_name: str | None,
    *,
    show_header: bool = True,
    show_footer: bool = True,
    show_page_number: bool = True,
):
    """Return a stable callback that draws headers, footers, and page numbers."""
    def decorate(canvas, document) -> None:
        canvas.saveState()
        width, height = document.pagesize
        canvas.setFont("Helvetica", 8)
        if show_header:
            canvas.drawString(
                document.leftMargin, height - 18, institution_name or title
            )
        if show_footer:
            footer = "TEOS"
            if show_page_number:
                footer += f" · Page {document.page}"
            canvas.drawRightString(width - document.rightMargin, 18, footer)
        canvas.restoreState()

    return decorate
