"""High-level atomic theme loading, registration, and resolution service."""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from pathlib import Path
from typing import Any

from .contracts import ThemeLayer
from .exceptions import ThemeRegistrationError
from .loader import ThemeLoader
from .registry import ThemeRegistry
from .resolver import ResolvedTheme, ThemeResolver
from .theme import BUILTIN_THEME, Theme


class ThemeManager:
    """Own an atomically replaceable registry and bound theme resolver."""

    __slots__ = ("default_theme_id", "loader", "_registry", "_resolver")

    def __init__(
        self,
        *,
        default_theme_id: str = "teos.builtin",
        loader: ThemeLoader | None = None,
    ) -> None:
        self.default_theme_id = default_theme_id
        self.loader = loader or ThemeLoader()
        self._registry = ThemeRegistry((BUILTIN_THEME,))
        self._resolver = ThemeResolver(
            self._registry, default_theme_id="teos.builtin"
        )

    @property
    def registry(self) -> ThemeRegistry:
        """Return the current immutable registry."""
        return self._registry

    @property
    def resolver(self) -> ThemeResolver:
        """Return the resolver bound to the current registry."""
        return self._resolver

    def load(
        self,
        sources: Iterable[str | Path],
        *,
        required_template_kinds: Iterable[str] = (),
    ) -> ThemeRegistry:
        """Atomically replace user themes after complete validation."""
        ordered = tuple(
            sorted((Path(source) for source in sources), key=lambda item: str(item))
        )
        registry = ThemeRegistry(
            (BUILTIN_THEME,) + tuple(self.loader.load(path) for path in ordered)
        )
        registry.validate(required_template_kinds=required_template_kinds)
        self._replace(registry)
        return registry

    def register(self, theme: Theme) -> ThemeRegistry:
        """Atomically add one immutable theme."""
        registry = ThemeRegistry((*self._registry, theme))
        self._replace(registry)
        return registry

    def register_plugin_extensions(self, extension_registry: Any) -> int:
        """Copy immutable selected-layer themes from active plugins."""
        from src.plugins import THEME

        additions: list[Theme] = []
        for registration in extension_registry.registrations(THEME):
            extension = registration.extension
            candidates = (
                (extension,)
                if isinstance(extension, Theme)
                else tuple(extension)
                if isinstance(extension, Iterable)
                and not isinstance(extension, (str, bytes, Mapping))
                else ()
            )
            if not candidates or any(
                not isinstance(item, Theme) for item in candidates
            ):
                raise ThemeRegistrationError(
                    f"plugin theme {registration.name!r} must provide Theme values"
                )
            for item in candidates:
                if item.metadata.layer is not ThemeLayer.THEME:
                    raise ThemeRegistrationError(
                        f"plugin theme {item.name!r} must use theme layer"
                    )
            additions.extend(candidates)
        if additions:
            self._replace(ThemeRegistry((*self._registry, *additions)))
        return len(additions)

    def resolve(
        self,
        theme_id: str | None = None,
        *,
        institution_override: str | Theme | None = None,
    ) -> ResolvedTheme:
        """Resolve presentation resources without mutating registered themes."""
        return self._resolver.resolve(
            theme_id, institution_override=institution_override
        )

    def _replace(self, registry: ThemeRegistry) -> None:
        default = self.default_theme_id
        if registry.get(default) is None:
            default = "teos.builtin"
        resolver = ThemeResolver(registry, default_theme_id=default)
        self._registry = registry
        self._resolver = resolver
