"""Deterministic, responsive, self-contained HTML generation."""

from __future__ import annotations

import base64
from html import escape
from pathlib import Path

from src.models.lifecycle import OutputFormat
from src.rendering import RenderedArtifact, RenderingContext, Template

from ..generator import Generator
from ..output import DocumentOutput


class HtmlGenerator(Generator):
    """Encode rendered artifacts as semantic standalone HTML."""

    name = "html"
    output_format = OutputFormat.HTML
    mime_type = "text/html; charset=utf-8"
    file_extension = ".html"

    def _encode(
        self,
        artifact: RenderedArtifact,
        output: DocumentOutput,
        *,
        template: Template | None,
        context: RenderingContext | None,
        asset_root: Path,
    ) -> bytes:
        colors = dict(context.theme.colors) if context is not None else {}
        primary = colors.get("primary", "#17324d")
        accent = colors.get("accent", "#2f6f9f")
        nav = "".join(
            f'<li><a href="#section-{index}">{escape(section.heading)}</a></li>'
            for index, section in enumerate(output.sections, 1)
        )
        logo = self.logo_asset(context)
        logo_html = ""
        if logo is not None:
            payload = base64.b64encode(
                self.load_asset(logo, asset_root)
            ).decode("ascii")
            logo_html = (
                f'<img class="brand-logo" alt="{escape(logo.description or "Logo")}" '
                f'src="data:{escape(logo.content_type)};base64,{payload}">'
            )
        body = "".join(
            self._section_html(index, section)
            for index, section in enumerate(output.sections, 1)
        )
        css = (
            ":root{--primary:"
            + primary
            + ";--accent:"
            + accent
            + ";font-family:system-ui,sans-serif;color:#17202a}"
            "body{margin:0;background:#f5f7f9}header,main,nav{max-width:72rem;"
            "margin:auto;padding:1rem}header{background:var(--primary);color:white}"
            ".brand-logo{max-height:4rem;max-width:14rem}nav ul{display:flex;"
            "flex-wrap:wrap;gap:1rem;list-style:none;padding:0}a{color:var(--accent)}"
            "section{background:white;margin:1rem 0;padding:1rem;border-radius:.25rem;"
            "overflow-x:auto}table{border-collapse:collapse;width:100%}th,td{border:"
            "1px solid #ccd3da;padding:.5rem;text-align:left}th{background:#e8eef3}"
            "@media(max-width:40rem){th,td{font-size:.875rem;padding:.35rem}}"
        )
        document = (
            "<!doctype html>\n"
            f'<html lang="'
            f'{escape(context.localization.language if context else "en")}">\n'
            "<head>\n<meta charset=\"utf-8\">\n"
            '<meta name="viewport" content="width=device-width,initial-scale=1">\n'
            f"<title>{escape(output.title)}</title>\n<style>{css}</style>\n</head>\n"
            f"<body>\n<header>{logo_html}<h1>{escape(output.title)}</h1>"
            f"<p>{escape(output.subtitle)}</p></header>\n"
            f"<nav aria-label=\"Document\"><ul>{nav}</ul></nav>\n"
            f"<main>{body}</main>\n</body>\n</html>\n"
        )
        return document.encode("utf-8")

    @staticmethod
    def _section_html(index, section) -> str:
        paragraphs = "".join(f"<p>{escape(value)}</p>" for value in section.paragraphs)
        items = (
            "<ul>"
            + "".join(f"<li>{escape(value)}</li>" for value in section.items)
            + "</ul>"
            if section.items
            else ""
        )
        tables = ""
        for table in section.tables:
            header = "".join(
                f'<th scope="col">{escape(value)}</th>'
                for value in table.headers
            )
            rows = "".join(
                "<tr>" + "".join(f"<td>{escape(value)}</td>" for value in row) + "</tr>"
                for row in table.rows
            )
            tables += (
                f"<table><thead><tr>{header}</tr></thead>"
                f"<tbody>{rows}</tbody></table>"
            )
        return (
            f'<section id="section-{index}"><h2>{escape(section.heading)}</h2>'
            f"{paragraphs}{items}{tables}</section>"
        )
