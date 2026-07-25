"""Course domain object and course-owned value objects.

A Course orders Instructional Units and defines curriculum completion
requirements.  It does not contain dates, institution assignments, learner
results, or scheduling behavior.
"""

from dataclasses import dataclass
from decimal import Decimal
from uuid import UUID

from .base import TEOSObject, require_identity, require_version
from .duration import Duration
from .lifecycle import LifecycleStatus
from .metadata import LocalizedString, Metadata, Organization
from .references import (
    CompetencyReference,
    CourseReference,
    DocumentReference,
    InstructionalUnitReference,
    Reference,
    StandardReference,
)


@dataclass(frozen=True, slots=True)
class CatalogInformation:
    """External catalog information that supplements Course identity."""

    namespace: str
    catalog_title: LocalizedString | None = None
    code: str | None = None
    subject: str | None = None
    number: str | None = None
    level: str | None = None
    summary: LocalizedString | None = None

    def __post_init__(self) -> None:
        """Require the governing catalog namespace."""
        if not self.namespace:
            raise ValueError("catalog namespace cannot be empty")


@dataclass(frozen=True, slots=True)
class CompletionRequirement:
    """An evaluable curriculum condition without learner-specific results."""

    requirement_type: str
    description: LocalizedString
    references: tuple[Reference, ...] = ()

    def __post_init__(self) -> None:
        """Require the documented completion-condition category."""
        if not self.requirement_type:
            raise ValueError("completion requirement type cannot be empty")


@dataclass(frozen=True, slots=True)
class CreditHours:
    """Credit hours under an explicitly identified authority and definition."""

    value: int | float | Decimal
    authority: Organization
    definition: DocumentReference

    def __post_init__(self) -> None:
        """Reject non-positive credit hours."""
        if isinstance(self.value, bool) or self.value <= 0:
            raise ValueError("credit hours must be positive")


@dataclass(frozen=True, slots=True, kw_only=True)
class Course(TEOSObject):
    """A complete, versioned curriculum offering of ordered Units."""

    course_id: UUID
    version: str
    owner: Organization
    title: LocalizedString
    description: LocalizedString
    instructional_unit_references: tuple[InstructionalUnitReference, ...]
    completion_requirements: tuple[CompletionRequirement, ...]
    estimated_instructional_hours: Duration
    lifecycle_status: LifecycleStatus
    catalog_information: CatalogInformation | None = None
    standard_references: tuple[StandardReference, ...] = ()
    prerequisite_competency_references: tuple[CompetencyReference, ...] = ()
    prerequisite_course_references: tuple[CourseReference, ...] = ()
    credit_hours: CreditHours | None = None
    references: tuple[DocumentReference, ...] = ()
    tags: tuple[str, ...] = ()
    maintainer: Organization | None = None
    revision_notes: str | None = None
    metadata: Metadata | None = None

    def __post_init__(self) -> None:
        """Check the object's identity and version invariants."""
        require_identity(self.course_id)
        require_version(self.version)

    @property
    def teos_id(self) -> UUID:
        """Return the Course identity."""
        return self.course_id

    @property
    def teos_version(self) -> str:
        """Return the Course version."""
        return self.version

    @property
    def lifecycle(self) -> LifecycleStatus:
        """Return the Course lifecycle."""
        return self.lifecycle_status

    @property
    def object_metadata(self) -> Metadata | None:
        """Return non-authoritative Course metadata."""
        return self.metadata

    def display_name(self) -> str:
        """Return the default approved title."""
        return self.title.default
