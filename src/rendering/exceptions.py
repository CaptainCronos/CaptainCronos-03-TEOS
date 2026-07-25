"""Rendering-layer exception hierarchy."""


class RenderingError(Exception):
    """Base class for presentation request failures."""


class RenderingContextError(RenderingError):
    """Raised when required presentation context is absent or invalid."""


class MissingBrandingError(RenderingContextError):
    """Raised when a template requires institution branding."""


class UnsupportedRendererError(RenderingError):
    """Raised when no renderer is registered for an output format."""


class UnsupportedOutputError(RenderingError):
    """Raised when a renderer cannot satisfy an output request."""


class TemplateError(RenderingError):
    """Base class for missing or incompatible templates."""


class UnsupportedTemplateError(TemplateError):
    """Raised when a template does not support a renderer."""


class AssetError(RenderingError):
    """Base class for asset declaration and resolution failures."""


class MissingAssetError(AssetError):
    """Raised when a referenced required asset cannot be resolved."""


class FormattingError(RenderingError):
    """Raised when presentation formatting is invalid."""
