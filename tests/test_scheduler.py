"""Scheduling Engine behavior, constraints, and immutability tests."""

from __future__ import annotations

from dataclasses import FrozenInstanceError, replace
from datetime import date, time, timedelta
from uuid import UUID

import pytest

from src.compiler import compile_repository
from src.models import (
    AcademicCalendar,
    Course,
    InstitutionProfile,
    InstructionalUnit,
    Session,
)
from src.models.academic_calendar import (
    AcademicYear,
    Closure,
    Holiday,
    InstructionalDay,
    InstructionalPeriod,
    SpecialSchedule,
    Term,
)
from src.models.course import CompletionRequirement
from src.models.duration import Duration
from src.models.institution_profile import (
    InstitutionInformation,
    MeetingPattern,
)
from src.models.lifecycle import (
    AvailabilityStatus,
    DurationUnit,
    LifecycleStatus,
    SessionType,
    Weekday,
)
from src.models.metadata import LocalizedString, Organization
from src.models.references import (
    AcademicCalendarReference,
    CourseReference,
    InstructionalUnitReference,
    SessionReference,
)
from src.models.session import SessionDependency
from src.repository import ObjectRegistry, Repository
from src.scheduler import (
    CalendarConfigurationError,
    CalendarReferenceError,
    ScheduleValidationError,
    ScheduleValidator,
    ScheduledRepository,
    Scheduler,
    SchedulingContext,
)


OWNER = Organization(
    identifier="scheduler-owner",
    name=LocalizedString("Scheduler Test Institution"),
)
START = date(2026, 1, 5)


def identifier(number: int) -> UUID:
    """Return a stable fixture UUID."""
    return UUID(int=number)


def session(number: int, prerequisite: int | None = None) -> Session:
    """Create a one-period schedulable Session."""
    dependencies = (
        (
            SessionDependency(
                SessionReference(
                    identifier=identifier(prerequisite), version="1.0.0"
                ),
                "must precede",
            ),
        )
        if prerequisite is not None
        else ()
    )
    return Session(
        session_id=identifier(number),
        version="1.0.0",
        owner=OWNER,
        session_title=LocalizedString(f"Session {number}"),
        session_type=SessionType.THEORY,
        duration=Duration(1, DurationUnit.HOURS),
        learning_objectives=(LocalizedString("Learn"),),
        competency_references=(),
        lifecycle_status=LifecycleStatus.APPROVED,
        prerequisite_session_references=dependencies,
    )


def unit(number: int, session_numbers: tuple[int, ...]) -> InstructionalUnit:
    """Create a Unit with an explicit Session declaration order."""
    return InstructionalUnit(
        instructional_unit_id=identifier(number),
        version="1.0.0",
        owner=OWNER,
        title=LocalizedString(f"Unit {number}"),
        description=LocalizedString("Unit"),
        included_competency_references=(),
        learning_objectives=(LocalizedString("Complete"),),
        session_references=tuple(
            SessionReference(identifier=identifier(item), version="1.0.0")
            for item in session_numbers
        ),
        estimated_duration=Duration(len(session_numbers), DurationUnit.HOURS),
        assessment_strategy=(),
        lifecycle_status=LifecycleStatus.APPROVED,
    )


def course(
    number: int, unit_number: int, prerequisite: int | None = None
) -> Course:
    """Create a Course with an optional Course prerequisite."""
    prerequisite_courses = (
        (
            CourseReference(
                identifier=identifier(prerequisite), version="1.0.0"
            ),
        )
        if prerequisite is not None
        else ()
    )
    return Course(
        course_id=identifier(number),
        version="1.0.0",
        owner=OWNER,
        title=LocalizedString(f"Course {number}"),
        description=LocalizedString("Course"),
        instructional_unit_references=(
            InstructionalUnitReference(
                identifier=identifier(unit_number), version="1.0.0"
            ),
        ),
        completion_requirements=(
            CompletionRequirement("completion", LocalizedString("Complete")),
        ),
        estimated_instructional_hours=Duration(2, DurationUnit.HOURS),
        lifecycle_status=LifecycleStatus.APPROVED,
        prerequisite_course_references=prerequisite_courses,
    )


