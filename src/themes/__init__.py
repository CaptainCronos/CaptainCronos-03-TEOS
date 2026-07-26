"""Public immutable Theme and Branding Framework API."""

from .assets import ThemeAsset, ThemeAssets
from .branding import Branding, ContactInformation
from .colors import ThemePalette
from .contracts import (
    FRAMEWORK_VERSION,
    THEME_CONTRACT_VERSION,
    AssetKind,
    Orientation,
    ThemeLayer,
)
from .exceptions import (
    AssetError,
    BrandingError,
    LayoutError,
    StyleResolutionError,
    TemplateError,
    ThemeCompatibilityError,
    ThemeError,
    ThemeLoadError,
    ThemeRegistrationError,
    ThemeResolutionError,
)
from .layout import LayoutDefinition, PageMargins, ThemeLayout
from .loader import ThemeLoader
from .manager import ThemeManager
from .metadata import ThemeMetadata
from .registry import ThemeRegistry
from .resolver import ResolvedTheme, ThemeResolver
from .styles import StyleDefinition, ThemeStyles
from .templates import DocumentTemplate, ThemeTemplates
from .theme import BUILTIN_THEME, Theme
from .typography import FontFamily, TextStyle, ThemeTypography

__all__ = [
    "FRAMEWORK_VERSION",
    "THEME_CONTRACT_VERSION",
    "AssetError",
    "AssetKind",
    "Branding",
    "BrandingError",
    "BUILTIN_THEME",
    "ContactInformation",
    "DocumentTemplate",
    "FontFamily",
    "LayoutDefinition",
    "LayoutError",
    "Orientation",
    "PageMargins",
    "ResolvedTheme",
    "StyleDefinition",
    "StyleResolutionError",
    "TemplateError",
    "TextStyle",
    "Theme",
    "ThemeAsset",
    "ThemeAssets",
    "ThemeCompatibilityError",
    "ThemeError",
    "ThemeLayer",
    "ThemeLayout",
    "ThemeLoadError",
    "ThemeLoader",
    "ThemeManager",
    "ThemeMetadata",
    "ThemePalette",
    "ThemeRegistrationError",
    "ThemeRegistry",
    "ThemeResolutionError",
    "ThemeResolver",
    "ThemeStyles",
    "ThemeTemplates",
    "ThemeTypography",
]
