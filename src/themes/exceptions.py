"""Typed failures raised by the theme and branding framework."""


class ThemeError(Exception):
    """Base class for all theme-framework failures."""


class ThemeLoadError(ThemeError):
    """A theme package could not be decoded or constructed."""


class ThemeCompatibilityError(ThemeError):
    """A theme targets an unsupported theme contract version."""


class ThemeRegistrationError(ThemeError):
    """A theme cannot be added to an immutable registry snapshot."""


class ThemeResolutionError(ThemeError):
    """A requested effective theme cannot be resolved."""


class AssetError(ThemeError):
    """An asset declaration or reference is invalid."""


class StyleResolutionError(ThemeResolutionError):
    """A style reference or inheritance chain cannot be resolved."""


class LayoutError(ThemeError):
    """A page-layout declaration or reference is invalid."""


class BrandingError(ThemeError):
    """A branding declaration is invalid."""


class TemplateError(ThemeError):
    """A document-template declaration or selection is invalid."""