def scheduling_sources(
    *,
    day_count: int = 8,
    wrong_reference: bool = False,
    unknown_period: bool = False,
    special_schedules: tuple[SpecialSchedule, ...] = (),
) -> tuple[InstitutionProfile, AcademicCalendar]:
    """Create compatible institution and calendar fixtures."""
    calendar_id = identifier(900)
    reference_id = identifier(901) if wrong_reference else calendar_id
    profile = InstitutionProfile(
        institution_profile_id=identifier(800),
        version="1.0.0",
        institution_information=InstitutionInformation(
            institution_identifier="test",
            display_name=LocalizedString("Test Institution"),
            owner=OWNER,
            time_zone="America/New_York",
        ),
        academic_calendar_references=(
            AcademicCalendarReference(
                identifier=reference_id, version="1.0.0"
            ),
        ),
        meeting_patterns=(
            MeetingPattern(
                meeting_pattern_id="morning",
                title=LocalizedString("Morning"),
                time_zone="America/New_York",
                eligible_weekdays=(
                    Weekday.MONDAY,
                    Weekday.TUESDAY,
                    Weekday.WEDNESDAY,
                    Weekday.THURSDAY,
                    Weekday.FRIDAY,
                ),
                start_time=time(9),
                end_time=time(10),
                recurrence=LocalizedString("Weekdays"),
                compatible_session_types=(SessionType.THEORY,),
            ),
        ),
        lifecycle_status=LifecycleStatus.APPROVED,
    )
    days = tuple(
        InstructionalDay(
            date=START + timedelta(days=offset),
            availability=AvailabilityStatus.AVAILABLE,
            term_id="term-1",
            instructional_period_ids=(
                ("unknown",) if unknown_period and offset == 0 else ("p1",)
            ),
        )
        for offset in range(day_count)
    )
    calendar = AcademicCalendar(
        academic_calendar_id=calendar_id,
        version="1.0.0",
        owner=OWNER,
        academic_year=AcademicYear(
            "2025-2026", START, START + timedelta(days=30)
        ),
        terms=(
            Term(
                "term-1",
                LocalizedString("Term 1"),
                START,
                START + timedelta(days=30),
                "instructional",
            ),
        ),
        instructional_days=days,
        time_zone="America/New_York",
        lifecycle_status=LifecycleStatus.APPROVED,
        holidays=(
            Holiday(
                "holiday",
                LocalizedString("Holiday"),
                START + timedelta(days=1),
                "holiday",
                AvailabilityStatus.UNAVAILABLE,
            ),
        ),
        closures=(
            Closure(
                "closure",
                START + timedelta(days=2),
                START + timedelta(days=2),
                LocalizedString("Institution"),
                LocalizedString("Closed"),
            ),
        ),
        special_schedules=special_schedules,
        instructional_periods=(
            InstructionalPeriod(
                "p1", LocalizedString("Period 1"), time(9), time(10)
            ),
        ),
    )
    return profile, calendar


def compiled_fixture(
    *,
    multi_course: bool = False,
    day_count: int = 8,
    wrong_reference: bool = False,
    unknown_period: bool = False,
    special_schedules: tuple[SpecialSchedule, ...] = (),
):
    """Compile curriculum and its independent scheduling context."""
    first = session(10)
    second = session(11, prerequisite=10)
    first_unit = unit(20, (10, 11))
    first_course = course(30, 20)
    objects: list[object] = [second, first_course, first_unit, first]
    if multi_course:
        third = session(12)
        second_unit = unit(21, (12,))
        second_course = course(31, 21, prerequisite=30)
        objects.extend((second_course, third, second_unit))
    profile, calendar = scheduling_sources(
        day_count=day_count,
        wrong_reference=wrong_reference,
        unknown_period=unknown_period,
        special_schedules=special_schedules,
    )
    objects.extend((profile, calendar))
    if wrong_reference:
        objects.append(
            replace(calendar, academic_calendar_id=identifier(901))
        )
    repository = Repository(ObjectRegistry(tuple(objects)), ())
    return compile_repository(repository), profile, calendar


def test_single_course_scheduling_and_instructional_period() -> None:
    """A Course is placed into chronological eligible period containers."""
    compiled, profile, calendar = compiled_fixture()

    schedule = Scheduler().schedule(compiled, profile, calendar)

    assert schedule.is_complete
    assert len(schedule.courses) == 1
    assert tuple(
        item.source.source.teos_id for item in schedule.sessions
    ) == (identifier(10), identifier(11))
    assert tuple(
        item.placement.calendar_date for item in schedule.sessions
    ) == (START, START + timedelta(days=3))
    assert all(
        item.placement.instructional_period.instructional_period_id == "p1"
        for item in schedule.sessions
        if item.placement.instructional_period is not None
    )


