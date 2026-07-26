"""Immutable font-family and text-style presentation definitions."""

from __future__ import annotations

from dataclasses import dataclass

from .contracts import require_name


@dataclass(frozen=True, slots=True)
class FontFamily:
    """One logical font family with ordered fallback names."""

    name: str
    fallbacks: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not self.name.strip():
            raise ValueError("font family name must not be empty")
        if any(not item.strip() for item in self.fallbacks):
            raise ValueError("font family fallbacks must not be empty")


@dataclass(frozen=True, slots=True)
class TextStyle:
    """Reusable logical typography for one class of text."""

    family: str
    size_pt: float
    weight: int = 400
    italic: bool = False
    color: str | None = None
    line_spacing: float | None = None
    paragraph_before_pt: float = 0.0
    paragraph_after_pt: float = 0.0

    def __post_init__(self) -> None:
        require_name(self.family, label="font family reference")
        if self.size_pt <= 0:
            raise ValueError("font size must be positive")
        if self.weight < 100 or self.weight > 900:
            raise ValueError("font weight must be between 100 and 900")
        if self.line_spacing is not None and self.line_spacing <= 0:
            raise ValueError("line spacing must be positive")
        if self.paragraph_before_pt < 0 or self.paragraph_after_pt < 0:
            raise ValueError("paragraph spacing must not be negative")


@dataclass(frozen=True, slots=True)
class ThemeTypography:
    """Font catalog and named body, heading, caption, code, and table styles."""

    families: tuple[tuple[str, FontFamily], ...] = ()
    body: TextStyle | None = None
    headings: tuple[tuple[str, TextStyle], ...] = ()
    caption: TextStyle | None = None
    code: TextStyle | None = None
    table: TextStyle | None = None

    def __post_init__(self) -> None:
        families = tuple(sorted(self.families))
        headings = tuple(sorted(self.headings))
        self._require_unique(families, "font family")
        self._require_unique(headings, "heading")
        for name, _ in (*families, *headings):
            require_name(name)
        known = {name for name, _ in families}
        for style in (
            self.body,
            *(style for _, style in headings),
            self.caption,
            self.code,
            self.table,
        ):
            if style is not None and style.family not in known:
                raise ValueError(f"unknown font family reference: {style.family!r}")
        object.__setattr__(self, "families", families)
        object.__setattr__(self, "headings", headings)

    @staticmethod
    def _require_unique(values: tuple[tuple[str, object], ...], label: str) -> None:
        names = tuple(name for name, _ in values)
        if len(names) != len(set(names)):
            raise ValueError(f"duplicate {label} name")
