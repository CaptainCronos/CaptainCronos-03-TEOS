"""Immutable scheduled view over one compiled repository."""

from dataclasses import dataclass

from src.compiler import CompiledRepository

from .schedule import InstitutionSchedule


@dataclass(frozen=True, slots=True)
class ScheduledRepository:
    """Retain the authoritative compilation and its institution schedules."""

    source: CompiledRepository
    institution_schedules: tuple[InstitutionSchedule, ...]

    def __post_init__(self) -> None:
        """Require every child schedule to derive from this compilation."""
        for schedule in self.institution_schedules:
            if schedule.source is not self.source:
                raise ValueError(
                    "institution schedule derives from another compilation"
                )
