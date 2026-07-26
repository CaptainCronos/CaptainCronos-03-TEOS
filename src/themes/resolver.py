"""Deterministic immutable theme, style, asset, layout, and template resolution."""

from __future__ import annotations

from dataclasses import dataclass, fields, replace

from .assets import ThemeAsset, ThemeAssets
from .branding import Branding, ContactInformation
from .colors import ThemePalette
from .contracts import ThemeLayer
from .exceptions import ThemeResolutionError
from .layout import LayoutDefinition, ThemeLayout
from .metadata import ThemeMetadata
from .registry import ThemeRegistry
from .styles import StyleDefinition, ThemeStyles
from .templates import DocumentTemplate, ThemeTemplates
from .theme import Theme
from .typography import FontFamily, TextStyle, ThemeTypography


@dataclass(frozen=True, slots=True)
class ResolvedTheme:
    """A fully merged immutable presentation-resource snapshot."""

    theme_id: str
    source_theme_ids: tuple[str, ...]
    branding: Branding
    typography: ThemeTypography
    palette: ThemePalette
    layout: ThemeLayout
    assets: ThemeAssets
    styles: ThemeStyles
    templates: ThemeTemplates

    def asset(self, asset_id: str) -> ThemeAsset:
        """Resolve one required asset."""
        return self.assets.require(asset_id)

    def style(self, name: str):
        """Resolve one style's inherited immutable properties."""
        return self.styles.resolve(name)

    def template(
        self, artifact_kind: str, output_format: str | None = None
    ) -> DocumentTemplate:
        """Select a template deterministically."""
        return self.templates.select(artifact_kind, output_format)

    def layouts_for(self, artifact_kind: str) -> tuple[LayoutDefinition, ...]:
        """Return layouts matching an artifact kind."""
        return self.layout.for_artifact(artifact_kind)


class ThemeResolver:
    """Resolve configured themes using fixed presentation precedence."""

    __slots__ = ("registry", "default_theme_id", "builtin_theme_id")

    def __init__(
        self,
        registry: ThemeRegistry,
        *,
        default_theme_id: str = "teos.builtin",
        builtin_theme_id: str = "teos.builtin",
    ) -> None:
        self.registry = registry
        self.default_theme_id = default_theme_id
        self.builtin_theme_id = builtin_theme_id
        self.registry.require(default_theme_id)
        builtin = self.registry.require(builtin_theme_id)
        if builtin.metadata.layer is not ThemeLayer.BUILTIN:
            raise ThemeResolutionError(
                f"built-in theme {builtin_theme_id!r} must use built-in layer"
            )

    def resolve(
        self,
        theme_id: str | None = None,
        *,
        institution_override: str | Theme | None = None,
    ) -> ResolvedTheme:
        """Resolve institution, selected, default, and built-in resources."""
        selected_id = theme_id or self.default_theme_id
        selected = self.registry.require(selected_id)
        override = self._override(institution_override)
        layers: list[Theme] = []
        layers.extend(reversed(self.registry.ancestry(self.builtin_theme_id)))
        layers.extend(reversed(self.registry.ancestry(self.default_theme_id)))
        layers.extend(reversed(self.registry.ancestry(selected.name)))
        if override is not None:
            if override.metadata.layer is not ThemeLayer.INSTITUTION:
                raise ThemeResolutionError(
                    "institution override must use institution layer"
                )
            if override.extends is not None:
                layers.extend(reversed(self.registry.ancestry(override.extends)))
            layers.append(override)
        ordered = self._deduplicate(layers)
        result = self._merge(selected_id, ordered)
        ThemeRegistry(
            (
                Theme(
                    ThemeMetadata(
                        "teos.resolved.validation",
                        "1.0.0",
                        ThemeLayer.THEME,
                    ),
                    branding=result.branding,
                    typography=result.typography,
                    palette=result.palette,
                    layout=result.layout,
                    assets=result.assets,
                    styles=result.styles,
                    templates=result.templates,
                ),
            )
        )
        return result

    def _override(self, value: str | Theme | None) -> Theme | None:
        if value is None:
            return None
        return self.registry.require(value) if isinstance(value, str) else value

    @staticmethod
    def _deduplicate(values: list[Theme]) -> tuple[Theme, ...]:
        result: dict[str, Theme] = {}
        for theme in values:
            result.pop(theme.name, None)
            result[theme.name] = theme
        return tuple(result.values())

    @staticmethod
    def _merge(theme_id: str, themes: tuple[Theme, ...]) -> ResolvedTheme:
        assets: dict[str, ThemeAsset] = {}
        styles: dict[str, StyleDefinition] = {}
        layouts: dict[str, LayoutDefinition] = {}
        templates: dict[str, DocumentTemplate] = {}
        families: dict[str, FontFamily] = {}
        headings: dict[str, TextStyle] = {}
        branding = Branding()
        typography = ThemeTypography()
        palette = ThemePalette()
        print_safe: dict[str, str] = {}
        high_contrast: dict[str, str] = {}
        for theme in themes:
            assets.update({item.asset_id: item for item in theme.assets.items})
            styles.update({item.name: item for item in theme.styles.items})
            layouts.update({item.layout_id: item for item in theme.layout.items})
            templates.update(
                {item.template_id: item for item in theme.templates.items}
            )
            branding = ThemeResolver._merge_branding(branding, theme.branding)
            families.update(dict(theme.typography.families))
            headings.update(dict(theme.typography.headings))
            typography = replace(
                theme.typography,
                families=tuple(families.items()),
                headings=tuple(headings.items()),
                body=theme.typography.body or typography.body,
                caption=theme.typography.caption or typography.caption,
                code=theme.typography.code or typography.code,
                table=theme.typography.table or typography.table,
            )
            print_safe.update(dict(theme.palette.print_safe))
            high_contrast.update(dict(theme.palette.high_contrast))
            palette = ThemePalette(
                *(
                    getattr(theme.palette, name) or getattr(palette, name)
                    for name in (
                        "primary", "secondary", "accent", "warning", "success",
                        "error", "neutral",
                    )
                ),
                tuple(print_safe.items()),
                tuple(high_contrast.items()),
            )
        return ResolvedTheme(
            theme_id,
            tuple(theme.name for theme in reversed(themes)),
            branding,
            typography,
            palette,
            ThemeLayout(tuple(layouts.values())),
            ThemeAssets(tuple(assets.values())),
            ThemeStyles(tuple(styles.values())),
            ThemeTemplates(tuple(templates.values())),
        )

    @staticmethod
    def _merge_branding(lower: Branding, higher: Branding) -> Branding:
        contact = ContactInformation(
            **{
                field.name: getattr(higher.contact, field.name)
                or getattr(lower.contact, field.name)
                for field in fields(ContactInformation)
            }
        )
        return Branding(
            **{
                field.name: (
                    contact
                    if field.name == "contact"
                    else getattr(higher, field.name) or getattr(lower, field.name)
                )
                for field in fields(Branding)
            }
        )
