"""Generic transactional registry for plugin extension points."""

from __future__ import annotations

import re
from dataclasses import dataclass
from types import MappingProxyType
from typing import Any, Iterator, Mapping

from .exceptions import PluginRegistrationError


_NAME = re.compile(r"[A-Za-z0-9](?:[A-Za-z0-9._-]*[A-Za-z0-9])?")
_CATEGORY = re.compile(r"[a-z][a-z0-9]*(?:[._-][a-z0-9]+)*")


@dataclass(frozen=True)
class ExtensionRegistration:
    """One immutable extension binding owned by a plugin."""

    plugin_id: str
    category: str
    name: str
    extension: Any


class PluginRegistrar:
    """A plugin-scoped view that enforces declared capabilities."""

    def __init__(
        self,
        registry: "ExtensionRegistry",
        plugin_id: str,
        capabilities: tuple[str, ...],
    ) -> None:
        self._registry = registry
        self._plugin_id = plugin_id
        self._capabilities = frozenset(capabilities)

    def register(
        self,
        category: str,
        extension: Any,
        *,
        name: str | None = None,
    ) -> None:
        """Register an extension only in a manifest-declared category."""
        if category not in self._capabilities:
            raise PluginRegistrationError(
                f"plugin {self._plugin_id!r} did not declare capability "
                f"{category!r}"
            )
        selected_name = name if name is not None else getattr(extension, "name", None)
        self._registry._register(
            ExtensionRegistration(
                plugin_id=self._plugin_id,
                category=category,
                name=selected_name,
                extension=extension,
            )
        )


class ExtensionRegistry:
    """Register and resolve extensions without knowing category internals."""

    def __init__(self) -> None:
        self._registrations: dict[tuple[str, str], ExtensionRegistration] = {}

    def registrar(
        self, plugin_id: str, capabilities: tuple[str, ...]
    ) -> PluginRegistrar:
        """Create a registration interface scoped to one plugin."""
        return PluginRegistrar(self, plugin_id, capabilities)

    def _register(self, registration: ExtensionRegistration) -> None:
        if not isinstance(registration.category, str) or not _CATEGORY.fullmatch(
            registration.category
        ):
            raise PluginRegistrationError(
                f"invalid extension category: {registration.category!r}"
            )
        if not isinstance(registration.name, str) or not _NAME.fullmatch(
            registration.name
        ):
            raise PluginRegistrationError(
                f"invalid extension name: {registration.name!r}"
            )
        if registration.extension is None:
            raise PluginRegistrationError("extension value cannot be None")
        key = (registration.category, registration.name)
        if key in self._registrations:
            existing = self._registrations[key]
            raise PluginRegistrationError(
                f"extension {registration.category}:{registration.name} "
                f"is already registered by {existing.plugin_id!r}"
            )
        self._registrations[key] = registration

    def resolve(self, category: str, name: str) -> Any:
        """Return one extension value by exact category and name."""
        try:
            return self._registrations[(category, name)].extension
        except KeyError as error:
            raise PluginRegistrationError(
                f"unknown extension: {category}:{name}"
            ) from error

    def registrations(
        self, category: str | None = None
    ) -> tuple[ExtensionRegistration, ...]:
        """Return registrations in deterministic category/name order."""
        values = self._registrations.values()
        if category is not None:
            values = (
                registration
                for registration in values
                if registration.category == category
            )
        return tuple(
            sorted(values, key=lambda item: (item.category, item.name, item.plugin_id))
        )

    def snapshot(self) -> Mapping[tuple[str, str], ExtensionRegistration]:
        """Return an immutable snapshot for inspection."""
        return MappingProxyType(dict(self._registrations))

    def unregister_plugin(self, plugin_id: str) -> None:
        """Remove every registration owned by one plugin."""
        for key in tuple(self._registrations):
            if self._registrations[key].plugin_id == plugin_id:
                del self._registrations[key]

    def __iter__(self) -> Iterator[ExtensionRegistration]:
        return iter(self.registrations())

    def __len__(self) -> int:
        return len(self._registrations)
