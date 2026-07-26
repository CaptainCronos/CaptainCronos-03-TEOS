"""Declarative, data-driven plural-category selection."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, InvalidOperation

from .exceptions import TranslationError


@dataclass(frozen=True, slots=True)
class PluralOperands:
    """CLDR-style numeric operands used by plural conditions."""

    n: Decimal
    i: int
    v: int
    f: int

    @classmethod
    def from_value(cls, value: int | float | Decimal | str) -> "PluralOperands":
        """Create stable operands without binary floating-point comparisons."""
        try:
            decimal = Decimal(str(value)).copy_abs()
        except (InvalidOperation, ValueError) as error:
            raise TranslationError(f"invalid plural count: {value!r}") from error
        if not decimal.is_finite():
            raise TranslationError("plural count must be finite")
        plain = format(decimal, "f")
        fraction = plain.partition(".")[2].rstrip("0")
        return cls(
            n=decimal,
            i=int(decimal),
            v=len(fraction),
            f=int(fraction or "0"),
        )


@dataclass(frozen=True, slots=True)
class PluralCondition:
    """One declarative comparison in a plural-category rule."""

    operand: str
    ranges: tuple[tuple[int, int], ...]
    modulus: int | None = None
    negated: bool = False

    def __post_init__(self) -> None:
        if self.operand not in {"n", "i", "v", "f"}:
            raise TranslationError(f"unsupported plural operand: {self.operand!r}")
        if self.modulus is not None and self.modulus <= 0:
            raise TranslationError("plural modulus must be positive")
        if not self.ranges or any(
            start > end or start < 0 for start, end in self.ranges
        ):
            raise TranslationError("plural ranges must be non-empty and ascending")

    def matches(self, operands: PluralOperands) -> bool:
        """Return whether numeric operands satisfy this condition."""
        value = getattr(operands, self.operand)
        if self.modulus is not None:
            value %= self.modulus
        matched = any(Decimal(start) <= value <= Decimal(end) for start, end in self.ranges)
        return not matched if self.negated else matched


@dataclass(frozen=True, slots=True)
class PluralCase:
    """One category with OR groups containing AND conditions."""

    category: str
    any_of: tuple[tuple[PluralCondition, ...], ...]

    def __post_init__(self) -> None:
        if not self.category or self.category == "other":
            raise TranslationError("explicit plural cases require a named non-other category")
        if not self.any_of or any(not group for group in self.any_of):
            raise TranslationError("plural cases require non-empty condition groups")

    def matches(self, operands: PluralOperands) -> bool:
        """Return whether any conjunction matches."""
        return any(
            all(condition.matches(operands) for condition in group)
            for group in self.any_of
        )


@dataclass(frozen=True, slots=True)
class PluralRule:
    """Ordered declarative plural cases with an implicit ``other`` fallback."""

    cases: tuple[PluralCase, ...] = ()

    def __post_init__(self) -> None:
        categories = tuple(case.category for case in self.cases)
        if len(categories) != len(set(categories)):
            raise TranslationError("plural rule categories must be unique")

    def select(self, value: int | float | Decimal | str) -> str:
        """Select the first matching category, otherwise ``other``."""
        operands = PluralOperands.from_value(value)
        for case in self.cases:
            if case.matches(operands):
                return case.category
        return "other"


ENGLISH_PLURAL_RULE = PluralRule(
    (
        PluralCase(
            "one",
            (
                (
                    PluralCondition("i", ((1, 1),)),
                    PluralCondition("v", ((0, 0),)),
                ),
            ),
        ),
    )
)
