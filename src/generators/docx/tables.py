"""DOCX table creation helpers."""


def add_table(
    document,
    output_table,
    *,
    alternating_rows: bool = False,
    repeat_header: bool = True,
):
    """Add a stable grid table for format-neutral table values."""
    from docx.oxml import OxmlElement
    from docx.oxml.ns import qn

    table = document.add_table(rows=1, cols=len(output_table.headers))
    table.style = "Table Grid"
    for cell, value in zip(table.rows[0].cells, output_table.headers):
        cell.text = value
        for run in cell.paragraphs[0].runs:
            run.bold = True
    if repeat_header:
        header_properties = table.rows[0]._tr.get_or_add_trPr()
        repeat = OxmlElement("w:tblHeader")
        repeat.set(qn("w:val"), "true")
        header_properties.append(repeat)
    for row_index, values in enumerate(output_table.rows, 1):
        cells = table.add_row().cells
        for cell, value in zip(cells, values):
            cell.text = value
            if alternating_rows and row_index % 2 == 0:
                shading = OxmlElement("w:shd")
                shading.set(qn("w:fill"), "E8EEF3")
                cell._tc.get_or_add_tcPr().append(shading)
    return table
