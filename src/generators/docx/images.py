"""DOCX image embedding helpers."""

from io import BytesIO


def add_image(paragraph, payload: bytes, *, max_width_inches: float = 2.0):
    """Embed one supported image payload in a paragraph."""
    from docx.shared import Inches

    run = paragraph.add_run()
    return run.add_picture(BytesIO(payload), width=Inches(max_width_inches))
