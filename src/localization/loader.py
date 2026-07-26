"""Strict JSON and YAML loading for data-driven localization packages."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping

import yaml

from .contracts import (
    DateOrder,
    HourCycle,
    MeasurementSystem,
    PageDirection,
    ResourceLayer,
)
from .exceptions import ResourceLoadError
from .language import Language
from .locale import CurrencyFormat, DocumentConventions, Locale, Region
from .metadata import ResourceMetadata
from .pluralization import PluralCase, PluralCondition, PluralRule
from .resources import LocalizationResource
from .terminology import Terminology
from .translation import Translation


class _UniqueKeyLoader(yaml.SafeLoader):
    """YAML loader that rejects duplicate mapping keys."""


def _construct_mapping(
    loader: _UniqueKeyLoader, node: yaml.MappingNode, deep: bool = False
) -> dict[Any, Any]:
    values: dict[Any, Any] = {}
    for key_node, value_node in node.value:
        key = loader.construct_object(key_node, deep=deep)
        if key in values:
            raise ResourceLoadError(f"duplicate resource key: {key!r}")
        values[key] = loader.construct_object(value_node, deep=deep)
    return values


_UniqueKeyLoader.add_constructor(
    yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, _construct_mapping
)


class LocalizationResourceLoader:
    """Decode and validate one localization resource file."""

    _TOP_LEVEL = {
        "resource_id",
        "version",
        "contract_version",
        "description",
        "locale_id",
        "layer",
        "language",
        "locale",
        "translations",
        "terminology",
        "plural_rule",
    }

    def load(self, source: str | Path) -> LocalizationResource:
        """Load a UTF-8 JSON or YAML resource from a local path."""
        path = Path(source)
        try:
            content = path.read_text(encoding="utf-8")
        except OSError as error:
            raise ResourceLoadError(
                f"cannot read localization resource {path}"
            ) from error
        suffix = path.suffix.lower()
        try:
            if suffix == ".json":
                document = json.loads(
                    content, object_pairs_hook=self._unique_json_mapping
                )
            elif suffix in {".yaml", ".yml"}:
                document = yaml.load(content, Loader=_UniqueKeyLoader)
            else:
                raise ResourceLoadError(
                    f"unsupported localization resource format: {suffix!r}"
                )
        except ResourceLoadError:
            raise
        except (json.JSONDecodeError, yaml.YAMLError) as error:
            raise ResourceLoadError(
                f"invalid localization resource syntax in {path}"
            ) from error
        try:
            return self.from_mapping(self._mapping(document, "resource"))
        except ResourceLoadError:
            raise
        except (TypeError, ValueError) as error:
            raise ResourceLoadError(
                f"invalid localization resource {path}: {error}"
            ) from error

    def from_mapping(self, document: Mapping[str, Any]) -> LocalizationResource:
        """Construct an immutable resource from an already decoded mapping."""
        self._only(document, self._TOP_LEVEL, "resource")
        locale_id = self._string(document, "locale_id")
        language = (
            self._language(self._mapping(document["language"], "language"))
            if "language" in document
            else None
        )
        locale = (
            self._locale(
                self._mapping(document["locale"], "locale"), locale_id
            )
            if "locale" in document
            else None
        )
        layer_name = str(document.get("layer", "language")).upper()
        try:
            layer = ResourceLayer[layer_name]
        except KeyError as error:
            raise ResourceLoadError(
                f"unsupported localization resource layer: {layer_name.lower()!r}"
            ) from error
        return LocalizationResource(
            metadata=ResourceMetadata(
                self._string(document, "resource_id"),
                self._string(document, "version"),
                str(document.get("contract_version", "1.0")),
                str(document.get("description", "")),
            ),
            locale_id=locale_id,
            layer=layer,
            language=language,
            locale=locale,
            translations=self._translations(
                self._mapping(document.get("translations", {}), "translations")
            ),
            terminology=tuple(
                Terminology(str(key), str(value))
                for key, value in sorted(
                    self._mapping(
                        document.get("terminology", {}), "terminology"
                    ).items()
                )
            ),
            plural_rule=self._plural_rule(
                self._mapping(document.get("plural_rule", {}), "plural_rule")
            ),
        )

    def _language(self, value: Mapping[str, Any]) -> Language:
        self._only(
            value, {"code", "name", "native_name", "script", "direction"}, "language"
        )
        return Language(
            self._string(value, "code"),
            self._string(value, "name"),
            self._string(value, "native_name"),
            str(value.get("script", "Latn")),
            PageDirection(str(value.get("direction", "ltr"))),
        )

    def _locale(self, value: Mapping[str, Any], locale_id: str) -> Locale:
        self._only(
            value,
            {
                "culture",
                "region",
                "script",
                "fallback",
                "conventions",
            },
            "locale",
        )
        region_value = value.get("region")
        region = None
        if region_value is not None:
            region_mapping = self._mapping(region_value, "locale.region")
            self._only(region_mapping, {"code", "name"}, "locale.region")
            region = Region(
                self._string(region_mapping, "code"),
                self._string(region_mapping, "name"),
            )
        return Locale(
            locale_id,
            locale_id.replace("_", "-").split("-", 1)[0].lower(),
            self._string(value, "culture"),
            self._conventions(
                self._mapping(value.get("conventions", {}), "locale.conventions")
            ),
            region,
            str(value["script"]) if "script" in value else None,
            str(value["fallback"]) if "fallback" in value else None,
        )

    def _conventions(self, value: Mapping[str, Any]) -> DocumentConventions:
        allowed = {
            "date_pattern",
            "time_pattern",
            "date_order",
            "hour_cycle",
            "paper_size",
            "measurement_system",
            "page_direction",
            "decimal_separator",
            "thousands_separator",
            "primary_quotes",
            "secondary_quotes",
            "numbering_digits",
            "default_time_zone",
            "default_currency",
            "currencies",
            "unit_labels",
        }
        self._only(value, allowed, "locale.conventions")
        defaults = DocumentConventions()
        currencies: list[CurrencyFormat] = []
        for item in self._sequence(value.get("currencies", []), "currencies"):
            mapping = self._mapping(item, "currency")
            self._only(
                mapping,
                {"code", "symbol", "symbol_position", "space", "decimal_places"},
                "currency",
            )
            currencies.append(
                CurrencyFormat(
                    self._string(mapping, "code"),
                    self._string(mapping, "symbol"),
                    str(mapping.get("symbol_position", "before")),
                    bool(mapping.get("space", False)),
                    int(mapping.get("decimal_places", 2)),
                )
            )
        return DocumentConventions(
            str(value.get("date_pattern", defaults.date_pattern)),
            str(value.get("time_pattern", defaults.time_pattern)),
            DateOrder(str(value.get("date_order", defaults.date_order.value))),
            HourCycle(str(value.get("hour_cycle", defaults.hour_cycle.value))),
            str(value.get("paper_size", defaults.paper_size)),
            MeasurementSystem(
                str(value.get("measurement_system", defaults.measurement_system.value))
            ),
            PageDirection(
                str(value.get("page_direction", defaults.page_direction.value))
            ),
            str(value.get("decimal_separator", defaults.decimal_separator)),
            str(value.get("thousands_separator", defaults.thousands_separator)),
            self._pair(value.get("primary_quotes", defaults.primary_quotes), "primary_quotes"),
            self._pair(
                value.get("secondary_quotes", defaults.secondary_quotes),
                "secondary_quotes",
            ),
            str(value.get("numbering_digits", defaults.numbering_digits)),
            str(value.get("default_time_zone", defaults.default_time_zone)),
            str(value.get("default_currency", defaults.default_currency)),
            tuple(currencies),
            tuple(
                (str(key), str(label))
                for key, label in sorted(
                    self._mapping(value.get("unit_labels", {}), "unit_labels").items()
                )
            ),
        )

    def _translations(
        self, values: Mapping[str, Any]
    ) -> tuple[Translation, ...]:
        translations: list[Translation] = []
        for key, value in sorted(values.items()):
            if isinstance(value, str):
                translations.append(Translation.singular(str(key), value))
            else:
                forms = self._mapping(value, f"translation {key}")
                translations.append(
                    Translation(
                        str(key),
                        tuple(
                            (str(category), str(text))
                            for category, text in sorted(forms.items())
                        ),
                    )
                )
        return tuple(translations)

    def _plural_rule(self, value: Mapping[str, Any]) -> PluralRule:
        self._only(value, {"cases"}, "plural_rule")
        cases: list[PluralCase] = []
        for raw_case in self._sequence(value.get("cases", []), "plural_rule.cases"):
            case = self._mapping(raw_case, "plural case")
            self._only(case, {"category", "any_of"}, "plural case")
            groups: list[tuple[PluralCondition, ...]] = []
            for raw_group in self._sequence(case.get("any_of", []), "plural any_of"):
                conditions: list[PluralCondition] = []
                for raw_condition in self._sequence(raw_group, "plural condition group"):
                    condition = self._mapping(raw_condition, "plural condition")
                    self._only(
                        condition,
                        {"operand", "ranges", "modulus", "negated"},
                        "plural condition",
                    )
                    ranges = tuple(
                        (int(pair[0]), int(pair[1]))
                        for pair in (
                            self._sequence(item, "plural range")
                            for item in self._sequence(
                                condition.get("ranges", []), "plural ranges"
                            )
                        )
                        if len(pair) == 2
                    )
                    conditions.append(
                        PluralCondition(
                            self._string(condition, "operand"),
                            ranges,
                            int(condition["modulus"])
                            if "modulus" in condition
                            else None,
                            bool(condition.get("negated", False)),
                        )
                    )
                groups.append(tuple(conditions))
            cases.append(
                PluralCase(self._string(case, "category"), tuple(groups))
            )
        return PluralRule(tuple(cases))

    @staticmethod
    def _unique_json_mapping(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
        values: dict[str, Any] = {}
        for key, value in pairs:
            if key in values:
                raise ResourceLoadError(f"duplicate resource key: {key!r}")
            values[key] = value
        return values

    @staticmethod
    def _mapping(value: Any, name: str) -> Mapping[str, Any]:
        if not isinstance(value, Mapping):
            raise ResourceLoadError(f"{name} must be a mapping")
        return value

    @staticmethod
    def _sequence(value: Any, name: str) -> tuple[Any, ...]:
        if not isinstance(value, (list, tuple)):
            raise ResourceLoadError(f"{name} must be a sequence")
        return tuple(value)

    @staticmethod
    def _pair(value: Any, name: str) -> tuple[str, str]:
        sequence = LocalizationResourceLoader._sequence(value, name)
        if len(sequence) != 2 or not all(isinstance(item, str) for item in sequence):
            raise ResourceLoadError(f"{name} must contain two strings")
        return str(sequence[0]), str(sequence[1])

    @staticmethod
    def _string(value: Mapping[str, Any], key: str) -> str:
        selected = value.get(key)
        if not isinstance(selected, str) or not selected:
            raise ResourceLoadError(f"{key} must be a non-empty string")
        return selected

    @staticmethod
    def _only(value: Mapping[str, Any], allowed: set[str], name: str) -> None:
        unknown = set(value).difference(allowed)
        if unknown:
            raise ResourceLoadError(
                f"{name} contains unsupported fields: "
                + ", ".join(sorted(str(item) for item in unknown))
            )
