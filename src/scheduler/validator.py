"""Post-placement validation for immutable institution schedules."""

from __future__ import annotations

from collections.abc import Iterable

from .constraints import (
    DEFAULT_CONSTRAINTS,
    ConstraintViolation,
    ScheduleConstraint,
)
from .exceptions import ScheduleValidationError
from .schedule import InstitutionSchedule


class ScheduleValidator:
    """Evaluate an ordered, deterministic set of schedule constraints."""

    def __init__(
        self,
        constraints: Iterable[ScheduleConstraint] = DEFAULT_CONSTRAINTS,
    ) -> None:
        self._constraints = tuple(constraints)

    def validate(
        self, schedule: InstitutionSchedule
    ) -> tuple[ConstraintViolation, ...]:
        """Return all violations in deterministic constraint order."""
        return tuple(
            violation
            for constraint in self._constraints
            for violation in constraint.evaluate(schedule)
        )

    def validate_or_raise(self, schedule: InstitutionSchedule) -> None:
        """Raise one aggregate exception when validation finds violations."""
        violations = self.validate(schedule)
        if violations:
            raise ScheduleValidationError(violations)


def validate_schedule(
    schedule: InstitutionSchedule,
) -> tuple[ConstraintViolation, ...]:
    """Validate a schedule with the default constraint set."""
    return ScheduleValidator().validate(schedule)
