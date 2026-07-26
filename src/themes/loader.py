"""Strict JSON and YAML loading for immutable theme packages."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping

import yaml

from .assets import ThemeAsset, ThemeAssets
from .branding import Branding, ContactInformation
from .colors import ThemePalette
from .contracts import AssetKind, Orientation, ThemeLayer
from .exceptions import ThemeLoadError
from .layout import LayoutDefinition, PageMargins, ThemeLayout
from .metadata import ThemeMetadata
from .styles import StyleDefinition, ThemeStyles
from .templates import DocumentTemplate, ThemeTemplates
from .theme import Theme
from .typography import FontFamily, TextStyle, ThemeTypography


class _UniqueKeyLoader(yaml.SafeLoader):
    """YAML loader that rejects duplicate mapping keys."""


def _construct_mapping(
    loader: _UniqueKeyLoader, node: yaml.MappingNode, deep: bool = False
) -> dict[Any, Any]:
    values: dict[Any, Any] = {}
    for key_node, value_node in node.value:
        key = loader.construct_object(key_node, deep=deep)
        if key in values:
            raise ThemeLoadError(f"duplicate theme key: {key!r}")
        values[key] = loader.construct_object(value_node, deep=deep)
    return values


_UniqueKeyLoader.add_constructor(
    yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, _construct_mapping
)


class ThemeLoader:
    """Decode and validate one local JSON or YAML theme package."""

    _TOP_LEVEL = {
        "theme_id", "version", "contract_version", "layer", "description",
        "extends", "branding", "typography", "palette", "assets", "styles",
        "layouts", "templates",
    }

    def load(self, source: str | Path) -> Theme:
        """Load one UTF-8 theme file without reading referenced assets."""
        path = Path(source)
        try:
            content = path.read_text(encoding="utf-8")
        except OSError as error:
            raise ThemeLoadError(f"cannot read theme package {path}") from error
        try:
            if path.suffix.lower() == ".json":
                document = json.loads(
                    content, object_pairs_hook=self._unique_json_mapping
                )
            elif path.suffix.lower() in {".yaml", ".yml"}:
                document = yaml.load(content, Loader=_UniqueKeyLoader)
            else:
                raise ThemeLoadError(
                    f"unsupported theme package format: {path.suffix.lower()!r}"
                )
        except ThemeLoadError:
            raise
        except (json.JSONDecodeError, yaml.YAMLError) as error:
            raise ThemeLoadError(f"invalid theme package syntax in {path}") from error
        try:
            return self.from_mapping(self._mapping(document, "theme"))
        except ThemeLoadError:
            raise
        except (KeyError, TypeError, ValueError) as error:
            raise ThemeLoadError(f"invalid theme package {path}: {error}") from error

    def from_mapping(self, document: Mapping[str, Any]) -> Theme:
        """Construct a theme from an already decoded strict mapping."""
        self._only(document, self._TOP_LEVEL, "theme")
        layer_name = str(document.get("layer", "theme")).upper()
        try:
            layer = ThemeLayer[layer_name]
        except KeyError as error:
            raise ThemeLoadError(f"unsupported theme layer: {layer_name!r}") from error
        return Theme(
            ThemeMetadata(
                self._string(document, "theme_id"),
                self._string(document, "version"),
                layer,
                str(document.get("contract_version", "1.0")),
                str(document.get("description", "")),
            ),
            str(document["extends"]) if "extends" in document else None,
            self._branding(self._mapping(document.get("branding", {}), "branding")),
            self._typography(
                self._mapping(document.get("typography", {}), "typography")
            ),
            self._palette(self._mapping(document.get("palette", {}), "palette")),
            self._layouts(self._sequence(document.get("layouts", []), "layouts")),
            self._assets(self._sequence(document.get("assets", []), "assets")),
            self._styles(self._mapping(document.get("styles", {}), "styles")),
            self._templates(
                self._sequence(document.get("templates", []), "templates")
            ),
        )

    def _branding(self, value: Mapping[str, Any]) -> Branding:
        allowed = {
            "institution_name", "department_name", "logo", "department_logo",
            "seal", "watermark", "cover_page", "header", "footer",
            "revision_block", "contact",
        }
        self._only(value, allowed, "branding")
        contact = self._mapping(value.get("contact", {}), "branding.contact")
        self._only(
            contact,
            {"organization", "department", "address", "phone", "email", "website"},
            "branding.contact",
        )
        return Branding(
            **{
                name: str(value[name]) if name in value else ""
                for name in ("institution_name", "department_name")
            },
            **{
                name: str(value[name]) if name in value else None
                for name in (
                    "logo", "department_logo", "seal", "watermark", "cover_page",
                    "header", "footer", "revision_block",
                )
            },
            contact=ContactInformation(
                **{
                    name: str(contact.get(name, ""))
                    for name in (
                        "organization", "department", "address", "phone", "email",
                        "website",
                    )
                }
            ),
        )

    def _typography(self, value: Mapping[str, Any]) -> ThemeTypography:
        self._only(
            value,
            {"families", "body", "headings", "caption", "code", "table"},
            "typography",
        )
        families: list[tuple[str, FontFamily]] = []
        for name, raw in self._mapping(
            value.get("families", {}), "typography.families"
        ).items():
            family = self._mapping(raw, f"font family {name}")
            self._only(family, {"name", "fallbacks"}, f"font family {name}")
            families.append(
                (
                    str(name),
                    FontFamily(
                        self._string(family, "name"),
                        tuple(
                            str(item)
                            for item in self._sequence(
                                family.get("fallbacks", []), "font fallbacks"
                            )
                        ),
                    ),
                )
            )
        headings = tuple(
            (str(name), self._text_style(self._mapping(raw, f"heading {name}")))
            for name, raw in self._mapping(
                value.get("headings", {}), "typography.headings"
            ).items()
        )
        return ThemeTypography(
            tuple(families),
            self._optional_text_style(value, "body"),
            headings,
            self._optional_text_style(value, "caption"),
            self._optional_text_style(value, "code"),
            self._optional_text_style(value, "table"),
        )

    def _optional_text_style(
        self, value: Mapping[str, Any], key: str
    ) -> TextStyle | None:
        if key not in value:
            return None
        return self._text_style(self._mapping(value[key], f"typography.{key}"))

    def _text_style(self, value: Mapping[str, Any]) -> TextStyle:
        allowed = {
            "family", "size_pt", "weight", "italic", "color", "line_spacing",
            "paragraph_before_pt", "paragraph_after_pt",
        }
        self._only(value, allowed, "text style")
        return TextStyle(
            self._string(value, "family"),
            float(value["size_pt"]),
            int(value.get("weight", 400)),
            bool(value.get("italic", False)),
            str(value["color"]) if "color" in value else None,
            float(value["line_spacing"]) if "line_spacing" in value else None,
            float(value.get("paragraph_before_pt", 0)),
            float(value.get("paragraph_after_pt", 0)),
        )

    def _palette(self, value: Mapping[str, Any]) -> ThemePalette:
        allowed = {
            "primary", "secondary", "accent", "warning", "success", "error",
            "neutral", "print_safe", "high_contrast",
        }
        self._only(value, allowed, "palette")
        return ThemePalette(
            *(str(value[name]) if name in value else None for name in (
                "primary", "secondary", "accent", "warning", "success", "error",
                "neutral",
            )),
            tuple(
                (str(key), str(color))
                for key, color in self._mapping(
                    value.get("print_safe", {}), "palette.print_safe"
                ).items()
            ),
            tuple(
                (str(key), str(color))
                for key, color in self._mapping(
                    value.get("high_contrast", {}), "palette.high_contrast"
                ).items()
            ),
        )

    def _assets(self, values: tuple[Any, ...]) -> ThemeAssets:
        items: list[ThemeAsset] = []
        for raw in values:
            item = self._mapping(raw, "asset")
            self._only(
                item, {"id", "kind", "uri", "media_type", "description"}, "asset"
            )
            items.append(
                ThemeAsset(
                    self._string(item, "id"),
                    AssetKind(self._string(item, "kind")),
                    self._string(item, "uri"),
                    str(item.get("media_type", "")),
                    str(item.get("description", "")),
                )
            )
        return ThemeAssets(tuple(items))

    def _styles(self, values: Mapping[str, Any]) -> ThemeStyles:
        items: list[StyleDefinition] = []
        for name, raw in values.items():
            item = self._mapping(raw, f"style {name}")
            self._only(item, {"extends", "properties"}, f"style {name}")
            items.append(
                StyleDefinition(
                    str(name),
                    self._mapping(item.get("properties", {}), "style properties"),
                    str(item["extends"]) if "extends" in item else None,
                )
            )
        return ThemeStyles(tuple(items))

    def _layouts(self, values: tuple[Any, ...]) -> ThemeLayout:
        items: list[LayoutDefinition] = []
        for raw in values:
            item = self._mapping(raw, "layout")
            self._only(
                item,
                {
                    "id", "artifact_kind", "page_size", "orientation", "margins",
                    "regions", "style_refs",
                },
                "layout",
            )
            margins = self._mapping(item.get("margins", {}), "layout.margins")
            self._only(margins, {"top", "right", "bottom", "left"}, "margins")
            items.append(
                LayoutDefinition(
                    self._string(item, "id"),
                    self._string(item, "artifact_kind"),
                    str(item.get("page_size", "letter")),
                    Orientation(str(item.get("orientation", "portrait"))),
                    PageMargins(
                        *(float(margins.get(name, 72)) for name in (
                            "top", "right", "bottom", "left"
                        ))
                    ),
                    tuple(
                        str(entry)
                        for entry in self._sequence(
                            item.get("regions", []), "regions"
                        )
                    ),
                    tuple(
                        str(entry)
                        for entry in self._sequence(
                            item.get("style_refs", []), "style_refs"
                        )
                    ),
                )
            )
        return ThemeLayout(tuple(items))

    def _templates(self, values: tuple[Any, ...]) -> ThemeTemplates:
        items: list[DocumentTemplate] = []
        for raw in values:
            item = self._mapping(raw, "template")
            self._only(
                item,
                {
                    "id", "artifact_kind", "uri", "output_format", "layout_ref",
                    "style_refs", "required_assets",
                },
                "template",
            )
            items.append(
                DocumentTemplate(
                    self._string(item, "id"),
                    self._string(item, "artifact_kind"),
                    self._string(item, "uri"),
                    str(item["output_format"]) if "output_format" in item else None,
                    str(item["layout_ref"]) if "layout_ref" in item else None,
                    tuple(
                        str(entry)
                        for entry in self._sequence(
                            item.get("style_refs", []), "style_refs"
                        )
                    ),
                    tuple(
                        str(entry)
                        for entry in self._sequence(
                            item.get("required_assets", []),
                            "required_assets",
                        )
                    ),
                )
            )
        return ThemeTemplates(tuple(items))

    @staticmethod
    def _unique_json_mapping(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
        values: dict[str, Any] = {}
        for key, value in pairs:
            if key in values:
                raise ThemeLoadError(f"duplicate theme key: {key!r}")
            values[key] = value
        return values

    @staticmethod
    def _mapping(value: Any, name: str) -> Mapping[str, Any]:
        if not isinstance(value, Mapping):
            raise ThemeLoadError(f"{name} must be a mapping")
        return value

    @staticmethod
    def _sequence(value: Any, name: str) -> tuple[Any, ...]:
        if not isinstance(value, (list, tuple)):
            raise ThemeLoadError(f"{name} must be a sequence")
        return tuple(value)

    @staticmethod
    def _string(value: Mapping[str, Any], key: str) -> str:
        selected = value.get(key)
        if not isinstance(selected, str) or not selected:
            raise ThemeLoadError(f"{key} must be a non-empty string")
        return selected

    @staticmethod
    def _only(value: Mapping[str, Any], allowed: set[str], name: str) -> None:
        unknown = set(value).difference(allowed)
        if unknown:
            raise ThemeLoadError(
                f"{name} contains unsupported fields: "
                + ", ".join(sorted(str(item) for item in unknown))
            )
