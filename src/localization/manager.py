"""High-level loading, registration, resolution, and formatting service."""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from pathlib import Path
from typing import Any

from .contracts import ResourceLayer, normalize_locale, require_resource_id
from .exceptions import ResourceRegistrationError
from .formatting import LocaleFormatter
from .loader import LocalizationResourceLoader
from .metadata import ResourceMetadata
from .registry import LocalizationRegistry
from .resolver import LocalizationResolver
from .resources import BUILTIN_ENGLISH, LocalizationResource
from .terminology import Terminology
from .translation import Translation


class LocalizationManager:
    """Own an atomically replaceable registry and its presentation services."""

    __slots__ = ("default_locale", "loader", "_registry", "_resolver")

    def __init__(
        self,
        *,
        default_locale: str = "en-US",
        loader: LocalizationResourceLoader | None = None,
    ) -> None:
        self.default_locale = normalize_locale(default_locale)
        self.loader = loader or LocalizationResourceLoader()
        self._registry = LocalizationRegistry((BUILTIN_ENGLISH,))
        self._resolver = LocalizationResolver(
            self._registry,
            default_locale=(
                self.default_locale
                if self.default_locale == "en-US"
                else "en-US"
            ),
        )

    @property
    def registry(self) -> LocalizationRegistry:
        """Return the current immutable-resource registry."""
        return self._registry

    @property
    def resolver(self) -> LocalizationResolver:
        """Return the resolver bound to the current registry."""
        return self._resolver

    def load(
        self,
        sources: Iterable[str | Path],
        *,
        required_translation_keys: Iterable[str] = (),
    ) -> LocalizationRegistry:
        """Atomically replace user resources after complete validation."""
        ordered = tuple(
            sorted((Path(source) for source in sources), key=lambda item: str(item))
        )
        resources = (BUILTIN_ENGLISH,) + tuple(
            self.loader.load(source) for source in ordered
        )
        registry = LocalizationRegistry(resources)
        registry.validate(required_translation_keys=required_translation_keys)
        self._replace(registry)
        return registry

    def register(
        self,
        resource: LocalizationResource,
        *,
        required_translation_keys: Iterable[str] = (),
    ) -> LocalizationRegistry:
        """Atomically add one immutable resource."""
        registry = LocalizationRegistry((*self._registry, resource))
        registry.validate(required_translation_keys=required_translation_keys)
        self._replace(registry)
        return registry

    def register_plugin_extensions(self, extension_registry: Any) -> int:
        """Copy resources from active plugin localization registrations."""
        from src.plugins import LOCALIZATION

        additions: list[LocalizationResource] = []
        for registration in extension_registry.registrations(LOCALIZATION):
            extension = registration.extension
            candidates = (
                (extension,)
                if isinstance(extension, LocalizationResource)
                else tuple(extension)
                if isinstance(extension, Iterable)
                and not isinstance(extension, (str, bytes, Mapping))
                else ()
            )
            if not candidates or any(
                not isinstance(item, LocalizationResource) for item in candidates
            ):
                raise ResourceRegistrationError(
                    f"plugin localization {registration.name!r} must provide "
                    "LocalizationResource values"
                )
            for item in candidates:
                if item.layer is not ResourceLayer.PLUGIN:
                    raise ResourceRegistrationError(
                        f"plugin resource {item.name!r} must use plugin layer"
                    )
            additions.extend(candidates)
        if additions:
            self._replace(LocalizationRegistry((*self._registry, *additions)))
        return len(additions)

    def institution_override(
        self,
        identifier: str,
        locale: str,
        *,
        translations: Mapping[str, str | Mapping[str, str]] | None = None,
        terminology: Mapping[str, str] | None = None,
        version: str = "1.0.0",
    ) -> LocalizationResource:
        """Create a presentation-only institution override resource."""
        require_resource_id(identifier)
        locale_id = normalize_locale(locale)
        self._registry.locale(locale_id)
        translated: list[Translation] = []
        for key, value in sorted((translations or {}).items()):
            if isinstance(value, str):
                translated.append(Translation.singular(key, value))
            elif isinstance(value, Mapping):
                translated.append(
                    Translation(
                        key,
                        tuple(
                            (str(category), str(text))
                            for category, text in sorted(value.items())
                        ),
                    )
                )
            else:
                raise ResourceRegistrationError(
                    f"institution translation {key!r} must be text or plural forms"
                )
        return LocalizationResource(
            ResourceMetadata(
                f"institution.{identifier}.{locale_id.lower()}",
                version,
                description=f"Institution overrides for {identifier}",
            ),
            locale_id,
            ResourceLayer.INSTITUTION,
            tuple(translated),
            tuple(
                Terminology(key, value)
                for key, value in sorted((terminology or {}).items())
            ),
        )

    def translate(self, key: str, **options: Any) -> str:
        """Resolve one translated display string."""
        return self._resolver.translate(key, **options)

    def term(self, canonical: str, **options: Any) -> str:
        """Resolve one localized canonical term."""
        return self._resolver.term(canonical, **options)

    def formatter(self, locale: str | None = None) -> LocaleFormatter:
        """Return a formatter for the selected locale conventions."""
        selected = locale or self.default_locale
        resource = self._resolver.resource_for_locale(selected)
        assert resource.locale is not None
        return LocaleFormatter(resource.locale.conventions)

    def _replace(self, registry: LocalizationRegistry) -> None:
        resolver = LocalizationResolver(
            registry, default_locale=self.default_locale
        )
        self._registry = registry
        self._resolver = resolver
