"""DOCX generation using python-docx."""

from __future__ import annotations

from io import BytesIO
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile, ZipInfo

from src.models.lifecycle import OutputFormat
from src.rendering import RenderedArtifact, RenderingContext, Template

from ..exceptions import AssetEmbeddingError, MissingResourceError
from ..generator import Generator
from ..output import DocumentOutput
from .images import add_image
from .numbering import add_list_item, add_page_number
from .styles import apply_document_styles
from .tables import add_table


def _normalized_package(payload: bytes) -> bytes:
    source = BytesIO(payload)
    target = BytesIO()
    with ZipFile(source, "r") as archive, ZipFile(
        target, "w", compression=ZIP_DEFLATED, compresslevel=9
    ) as normalized:
        for name in sorted(archive.namelist()):
            original = archive.getinfo(name)
            info = ZipInfo(name, date_time=(1980, 1, 1, 0, 0, 0))
            info.compress_type = ZIP_DEFLATED
            info.external_attr = original.external_attr
            info.create_system = 0
            normalized.writestr(info, archive.read(name))
    return target.getvalue()


class DocxGenerator(Generator):
    """Encode rendered artifacts as deterministic Office Open XML."""

    name = "docx"
    output_format = OutputFormat.DOCX
    mime_type = (
        "application/vnd.openxmlformats-officedocument."
        "wordprocessingml.document"
    )
    file_extension = ".docx"

    def _encode(
        self,
        artifact: RenderedArtifact,
        output: DocumentOutput,
        *,
        template: Template | None,
        context: RenderingContext | None,
        asset_root: Path,
    ) -> bytes:
        try:
            from docx import Document
            from docx.enum.text import WD_ALIGN_PARAGRAPH
        except ImportError as error:
            raise MissingResourceError(
                "DOCX generation requires python-docx"
            ) from error

        document = Document()
        apply_document_styles(document, template, context)
        document.core_properties.author = "TEOS"
        document.core_properties.title = output.title
        document.core_properties.subject = artifact.template_identifier
        document.core_properties.created = artifact.generation_timestamp
        document.core_properties.modified = artifact.generation_timestamp

        logo = self.logo_asset(context)
        formatting = template.formatting if template is not None else None
        logo_position = (
            formatting.branding.logo_position
            if formatting is not None
            else "header"
        )
        if logo is not None:
            if logo.content_type not in {
                "image/png",
                "image/jpeg",
                "image/gif",
                "image/bmp",
                "image/tiff",
            }:
                raise AssetEmbeddingError(
                    f"unsupported DOCX image type: {logo.content_type}"
                )
            try:
                if logo_position == "footer":
                    paragraph = document.sections[0].footer.paragraphs[0]
                elif logo_position == "cover":
                    paragraph = document.add_paragraph()
                elif logo_position == "none":
                    paragraph = None
                else:
                    paragraph = document.sections[0].header.paragraphs[0]
                if paragraph is None:
                    payload = None
                else:
                    payload = self.load_asset(logo, asset_root)
                if payload is not None:
                    add_image(paragraph, payload)
            except Exception as error:
                if isinstance(error, AssetEmbeddingError):
                    raise
                raise AssetEmbeddingError(
                    f"cannot embed DOCX asset: {logo.identifier}"
                ) from error

        document.add_heading(output.title, level=0)
        document.add_paragraph(output.subtitle, style="Subtitle")
        table_style = formatting.tables if formatting is not None else None
        alternating = table_style.alternating_rows if table_style else False
        repeat_header = table_style.repeat_header if table_style else True
        for index, section in enumerate(output.sections):
            if index:
                document.add_section()
            document.add_heading(section.heading, level=1)
            for paragraph in section.paragraphs:
                document.add_paragraph(paragraph)
            for item in section.items:
                add_list_item(document, item)
            for table in section.tables:
                add_table(
                    document,
                    table,
                    alternating_rows=alternating,
                    repeat_header=repeat_header,
                )

        header_footer = (
            formatting.headers_and_footers if formatting is not None else None
        )
        for section in document.sections:
            if (
                (header_footer is None or header_footer.show_header)
                and context is not None
                and context.branding is not None
            ):
                header = section.header.paragraphs[0]
                if not header.text:
                    header.text = context.branding.institution_name
            if header_footer is None or header_footer.show_footer:
                footer = section.footer.paragraphs[0]
                footer.alignment = WD_ALIGN_PARAGRAPH.CENTER
                footer.add_run("TEOS")
                if header_footer is None or header_footer.show_page_number:
                    footer.add_run(" · ")
                    add_page_number(footer)

        buffer = BytesIO()
        document.save(buffer)
        return _normalized_package(buffer.getvalue())
