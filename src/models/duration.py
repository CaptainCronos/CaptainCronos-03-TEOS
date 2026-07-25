"""Immutable instructional-duration values.

Durations represent quantities only; they do not assign calendar dates,
meeting periods, or scheduled occurrences.
"""

from dataclasses import dataclass
from decimal import Decimal

from .lifecycle import DurationUnit


@dataclass(frozen=True, slots=True)
class Duration:
    """A positive quantity of instructional or preparation time."""

    value: int | float | Decimal
    unit: DurationUnit

    def __post_init__(self) -> None:
        """Reject non-positive quantities, the value object's local invariant."""
        if isinstance(self.value, bool) or self.value <= 0:
            raise ValueError("duration value must be positive")
