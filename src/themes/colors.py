"""Immutable semantic color-palette definitions."""

from __future__ import annotations

import re
from dataclasses import dataclass

from .contracts import require_name


_COLOR = re.compile(r"#[0-9A-Fa-f]{6}(?:[0-9A-Fa-f]{2})?")


def _color(value: str, name: str) -> str:
    if _COLOR.fullmatch(value) is None:
        raise ValueError(f"invalid {name} color: {value!r}")
    return value.upper()


@dataclass(frozen=True, slots=True)
class ThemePalette:
    """Semantic colors plus print-safe and high-contrast variants."""

    primary: str | None = None
    secondary: str | None = None
    accent: str | None = None
    warning: str | None = None
    success: str | None = None
    error: str | None = None
    neutral: str | None = None
    print_safe: tuple[tuple[str, str], ...] = ()
    high_contrast: tuple[tuple[str, str], ...] = ()

    def __post_init__(self) -> None:
        for field in (
            "primary", "secondary", "accent", "warning",
            "success", "error", "neutral",
        ):
            value = getattr(self, field)
            if value is not None:
                object.__setattr__(self, field, _color(value, field))
        object.__setattr__(
            self, "print_safe", self._variant(self.print_safe, "print-safe")
        )
        object.__setattr__(
            self,
            "high_contrast",
            self._variant(self.high_contrast, "high-contrast"),
        )

    @staticmethod
    def _variant(
        values: tuple[tuple[str, str], ...], label: str
    ) -> tuple[tuple[str, str], ...]:
        result = tuple(
            sorted((require_name(name), _color(value, name)) for name, value in values)
        )
        names = tuple(name for name, _ in result)
        if len(names) != len(set(names)):
            raise ValueError(f"duplicate {label} palette color")
        return result
