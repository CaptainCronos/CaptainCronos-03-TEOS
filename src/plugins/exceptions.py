"""Exception hierarchy for plugin discovery, validation, and lifecycle."""

from __future__ import annotations


class PluginError(Exception):
    """Base class for all plugin-framework failures."""


class PluginDiscoveryError(PluginError):
    """Plugin metadata could not be discovered deterministically."""


class PluginManifestError(PluginError):
    """A plugin manifest is missing, malformed, or semantically invalid."""


class PluginCompatibilityError(PluginError):
    """A plugin is incompatible with TEOS or with another plugin."""


class PluginDependencyError(PluginCompatibilityError):
    """Plugin dependencies are missing, incompatible, or cyclic."""


class DuplicatePluginError(PluginManifestError):
    """More than one discovered plugin uses the same identifier."""


class PluginPermissionError(PluginError):
    """A plugin requested a permission the host did not grant."""


class PluginRegistrationError(PluginError):
    """An extension registration is invalid or ambiguous."""


class PluginLoadError(PluginError):
    """A plugin entry point could not be imported or constructed."""


class PluginLifecycleError(PluginError):
    """A plugin failed during activation or deactivation."""
