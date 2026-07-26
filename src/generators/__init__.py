"""Physical document generation from immutable rendering artifacts."""

from .docx import DocxGenerator
from .exceptions import (
    AssetEmbeddingError,
    FileCreationError,
    GenerationError,
    MissingResourceError,
    OutputError,
    TemplateMismatchError,
    UnsupportedGeneratorError,
)
from .files import GeneratedDirectory, GeneratedFile, GeneratedPackage
from .generator import Generator
from .html import HtmlGenerator
from .markdown import MarkdownGenerator
from .metadata import GenerationMetadata
from .output import DocumentOutput, OutputSection, OutputTable
from .pdf import PdfGenerator
from .registry import GeneratorRegistry

__all__ = [
    "AssetEmbeddingError",
    "DocumentOutput",
    "DocxGenerator",
    "FileCreationError",
    "GeneratedDirectory",
    "GeneratedFile",
    "GeneratedPackage",
    "GenerationError",
    "GenerationMetadata",
    "Generator",
    "GeneratorRegistry",
    "HtmlGenerator",
    "MarkdownGenerator",
    "MissingResourceError",
    "OutputError",
    "OutputSection",
    "OutputTable",
    "PdfGenerator",
    "TemplateMismatchError",
    "UnsupportedGeneratorError",
]
