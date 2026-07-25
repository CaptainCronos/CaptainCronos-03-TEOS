"""Renderer registration and output-format selection."""

from __future__ import annotations

from src.models.lifecycle import OutputFormat

from .docx_renderer import DocxRenderer
from .exceptions import UnsupportedRendererError
from .html_renderer import HtmlRenderer
from .markdown_renderer import MarkdownRenderer
from .pdf_renderer import PdfRenderer
from .renderer import Renderer


class RendererRegistry:
    """Select independent renderer implementations by canonical format."""

    def __init__(self, renderers: tuple[Renderer, ...] = ()) -> None:
        """Initialize an ordered renderer registry."""
        self._renderers: dict[OutputFormat, Renderer] = {}
        for renderer in renderers:
            self.register(renderer)

    @classmethod
    def with_defaults(cls) -> RendererRegistry:
        """Return a registry containing the four framework renderers."""
        return cls(
            (
                DocxRenderer(),
                PdfRenderer(),
                HtmlRenderer(),
                MarkdownRenderer(),
            )
        )

    def register(self, renderer: Renderer) -> None:
        """Register one renderer without replacing an existing format."""
        if not isinstance(renderer, Renderer):
            raise UnsupportedRendererError(
                "registered renderer must implement Renderer"
            )
        if renderer.output_format in self._renderers:
            raise UnsupportedRendererError(
                f"renderer already registered for "
                f"{renderer.output_format.value}"
            )
        self._renderers[renderer.output_format] = renderer

    def select(self, output_format: OutputFormat | str) -> Renderer:
        """Return the renderer registered for a canonical output format."""
        try:
            canonical = OutputFormat(output_format)
        except (TypeError, ValueError) as error:
            raise UnsupportedRendererError(
                f"unsupported renderer: {output_format}"
            ) from error
        try:
            return self._renderers[canonical]
        except KeyError as error:
            raise UnsupportedRendererError(
                f"no renderer registered for {canonical.value}"
            ) from error

    def __iter__(self):
        """Iterate renderers in registration order."""
        return iter(self._renderers.values())
