"""Immutable locale, region, and document-convention definitions."""

from __future__ import annotations

import re
from dataclasses import dataclass
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from .contracts import (
    DateOrder,
    HourCycle,
    MeasurementSystem,
    PageDirection,
    locale_language,
    normalize_locale,
)
from .exceptions import LocaleError
from .language import Script


@dataclass(frozen=True, slots=True)
class Culture:
    """A named language-and-region cultural convention."""

    identifier: str
    name: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "identifier", normalize_locale(self.identifier))
        if not self.name.strip():
            raise LocaleError("culture name cannot be empty")


@dataclass(frozen=True, slots=True)
class Region:
    """A geographic region used by a locale."""

    code: str
    name: str

    def __post_init__(self) -> None:
        code = self.code.upper()
        if re.fullmatch(r"(?:[A-Z]{2}|\d{3})", code) is None:
            raise LocaleError(f"invalid region code: {self.code!r}")
        if not self.name.strip():
            raise LocaleError("region name cannot be empty")
        object.__setattr__(self, "code", code)


@dataclass(frozen=True, slots=True)
class CurrencyFormat:
    """Locale presentation metadata for one ISO-style currency."""

    code: str
    symbol: str
    symbol_position: str = "before"
    space: bool = False
    decimal_places: int = 2

    def __post_init__(self) -> None:
        code = self.code.upper()
        if re.fullmatch(r"[A-Z]{3}", code) is None:
            raise LocaleError(f"invalid currency code: {self.code!r}")
        if not self.symbol:
            raise LocaleError("currency symbol cannot be empty")
        if self.symbol_position not in {"before", "after"}:
            raise LocaleError("currency symbol position must be before or after")
        if not 0 <= self.decimal_places <= 6:
            raise LocaleError("currency decimal places must be between 0 and 6")
        object.__setattr__(self, "code", code)


@dataclass(frozen=True, slots=True)
class DocumentConventions:
    """All locale-owned formatting and physical-document conventions."""

    date_pattern: str = "%m/%d/%Y"
    time_pattern: str = "%I:%M %p"
    date_order: DateOrder = DateOrder.MONTH_DAY_YEAR
    hour_cycle: HourCycle = HourCycle.HOUR_12
    paper_size: str = "letter"
    measurement_system: MeasurementSystem = MeasurementSystem.US
    page_direction: PageDirection = PageDirection.LEFT_TO_RIGHT
    decimal_separator: str = "."
    thousands_separator: str = ","
    primary_quotes: tuple[str, str] = ("\u201c", "\u201d")
    secondary_quotes: tuple[str, str] = ("\u2018", "\u2019")
    numbering_digits: str = "0123456789"
    default_time_zone: str = "UTC"
    default_currency: str = "USD"
    currencies: tuple[CurrencyFormat, ...] = ()
    unit_labels: tuple[tuple[str, str], ...] = ()

    def __post_init__(self) -> None:
        if not self.date_pattern or not self.time_pattern:
            raise LocaleError("date and time patterns cannot be empty")
        if not self.paper_size or not self.default_time_zone:
            raise LocaleError("paper size and default time zone cannot be empty")
        if (
            len(self.decimal_separator) != 1
            or len(self.thousands_separator) != 1
            or self.decimal_separator == self.thousands_separator
        ):
            raise LocaleError("decimal and thousands separators must be distinct")
        if len(self.numbering_digits) != 10 or len(set(self.numbering_digits)) != 10:
            raise LocaleError("numbering digits must contain ten unique characters")
        if any(len(pair) != 2 or not all(pair) for pair in (
            self.primary_quotes,
            self.secondary_quotes,
        )):
            raise LocaleError("quotation styles require opening and closing marks")
        currency_codes = tuple(item.code for item in self.currencies)
        if len(currency_codes) != len(set(currency_codes)):
            raise LocaleError("currency definitions contain duplicate codes")
        unit_keys = tuple(key for key, _ in self.unit_labels)
        if len(unit_keys) != len(set(unit_keys)) or any(
            not key or not value for key, value in self.unit_labels
        ):
            raise LocaleError("unit labels must have unique non-empty values")
        default_currency = self.default_currency.upper()
        if re.fullmatch(r"[A-Z]{3}", default_currency) is None:
            raise LocaleError("default currency must be a three-letter code")
        if currency_codes and default_currency not in currency_codes:
            raise LocaleError("default currency requires a currency definition")
        try:
            ZoneInfo(self.default_time_zone)
        except ZoneInfoNotFoundError as error:
            raise LocaleError(
                f"unknown default time zone: {self.default_time_zone!r}"
            ) from error
        object.__setattr__(self, "default_currency", default_currency)
        object.__setattr__(
            self, "currencies", tuple(sorted(self.currencies, key=lambda item: item.code))
        )
        object.__setattr__(self, "unit_labels", tuple(sorted(self.unit_labels)))


@dataclass(frozen=True, slots=True)
class Locale:
    """A culture combining language, region, fallback, and conventions."""

    identifier: str
    language: str
    culture: Culture | str
    conventions: DocumentConventions = DocumentConventions()
    region: Region | None = None
    script: Script | str | None = None
    fallback: str | None = None

    def __post_init__(self) -> None:
        identifier = normalize_locale(self.identifier)
        language = self.language.lower()
        if locale_language(identifier) != language:
            raise LocaleError("locale language does not match its identifier")
        culture = (
            self.culture
            if isinstance(self.culture, Culture)
            else Culture(identifier, self.culture)
        )
        fallback = normalize_locale(self.fallback) if self.fallback else None
        if fallback == identifier:
            raise LocaleError("locale cannot fall back to itself")
        script = (
            self.script
            if isinstance(self.script, Script)
            else Script(self.script, direction=self.conventions.page_direction)
            if self.script is not None
            else None
        )
        object.__setattr__(self, "identifier", identifier)
        object.__setattr__(self, "language", language)
        object.__setattr__(self, "culture", culture)
        object.__setattr__(self, "fallback", fallback)
        object.__setattr__(self, "script", script)
