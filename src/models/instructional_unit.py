"""Instructional Unit domain object.

An Instructional Unit groups Competencies and orders Session references.  It
does not assign dates, meeting patterns, instructors, rooms, or equipment.
"""

from dataclasses import dataclass
from uuid import UUID

from .base import TEOSObject, require_identity, require_version
from .duration import Duration
from .lifecycle import LifecycleStatus
from .metadata import LocalizedString, Metadata, Organization
from .references import (
    AssessmentExpectation,
    CompetencyReference,
    DocumentReference,
    InstructionalUnitReference,
    ResourceReference,
    SafetyReference,
    SessionReference,
)


@dataclass(frozen=True, slots=True, kw_only=True)
class InstructionalUnit(TEOSObject):
    """A coherent, versioned grouping of related curriculum."""

    instructional_unit_id: UUID
    version: str
    owner: Organization
    title: LocalizedString
    description: LocalizedString
    included_competency_references: tuple[CompetencyReference, ...]
    learning_objectives: tuple[LocalizedString, ...]
    session_references: tuple[SessionReference, ...]
    estimated_duration: Duration
    assessment_strategy: tuple[AssessmentExpectation, ...]
    lifecycle_status: LifecycleStatus
    required_resources: tuple[ResourceReference, ...] = ()
    required_equipment: tuple[ResourceReference, ...] = ()
    required_safety_controls: tuple[SafetyReference, ...] = ()
    prerequisite_competency_references: tuple[CompetencyReference, ...] = ()
    prerequisite_instructional_unit_references: tuple[
        InstructionalUnitReference, ...
    ] = ()
    references: tuple[DocumentReference, ...] = ()
    tags: tuple[str, ...] = ()
    maintainer: Organization | None = None
    revision_notes: str | None = None
    metadata: Metadata | None = None

    def __post_init__(self) -> None:
        """Check the object's identity and version invariants."""
        require_identity(self.instructional_unit_id)
        require_version(self.version)

    @property
    def teos_id(self) -> UUID:
        """Return the Instructional Unit identity."""
        return self.instructional_unit_id

    @property
    def teos_version(self) -> str:
        """Return the Instructional Unit version."""
        return self.version

    @property
    def lifecycle(self) -> LifecycleStatus:
        """Return the Instructional Unit lifecycle."""
        return self.lifecycle_status

    @property
    def object_metadata(self) -> Metadata | None:
        """Return non-authoritative Instructional Unit metadata."""
        return self.metadata

    def display_name(self) -> str:
        """Return the default approved title."""
        return self.title.default
