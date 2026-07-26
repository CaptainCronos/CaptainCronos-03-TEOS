"""Stable public interfaces implemented and consumed by TEOS plugins."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Protocol, runtime_checkable

from .metadata import PluginMetadata
from .permissions import Permission, PermissionSet


RENDERER = "renderer"
GENERATOR = "generator"
VALIDATOR = "validator"
IMPORTER = "importer"
EXPORTER = "exporter"
THEME = "theme"
INSTITUTION_TEMPLATE = "institution-template"
LOCALIZATION = "localization"


@runtime_checkable
class Extension(Protocol):
    """Minimal named extension contract accepted by the generic registry."""

    @property
    def name(self) -> str:
        """Return a stable name within the extension category."""
        ...


class PluginRegistrar(Protocol):
    """Plugin-scoped registration interface supplied during activation."""

    def register(
        self, category: str, extension: Any, *, name: str | None = None
    ) -> None:
        """Register one extension value under a declared category."""
        ...


@dataclass(frozen=True)
class PluginContext:
    """Immutable host context available to one plugin."""

    metadata: PluginMetadata
    permissions: PermissionSet
    registrar: PluginRegistrar

    def require_permission(self, permission: Permission) -> None:
        """Assert that a host capability was granted to this plugin."""
        self.permissions.require(permission, plugin_id=self.metadata.identifier)


class Plugin(ABC):
    """Base interface for plugin registration and lifecycle callbacks."""

    @abstractmethod
    def activate(self, context: PluginContext) -> None:
        """Register extensions and initialize plugin-owned resources."""

    def deactivate(self, context: PluginContext) -> None:
        """Release plugin-owned resources before registrations are removed."""
