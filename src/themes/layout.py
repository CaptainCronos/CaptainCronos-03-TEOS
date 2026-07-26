"""Immutable reusable page-layout presentation configuration."""

from __future__ import annotations

from dataclasses import dataclass

from .contracts import Orientation, require_name
from .exceptions import LayoutError


@dataclass(frozen=True, slots=True)
class PageMargins:
    """Logical page margins in points."""

    top: float = 72.0
    right: float = 72.0
    bottom: float = 72.0
    left: float = 72.0

    def __post_init__(self) -> None:
        if min(self.top, self.right, self.bottom, self.left) < 0:
            raise LayoutError("page margins must not be negative")


@dataclass(frozen=True, slots=True)
class LayoutDefinition:
    """One named layout for an artifact kind."""

    layout_id: str
    artifact_kind: str
    page_size: str = "letter"
    orientation: Orientation = Orientation.PORTRAIT
    margins: PageMargins = PageMargins()
    regions: tuple[str, ...] = ()
    style_refs: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        require_name(self.layout_id, label="layout identifier")
        require_name(self.artifact_kind, label="artifact kind")
        if not self.page_size.strip():
            raise LayoutError("page size must not be empty")
        for name in (*self.regions, *self.style_refs):
            require_name(name)
        if len(self.regions) != len(set(self.regions)):
            raise LayoutError(f"layout {self.layout_id!r} has duplicate regions")


@dataclass(frozen=True, slots=True)
class ThemeLayout:
    """An immutable catalog of layouts for supported document kinds."""

    items: tuple[LayoutDefinition, ...] = ()

    def __post_init__(self) -> None:
        ordered = tuple(sorted(self.items, key=lambda item: item.layout_id))
        identifiers = tuple(item.layout_id for item in ordered)
        if len(identifiers) != len(set(identifiers)):
            raise LayoutError("theme contains duplicate layout identifiers")
        object.__setattr__(self, "items", ordered)

    def get(self, layout_id: str) -> LayoutDefinition | None:
        """Return an exact layout definition."""
        return next(
            (item for item in self.items if item.layout_id == layout_id), None
        )

    def for_artifact(self, artifact_kind: str) -> tuple[LayoutDefinition, ...]:
        """Return matching layouts in deterministic identifier order."""
        return tuple(
            item for item in self.items if item.artifact_kind == artifact_kind
        )
