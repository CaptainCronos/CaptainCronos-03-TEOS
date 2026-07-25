"""Immutable presentation context supplied to renderers."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import PurePosixPath

from .assets import AssetCatalog, AssetReference
from .exceptions import RenderingContextError
from .formatting import Typography


@dataclass(frozen=True, slots=True)
class RenderOptions:
    """Per-request output naming and reproducibility options."""

    output_filename: PurePosixPath
    generation_timestamp: datetime

    def __post_init__(self) -> None:
        """Require a safe relative filename and an aware timestamp."""
        path = PurePosixPath(self.output_filename)
        object.__setattr__(self, "output_filename", path)
        if path.is_absolute() or ".." in path.parts or path.name in {"", "."}:
            raise RenderingContextError(
                "output filename must be a safe relative path"
            )
        if (
            self.generation_timestamp.tzinfo is None
            or self.generation_timestamp.utcoffset() is None
        ):
            raise RenderingContextError(
                "generation timestamp must include a time zone"
            )


@dataclass(frozen=True, slots=True)
class InstitutionBranding:
    """Institution display identity and referenced brand assets."""

    institution_name: str
    logo: AssetReference | None = None
    additional_assets: tuple[AssetReference, ...] = ()

    def __post_init__(self) -> None:
        """Require a display name."""
        if not self.institution_name:
            raise RenderingContextError("institution name cannot be empty")


@dataclass(frozen=True, slots=True)
class Theme:
    """Named colors, typography, and referenced theme assets."""

    name: str = "default"
    colors: tuple[tuple[str, str], ...] = ()
    typography: Typography = Typography()
    assets: tuple[AssetReference, ...] = ()

    def __post_init__(self) -> None:
        """Require a name and unique color roles."""
        if not self.name:
            raise RenderingContextError("theme name cannot be empty")
        roles = tuple(role for role, _ in self.colors)
        if len(roles) != len(set(roles)):
            raise RenderingContextError("theme color roles must be unique")


@dataclass(frozen=True, slots=True)
class Localization:
    """Locale and display-label configuration."""

    locale: str = "en-US"
    language: str = "en"
    time_zone: str = "UTC"
    labels: tuple[tuple[str, str], ...] = ()

    def __post_init__(self) -> None:
        """Require named locale, language, and time zone."""
        if not self.locale or not self.language or not self.time_zone:
            raise RenderingContextError(
                "localization fields cannot be empty"
            )


@dataclass(frozen=True, slots=True)
class PageSettings:
    """Physical page presentation settings."""

    size: str = "letter"
    orientation: str = "portrait"
    margin_top_mm: float = 25.4
    margin_right_mm: float = 25.4
    margin_bottom_mm: float = 25.4
    margin_left_mm: float = 25.4

    def __post_init__(self) -> None:
        """Require a supported orientation and non-negative margins."""
        if not self.size:
            raise RenderingContextError("page size cannot be empty")
        if self.orientation not in {"portrait", "landscape"}:
            raise RenderingContextError("unsupported page orientation")
        if min(
            self.margin_top_mm,
            self.margin_right_mm,
            self.margin_bottom_mm,
            self.margin_left_mm,
        ) < 0:
            raise RenderingContextError("page margins cannot be negative")


@dataclass(frozen=True, slots=True)
class RenderingContext:
    """All presentation-only input for one render request."""

    options: RenderOptions
    branding: InstitutionBranding | None = None
    theme: Theme = Theme()
    localization: Localization = Localization()
    page_settings: PageSettings = PageSettings()
    assets: AssetCatalog = AssetCatalog()