def test_multi_course_and_course_prerequisite_order() -> None:
    """Prerequisite Courses and their Sessions occur before dependents."""
    compiled, profile, calendar = compiled_fixture(multi_course=True)

    schedule = Scheduler().schedule(compiled, profile, calendar)

    assert schedule.is_complete
    assert tuple(item.source.source.teos_id for item in schedule.courses) == (
        identifier(30),
        identifier(31),
    )
    assert tuple(item.source.source.teos_id for item in schedule.sessions) == (
        identifier(10),
        identifier(11),
        identifier(12),
    )


def test_holidays_closures_and_prerequisites_are_preserved() -> None:
    """Unavailable holidays and closures shift, never delete, curriculum."""
    compiled, profile, calendar = compiled_fixture()

    schedule = Scheduler().schedule(compiled, profile, calendar)

    dates = tuple(item.placement.calendar_date for item in schedule.sessions)
    assert START + timedelta(days=1) not in dates
    assert START + timedelta(days=2) not in dates
    assert (
        schedule.sessions[0].placement.meeting_sequence
        < schedule.sessions[1].placement.meeting_sequence
    )
    assert ScheduleValidator().validate(schedule) == ()


def test_special_schedule_precedence_restores_holiday_availability() -> None:
    """The highest-precedence explicit exception overrides holiday handling."""
    special = SpecialSchedule(
        "holiday-instruction",
        START + timedelta(days=1),
        LocalizedString("Instruction held"),
        AvailabilityStatus.AVAILABLE,
        10,
        ("p1",),
    )
    compiled, profile, calendar = compiled_fixture(
        special_schedules=(special,)
    )

    schedule = Scheduler().schedule(compiled, profile, calendar)

    assert schedule.sessions[1].placement.calendar_date == START + timedelta(
        days=1
    )
    assert schedule.sessions[1].placement.special_schedule is special


def test_calendar_and_reference_validation() -> None:
    """Invalid calendar periods and profile references fail before placement."""
    compiled, profile, calendar = compiled_fixture(wrong_reference=True)
    with pytest.raises(CalendarReferenceError):
        Scheduler().schedule(compiled, profile, calendar)

    compiled, profile, calendar = compiled_fixture(unknown_period=True)
    with pytest.raises(CalendarConfigurationError):
        Scheduler().schedule(compiled, profile, calendar)


def test_constraint_failures_detect_duplicates_dates_and_prerequisites() -> None:
    """Validation identifies independently constructed invalid schedules."""
    compiled, profile, calendar = compiled_fixture()
    schedule = Scheduler().schedule(compiled, profile, calendar)
    second = schedule.sessions[1]
    invalid_second = replace(
        second,
        placement=replace(
            second.placement,
            calendar_date=START + timedelta(days=20),
        ),
    )
    invalid = replace(
        schedule,
        sessions=(second, invalid_second),
        unscheduled_sessions=(),
    )

    violations = ScheduleValidator().validate(invalid)
    codes = tuple(item.code for item in violations)

    assert "duplicate-session" in codes
    assert "invalid-date" in codes
    assert "missing-prerequisite" in codes
    with pytest.raises(ScheduleValidationError):
        ScheduleValidator().validate_or_raise(invalid)


def test_unscheduled_required_sessions_are_explicit() -> None:
    """Capacity exhaustion creates an incomplete, diagnosable schedule."""
    compiled, profile, calendar = compiled_fixture(day_count=1)

    schedule = Scheduler().schedule(compiled, profile, calendar)

    assert not schedule.is_complete
    assert tuple(
        item.source.teos_id for item in schedule.unscheduled_sessions
    ) == (identifier(11),)
    assert {
        item.code for item in ScheduleValidator().validate(schedule)
    } == {"unscheduled-required-session"}


def test_scheduling_is_deterministic_repeatable_and_immutable() -> None:
    """Identical inputs produce equal frozen execution plans."""
    compiled, profile, calendar = compiled_fixture()
    scheduler = Scheduler()

    first = scheduler.schedule(compiled, profile, calendar)
    second = scheduler.schedule(compiled, profile, calendar)
    scheduled_repository = scheduler.schedule_repository(
        compiled, (SchedulingContext(profile, calendar),)
    )

    assert first == second
    assert isinstance(scheduled_repository, ScheduledRepository)
    assert scheduled_repository.institution_schedules == (first,)
    with pytest.raises(FrozenInstanceError):
        first.sessions[0].placement = first.sessions[0].placement  # type: ignore[misc]
    with pytest.raises(AttributeError):
        first.sessions.append(first.sessions[0])  # type: ignore[attr-defined]
