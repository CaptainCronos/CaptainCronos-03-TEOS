"""ReportLab font resolution helpers."""


def font_names(template) -> tuple[str, str]:
    """Return stable built-in PDF fonts for body and headings."""
    if template is None:
        return ("Helvetica", "Helvetica-Bold")
    body = template.formatting.typography.body_family.lower()
    heading = template.formatting.typography.heading_family.lower()
    body_name = "Times-Roman" if "serif" in body and "sans" not in body else "Helvetica"
    heading_name = "Times-Bold"
    if "serif" not in heading or "sans" in heading:
        heading_name = "Helvetica-Bold"
    return body_name, heading_name
