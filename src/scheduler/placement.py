"""Immutable institutional placement values produced by the scheduler."""

from dataclasses import dataclass
from datetime import date

from src.models.academic_calendar import (
    AcademicYear,
    Closure,
    Holiday,
    InstructionalPeriod,
    SpecialSchedule,
    Term,
)
from src.models.institution_profile import MeetingPattern
from src.models.lifecycle import AvailabilityStatus


@dataclass(frozen=True, slots=True)
class Placement:
    """Place one Session in one institution-owned calendar container."""

    calendar_date: date
    academic_year: AcademicYear
    term: Term | None
    instructional_period: InstructionalPeriod | None
    meeting_pattern: MeetingPattern
    meeting_sequence: int
    availability: AvailabilityStatus
    holiday: Holiday | None = None
    closure: Closure | None = None
    special_schedule: SpecialSchedule | None = None

    def __post_init__(self) -> None:
        """Require a positive, deterministic occurrence sequence."""
        if self.meeting_sequence < 1:
            raise ValueError("meeting sequence must be positive")
