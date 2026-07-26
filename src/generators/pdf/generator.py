"""PDF generation using ReportLab."""

from __future__ import annotations

from io import BytesIO
from pathlib import Path

from src.models.lifecycle import OutputFormat
from src.rendering import RenderedArtifact, RenderingContext, Template

from ..exceptions import AssetEmbeddingError, MissingResourceError
from ..generator import Generator
from ..output import DocumentOutput
from .fonts import font_names
from .layout import page_decorator, page_geometry


class PdfGenerator(Generator):
    """Encode rendered artifacts as deterministic paginated PDFs."""

    name = "pdf"
    output_format = OutputFormat.PDF
    mime_type = "application/pdf"
    file_extension = ".pdf"

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
            from reportlab.lib import colors
            from reportlab.lib.enums import TA_CENTER
            from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
            from reportlab.lib.units import inch
            from reportlab.pdfgen.canvas import Canvas
            from reportlab.platypus import (
                Image,
                KeepTogether,
                ListFlowable,
                ListItem,
                PageBreak,
                Paragraph,
                SimpleDocTemplate,
                Spacer,
                Table,
                TableStyle,
            )
        except ImportError as error:
            raise MissingResourceError(
                "PDF generation requires ReportLab"
            ) from error

        class InvariantCanvas(Canvas):
            def __init__(self, *args, **kwargs):
                kwargs["invariant"] = 1
                kwargs["pageCompression"] = 1
                super().__init__(*args, **kwargs)

        page_size, margins = page_geometry(context)
        left, right, top, bottom = margins
        buffer = BytesIO()
        document = SimpleDocTemplate(
            buffer,
            pagesize=page_size,
            leftMargin=left,
            rightMargin=right,
            topMargin=top,
            bottomMargin=bottom,
            title=output.title,
            author="TEOS",
            subject=artifact.template_identifier,
        )
        body_font, heading_font = font_names(template)
        styles = getSampleStyleSheet()
        styles["BodyText"].fontName = body_font
        styles["Title"].fontName = heading_font
        styles["Heading1"].fontName = heading_font
        subtitle_style = ParagraphStyle(
            "TEOSSubtitle",
            parent=styles["BodyText"],
            alignment=TA_CENTER,
            spaceAfter=12,
        )
        story = [
            Paragraph(output.title, styles["Title"]),
            Paragraph(output.subtitle, subtitle_style),
        ]
        logo = self.logo_asset(context)
        if logo is not None:
            if logo.content_type not in {
                "image/png",
                "image/jpeg",
                "image/gif",
                "image/bmp",
                "image/tiff",
            }:
                raise AssetEmbeddingError(
                    f"unsupported PDF image type: {logo.content_type}"
                )
            try:
                image = Image(BytesIO(self.load_asset(logo, asset_root)))
                image._restrictSize(2 * inch, 1 * inch)
                story.extend((image, Spacer(1, 8)))
            except Exception as error:
                if isinstance(error, AssetEmbeddingError):
                    raise
                raise AssetEmbeddingError(
                    f"cannot embed PDF asset: {logo.identifier}"
                ) from error

        for index, section in enumerate(output.sections):
            if index:
                story.append(PageBreak())
            content = [Paragraph(section.heading, styles["Heading1"])]
            content.extend(
                Paragraph(paragraph, styles["BodyText"])
                for paragraph in section.paragraphs
            )
            if section.items:
                content.append(
                    ListFlowable(
                        [
                            ListItem(Paragraph(item, styles["BodyText"]))
                            for item in section.items
                        ],
                        bulletType="bullet",
                    )
                )
            for table in section.tables:
                data = [list(table.headers), *map(list, table.rows)]
                flowable = Table(data, repeatRows=1, hAlign="LEFT")
                flowable.setStyle(
                    TableStyle(
                        (
                            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#E8EEF3")),
                            ("FONTNAME", (0, 0), (-1, 0), heading_font),
                            ("FONTNAME", (0, 1), (-1, -1), body_font),
                            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#9AA7B2")),
                            ("VALIGN", (0, 0), (-1, -1), "TOP"),
                            ("LEFTPADDING", (0, 0), (-1, -1), 5),
                            ("RIGHTPADDING", (0, 0), (-1, -1), 5),
                        )
                    )
                )
                content.extend((Spacer(1, 6), flowable))
            story.append(KeepTogether(content[:1]))
            story.extend(content[1:])

        institution = (
            context.branding.institution_name
            if context is not None and context.branding is not None
            else None
        )
        header_footer = (
            template.formatting.headers_and_footers
            if template is not None
            else None
        )
        decorate = page_decorator(
            output.title,
            institution,
            show_header=(
                header_footer.show_header if header_footer is not None else True
            ),
            show_footer=(
                header_footer.show_footer if header_footer is not None else True
            ),
            show_page_number=(
                header_footer.show_page_number
                if header_footer is not None
                else True
            ),
        )
        document.build(
            story,
            onFirstPage=decorate,
            onLaterPages=decorate,
            canvasmaker=InvariantCanvas,
        )
        return buffer.getvalue()
