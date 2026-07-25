"""Exception hierarchy for deterministic curriculum scheduling."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .constraints import ConstraintViolation


class SchedulerError(Exception):
    """Base class for every scheduling-layer failure."""


class SchedulingInputError(SchedulerError):
    """Raised when scheduling inputs do not form a valid scheduling context."""


class CalendarConfigurationError(SchedulingInputError):
    """Raised when calendar or institutional time configuration is invalid."""


class CalendarReferenceError(SchedulingInputError):
    """Raised when a profile does not reference the selected calendar exactly."""


class ScheduleValidationError(SchedulerError):
    """Raised when an immutable schedule violates one or more constraints."""

    def __init__(self, violations: tuple[ConstraintViolation, ...]) -> None:
        self.violations = violations
        summary = "; ".join(
            f"{violation.code}: {violation.message}"
            for violation in violations
        )
        super().__init__(summary)
