"""Session domain object and its tightly scoped value objects.

A Session is the smallest schedulable curriculum primitive.  These objects
express curriculum-owned duration and continuity constraints but never assign
dates, institutional periods, people, rooms, or equipment.
"""

from dataclasses import dataclass
from uuid import UUID

from .base import TEOSObject, require_identity, require_version
from .duration import Duration
from .lifecycle import LifecycleStatus, SessionType
from .metadata import LocalizedString, Metadata, Organization
from .references import (
    CompetencyReference,
    DocumentReference,
    ResourceReference,
    SafetyReference,
    SessionReference,
)


@dataclass(frozen=True, slots=True)
class ModeAllocation:
    """A portion of Session duration assigned to an instructional mode."""

    mode: SessionType
    duration: Duration


@dataclass(frozen=True, slots=True)
class SessionDependency:
    """A version-bound Session dependency with explicit relationship semantics."""

    session_reference: SessionReference
    relationship: str

    def __post_init__(self) -> None:
        """Require a meaningful relationship description."""
        if not self.relationship:
            raise ValueError("session dependency relationship cannot be empty")


@dataclass(frozen=True, slots=True)
class RenderingMetadata:
    """Bounded presentation-neutral hints available to later renderers."""

    audiences: tuple[str, ...] = ()
    display_label: LocalizedString | None = None
    available_sections: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class SchedulingConstraints:
    """Curriculum continuity constraints without any assigned occurrence."""

    may_span_occurrences: bool | None = None
    may_share_occurrence: bool | None = None
    requires_uninterrupted_occurrence: bool | None = None


@dataclass(frozen=True, slots=True, kw_only=True)
class Session(TEOSObject):
    """The versioned smallest schedulable instructional event in TEOS."""

    session_id: UUID
    version: str
    owner: Organization
    session_title: LocalizedString
    session_type: SessionType
    duration: Duration
    learning_objectives: tuple[LocalizedString, ...]
    competency_references: tuple[CompetencyReference, ...]
    lifecycle_status: LifecycleStatus
    description: LocalizedString | None = None
    mode_allocations: tuple[ModeAllocation, ...] = ()
    required_resources: tuple[ResourceReference, ...] = ()
    required_instructor_materials: tuple[ResourceReference, ...] = ()
    required_student_materials: tuple[ResourceReference, ...] = ()
    required_equipment: tuple[ResourceReference, ...] = ()
    required_safety_controls: tuple[SafetyReference, ...] = ()
    prerequisite_session_references: tuple[SessionDependency, ...] = ()
    dependent_session_references: tuple[SessionDependency, ...] = ()
    prerequisite_competency_references: tuple[CompetencyReference, ...] = ()
    notes: LocalizedString | None = None
    estimated_preparation_time: Duration | None = None
    rendering_metadata: RenderingMetadata | None = None
    scheduling_constraints: SchedulingConstraints | None = None
    references: tuple[DocumentReference, ...] = ()
    tags: tuple[str, ...] = ()
    maintainer: Organization | None = None
    revision_notes: str | None = None
    metadata: Metadata | None = None

    def __post_init__(self) -> None:
        """Check the object's identity and version invariants."""
        require_identity(self.session_id)
        require_version(self.version)

    @property
    def teos_id(self) -> UUID:
        """Return the Session identity."""
        return self.session_id

    @property
    def teos_version(self) -> str:
        """Return the Session version."""
        return self.version

    @property
    def lifecycle(self) -> LifecycleStatus:
        """Return the Session lifecycle."""
        return self.lifecycle_status

    @property
    def object_metadata(self) -> Metadata | None:
        """Return non-authoritative Session metadata."""
        return self.metadata

    def display_name(self) -> str:
        """Return the default Session title."""
        return self.session_title.default
