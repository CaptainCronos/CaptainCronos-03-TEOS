"""Immutable institution-owned academic calendar configuration."""

from dataclasses import dataclass
from datetime import date
from enum import StrEnum


class CalendarSystem(StrEnum):
    """Supported academic period organization systems."""

    SEMESTER = "semester"
    QUARTER = "quarter"
    TRIMESTER = "trimester"
    BLOCK = "block"


class CalendarDayKind(StrEnum):
    """Institution-owned calendar date classifications."""

    HOLIDAY = "holiday"
    BREAK = "break"
    INSTRUCTIONAL = "instructional"
    MAKE_UP = "make-up"


@dataclass(frozen=True, slots=True)
class AcademicPeriod:
    """Named academic period independent of curriculum sequencing."""

    identifier: str
    name: str
    start_date: date
    end_date: date

    def __post_init__(self) -> None:
        if not self.identifier or not self.name:
            raise ValueError("academic period identifier and name are required")
        if self.end_date < self.start_date:
            raise ValueError("academic period end date cannot precede start date")


@dataclass(frozen=True, slots=True)
class CalendarDay:
    """One explicit calendar fact or availability classification."""

    date: date
    kind: CalendarDayKind
    name: str | None = None


@dataclass(frozen=True, slots=True)
class AcademicCalendarProfile:
    """Versioned academic calendar facts assembled for a profile."""

    calendar_id: str
    version: str
    system: CalendarSystem
    periods: tuple[AcademicPeriod, ...]
    days: tuple[CalendarDay, ...] = ()
    metadata: tuple[tuple[str, str], ...] = ()

    def __post_init__(self) -> None:
        if not self.calendar_id or not self.version:
            raise ValueError("calendar identifier and version are required")
