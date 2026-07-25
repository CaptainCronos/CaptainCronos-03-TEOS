"""Immutable institution-specific schedule aggregate."""

from __future__ import annotations

from dataclasses import dataclass

from src.compiler import CompiledRepository, CompiledSession
from src.models import AcademicCalendar, InstitutionProfile

from .scheduled_course import ScheduledCourse
from .scheduled_session import ScheduledSession


@dataclass(frozen=True, slots=True)
class InstitutionSchedule:
    """An immutable execution plan for one profile and calendar."""

    source: CompiledRepository
    institution_profile: InstitutionProfile
    academic_calendar: AcademicCalendar
    courses: tuple[ScheduledCourse, ...]
    sessions: tuple[ScheduledSession, ...]
    unscheduled_sessions: tuple[CompiledSession, ...] = ()

    @property
    def is_complete(self) -> bool:
        """Return whether every required compiled Session was placed."""
        return not self.unscheduled_sessions


Schedule = InstitutionSchedule
"""Compatibility name for the core institution-specific schedule."""
