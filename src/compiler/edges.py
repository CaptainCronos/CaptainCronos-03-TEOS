"""Immutable typed edges for declared TEOS object relationships."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from .node import NodeKey


class EdgeKind(StrEnum):
    """Contract-defined relationship categories understood by the compiler."""

    COURSE_INSTRUCTIONAL_UNIT = "course-instructional-unit"
    COURSE_STANDARD = "course-standard"
    COURSE_PREREQUISITE_COMPETENCY = "course-prerequisite-competency"
    COURSE_PREREQUISITE_COURSE = "course-prerequisite-course"
    UNIT_COMPETENCY = "unit-competency"
    UNIT_SESSION = "unit-session"
    UNIT_PREREQUISITE_COMPETENCY = "unit-prerequisite-competency"
    UNIT_PREREQUISITE_UNIT = "unit-prerequisite-unit"
    SESSION_COMPETENCY = "session-competency"
    SESSION_PREREQUISITE_SESSION = "session-prerequisite-session"
    SESSION_PREREQUISITE_COMPETENCY = "session-prerequisite-competency"
    COMPETENCY_PREREQUISITE_COMPETENCY = (
        "competency-prerequisite-competency"
    )
    COMPETENCY_STANDARD = "competency-standard"
    STANDARD_COMPETENCY_TRACE = "standard-competency-trace"
    PROFILE_CALENDAR = "profile-calendar"
    PROFILE_COMPOSITION = "profile-composition"
    PROFILE_COURSE = "profile-course"
    ARTIFACT_SOURCE = "artifact-source"
    ARTIFACT_PROFILE = "artifact-profile"
    ARTIFACT_CALENDAR = "artifact-calendar"
    ARTIFACT_SUPERSEDES = "artifact-supersedes"
    DOCUMENT_REFERENCE = "document-reference"


NON_ORDERING_EDGE_KINDS = frozenset(
    {
        EdgeKind.STANDARD_COMPETENCY_TRACE,
    }
)


@dataclass(frozen=True, slots=True)
class DependencyEdge:
    """A stable directed relationship between two exact object versions."""

    source: NodeKey
    target: NodeKey
    kind: EdgeKind
    ordinal: int = 0

    def __post_init__(self) -> None:
        """Require a relationship kind and non-negative declared ordinal."""
        if not isinstance(self.kind, EdgeKind):
            raise TypeError("edge kind must be an EdgeKind")
        if isinstance(self.ordinal, bool) or self.ordinal < 0:
            raise ValueError("edge ordinal cannot be negative")

    @property
    def constrains_order(self) -> bool:
        """Return whether this edge participates in dependency ordering."""
        return self.kind not in NON_ORDERING_EDGE_KINDS

    def sort_key(self) -> tuple[object, ...]:
        """Return a deterministic ordering key for this relationship."""
        return (
            self.source,
            self.target,
            self.kind.value,
            self.ordinal,
        )
