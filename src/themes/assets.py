"""Immutable references to externally managed presentation assets."""

from __future__ import annotations

from dataclasses import dataclass

from .contracts import AssetKind, require_name
from .exceptions import AssetError


@dataclass(frozen=True, slots=True)
class ThemeAsset:
    """Metadata and URI for one asset without binary-file manipulation."""

    asset_id: str
    kind: AssetKind
    uri: str
    media_type: str = ""
    description: str = ""

    def __post_init__(self) -> None:
        require_name(self.asset_id, label="asset identifier")
        if not isinstance(self.uri, str) or not self.uri.strip():
            raise AssetError(f"asset {self.asset_id!r} requires a URI")
        if self.media_type and "/" not in self.media_type:
            raise AssetError(
                f"asset {self.asset_id!r} has invalid media type "
                f"{self.media_type!r}"
            )


@dataclass(frozen=True, slots=True)
class ThemeAssets:
    """A deterministic immutable catalog of theme asset references."""

    items: tuple[ThemeAsset, ...] = ()

    def __post_init__(self) -> None:
        ordered = tuple(sorted(self.items, key=lambda item: item.asset_id))
        identifiers = tuple(item.asset_id for item in ordered)
        if len(identifiers) != len(set(identifiers)):
            raise AssetError("theme contains duplicate asset identifiers")
        object.__setattr__(self, "items", ordered)

    def get(self, asset_id: str) -> ThemeAsset | None:
        """Return an exact asset or ``None`` when absent."""
        return next((item for item in self.items if item.asset_id == asset_id), None)

    def require(self, asset_id: str) -> ThemeAsset:
        """Return an exact asset or raise a typed error."""
        selected = self.get(asset_id)
        if selected is None:
            raise AssetError(f"missing theme asset: {asset_id!r}")
        return selected
