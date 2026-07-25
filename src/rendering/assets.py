"""Immutable referenced presentation assets and asset catalogs."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from .exceptions import AssetError, MissingAssetError


class AssetKind(StrEnum):
    """Presentation roles supported by the rendering framework."""

    LOGO = "logo"
    IMAGE = "image"
    ICON = "icon"
    BRANDING = "branding"
    THEME = "theme"


@dataclass(frozen=True, slots=True)
class Asset:
    """Metadata and a locator for one externally stored presentation asset."""

    identifier: str
    uri: str
    content_type: str
    kind: AssetKind
    description: str | None = None

    def __post_init__(self) -> None:
        """Require stable identity, a locator, and a media type."""
        if not self.identifier:
            raise AssetError("asset identifier cannot be empty")
        if not self.uri:
            raise AssetError("asset URI cannot be empty")
        if "/" not in self.content_type:
            raise AssetError("asset content type must be a media type")


@dataclass(frozen=True, slots=True)
class AssetReference:
    """A presentation-only reference to an asset catalog entry."""

    identifier: str

    def __post_init__(self) -> None:
        """Require a stable referenced identifier."""
        if not self.identifier:
            raise AssetError("asset reference identifier cannot be empty")


@dataclass(frozen=True, slots=True)
class AssetRequirement:
    """A required asset and its accepted media types."""

    reference: AssetReference
    accepted_content_types: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class AssetCatalog:
    """An immutable, exact-identifier index of referenced assets."""

    assets: tuple[Asset, ...] = ()

    def __post_init__(self) -> None:
        """Reject ambiguous asset identities."""
        identifiers = tuple(asset.identifier for asset in self.assets)
        if len(set(identifiers)) != len(identifiers):
            raise AssetError("asset identifiers must be unique")

    def resolve(self, reference: AssetReference) -> Asset:
        """Resolve one exact asset reference without loading its content."""
        for asset in self.assets:
            if asset.identifier == reference.identifier:
                return asset
        raise MissingAssetError(f"asset not found: {reference.identifier}")

    def require(self, requirement: AssetRequirement) -> Asset:
        """Resolve an asset and enforce its declared media-type contract."""
        asset = self.resolve(requirement.reference)
        accepted = requirement.accepted_content_types
        if accepted and asset.content_type not in accepted:
            raise AssetError(
                f"asset {asset.identifier!r} has unsupported content type "
                f"{asset.content_type!r}"
            )
        return asset
