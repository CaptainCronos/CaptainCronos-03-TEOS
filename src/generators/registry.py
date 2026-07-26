"""Exact output-format registry for document generators."""

from src.models.lifecycle import OutputFormat

from .exceptions import UnsupportedGeneratorError
from .generator import Generator


class GeneratorRegistry:
    """Register and resolve one generator per canonical output format."""

    def __init__(self, generators: tuple[Generator, ...] = ()) -> None:
        """Initialize the registry in deterministic registration order."""
        self._generators: dict[OutputFormat, Generator] = {}
        for generator in generators:
            self.register(generator)

    @classmethod
    def with_defaults(cls) -> "GeneratorRegistry":
        """Return a registry containing all supported document generators."""
        from .docx import DocxGenerator
        from .html import HtmlGenerator
        from .markdown import MarkdownGenerator
        from .pdf import PdfGenerator

        return cls(
            (
                DocxGenerator(),
                PdfGenerator(),
                HtmlGenerator(),
                MarkdownGenerator(),
            )
        )

    def register(self, generator: Generator) -> None:
        """Register a generator without replacing an existing format."""
        if not isinstance(generator, Generator):
            raise UnsupportedGeneratorError("registry requires a Generator")
        if generator.output_format in self._generators:
            raise UnsupportedGeneratorError(
                f"generator already registered for {generator.output_format.value}"
            )
        self._generators[generator.output_format] = generator

    def select(self, output_format: OutputFormat | str) -> Generator:
        """Resolve a canonical output format."""
        try:
            canonical = OutputFormat(output_format)
            return self._generators[canonical]
        except (ValueError, KeyError) as error:
            raise UnsupportedGeneratorError(
                f"unsupported generator: {output_format}"
            ) from error

    def __iter__(self):
        """Iterate generators in registration order."""
        return iter(self._generators.values())
