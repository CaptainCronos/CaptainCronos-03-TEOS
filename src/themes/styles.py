"""Immutable reusable styles and deterministic local inheritance."""

from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType
from typing import Any, Mapping

from .contracts import frozen_mapping, require_name
from .exceptions import StyleResolutionError


@dataclass(frozen=True, slots=True)
class StyleDefinition:
    """One named property set with an optional parent style."""

    name: str
    properties: Mapping[str, Any] = MappingProxyType({})
    extends: str | None = None

    def __post_init__(self) -> None:
        require_name(self.name, label="style name")
        if self.extends is not None:
            require_name(self.extends, label="parent style name")
        object.__setattr__(self, "properties", frozen_mapping(self.properties))


@dataclass(frozen=True, slots=True)
class ThemeStyles:
    """A deterministic immutable collection of named style definitions."""

    items: tuple[StyleDefinition, ...] = ()

    def __post_init__(self) -> None:
        ordered = tuple(sorted(self.items, key=lambda item: item.name))
        names = tuple(item.name for item in ordered)
        if len(names) != len(set(names)):
            raise StyleResolutionError("theme contains duplicate style names")
        object.__setattr__(self, "items", ordered)

    def get(self, name: str) -> StyleDefinition | None:
        """Return an exact style definition."""
        return next((item for item in self.items if item.name == name), None)

    def resolve(self, name: str) -> Mapping[str, Any]:
        """Resolve one style's local parent chain into immutable properties."""
        return self._resolve(name, ())

    def validate(self) -> None:
        """Validate every parent reference and reject inheritance cycles."""
        for item in self.items:
            self.resolve(item.name)

    def _resolve(self, name: str, stack: tuple[str, ...]) -> Mapping[str, Any]:
        selected = self.get(name)
        if selected is None:
            raise StyleResolutionError(f"missing style reference: {name!r}")
        if name in stack:
            raise StyleResolutionError(
                "style inheritance cycle: " + " -> ".join((*stack, name))
            )
        merged: dict[str, Any] = {}
        if selected.extends is not None:
            merged.update(self._resolve(selected.extends, (*stack, name)))
        merged.update(selected.properties)
        return frozen_mapping(merged)
