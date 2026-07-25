"""Competency domain object.

A Competency states an observable capability and its evidence expectations.
It does not schedule instruction, evaluate learners, or resolve alignments.
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
    StandardReference,
)


@dataclass(frozen=True, slots=True, kw_only=True)
class Competency(TEOSObject):
    """A versioned observable technical capability."""

    competency_id: UUID
    version: str
    owner: Organization
    title: LocalizedString
    description: LocalizedString
    learning_outcome: LocalizedString
    performance_criteria: tuple[LocalizedString, ...]
    assessment_evidence: tuple[AssessmentExpectation, ...]
    lifecycle_status: LifecycleStatus
    prerequisite_competency_references: tuple[CompetencyReference, ...] = ()
    standard_references: tuple[StandardReference, ...] = ()
    references: tuple[DocumentReference, ...] = ()
    tags: tuple[str, ...] = ()
    estimated_instructional_effort: Duration | None = None
    maintainer: Organization | None = None
    revision_notes: str | None = None
    metadata: Metadata | None = None

    def __post_init__(self) -> None:
        """Check the object's identity and version invariants."""
        require_identity(self.competency_id)
        require_version(self.version)

    @property
    def teos_id(self) -> UUID:
        """Return the Competency identity."""
        return self.competency_id

    @property
    def teos_version(self) -> str:
        """Return the Competency version."""
        return self.version

    @property
    def lifecycle(self) -> LifecycleStatus:
        """Return the Competency lifecycle."""
        return self.lifecycle_status

    @property
    def object_metadata(self) -> Metadata | None:
        """Return non-authoritative Competency metadata."""
        return self.metadata

    def display_name(self) -> str:
        """Return the default approved title."""
        return self.title.default
