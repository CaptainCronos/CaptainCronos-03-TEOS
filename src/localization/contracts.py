"""Shared immutable contracts for localization resources and diagnostics."""

from __future__ import annotations

import re
from dataclasses import dataclass
from enum import IntEnum, StrEnum

from .exceptions import LocaleError


FRAMEWORK_VERSION = "1.0.0"
RESOURCE_CONTRACT_VERSION = "1.0"

_LANGUAGE = re.compile(r"[A-Za-z]{2,3}")
_SCRIPT = re.compile(r"[A-Za-z]{4}")
_REGION = re.compile(r"(?:[A-Za-z]{2}|\d{3})")
_KEY = re.compile(r"[A-Za-z][A-Za-z0-9_-]*(?:\.[A-Za-z0-9_-]+)*")
_RESOURCE_ID = re.compile(
    r"[a-z0-9](?:[a-z0-9._-]*[a-z0-9])?"
)


class ResourceLayer(IntEnum):
    """Stable precedence of localization resource sources."""

    BUILTIN = 10
    DEFAULT = 20
    LANGUAGE = 30
    PLUGIN = 40
    INSTITUTION = 50


class PageDirection(StrEnum):
    """Supported page flow directions."""

    LEFT_TO_RIGHT = "ltr"
    RIGHT_TO_LEFT = "rtl"


class DateOrder(StrEnum):
    """Conventional ordering of numeric date components."""

    MONTH_DAY_YEAR = "mdy"
    DAY_MONTH_YEAR = "dmy"
    YEAR_MONTH_DAY = "ymd"


class HourCycle(StrEnum):
    """Supported civil-time display cycles."""

    HOUR_12 = "h12"
    HOUR_24 = "h24"


class MeasurementSystem(StrEnum):
    """Supported measurement-system labels."""

    METRIC = "metric"
    US = "us"
    UK = "uk"


class DiagnosticSeverity(StrEnum):
    """Severity of non-fatal localization validation findings."""

    WARNING = "warning"
    ERROR = "error"


@dataclass(frozen=True, slots=True)
class LocalizationDiagnostic:
    """One immutable validation or missing-content finding."""

    code: str
    severity: DiagnosticSeverity
    message: str
    resource_id: str | None = None
    key: str | None = None


def normalize_locale(value: str) -> str:
    """Validate and normalize a basic BCP 47 language identifier."""
    if not isinstance(value, str) or not value.strip():
        raise LocaleError("locale identifier must be a non-empty string")
    parts = value.replace("_", "-").split("-")
    if not _LANGUAGE.fullmatch(parts[0]):
        raise LocaleError(f"invalid locale identifier: {value!r}")
    normalized = [parts[0].lower()]
    seen_script = False
    seen_region = False
    for part in parts[1:]:
        if _SCRIPT.fullmatch(part) and not seen_script and not seen_region:
            normalized.append(part.title())
            seen_script = True
        elif _REGION.fullmatch(part) and not seen_region:
            normalized.append(part.upper())
            seen_region = True
        elif re.fullmatch(r"[A-Za-z0-9]{4,8}", part):
            normalized.append(part.lower())
        else:
            raise LocaleError(f"invalid locale identifier: {value!r}")
    return "-".join(normalized)


def locale_language(value: str) -> str:
    """Return the normalized primary language subtag."""
    return normalize_locale(value).split("-", 1)[0]


def require_translation_key(value: str) -> str:
    """Validate a stable translation key."""
    if not isinstance(value, str) or _KEY.fullmatch(value) is None:
        raise ValueError(f"invalid translation key: {value!r}")
    return value


def require_resource_id(value: str) -> str:
    """Validate a stable lowercase resource identifier."""
    if not isinstance(value, str) or _RESOURCE_ID.fullmatch(value) is None:
        raise ValueError(f"invalid resource identifier: {value!r}")
    return value
