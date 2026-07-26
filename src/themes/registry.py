"""Immutable registration and cross-reference validation for themes."""

from __future__ import annotations

from types import MappingProxyType
from typing import Iterable, Mapping

from .assets import ThemeAssets
from .contracts import ThemeLayer
from .exceptions import (
    AssetError,
    BrandingError,
    LayoutError,
    StyleResolutionError,
    TemplateError,
    ThemeRegistrationError,
)
from .layout import ThemeLayout
from .styles import ThemeStyles
from .templates import ThemeTemplates
from .theme import Theme


class ThemeRegistry:
    """Register themes and expose deterministic immutable snapshots."""

    __slots__ = ("_themes",)

    def __init__(self, themes: Iterable[Theme] = ()) -> None:
        registered: dict[str, Theme] = {}
        for theme in themes:
            identifier = theme.metadata.theme_id
            if identifier in registered:
                raise ThemeRegistrationError(
                    f"duplicate theme identifier: {identifier!r}"
                )
            registered[identifier] = theme
        self._themes = MappingProxyType(dict(sorted(registered.items())))
        self.validate()

    def get(self, theme_id: str) -> Theme | None:
        """Return an exact registered theme."""
        return self._themes.get(theme_id)

    def require(self, theme_id: str) -> Theme:
        """Return an exact registered theme or raise a typed error."""
        selected = self.get(theme_id)
        if selected is None:
            raise ThemeRegistrationError(f"unknown theme: {theme_id!r}")
        return selected

    def ancestry(self, theme_id: str) -> tuple[Theme, ...]:
        """Return a theme followed by its parents, rejecting broken chains."""
        chain: list[Theme] = []
        seen: set[str] = set()
        current = theme_id
        while True:
            if current in seen:
                raise ThemeRegistrationError(
                    "theme inheritance cycle: "
                    + " -> ".join((*[item.name for item in chain], current))
                )
            seen.add(current)
            theme = self.get(current)
            if theme is None:
                raise ThemeRegistrationError(
                    f"missing parent theme reference: {current!r}"
                )
            chain.append(theme)
            if theme.extends is None:
                return tuple(chain)
            current = theme.extends

    def validate(
        self, *, required_template_kinds: Iterable[str] = ()
    ) -> None:
        """Validate compatibility, references, and optional template coverage."""
        required = tuple(sorted(set(required_template_kinds)))
        for theme in self._themes.values():
            theme.metadata.require_compatible()
            ancestry = self.ancestry(theme.name)
            assets = self._effective_assets(ancestry)
            styles = self._effective_styles(ancestry)
            layouts = self._effective_layouts(ancestry)
            templates = self._effective_templates(ancestry)
            styles.validate()
            if theme.metadata.layer is not ThemeLayer.BUILTIN:
                for artifact_kind in required:
                    if not any(
                        item.artifact_kind == artifact_kind
                        for item in templates.items
                    ):
                        raise TemplateError(
                            f"theme {theme.name!r} is missing required template "
                            f"for artifact {artifact_kind!r}"
                        )
            for label, asset_id in theme.branding.asset_references():
                if assets.get(asset_id) is None:
                    raise BrandingError(
                        f"theme {theme.name!r} {label} references missing "
                        f"asset {asset_id!r}"
                    )
            for layout in layouts.items:
                for style_name in layout.style_refs:
                    if styles.get(style_name) is None:
                        raise LayoutError(
                            f"layout {layout.layout_id!r} references missing "
                            f"style {style_name!r}"
                        )
            for template in templates.items:
                if (
                    template.layout_ref is not None
                    and layouts.get(template.layout_ref) is None
                ):
                    raise TemplateError(
                        f"template {template.template_id!r} references missing "
                        f"layout {template.layout_ref!r}"
                    )
                for style_name in template.style_refs:
                    if styles.get(style_name) is None:
                        raise StyleResolutionError(
                            f"template {template.template_id!r} references "
                            f"missing style {style_name!r}"
                        )
                for asset_id in template.required_assets:
                    if assets.get(asset_id) is None:
                        raise AssetError(
                            f"template {template.template_id!r} references "
                            f"missing asset {asset_id!r}"
                        )

    def snapshot(self) -> Mapping[str, Theme]:
        """Return the immutable theme registration mapping."""
        return self._themes

    def __iter__(self):
        """Iterate themes in deterministic identifier order."""
        return iter(self._themes.values())

    def __len__(self) -> int:
        """Return the number of registered themes."""
        return len(self._themes)

    @staticmethod
    def _merged_items(
        ancestry: tuple[Theme, ...], attribute: str, key: str
    ) -> tuple[object, ...]:
        merged: dict[str, object] = {}
        for theme in reversed(ancestry):
            collection = getattr(theme, attribute)
            for item in collection.items:
                merged[getattr(item, key)] = item
        return tuple(merged[name] for name in sorted(merged))

    @classmethod
    def _effective_assets(cls, ancestry: tuple[Theme, ...]) -> ThemeAssets:
        return ThemeAssets(cls._merged_items(ancestry, "assets", "asset_id"))

    @classmethod
    def _effective_styles(cls, ancestry: tuple[Theme, ...]) -> ThemeStyles:
        return ThemeStyles(cls._merged_items(ancestry, "styles", "name"))

    @classmethod
    def _effective_layouts(cls, ancestry: tuple[Theme, ...]) -> ThemeLayout:
        return ThemeLayout(cls._merged_items(ancestry, "layout", "layout_id"))

    @classmethod
    def _effective_templates(cls, ancestry: tuple[Theme, ...]) -> ThemeTemplates:
        return ThemeTemplates(
            cls._merged_items(ancestry, "templates", "template_id")
        )
