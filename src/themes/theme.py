"""Immutable aggregate theme definitions and the built-in safety theme."""

from __future__ import annotations

from dataclasses import dataclass

from .assets import ThemeAssets
from .branding import Branding
from .colors import ThemePalette
from .contracts import ThemeLayer, require_identifier
from .layout import ThemeLayout
from .metadata import ThemeMetadata
from .styles import ThemeStyles
from .templates import ThemeTemplates
from .typography import FontFamily, TextStyle, ThemeTypography


@dataclass(frozen=True, slots=True)
class Theme:
    """One versioned immutable collection of presentation resources."""

    metadata: ThemeMetadata
    extends: str | None = None
    branding: Branding = Branding()
    typography: ThemeTypography = ThemeTypography()
    palette: ThemePalette = ThemePalette()
    layout: ThemeLayout = ThemeLayout()
    assets: ThemeAssets = ThemeAssets()
    styles: ThemeStyles = ThemeStyles()
    templates: ThemeTemplates = ThemeTemplates()

    @property
    def name(self) -> str:
        """Return the stable name consumed by the plugin registry."""
        return self.metadata.theme_id

    def __post_init__(self) -> None:
        self.metadata.require_compatible()
        if self.extends is not None:
            require_identifier(self.extends, label="parent theme identifier")
            if self.extends == self.metadata.theme_id:
                raise ValueError("a theme cannot extend itself")


BUILTIN_THEME = Theme(
    ThemeMetadata(
        "teos.builtin",
        "1.0.0",
        ThemeLayer.BUILTIN,
        description="Minimal built-in presentation safety fallback",
    ),
    typography=ThemeTypography(
        families=(
            ("body", FontFamily("sans-serif", ("Arial", "Helvetica"))),
            ("mono", FontFamily("monospace", ("Courier New",))),
        ),
        body=TextStyle("body", 11.0, line_spacing=1.15, paragraph_after_pt=6.0),
        headings=(
            ("h1", TextStyle("body", 20.0, 700, paragraph_after_pt=10.0)),
            ("h2", TextStyle("body", 16.0, 700, paragraph_after_pt=8.0)),
        ),
        caption=TextStyle("body", 9.0, italic=True),
        code=TextStyle("mono", 10.0),
        table=TextStyle("body", 10.0),
    ),
    palette=ThemePalette(
        "#1F2937",
        "#4B5563",
        "#2563EB",
        "#D97706",
        "#15803D",
        "#B91C1C",
        "#F3F4F6",
    ),
)
