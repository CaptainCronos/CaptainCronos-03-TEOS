"""Read-only repository result exposed above the loading layer."""

from __future__ import annotations

from pathlib import Path

from .registry import ObjectRegistry


class Repository:
    """A successfully validated immutable TEOS object repository."""

    __slots__ = ("_registry", "_sources")

    def __init__(self, registry: ObjectRegistry, sources: tuple[Path, ...]) -> None:
        self._registry = registry
        self._sources = sources

    @property
    def registry(self) -> ObjectRegistry:
        """Return the repository's immutable object registry."""
        return self._registry

    @property
    def sources(self) -> tuple[Path, ...]:
        """Return source document paths without exposing their raw JSON."""
        return self._sources

    def __len__(self) -> int:
        """Return the number of loaded object versions."""
        return len(self._registry)
