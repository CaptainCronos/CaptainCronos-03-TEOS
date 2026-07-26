"""Deterministic locale-aware presentation formatting."""

from __future__ import annotations

from datetime import date, datetime, time
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from .exceptions import FormattingError
from .locale import CurrencyFormat, DocumentConventions


_ROMAN = (
    (1000, "M"),
    (900, "CM"),
    (500, "D"),
    (400, "CD"),
    (100, "C"),
    (90, "XC"),
    (50, "L"),
    (40, "XL"),
    (10, "X"),
    (9, "IX"),
    (5, "V"),
    (4, "IV"),
    (1, "I"),
)


class LocaleFormatter:
    """Format presentation values using one immutable convention set."""

    __slots__ = ("conventions",)

    def __init__(self, conventions: DocumentConventions) -> None:
        self.conventions = conventions

    def format_date(self, value: date | datetime) -> str:
        """Format a date with the configured calendar pattern."""
        if not isinstance(value, (date, datetime)):
            raise FormattingError("date formatting requires a date value")
        return value.strftime(self.conventions.date_pattern)

    def format_time(
        self,
        value: time | datetime,
        *,
        time_zone: str | None = None,
    ) -> str:
        """Format a time, optionally converting an aware datetime."""
        if isinstance(value, datetime) and time_zone is not None:
            value = self.convert_time_zone(value, time_zone)
        if not isinstance(value, (time, datetime)):
            raise FormattingError("time formatting requires a time value")
        return value.strftime(self.conventions.time_pattern)

    def format_datetime(
        self, value: datetime, *, time_zone: str | None = None
    ) -> str:
        """Format date and time in the selected zone."""
        selected = (
            self.convert_time_zone(value, time_zone or self.conventions.default_time_zone)
            if value.tzinfo is not None
            else value
        )
        return f"{self.format_date(selected)} {self.format_time(selected)}"

    def convert_time_zone(self, value: datetime, time_zone: str) -> datetime:
        """Convert an aware datetime through the standard IANA zone database."""
        if value.tzinfo is None or value.utcoffset() is None:
            raise FormattingError("time-zone conversion requires an aware datetime")
        try:
            zone = ZoneInfo(time_zone)
        except ZoneInfoNotFoundError as error:
            raise FormattingError(f"unknown time zone: {time_zone!r}") from error
        return value.astimezone(zone)

    def format_number(
        self,
        value: int | float | Decimal | str,
        *,
        decimal_places: int | None = None,
        grouping: bool = True,
    ) -> str:
        """Format a finite decimal using configured digits and separators."""
        decimal = self._decimal(value)
        if decimal_places is None:
            plain = format(decimal, "f")
        else:
            if decimal_places < 0 or decimal_places > 12:
                raise FormattingError("decimal places must be between 0 and 12")
            quantum = Decimal(1).scaleb(-decimal_places)
            plain = format(decimal.quantize(quantum, rounding=ROUND_HALF_UP), "f")
        integer, dot, fraction = plain.partition(".")
        sign = ""
        if integer.startswith("-"):
            sign, integer = "-", integer[1:]
        if grouping:
            groups: list[str] = []
            while integer:
                groups.append(integer[-3:])
                integer = integer[:-3]
            integer = self.conventions.thousands_separator.join(reversed(groups))
        result = sign + integer
        if dot:
            result += self.conventions.decimal_separator + fraction
        return self._localize_digits(result)

    def format_percentage(
        self,
        value: int | float | Decimal | str,
        *,
        decimal_places: int = 0,
    ) -> str:
        """Format a fractional numeric value as a percentage."""
        return self.format_number(
            self._decimal(value) * Decimal(100),
            decimal_places=decimal_places,
        ) + "%"

    def format_currency(
        self,
        value: int | float | Decimal | str,
        currency: str | None = None,
    ) -> str:
        """Format a monetary amount using resource currency metadata."""
        code = (currency or self.conventions.default_currency).upper()
        definition = next(
            (item for item in self.conventions.currencies if item.code == code),
            CurrencyFormat(code, code),
        )
        number = self.format_number(
            value, decimal_places=definition.decimal_places
        )
        separator = " " if definition.space else ""
        if definition.symbol_position == "before":
            return definition.symbol + separator + number
        return number + separator + definition.symbol

    def format_page_number(self, value: int, *, style: str = "decimal") -> str:
        """Format a positive page number using decimal or Roman style."""
        if not isinstance(value, int) or value <= 0:
            raise FormattingError("page number must be a positive integer")
        if style == "decimal":
            return self._localize_digits(str(value))
        if style not in {"roman", "ROMAN"} or value > 3999:
            raise FormattingError(f"unsupported page numbering style: {style!r}")
        remainder = value
        parts: list[str] = []
        for amount, symbol in _ROMAN:
            count, remainder = divmod(remainder, amount)
            parts.append(symbol * count)
        result = "".join(parts)
        return result.lower() if style == "roman" else result

    def format_measurement(
        self,
        value: int | float | Decimal | str,
        unit: str,
        *,
        decimal_places: int | None = None,
    ) -> str:
        """Format a measurement with a locale-owned unit label."""
        labels = dict(self.conventions.unit_labels)
        return (
            self.format_number(value, decimal_places=decimal_places)
            + " "
            + labels.get(unit, unit)
        )

    def quote(self, text: str, *, secondary: bool = False) -> str:
        """Wrap text in the configured quotation marks."""
        opening, closing = (
            self.conventions.secondary_quotes
            if secondary
            else self.conventions.primary_quotes
        )
        return opening + text + closing

    @staticmethod
    def _decimal(value: int | float | Decimal | str) -> Decimal:
        try:
            result = Decimal(str(value))
        except (InvalidOperation, ValueError) as error:
            raise FormattingError(f"invalid numeric value: {value!r}") from error
        if not result.is_finite():
            raise FormattingError("numeric value must be finite")
        return result

    def _localize_digits(self, value: str) -> str:
        return value.translate(str.maketrans("0123456789", self.conventions.numbering_digits))
