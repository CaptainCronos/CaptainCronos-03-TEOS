"""Immutable deterministic Scheduling Engine for compiled TEOS curriculum."""

from .calendar import CalendarSlot, SchedulingCalendar
from .constraints import (
    DEFAULT_CONSTRAINTS,
    CalendarConstraint,
    ConstraintViolation,
    DeclaredSequenceConstraint,
    DuplicatePlacementConstraint,
    InstitutionConstraint,
    PrerequisiteConstraint,
    RequiredSessionConstraint,
    ScheduleConstraint,
)
from .exceptions import (
    CalendarConfigurationError,
    CalendarReferenceError,
    SchedulerError,
    SchedulingInputError,
    ScheduleValidationError,
)
from .placement import Placement
from .schedule import InstitutionSchedule, Schedule
from .scheduled_course import ScheduledCourse
from .scheduled_instructional_unit import ScheduledInstructionalUnit
from .scheduled_repository import ScheduledRepository
from .scheduled_session import ScheduledSession
from .scheduler import Scheduler, SchedulingContext, schedule_repository
from .validator import ScheduleValidator, validate_schedule

__all__ = [
    "DEFAULT_CONSTRAINTS",
    "CalendarConfigurationError",
    "CalendarConstraint",
    "CalendarReferenceError",
    "CalendarSlot",
    "ConstraintViolation",
    "DeclaredSequenceConstraint",
    "DuplicatePlacementConstraint",
    "InstitutionSchedule",
    "InstitutionConstraint",
    "Placement",
    "PrerequisiteConstraint",
    "RequiredSessionConstraint",
    "Schedule",
    "ScheduleConstraint",
    "ScheduleValidationError",
    "ScheduleValidator",
    "ScheduledCourse",
    "ScheduledInstructionalUnit",
    "ScheduledRepository",
    "ScheduledSession",
    "Scheduler",
    "SchedulerError",
    "SchedulingCalendar",
    "SchedulingContext",
    "SchedulingInputError",
    "schedule_repository",
    "validate_schedule",
]
