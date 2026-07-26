"""Predictable translation, terminology, and fallback resolution."""

from __future__ import annotations

from typing import Any, Mapping

from .contracts import (
    DiagnosticSeverity,
    LocalizationDiagnostic,
    normalize_locale,
    require_translation_key,
)
from .registry import LocalizationRegistry
from .resources import LocalizationResource


class LocalizationResolver:
    """Resolve display values across locale and resource precedence."""

    __slots__ = ("registry", "default_locale", "_diagnostics")

    def __init__(
        self,
        registry: LocalizationRegistry,
        *,
        default_locale: str = "en-US",
    ) -> None:
        self.registry = registry
        self.default_locale = normalize_locale(default_locale)
        self.registry.locale(self.default_locale)
        self._diagnostics: list[LocalizationDiagnostic] = []

    @property
    def diagnostics(self) -> tuple[LocalizationDiagnostic, ...]:
        """Return non-fatal findings in lookup order."""
        return tuple(self._diagnostics)

    def clear_diagnostics(self) -> None:
        """Clear accumulated non-fatal lookup findings."""
        self._diagnostics.clear()

    def locale_chain(self, locale_id: str) -> tuple[str, ...]:
        """Return the complete deduplicated lookup locale sequence."""
        requested = normalize_locale(locale_id)
        candidates = (
            requested,
            *self.registry.fallback_chain(requested),
            self.default_locale,
            "en-US",
        )
        return tuple(dict.fromkeys(candidates))

    def translate(
        self,
        key: str,
        *,
        locale: str | None = None,
        default: str | None = None,
        count: int | float | str | None = None,
        parameters: Mapping[str, Any] | None = None,
    ) -> str:
        """Resolve, pluralize, and interpolate one translation."""
        require_translation_key(key)
        selected_locale = locale or self.default_locale
        for locale_id in self.locale_chain(selected_locale):
            for resource in self.registry.resources_for(locale_id):
                translation = resource.translation(key)
                if translation is None:
                    continue
                category = (
                    resource.plural_rule.select(count)
                    if count is not None
                    else "other"
                )
                values = dict(parameters or {})
                if count is not None:
                    values.setdefault("count", count)
                return translation.render(category, values)
        fallback = default if default is not None else key
        self._diagnostics.append(
            LocalizationDiagnostic(
                "localization.translation.missing",
                DiagnosticSeverity.WARNING,
                f"missing translation {key!r} for locale {selected_locale!r}",
                key=key,
            )
        )
        return fallback

    def term(
        self,
        canonical: str,
        *,
        locale: str | None = None,
        default: str | None = None,
    ) -> str:
        """Resolve one localized canonical presentation term."""
        selected_locale = locale or self.default_locale
        for locale_id in self.locale_chain(selected_locale):
            for resource in self.registry.resources_for(locale_id):
                label = resource.term(canonical)
                if label is not None:
                    return label
        fallback = default if default is not None else canonical
        self._diagnostics.append(
            LocalizationDiagnostic(
                "localization.terminology.missing",
                DiagnosticSeverity.WARNING,
                f"missing terminology {canonical!r} for locale {selected_locale!r}",
                key=canonical,
            )
        )
        return fallback

    def resource_for_locale(self, locale_id: str) -> LocalizationResource:
        """Return the highest-precedence resource carrying locale conventions."""
        for candidate in self.locale_chain(locale_id):
            for resource in self.registry.resources_for(candidate):
                if resource.locale is not None:
                    return resource
        raise AssertionError("validated locale chain has no locale definition")
