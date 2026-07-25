"""Academic Calendar domain object and calendar-owned value objects.

An Academic Calendar describes institutional dates and availability.  It does
not contain curriculum, place Sessions, resolve constraints, or create a
schedule.
"""

from dataclasses import dataclass
from datetime import date, time
from uuid import UUID

from .base import TEOSObject, require_identity, require_version
from .lifecycle import AvailabilityStatus, LifecycleStatus
from .metadata import LocalizedString, Metadata, Organization
from .references import DocumentReference


@dataclass(frozen=True, slots=True)
class AcademicYear:
    """An institution-owned academic-year label and inclusive date range."""

    label: str
    start_date: date
    end_date: date

    def __post_init__(self) -> None:
        """Require a label and a non-reversed local date range."""
        if not self.label:
            raise ValueError("academic year label cannot be empty")
        if self.end_date < self.start_date:
            raise ValueError("academic year end date cannot precede start date")


@dataclass(frozen=True, slots=True)
class Term:
    """An academic period that organizes dates without organizing curriculum."""

    term_id: str
    title: LocalizedString
    start_date: date
    end_date: date
    classification: str
    overlap_relationship: LocalizedString | None = None

    def __post_init__(self) -> None:
        """Require local identity and a non-reversed date range."""
        if not self.term_id or not self.classification:
            raise ValueError("term identity and classification cannot be empty")
        if self.end_date < self.start_date:
            raise ValueError("term end date cannot precede start date")


@dataclass(frozen=True, slots=True)
class InstructionalDay:
    """An explicit availability fact for a date or named period."""

    date: date
    availability: AvailabilityStatus
    term_id: str | None = None
    instructional_period_ids: tuple[str, ...] = ()
    special_schedule_id: str | None = None
    condition: LocalizedString | None = None


@dataclass(frozen=True, slots=True)
class Holiday:
    """A named holiday date fact without operation-specific handling logic."""

    holiday_id: str
    name: LocalizedString
    date: date
    classification: str
    availability: AvailabilityStatus

    def __post_init__(self) -> None:
        """Require local holiday identity and classification."""
        if not self.holiday_id or not self.classification:
            raise ValueError("holiday identity and classification cannot be empty")


@dataclass(frozen=True, slots=True)
class Closure:
    """A bounded interval of institutional unavailability."""

    closure_id: str
    start_date: date
    end_date: date
    scope: LocalizedString
    reason: LocalizedString

    def __post_init__(self) -> None:
        """Require local identity and a non-reversed date range."""
        if not self.closure_id:
            raise ValueError("closure identifier cannot be empty")
        if self.end_date < self.start_date:
            raise ValueError("closure end date cannot precede start date")


@dataclass(frozen=True, slots=True)
class SpecialSchedule:
    """A date-specific availability exception with explicit precedence."""

    special_schedule_id: str
    date: date
    title: LocalizedString
    availability: AvailabilityStatus
    precedence: int
    instructional_period_ids: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        """Require local identity and non-negative precedence."""
        if not self.special_schedule_id:
            raise ValueError("special schedule identifier cannot be empty")
        if isinstance(self.precedence, bool) or self.precedence < 0:
            raise ValueError("special schedule precedence cannot be negative")


@dataclass(frozen=True, slots=True)
class InstructionalPeriod:
    """A named institution-owned operating period independent of curriculum."""

    instructional_period_id: str
    title: LocalizedString
    start_time: time
    end_time: time

    def __post_init__(self) -> None:
        """Require the period's local identifier."""
        if not self.instructional_period_id:
            raise ValueError("instructional period identifier cannot be empty")


@dataclass(frozen=True, slots=True)
class DateAnnotation:
    """A non-curriculum institution annotation attached to a date."""

    date: date
    annotation: LocalizedString


@dataclass(frozen=True, slots=True, kw_only=True)
class AcademicCalendar(TEOSObject):
    """A versioned institution-owned calendar and availability contract."""

    academic_calendar_id: UUID
    version: str
    owner: Organization
    academic_year: AcademicYear
    terms: tuple[Term, ...]
    instructional_days: tuple[InstructionalDay, ...]
    time_zone: str
    lifecycle_status: LifecycleStatus
    holidays: tuple[Holiday, ...] = ()
    closures: tuple[Closure, ...] = ()
    special_schedules: tuple[SpecialSchedule, ...] = ()
    instructional_periods: tuple[InstructionalPeriod, ...] = ()
    date_annotations: tuple[DateAnnotation, ...] = ()
    source: DocumentReference | None = None
    maintainer: Organization | None = None
    revision_notes: str | None = None
    metadata: Metadata | None = None

    def __post_init__(self) -> None:
        """Check identity, version, and required time-zone invariants."""
        require_identity(self.academic_calendar_id)
        require_version(self.version)
        if not self.time_zone:
            raise ValueError("academic calendar time zone cannot be empty")

    @property
    def teos_id(self) -> UUID:
        """Return the Academic Calendar identity."""
        return self.academic_calendar_id

    @property
    def teos_version(self) -> str:
        """Return the Academic Calendar version."""
        return self.version

    @property
    def lifecycle(self) -> LifecycleStatus:
        """Return the Academic Calendar lifecycle."""
        return self.lifecycle_status

    @property
    def object_metadata(self) -> Metadata | None:
        """Return non-authoritative Academic Calendar metadata."""
        return self.metadata

    def display_name(self) -> str:
        """Return the institution-approved academic-year label."""
        return self.academic_year.label
