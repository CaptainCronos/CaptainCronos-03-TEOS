"""Side-effect-free presentation framework for scheduled TEOS repositories."""

from .assets import (
    Asset,
    AssetCatalog,
    AssetKind,
    AssetReference,
    AssetRequirement,
)
from .context import (
    InstitutionBranding,
    Localization,
    PageSettings,
    RenderingContext,
    RenderOptions,
    Theme,
)
from .docx_renderer import DocxRenderer
from .exceptions import (
    AssetError,
    FormattingError,
    MissingAssetError,
    MissingBrandingError,
    RenderingContextError,
    RenderingError,
    TemplateError,
    UnsupportedOutputError,
    UnsupportedRendererError,
    UnsupportedTemplateError,
)
from .formatting import (
    BrandingStyle,
    CaptionStyle,
    FormattingProfile,
    HeaderFooterStyle,
    ImageStyle,
    ListStyle,
    PageLayout,
    TableStyle,
    Typography,
)
from .html_renderer import HtmlRenderer
from .markdown_renderer import MarkdownRenderer
from .pdf_renderer import PdfRenderer
from .rendered_artifact import (
    RenderedArtifact,
    RenderedDocument,
    RenderedPackage,
    RenderedPackageEntry,
)
from .renderer import Renderer
from .registry import RendererRegistry
from .templates import Template, TemplateRegion, TemplateRegistry

__all__ = [
    "Asset",
    "AssetCatalog",
    "AssetError",
    "AssetKind",
    "AssetReference",
    "AssetRequirement",
    "BrandingStyle",
    "CaptionStyle",
    "DocxRenderer",
    "FormattingError",
    "FormattingProfile",
    "HeaderFooterStyle",
    "HtmlRenderer",
    "ImageStyle",
    "InstitutionBranding",
    "ListStyle",
    "Localization",
    "MarkdownRenderer",
    "MissingAssetError",
    "MissingBrandingError",
    "PageLayout",
    "PageSettings",
    "PdfRenderer",
    "RenderedArtifact",
    "RenderedDocument",
    "RenderedPackage",
    "RenderedPackageEntry",
    "Renderer",
    "RendererRegistry",
    "RenderingContext",
    "RenderingContextError",
    "RenderingError",
    "RenderOptions",
    "TableStyle",
    "Template",
    "TemplateError",
    "TemplateRegion",
    "TemplateRegistry",
    "Theme",
    "Typography",
    "UnsupportedOutputError",
    "UnsupportedRendererError",
    "UnsupportedTemplateError",
]
