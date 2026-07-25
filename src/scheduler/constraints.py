"""Deterministic constraints over immutable institution schedules."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol
from uuid import UUID

from src.models.lifecycle import AvailabilityStatus, Weekday

from .calendar import duration_minutes
from .schedule import InstitutionSchedule


_WEEKDAYS = (
    Weekday.MONDAY,
    Weekday.TUESDAY,
    Weekday.WEDNESDAY,
    Weekday.THURSDAY,
    Weekday.FRIDAY,
    Weekday.SATURDAY,
    Weekday.SUNDAY,
)


@dataclass(frozen=True, slots=True)
class ConstraintViolation:
    """A stable, actionable schedule-constraint diagnostic."""

    code: str
    message: str
    session_id: UUID | None = None


class ScheduleConstraint(Protocol):
    """Interface implemented by deterministic schedule constraints."""

    def evaluate(
        self, schedule: InstitutionSchedule
    ) -> tuple[ConstraintViolation, ...]:
        """Return stable violations without mutating the schedule."""


class DuplicatePlacementConstraint:
    """Reject repeated Sessions and shared institutional time containers."""

    def evaluate(
        self, schedule: InstitutionSchedule
    ) -> tuple[ConstraintViolation, ...]:
        """Find duplicate Session and placement keys."""
        violations: list[ConstraintViolation] = []
        sessions: set[tuple[UUID, str]] = set()
        placements: dict[tuple[object, ...], UUID] = {}
        for scheduled in schedule.sessions:
            source = scheduled.source.source
            session_key = (source.teos_id, source.teos_version)
            if session_key in sessions:
                violations.append(
                    ConstraintViolation(
                        "duplicate-session",
                        f"Session {source.teos_id}@{source.teos_version} "
                        "is placed more than once",
                        source.teos_id,
                    )
                )
            sessions.add(session_key)
            placement = scheduled.placement
            placement_key = (
                placement.calendar_date,
                (
                    placement.instructional_period.instructional_period_id
                    if placement.instructional_period is not None
                    else (
                        placement.meeting_pattern.start_time,
                        placement.meeting_pattern.end_time,
                    )
                ),
            )
            previous = placements.get(placement_key)
            if previous is not None and previous != source.teos_id:
                violations.append(
                    ConstraintViolation(
                        "duplicate-placement",
                        "Sessions share calendar container "
                        f"{placement.calendar_date.isoformat()} "
                        f"{placement_key[1]}",
                        source.teos_id,
                    )
                )
            placements[placement_key] = source.teos_id
        return tuple(violations)


class CalendarConstraint:
    """Require placements to remain within selected calendar availability."""

    def evaluate(
        self, schedule: InstitutionSchedule
    ) -> tuple[ConstraintViolation, ...]:
        """Find invalid dates, periods, holidays, closures, and availability."""
        calendar = schedule.academic_calendar
        days = {day.date: day for day in calendar.instructional_days}
        periods = {
            period.instructional_period_id: period
            for period in calendar.instructional_periods
        }
        holidays = {holiday.date: holiday for holiday in calendar.holidays}
        effective_specials = {}
        for special in sorted(
            calendar.special_schedules,
            key=lambda item: (item.date, item.precedence),
        ):
            effective_specials[special.date] = special
        violations: list[ConstraintViolation] = []
        for scheduled in schedule.sessions:
            source = scheduled.source.source
            placement = scheduled.placement
            day = days.get(placement.calendar_date)
            if day is None:
                violations.append(
                    self._violation(
                        "invalid-date",
                        "placement date is not an instructional date",
                        source.teos_id,
                    )
                )
                continue
            special = effective_specials.get(placement.calendar_date)
            expected_availability = (
                special.availability
                if special is not None
                else day.availability
            )
            if placement.availability is not expected_availability:
                violations.append(
                    self._violation(
                        "calendar-availability-mismatch",
                        "placement availability differs from calendar state",
                        source.teos_id,
                    )
                )
            if expected_availability is not AvailabilityStatus.AVAILABLE:
                violations.append(
                    self._violation(
                        "calendar-unavailable",
                        "placement is not explicitly available",
                        source.teos_id,
                    )
                )
            if any(
                closure.start_date
                <= placement.calendar_date
                <= closure.end_date
                for closure in calendar.closures
            ):
                violations.append(
                    self._violation(
                        "closure-violation",
                        "placement falls within an institutional closure",
                        source.teos_id,
                    )
                )
            if placement.special_schedule != special:
                violations.append(
                    self._violation(
                        "special-schedule-precedence",
                        "placement does not use the effective special schedule",
                        source.teos_id,
                    )
                )
            holiday = holidays.get(placement.calendar_date)
            if placement.holiday != holiday:
                violations.append(
                    self._violation(
                        "holiday-context-mismatch",
                        "placement holiday context differs from calendar",
                        source.teos_id,
                    )
                )
            if (
                holiday is not None
                and holiday.availability is not AvailabilityStatus.AVAILABLE
                and special is None
            ):
                violations.append(
                    self._violation(
                        "holiday-violation",
                        "placement falls on an unavailable holiday",
                        source.teos_id,
                    )
                )
            period = placement.instructional_period
            if (
                period is not None
                and periods.get(period.instructional_period_id) != period
            ):
                violations.append(
                    self._violation(
                        "invalid-instructional-period",
                        "placement references an unknown instructional period",
                        source.teos_id,
                    )
                )
            if placement.academic_year != calendar.academic_year:
                violations.append(
                    self._violation(
                        "invalid-academic-year",
                        "placement academic year differs from calendar",
                        source.teos_id,
                    )
                )
            expected_term = (
                next(
                    (
                        term
                        for term in calendar.terms
                        if term.term_id == day.term_id
                    ),
                    None,
                )
                if day.term_id is not None
                else next(
                    (
                        term
                        for term in calendar.terms
                        if term.start_date
                        <= placement.calendar_date
                        <= term.end_date
                    ),
                    None,
                )
            )
            if placement.term != expected_term:
                violations.append(
                    self._violation(
                        "invalid-term",
                        "placement term differs from calendar",
                        source.teos_id,
                    )
                )
            permitted = (
                special.instructional_period_ids
                if special is not None
                and special.instructional_period_ids
                else day.instructional_period_ids
            )
            if (
                period is not None
                and permitted
                and period.instructional_period_id not in permitted
            ):
                violations.append(
                    self._violation(
                        "instructional-period-unavailable",
                        "instructional period is unavailable on placement date",
                        source.teos_id,
                    )
                )
        return tuple(violations)

    @staticmethod
    def _violation(
        code: str, message: str, session_id: UUID
    ) -> ConstraintViolation:
        return ConstraintViolation(code, message, session_id)


class InstitutionConstraint:
    """Require placements to satisfy selected institution meeting rules."""

    def evaluate(
        self, schedule: InstitutionSchedule
    ) -> tuple[ConstraintViolation, ...]:
        """Find invalid profile/calendar references and meeting containers."""
        profile = schedule.institution_profile
        calendar = schedule.academic_calendar
        violations: list[ConstraintViolation] = []
        if not any(
            reference.identifier == calendar.teos_id
            and reference.version == calendar.teos_version
            for reference in profile.academic_calendar_references
        ):
            violations.append(
                ConstraintViolation(
                    "invalid-calendar-reference",
                    "institution profile does not reference schedule calendar",
                )
            )
        patterns = {
            pattern.meeting_pattern_id: pattern
            for pattern in profile.meeting_patterns
        }
        for scheduled in schedule.sessions:
            source = scheduled.source.source
            placement = scheduled.placement
            pattern = patterns.get(
                placement.meeting_pattern.meeting_pattern_id
            )
            if pattern is None or pattern != placement.meeting_pattern:
                violations.append(
                    ConstraintViolation(
                        "invalid-meeting-pattern",
                        "placement does not use a declared meeting pattern",
                        source.teos_id,
                    )
                )
                continue
            weekday = _WEEKDAYS[placement.calendar_date.weekday()]
            if weekday not in pattern.eligible_weekdays:
                violations.append(
                    ConstraintViolation(
                        "meeting-pattern-weekday",
                        "placement weekday is not institutionally eligible",
                        source.teos_id,
                    )
                )
            if (
                pattern.compatible_session_types
                and source.session_type
                not in pattern.compatible_session_types
            ):
                violations.append(
                    ConstraintViolation(
                        "meeting-pattern-session-type",
                        "Session type is incompatible with meeting pattern",
                        source.teos_id,
                    )
                )
            period = placement.instructional_period
            if period is not None:
                capacity = (
                    period.end_time.hour * 60
                    + period.end_time.minute
                    - period.start_time.hour * 60
                    - period.start_time.minute
                )
                if duration_minutes(source.duration) > capacity:
                    violations.append(
                        ConstraintViolation(
                            "meeting-duration",
                            "Session duration exceeds instructional period",
                            source.teos_id,
                        )
                    )
            pattern_capacity = (
                duration_minutes(pattern.instructional_duration)
                if pattern.instructional_duration is not None
                else (
                    pattern.end_time.hour * 60
                    + pattern.end_time.minute
                    - pattern.start_time.hour * 60
                    - pattern.start_time.minute
                )
            )
            if duration_minutes(source.duration) > pattern_capacity:
                violations.append(
                    ConstraintViolation(
                        "meeting-pattern-duration",
                        "Session duration exceeds meeting-pattern capacity",
                        source.teos_id,
                    )
                )
        return tuple(violations)


class PrerequisiteConstraint:
    """Require every compiled Session prerequisite to occur first."""

    def evaluate(
        self, schedule: InstitutionSchedule
    ) -> tuple[ConstraintViolation, ...]:
        """Find missing and incorrectly ordered Session prerequisites."""
        positions = {
            (
                scheduled.source.source.teos_id,
                scheduled.source.source.teos_version,
            ): scheduled.placement.meeting_sequence
            for scheduled in schedule.sessions
        }
        violations: list[ConstraintViolation] = []
        for scheduled in schedule.sessions:
            source = scheduled.source.source
            position = scheduled.placement.meeting_sequence
            for prerequisite in scheduled.source.prerequisite_sessions:
                key = (prerequisite.teos_id, prerequisite.teos_version)
                prerequisite_position = positions.get(key)
                if prerequisite_position is None:
                    violations.append(
                        ConstraintViolation(
                            "missing-prerequisite",
                            f"required Session {prerequisite.teos_id}@"
                            f"{prerequisite.teos_version} is not scheduled",
                            source.teos_id,
                        )
                    )
                elif prerequisite_position >= position:
                    violations.append(
                        ConstraintViolation(
                            "prerequisite-order",
                            f"required Session {prerequisite.teos_id}@"
                            f"{prerequisite.teos_version} does not occur first",
                            source.teos_id,
                        )
                    )
            for dependent in scheduled.source.dependent_sessions:
                key = (dependent.teos_id, dependent.teos_version)
                dependent_position = positions.get(key)
                if dependent_position is None:
                    violations.append(
                        ConstraintViolation(
                            "missing-dependent-session",
                            f"dependent Session {dependent.teos_id}@"
                            f"{dependent.teos_version} is not scheduled",
                            source.teos_id,
                        )
                    )
                elif dependent_position <= position:
                    violations.append(
                        ConstraintViolation(
                            "dependent-session-order",
                            f"dependent Session {dependent.teos_id}@"
                            f"{dependent.teos_version} does not occur after "
                            "its source Session",
                            source.teos_id,
                        )
                    )

        unit_positions: dict[tuple[UUID, str], tuple[int, int]] = {}
        course_positions: dict[tuple[UUID, str], tuple[int, int]] = {}
        for course in schedule.courses:
            course_sequence: list[int] = []
            for unit in course.instructional_units:
                sequence = tuple(
                    session.placement.meeting_sequence
                    for session in unit.sessions
                )
                if sequence:
                    unit_positions[
                        (
                            unit.source.source.teos_id,
                            unit.source.source.teos_version,
                        )
                    ] = (min(sequence), max(sequence))
                    course_sequence.extend(sequence)
            if course_sequence:
                course_positions[
                    (
                        course.source.source.teos_id,
                        course.source.source.teos_version,
                    )
                ] = (min(course_sequence), max(course_sequence))

        for course in schedule.courses:
            course_key = (
                course.source.source.teos_id,
                course.source.source.teos_version,
            )
            current = course_positions.get(course_key)
            if current is not None:
                for prerequisite in course.source.prerequisite_courses:
                    prerequisite_position = course_positions.get(
                        (
                            prerequisite.teos_id,
                            prerequisite.teos_version,
                        )
                    )
                    if (
                        prerequisite_position is not None
                        and prerequisite_position[1] >= current[0]
                    ):
                        violations.append(
                            ConstraintViolation(
                                "prerequisite-course-order",
                                "prerequisite Course does not complete before "
                                f"Course {course.source.source.teos_id}",
                            )
                        )
            for unit in course.instructional_units:
                unit_key = (
                    unit.source.source.teos_id,
                    unit.source.source.teos_version,
                )
                current_unit = unit_positions.get(unit_key)
                if current_unit is None:
                    continue
                for prerequisite in (
                    unit.source.prerequisite_instructional_units
                ):
                    prerequisite_position = unit_positions.get(
                        (prerequisite.teos_id, prerequisite.teos_version)
                    )
                    if (
                        prerequisite_position is not None
                        and prerequisite_position[1] >= current_unit[0]
                    ):
                        violations.append(
                            ConstraintViolation(
                                "prerequisite-unit-order",
                                "prerequisite Unit does not complete before "
                                f"Unit {unit.source.source.teos_id}",
                            )
                        )
        return tuple(violations)


class DeclaredSequenceConstraint:
    """Preserve Course, Unit, and Session declaration order."""

    def evaluate(
        self, schedule: InstitutionSchedule
    ) -> tuple[ConstraintViolation, ...]:
        """Find scheduled children that contradict declared sequence."""
        violations: list[ConstraintViolation] = []
        for course in schedule.courses:
            previous_unit_end = 0
            for unit in course.instructional_units:
                positions = tuple(
                    session.placement.meeting_sequence
                    for session in unit.sessions
                )
                if positions != tuple(sorted(positions)):
                    violations.append(
                        ConstraintViolation(
                            "declared-session-order",
                            "scheduled Sessions contradict Unit declaration "
                            f"{unit.source.source.teos_id}",
                        )
                    )
                if positions and min(positions) <= previous_unit_end:
                    violations.append(
                        ConstraintViolation(
                            "declared-unit-order",
                            "scheduled Units contradict Course declaration "
                            f"{course.source.source.teos_id}",
                        )
                    )
                if positions:
                    previous_unit_end = max(positions)
        return tuple(violations)


class RequiredSessionConstraint:
    """Require all requested compiled Sessions to be placed."""

    def evaluate(
        self, schedule: InstitutionSchedule
    ) -> tuple[ConstraintViolation, ...]:
        """Report each explicitly unscheduled required Session."""
        scheduled = {
            (
                item.source.source.teos_id,
                item.source.source.teos_version,
            )
            for item in schedule.sessions
        }
        explicitly_unscheduled = {
            (item.source.teos_id, item.source.teos_version)
            for item in schedule.unscheduled_sessions
        }
        violations: list[ConstraintViolation] = []
        for session in schedule.source.sessions:
            key = (session.source.teos_id, session.source.teos_version)
            if key not in scheduled:
                state = (
                    "is unscheduled"
                    if key in explicitly_unscheduled
                    else "is absent from the schedule result"
                )
                violations.append(
                    ConstraintViolation(
                        "unscheduled-required-session",
                        f"required Session {session.source.teos_id}@"
                        f"{session.source.teos_version} {state}",
                        session.source.teos_id,
                    )
                )
            elif key in explicitly_unscheduled:
                violations.append(
                    ConstraintViolation(
                        "inconsistent-session-state",
                        f"Session {session.source.teos_id}@"
                        f"{session.source.teos_version} is both scheduled "
                        "and unscheduled",
                        session.source.teos_id,
                    )
                )
        return tuple(violations)


DEFAULT_CONSTRAINTS: tuple[ScheduleConstraint, ...] = (
    DuplicatePlacementConstraint(),
    CalendarConstraint(),
    InstitutionConstraint(),
    PrerequisiteConstraint(),
    DeclaredSequenceConstraint(),
    RequiredSessionConstraint(),
)
"""Default constraints evaluated in stable architectural order."""
