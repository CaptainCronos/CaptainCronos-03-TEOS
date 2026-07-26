"""Isolated discovery, validation, and lifecycle management for TEOS plugins."""

from .discovery import DiscoveryProvider, PluginCandidate, PluginDiscovery
from .exceptions import (
    DuplicatePluginError,
    PluginCompatibilityError,
    PluginDependencyError,
    PluginDiscoveryError,
    PluginError,
    PluginLifecycleError,
    PluginLoadError,
    PluginManifestError,
    PluginPermissionError,
    PluginRegistrationError,
)
from .interfaces import (
    EXPORTER,
    GENERATOR,
    IMPORTER,
    INSTITUTION_TEMPLATE,
    LOCALIZATION,
    RENDERER,
    THEME,
    VALIDATOR,
    Extension,
    Plugin,
    PluginContext,
)
from .lifecycle import PluginState, PluginStatus
from .loader import LoadedPlugin, PluginLoader
from .manager import PluginManager
from .manifest import MANIFEST_FILENAME, load_manifest, parse_manifest
from .metadata import (
    PluginDependency,
    PluginMetadata,
    SemanticVersion,
    VersionConstraint,
)
from .permissions import Permission, PermissionSet
from .registry import ExtensionRegistration, ExtensionRegistry
from .sandbox import PluginSandbox, SandboxResult

__all__ = [
    "DiscoveryProvider",
    "DuplicatePluginError",
    "EXPORTER",
    "Extension",
    "ExtensionRegistration",
    "ExtensionRegistry",
    "GENERATOR",
    "IMPORTER",
    "INSTITUTION_TEMPLATE",
    "LOCALIZATION",
    "LoadedPlugin",
    "MANIFEST_FILENAME",
    "Permission",
    "PermissionSet",
    "Plugin",
    "PluginCandidate",
    "PluginCompatibilityError",
    "PluginContext",
    "PluginDependency",
    "PluginDependencyError",
    "PluginDiscovery",
    "PluginDiscoveryError",
    "PluginError",
    "PluginLifecycleError",
    "PluginLoadError",
    "PluginLoader",
    "PluginManager",
    "PluginManifestError",
    "PluginMetadata",
    "PluginPermissionError",
    "PluginRegistrationError",
    "PluginSandbox",
    "PluginState",
    "PluginStatus",
    "RENDERER",
    "SandboxResult",
    "SemanticVersion",
    "THEME",
    "VALIDATOR",
    "VersionConstraint",
    "load_manifest",
    "parse_manifest",
]
