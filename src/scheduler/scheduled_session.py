"""Immutable scheduled view of one compiled Session."""

from dataclasses import dataclass

from src.compiler import CompiledSession

from .placement import Placement


@dataclass(frozen=True, slots=True)
class ScheduledSession:
    """Retain a compiled Session and add its execution placement."""

    source: CompiledSession
    placement: Placement
