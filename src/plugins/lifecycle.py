"""Plugin lifecycle states and immutable status reports."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class PluginState(str, Enum):
    """Observable states in the managed plugin lifecycle."""

    DISCOVERED = "discovered"
    VALIDATED = "validated"
    LOADED = "loaded"
    ACTIVATING = "activating"
    ACTIVE = "active"
    DEACTIVATING = "deactivating"
    UNLOADED = "unloaded"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass(frozen=True)
class PluginStatus:
    """The current state and optional isolated failure for one plugin."""

    plugin_id: str
    state: PluginState
    error: Exception | None = None
