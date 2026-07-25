"""Calendar integration and deterministic instructional-slot generation."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal
from collections.abc import Iterable

from src.models import AcademicCalendar, InstitutionProfile, Session
from src.models.academic_calendar import (
    AcademicYear,
    InstructionalDay,
    InstructionalPeriod,
    SpecialSchedule,
    Term,
)
from src.models.duration import Duration
from src.models.institution_profile import MeetingPattern
from src.models.lifecycle import (
    AvailabilityStatus,
    DurationUnit,
    SessionType,
    Weekday,
)

from .exceptions import CalendarConfigurationError, CalendarReferenceError
from .placement import Placement


_WEEKDAYS = (
    Weekday.MONDAY,
    Weekday.TUESDAY,
    Weekday.WEDNESDAY,
    Weekday.THURSDAY,
    Weekday.FRIDAY,
    Weekday.SATURDAY,
    Weekday.SUNDAY,
)


def duration_minutes(duration: Duration) -> Decimal:
    """Convert an approved curriculum duration to exact minutes."""
    value = Decimal(str(duration.value))
    if duration.unit is DurationUnit.HOURS:
        return value * Decimal(60)
    return value


@dataclass(frozen=True, slots=True)
class CalendarSlot:
    """One deterministic institution/calendar placement candidate."""

    placement: Placement
    capacity_minutes: Decimal
    compatible_session_types: tuple[SessionType, ...]

    def accepts(self, session: Session) -> bool:
        """Return whether the Session type and duration fit this slot."""
        compatible = self.compatible_session_types
        return (
            (not compatible or session.session_type in compatible)
            and duration_minutes(session.duration) <= self.capacity_minutes
        )


class SchedulingCalendar:
    """Validate and expose eligible slots for one profile/calendar pair."""

    def __init__(
        self,
        institution_profile: InstitutionProfile,
        academic_calendar: AcademicCalendar,
    ) -> None:
        self.institution_profile = institution_profile
        self.academic_calendar = academic_calendar
        self._validate()
        self._slots = self._build_slots()

    @property
    def slots(self) -> tuple[CalendarSlot, ...]:
        """Return eligible slots in deterministic chronological order."""
        return self._slots

    def _validate(self) -> None:
        calendar = self.academic_calendar
        profile = self.institution_profile
        referenced = any(
            reference.identifier == calendar.teos_id
            and reference.version == calendar.teos_version
            for reference in profile.academic_calendar_references
        )
        if not referenced:
            raise CalendarReferenceError(
                "institution profile does not reference selected calendar "
                f"{calendar.teos_id}@{calendar.teos_version}"
            )
        if (
            profile.institution_information.time_zone != calendar.time_zone
        ):
            raise CalendarConfigurationError(
                "institution profile and academic calendar time zones differ"
            )

        year = calendar.academic_year
        term_ids = self._unique_ids(
            (term.term_id for term in calendar.terms), "term"
        )
        period_ids = self._unique_ids(
            (
                period.instructional_period_id
                for period in calendar.instructional_periods
            ),
            "instructional period",
        )
        self._unique_ids(
            (
                pattern.meeting_pattern_id
                for pattern in profile.meeting_patterns
            ),
            "meeting pattern",
        )
        self._unique_ids(
            (
                schedule.special_schedule_id
                for schedule in calendar.special_schedules
            ),
            "special schedule",
        )
        self._unique_ids(
            (holiday.holiday_id for holiday in calendar.holidays),
            "holiday",
        )
        self._unique_ids(
            (closure.closure_id for closure in calendar.closures),
            "closure",
        )
        holiday_dates = tuple(
            holiday.date for holiday in calendar.holidays
        )
        if len(set(holiday_dates)) != len(holiday_dates):
            raise CalendarConfigurationError(
                "multiple holidays cannot define the same date"
            )

        for term in calendar.terms:
            self._require_in_year(term.start_date, year, "term start")
            self._require_in_year(term.end_date, year, "term end")
        for period in calendar.instructional_periods:
            if period.end_time <= period.start_time:
                raise CalendarConfigurationError(
                    "instructional period end must follow start: "
                    f"{period.instructional_period_id}"
                )
        for pattern in profile.meeting_patterns:
            if pattern.end_time <= pattern.start_time:
                raise CalendarConfigurationError(
                    "meeting pattern end must follow start: "
                    f"{pattern.meeting_pattern_id}"
                )

        seen_dates: set[date] = set()
        special_by_id = {
            special.special_schedule_id: special
            for special in calendar.special_schedules
        }
        for day in calendar.instructional_days:
            if day.date in seen_dates:
                raise CalendarConfigurationError(
                    f"duplicate instructional date: {day.date.isoformat()}"
                )
            seen_dates.add(day.date)
            self._require_in_year(day.date, year, "instructional date")
            if day.term_id is not None and day.term_id not in term_ids:
                raise CalendarConfigurationError(
                    f"unknown term on {day.date.isoformat()}: {day.term_id}"
                )
            self._require_periods(day.instructional_period_ids, period_ids)
            if day.special_schedule_id is not None:
                special = special_by_id.get(day.special_schedule_id)
                if special is None or special.date != day.date:
                    raise CalendarConfigurationError(
                        "instructional date references an unknown or "
                        "date-mismatched special schedule"
                    )

        for holiday in calendar.holidays:
            self._require_in_year(holiday.date, year, "holiday date")
        for closure in calendar.closures:
            self._require_in_year(
                closure.start_date, year, "closure start"
            )
            self._require_in_year(closure.end_date, year, "closure end")

        precedence_by_date: set[tuple[date, int]] = set()
        for special in calendar.special_schedules:
            self._require_in_year(special.date, year, "special schedule date")
            self._require_periods(
                special.instructional_period_ids, period_ids
            )
            key = (special.date, special.precedence)
            if key in precedence_by_date:
                raise CalendarConfigurationError(
                    "special schedules on one date cannot share precedence: "
                    f"{special.date.isoformat()} precedence {special.precedence}"
                )
            precedence_by_date.add(key)

    @staticmethod
    def _unique_ids(values: Iterable[str], label: str) -> set[str]:
        collected = tuple(values)
        if len(set(collected)) != len(collected):
            raise CalendarConfigurationError(f"duplicate {label} identifier")
        return set(collected)

    @staticmethod
    def _require_in_year(
        value: date, year: AcademicYear, label: str
    ) -> None:
        if not year.start_date <= value <= year.end_date:
            raise CalendarConfigurationError(
                f"{label} {value.isoformat()} is outside academic year"
            )

    @staticmethod
    def _require_periods(
        requested: tuple[str, ...], available: set[str]
    ) -> None:
        unknown = tuple(item for item in requested if item not in available)
        if unknown:
            raise CalendarConfigurationError(
                "unknown instructional period identifier(s): "
                + ", ".join(unknown)
            )
        if len(set(requested)) != len(requested):
            raise CalendarConfigurationError(
                "instructional period identifiers cannot repeat on one date"
            )

    def _build_slots(self) -> tuple[CalendarSlot, ...]:
        calendar = self.academic_calendar
        periods = {
            period.instructional_period_id: period
            for period in calendar.instructional_periods
        }
        specials = self._effective_specials()
        holidays = {holiday.date: holiday for holiday in calendar.holidays}
        slots: list[CalendarSlot] = []
        sequence = 0
        for day in sorted(calendar.instructional_days, key=lambda item: item.date):
            special = specials.get(day.date)
            closure = next(
                (
                    item
                    for item in calendar.closures
                    if item.start_date <= day.date <= item.end_date
                ),
                None,
            )
            holiday = holidays.get(day.date)
            availability = (
                special.availability if special is not None else day.availability
            )
            if closure is not None:
                continue
            if availability is not AvailabilityStatus.AVAILABLE:
                continue
            if (
                holiday is not None
                and holiday.availability is not AvailabilityStatus.AVAILABLE
                and special is None
            ):
                continue

            period_ids = (
                special.instructional_period_ids
                if special is not None
                and special.instructional_period_ids
                else day.instructional_period_ids
            )
            selected_periods: tuple[InstructionalPeriod | None, ...] = (
                tuple(
                    sorted(
                        (periods[item] for item in period_ids),
                        key=lambda item: (
                            item.start_time,
                            item.end_time,
                            item.instructional_period_id,
                        ),
                    )
                )
                if period_ids
                else (None,)
            )
            term = self._term_for(day)
            weekday = _WEEKDAYS[day.date.weekday()]
            for period in selected_periods:
                for pattern in sorted(
                    self.institution_profile.meeting_patterns,
                    key=lambda item: item.meeting_pattern_id,
                ):
                    if weekday not in pattern.eligible_weekdays:
                        continue
                    if not self._period_fits_pattern(period, pattern):
                        continue
                    sequence += 1
                    placement = Placement(
                        calendar_date=day.date,
                        academic_year=calendar.academic_year,
                        term=term,
                        instructional_period=period,
                        meeting_pattern=pattern,
                        meeting_sequence=sequence,
                        availability=availability,
                        holiday=holiday,
                        special_schedule=special,
                    )
                    slots.append(
                        CalendarSlot(
                            placement=placement,
                            capacity_minutes=self._capacity(period, pattern),
                            compatible_session_types=(
                                pattern.compatible_session_types
                            ),
                        )
                    )
        return tuple(slots)

    def _effective_specials(self) -> dict[date, SpecialSchedule]:
        effective: dict[date, SpecialSchedule] = {}
        for special in sorted(
            self.academic_calendar.special_schedules,
            key=lambda item: (item.date, item.precedence),
        ):
            effective[special.date] = special
        return effective

    def _term_for(self, day: InstructionalDay) -> Term | None:
        if day.term_id is not None:
            return next(
                term
                for term in self.academic_calendar.terms
                if term.term_id == day.term_id
            )
        matches = tuple(
            term
            for term in self.academic_calendar.terms
            if term.start_date <= day.date <= term.end_date
        )
        if len(matches) > 1:
            raise CalendarConfigurationError(
                "instructional date belongs to overlapping terms without an "
                f"explicit term identifier: {day.date.isoformat()}"
            )
        return matches[0] if matches else None

    @staticmethod
    def _period_fits_pattern(
        period: InstructionalPeriod | None,
        pattern: MeetingPattern,
    ) -> bool:
        return period is None or (
            pattern.start_time <= period.start_time
            and period.end_time <= pattern.end_time
        )

    @staticmethod
    def _capacity(
        period: InstructionalPeriod | None,
        pattern: MeetingPattern,
    ) -> Decimal:
        start = period.start_time if period is not None else pattern.start_time
        end = period.end_time if period is not None else pattern.end_time
        elapsed = datetime.combine(date.min, end) - datetime.combine(
            date.min, start
        )
        time_capacity = Decimal(str(elapsed.total_seconds())) / Decimal(60)
        if pattern.instructional_duration is None:
            return time_capacity
        return min(time_capacity, duration_minutes(pattern.instructional_duration))
