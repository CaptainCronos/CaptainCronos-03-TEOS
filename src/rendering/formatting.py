"""Immutable presentation formatting values without business rules."""

from dataclasses import dataclass

from .exceptions import FormattingError


@dataclass(frozen=True, slots=True)
class PageLayout:
    """Page-level flow and spacing settings."""

    columns: int = 1
    section_spacing_points: float = 12.0

    def __post_init__(self) -> None:
        """Require usable layout dimensions."""
        if self.columns < 1 or self.section_spacing_points < 0:
            raise FormattingError("page layout values must be non-negative")


@dataclass(frozen=True, slots=True)
class Typography:
    """Font families and sizes for a presentation."""

    body_family: str = "sans-serif"
    heading_family: str = "sans-serif"
    body_size_points: float = 11.0
    heading_scale: float = 1.25

    def __post_init__(self) -> None:
        """Require named fonts and positive sizes."""
        if not self.body_family or not self.heading_family:
            raise FormattingError("font family cannot be empty")
        if self.body_size_points <= 0 or self.heading_scale <= 0:
            raise FormattingError("typography sizes must be positive")


@dataclass(frozen=True, slots=True)
class HeaderFooterStyle:
    """Header and footer presentation settings."""

    show_header: bool = True
    show_footer: bool = True
    show_page_number: bool = True
    separator: str | None = None


@dataclass(frozen=True, slots=True)
class TableStyle:
    """Table presentation settings."""

    header_emphasis: bool = True
    alternating_rows: bool = False
    repeat_header: bool = True


@dataclass(frozen=True, slots=True)
class ImageStyle:
    """Image presentation settings."""

    max_width_percent: float = 100.0
    preserve_aspect_ratio: bool = True

    def __post_init__(self) -> None:
        """Require a useful relative width."""
        if not 0 < self.max_width_percent <= 100:
            raise FormattingError("image width must be in (0, 100]")


@dataclass(frozen=True, slots=True)
class CaptionStyle:
    """Caption placement and numbering settings."""

    position: str = "below"
    numbered: bool = False

    def __post_init__(self) -> None:
        """Restrict caption placement to stable choices."""
        if self.position not in {"above", "below"}:
            raise FormattingError("caption position must be above or below")


@dataclass(frozen=True, slots=True)
class ListStyle:
    """List indentation and marker settings."""

    unordered_marker: str = "bullet"
    ordered_marker: str = "decimal"
    indent_points: float = 18.0

    def __post_init__(self) -> None:
        """Require non-negative indentation."""
        if self.indent_points < 0:
            raise FormattingError("list indentation cannot be negative")


@dataclass(frozen=True, slots=True)
class BrandingStyle:
    """Placement of branding elements within an artifact."""

    logo_position: str = "header"
    display_institution_name: bool = True

    def __post_init__(self) -> None:
        """Restrict logo placement to presentation regions."""
        if self.logo_position not in {"header", "footer", "cover", "none"}:
            raise FormattingError("unsupported logo position")


@dataclass(frozen=True, slots=True)
class FormattingProfile:
    """Complete renderer-independent formatting configuration."""

    page_layout: PageLayout = PageLayout()
    typography: Typography = Typography()
    headers_and_footers: HeaderFooterStyle = HeaderFooterStyle()
    tables: TableStyle = TableStyle()
    images: ImageStyle = ImageStyle()
    captions: CaptionStyle = CaptionStyle()
    lists: ListStyle = ListStyle()
    branding: BrandingStyle = BrandingStyle()
