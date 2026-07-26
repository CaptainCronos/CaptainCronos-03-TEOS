"""Immutable institution branding configuration."""

import re
from dataclasses import dataclass
from pathlib import PurePosixPath

from .contracts import AssetKind


_HEX_COLOR = re.compile(r"#[0-9A-Fa-f]{6}")


@dataclass(frozen=True, slots=True)
class BrandAsset:
    """Reference to a separately stored branding asset."""

    identifier: str
    kind: AssetKind
    path: PurePosixPath
    required: bool = True
    alt_text: str | None = None

    def __post_init__(self) -> None:
        if not self.identifier:
            raise ValueError("brand asset identifier cannot be empty")
        if self.path.is_absolute() or ".." in self.path.parts:
            raise ValueError("brand asset path must be a safe relative path")
        if self.kind is AssetKind.LOGO and not self.alt_text:
            raise ValueError("logo assets require alternative text")


@dataclass(frozen=True, slots=True)
class InstitutionBrand:
    """Complete presentation-safe brand configuration for an institution."""

    display_name: str
    assets: tuple[BrandAsset, ...] = ()
    colors: tuple[tuple[str, str], ...] = ()
    fonts: tuple[str, ...] = ()
    headers: tuple[str, ...] = ()
    footers: tuple[str, ...] = ()
    copyright_text: str | None = None
    revision_text: str | None = None

    def __post_init__(self) -> None:
        if not self.display_name:
            raise ValueError("brand display name cannot be empty")
        if any(not name or not _HEX_COLOR.fullmatch(value) for name, value in self.colors):
            raise ValueError("brand colors require names and six-digit hex values")
