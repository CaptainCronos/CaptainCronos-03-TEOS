"""DOCX list and page-number field helpers."""


def add_list_item(document, text: str, *, ordered: bool = False):
    """Add one paragraph using a built-in deterministic list style."""
    style = "List Number" if ordered else "List Bullet"
    return document.add_paragraph(text, style=style)


def add_page_number(paragraph) -> None:
    """Insert a Word PAGE field into a paragraph."""
    from docx.oxml import OxmlElement
    from docx.oxml.ns import qn

    run = paragraph.add_run()
    begin = OxmlElement("w:fldChar")
    begin.set(qn("w:fldCharType"), "begin")
    instruction = OxmlElement("w:instrText")
    instruction.set(qn("xml:space"), "preserve")
    instruction.text = " PAGE "
    end = OxmlElement("w:fldChar")
    end.set(qn("w:fldCharType"), "end")
    run._r.extend((begin, instruction, end))
