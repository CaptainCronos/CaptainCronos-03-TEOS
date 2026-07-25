"""Immutable scheduled view of one compiled Instructional Unit."""

from dataclasses import dataclass

from src.compiler import CompiledInstructionalUnit

from .scheduled_session import ScheduledSession


@dataclass(frozen=True, slots=True)
class ScheduledInstructionalUnit:
    """Retain a compiled Unit and its declared scheduled Session sequence."""

    source: CompiledInstructionalUnit
    sessions: tuple[ScheduledSession, ...]
