"""Public plugin discovery contract for application-service injection."""

from typing import Protocol, runtime_checkable

from src.api.results import PluginResult


@runtime_checkable
class PluginService(Protocol):
    """Discover plugin metadata without activating plugin code."""

    def list_plugins(self) -> tuple[PluginResult, ...]:
        """Return ordered public plugin descriptors."""
        ...

