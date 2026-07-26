"""Immutable translated-message values and safe interpolation."""

from __future__ import annotations

from dataclasses import dataclass
from string import Formatter
from typing import Any, Mapping

from .contracts import require_translation_key
from .exceptions import TranslationError


@dataclass(frozen=True, slots=True)
class Translation:
    """A singular message or category-indexed plural message."""

    key: str
    forms: tuple[tuple[str, str], ...]

    def __post_init__(self) -> None:
        require_translation_key(self.key)
        categories = tuple(category for category, _ in self.forms)
        if not self.forms or len(categories) != len(set(categories)):
            raise TranslationError(
                f"translation {self.key!r} has missing or duplicate forms"
            )
        if any(not category or not text for category, text in self.forms):
            raise TranslationError(
                f"translation {self.key!r} contains an empty form"
            )
        if len(self.forms) > 1 and "other" not in categories:
            raise TranslationError(
                f"plural translation {self.key!r} requires an 'other' form"
            )
        object.__setattr__(self, "forms", tuple(sorted(self.forms)))

    @classmethod
    def singular(cls, key: str, text: str) -> "Translation":
        """Create a non-plural translation."""
        return cls(key, (("other", text),))

    def select(self, category: str = "other") -> str:
        """Select a category and deterministically fall back to ``other``."""
        values = dict(self.forms)
        return values.get(category, values.get("other", next(iter(values.values()))))

    def render(self, category: str, parameters: Mapping[str, Any]) -> str:
        """Interpolate named fields after rejecting missing parameters."""
        template = self.select(category)
        required = {
            field_name
            for _, field_name, _, _ in Formatter().parse(template)
            if field_name
        }
        missing = required.difference(parameters)
        if missing:
            raise TranslationError(
                f"translation {self.key!r} is missing parameters: "
                + ", ".join(sorted(missing))
            )
        try:
            return template.format_map(dict(parameters))
        except (KeyError, ValueError, IndexError) as error:
            raise TranslationError(
                f"translation {self.key!r} could not be formatted"
            ) from error
