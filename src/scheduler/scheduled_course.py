"""Immutable scheduled view of one compiled Course."""

from dataclasses import dataclass

from src.compiler import CompiledCourse

from .scheduled_instructional_unit import ScheduledInstructionalUnit


@dataclass(frozen=True, slots=True)
class ScheduledCourse:
    """Retain a compiled Course and its declared scheduled Unit sequence."""

    source: CompiledCourse
    instructional_units: tuple[ScheduledInstructionalUnit, ...]
