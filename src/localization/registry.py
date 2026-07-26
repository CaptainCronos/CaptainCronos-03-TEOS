"""Deterministic registry and validation for localization resources."""

from __future__ import annotations

from collections import defaultdict
from types import MappingProxyType
from typing import Iterable, Mapping

from .contracts import (
    DiagnosticSeverity,
    LocalizationDiagnostic,
    normalize_locale,
)
from .exceptions import (
    FallbackResolutionError,
    LocaleError,
    ResourceRegistrationError,
)
from .language import Language
from .locale import Locale
from .resources import LocalizationResource


class LocalizationRegistry:
    """Register immutable resources and expose deterministic locale views."""

    __slots__ = ("_resources", "_by_locale")

    def __init__(
        self, resources: Iterable[LocalizationResource] = ()
    ) -> None:
        registered: dict[str, LocalizationResource] = {}
        for resource in resources:
            identifier = resource.metadata.resource_id
            if identifier in registered:
                raise ResourceRegistrationError(
                    f"duplicate localization resource identifier: {identifier!r}"
                )
            registered[identifier] = resource
        self._resources = MappingProxyType(dict(sorted(registered.items())))
        by_locale: dict[str, list[LocalizationResource]] = defaultdict(list)
        for resource in self._resources.values():
            by_locale[resource.locale_id].append(resource)
        self._by_locale = MappingProxyType(
            {
                locale_id: tuple(
                    sorted(
                        values,
                        key=lambda item: (
                            -int(item.layer),
                            item.metadata.resource_id,
                            item.metadata.version,
                        ),
                    )
                )
                for locale_id, values in sorted(by_locale.items())
            }
        )
        self.validate()

    def resources_for(self, locale_id: str) -> tuple[LocalizationResource, ...]:
        """Return locale resources in precedence and identity order."""
        return self._by_locale.get(normalize_locale(locale_id), ())

    def locale(self, locale_id: str) -> Locale:
        """Return the single effective locale definition."""
        selected = [
            resource.locale
            for resource in self.resources_for(locale_id)
            if resource.locale is not None
        ]
        if not selected:
            raise LocaleError(f"unsupported locale: {normalize_locale(locale_id)!r}")
        first = selected[0]
        if any(item != first for item in selected[1:]):
            raise ResourceRegistrationError(
                f"conflicting locale definitions for {first.identifier!r}"
            )
        return first

    def language(self, code: str) -> Language:
        """Return the single effective language definition."""
        selected = [
            resource.language
            for resource in self._resources.values()
            if resource.language is not None and resource.language.code == code.lower()
        ]
        if not selected:
            raise LocaleError(f"unsupported language: {code!r}")
        first = selected[0]
        if any(item != first for item in selected[1:]):
            raise ResourceRegistrationError(
                f"conflicting language definitions for {code!r}"
            )
        return first

    def fallback_chain(self, locale_id: str) -> tuple[str, ...]:
        """Return declared fallbacks after the requested supported locale."""
        current = normalize_locale(locale_id)
        self.locale(current)
        chain: list[str] = []
        visited = [current]
        seen = {current}
        while True:
            fallback = self.locale(current).fallback
            if fallback is None:
                return tuple(chain)
            if fallback in seen:
                raise FallbackResolutionError(
                    "locale fallback cycle: "
                    + " -> ".join((*visited, fallback))
                )
            if fallback not in self._by_locale:
                raise FallbackResolutionError(
                    f"locale {current!r} falls back to unsupported locale "
                    f"{fallback!r}"
                )
            seen.add(fallback)
            visited.append(fallback)
            chain.append(fallback)
            current = fallback

    def validate(
        self, *, required_translation_keys: Iterable[str] = ()
    ) -> tuple[LocalizationDiagnostic, ...]:
        """Validate compatibility, definitions, fallbacks, and required keys."""
        diagnostics: list[LocalizationDiagnostic] = []
        for resource in self._resources.values():
            resource.metadata.require_compatible()
            if not any(
                item.locale is not None
                for item in self.resources_for(resource.locale_id)
            ):
                raise LocaleError(
                    f"unsupported locale {resource.locale_id!r} for resource "
                    f"{resource.metadata.resource_id!r}"
                )
        for locale_id, resources in self._by_locale.items():
            self._reject_ambiguous_keys(locale_id, resources)
            self.locale(locale_id)
            self.fallback_chain(locale_id)
        for language_code in sorted(
            {
                resource.language.code
                for resource in self._resources.values()
                if resource.language is not None
            }
        ):
            self.language(language_code)
        for key in sorted(set(required_translation_keys)):
            for locale_id in self._by_locale:
                if not self._has_translation(locale_id, key):
                    diagnostics.append(
                        LocalizationDiagnostic(
                            "localization.translation.missing",
                            DiagnosticSeverity.WARNING,
                            f"missing translation {key!r} for locale {locale_id!r}",
                            key=key,
                        )
                    )
        return tuple(diagnostics)

    def snapshot(self) -> Mapping[str, LocalizationResource]:
        """Return the immutable resource registration mapping."""
        return self._resources

    def __iter__(self):
        """Iterate resources in deterministic identifier order."""
        return iter(self._resources.values())

    def __len__(self) -> int:
        """Return the number of registered resources."""
        return len(self._resources)

    @staticmethod
    def _reject_ambiguous_keys(
        locale_id: str, resources: tuple[LocalizationResource, ...]
    ) -> None:
        seen_translations: set[tuple[int, str]] = set()
        seen_terms: set[tuple[int, str]] = set()
        for resource in resources:
            for translation in resource.translations:
                key = (int(resource.layer), translation.key)
                if key in seen_translations:
                    raise ResourceRegistrationError(
                        f"duplicate translation {translation.key!r} at layer "
                        f"{resource.layer.name.lower()} for locale {locale_id!r}"
                    )
                seen_translations.add(key)
            for term in resource.terminology:
                key = (int(resource.layer), term.canonical)
                if key in seen_terms:
                    raise ResourceRegistrationError(
                        f"duplicate terminology {term.canonical!r} at layer "
                        f"{resource.layer.name.lower()} for locale {locale_id!r}"
                    )
                seen_terms.add(key)

    def _has_translation(self, locale_id: str, key: str) -> bool:
        locales = (locale_id, *self.fallback_chain(locale_id))
        return any(
            resource.translation(key) is not None
            for selected in locales
            for resource in self.resources_for(selected)
        )
