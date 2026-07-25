"""Immutable generic, typed, document, resource, and safety references.

References preserve target identity and version.  They do not resolve targets,
traverse dependency graphs, read documents, or perform compatibility checks.
"""

from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal
from uuid import UUID

from .lifecycle import ReferenceObjectType
from .metadata import LocalizedString, Organization


def _require_reference_fields(identifier: UUID, version: str) -> None:
    if not isinstance(identifier, UUID):
        raise TypeError("reference identifier must be a UUID")
    if not version:
        raise ValueError("reference version cannot be empty")


@dataclass(frozen=True, slots=True, kw_only=True)
class Reference:
    """A version-bound reference to an intentionally polymorphic TEOS target."""

    object_type: ReferenceObjectType
    identifier: UUID
    version: str
    role: str | None = None
    locator: str | None = None

    def __post_init__(self) -> None:
        """Require a UUID and a non-empty target version."""
        _require_reference_fields(self.identifier, self.version)


@dataclass(frozen=True, slots=True, kw_only=True)
class StandardReference(Reference):
    """A version-bound reference that can target only a Standard."""

    object_type: ReferenceObjectType = field(
        init=False, default=ReferenceObjectType.STANDARD
    )


@dataclass(frozen=True, slots=True, kw_only=True)
class CompetencyReference(Reference):
    """A version-bound reference that can target only a Competency."""

    object_type: ReferenceObjectType = field(
        init=False, default=ReferenceObjectType.COMPETENCY
    )


@dataclass(frozen=True, slots=True, kw_only=True)
class InstructionalUnitReference(Reference):
    """A version-bound reference that can target only an Instructional Unit."""

    object_type: ReferenceObjectType = field(
        init=False, default=ReferenceObjectType.INSTRUCTIONAL_UNIT
    )


@dataclass(frozen=True, slots=True, kw_only=True)
class SessionReference(Reference):
    """A version-bound reference that can target only a Session."""

    object_type: ReferenceObjectType = field(
        init=False, default=ReferenceObjectType.SESSION
    )


@dataclass(frozen=True, slots=True, kw_only=True)
class CourseReference(Reference):
    """A version-bound reference that can target only a Course."""

    object_type: ReferenceObjectType = field(
        init=False, default=ReferenceObjectType.COURSE
    )


@dataclass(frozen=True, slots=True, kw_only=True)
class InstitutionProfileReference(Reference):
    """A version-bound reference that can target only an Institution Profile."""

    object_type: ReferenceObjectType = field(
        init=False, default=ReferenceObjectType.INSTITUTION_PROFILE
    )


@dataclass(frozen=True, slots=True, kw_only=True)
class AcademicCalendarReference(Reference):
    """A version-bound reference that can target only an Academic Calendar."""

    object_type: ReferenceObjectType = field(
        init=False, default=ReferenceObjectType.ACADEMIC_CALENDAR
    )


@dataclass(frozen=True, slots=True, kw_only=True)
class RenderedArtifactReference(Reference):
    """A version-bound reference that can target only a Rendered Artifact."""

    object_type: ReferenceObjectType = field(
        init=False, default=ReferenceObjectType.RENDERED_ARTIFACT
    )


@dataclass(frozen=True, slots=True, kw_only=True)
class TemplateReference(Reference):
    """A version-bound reference that can target only a Template."""

    object_type: ReferenceObjectType = field(
        init=False, default=ReferenceObjectType.TEMPLATE
    )


@dataclass(frozen=True, slots=True, kw_only=True)
class ResourceObjectReference(Reference):
    """A version-bound reference that can target only a maintained Resource."""

    object_type: ReferenceObjectType = field(
        init=False, default=ReferenceObjectType.RESOURCE
    )


@dataclass(frozen=True, slots=True, kw_only=True)
class DocumentObjectReference(Reference):
    """A version-bound reference that can target only a maintained Document."""

    object_type: ReferenceObjectType = field(
        init=False, default=ReferenceObjectType.DOCUMENT
    )


@dataclass(frozen=True, slots=True, kw_only=True)
class PolicyReference(Reference):
    """A version-bound reference that can target only a Policy."""

    object_type: ReferenceObjectType = field(
        init=False, default=ReferenceObjectType.POLICY
    )


@dataclass(frozen=True, slots=True, kw_only=True)
class ScheduleReference(Reference):
    """A version-bound reference that can target only a Schedule."""

    object_type: ReferenceObjectType = field(
        init=False, default=ReferenceObjectType.SCHEDULE
    )


@dataclass(frozen=True, slots=True, kw_only=True)
class AssessmentObjectReference(Reference):
    """A version-bound reference that can target only an Assessment."""

    object_type: ReferenceObjectType = field(
        init=False, default=ReferenceObjectType.ASSESSMENT
    )


@dataclass(frozen=True, slots=True, kw_only=True)
class GeneratorReference(Reference):
    """A version-bound reference that can target only a Generator."""

    object_type: ReferenceObjectType = field(
        init=False, default=ReferenceObjectType.GENERATOR
    )


@dataclass(frozen=True, slots=True, kw_only=True)
class RendererReference(Reference):
    """A version-bound reference that can target only a Renderer."""

    object_type: ReferenceObjectType = field(
        init=False, default=ReferenceObjectType.RENDERER
    )


@dataclass(frozen=True, slots=True, kw_only=True)
class AssetReference(Reference):
    """A version-bound reference that can target only an Asset."""

    object_type: ReferenceObjectType = field(
        init=False, default=ReferenceObjectType.ASSET
    )


@dataclass(frozen=True, slots=True, kw_only=True)
class DestinationReference(Reference):
    """A version-bound reference that can target only a Destination contract."""

    object_type: ReferenceObjectType = field(
        init=False, default=ReferenceObjectType.DESTINATION
    )


@dataclass(frozen=True, slots=True)
class ResourceReference:
    """A curriculum-owned resource requirement without a local assignment."""

    name: LocalizedString
    requirement: LocalizedString
    quantity: int | float | Decimal | None = None
    reference: ResourceObjectReference | None = None

    def __post_init__(self) -> None:
        """Reject a non-positive explicitly supplied quantity."""
        if self.quantity is not None and (
            isinstance(self.quantity, bool) or self.quantity <= 0
        ):
            raise ValueError("resource quantity must be positive")


@dataclass(frozen=True, slots=True)
class DocumentReference:
    """A citation or version-bound reference to a controlled document."""

    title: LocalizedString
    publisher: Organization | None = None
    uri: str | None = None
    publication_date: date | None = None
    version: str | None = None
    locator: str | None = None
    reference: Reference | None = None


@dataclass(frozen=True, slots=True)
class SafetyReference:
    """A curriculum safety-control requirement independent of assignments."""

    control_type: str
    requirement: LocalizedString
    source: DocumentReference | None = None

    def __post_init__(self) -> None:
        """Require the documented safety-control category."""
        if not self.control_type:
            raise ValueError("safety control type cannot be empty")


@dataclass(frozen=True, slots=True)
class AssessmentExpectation:
    """An assessment or evidence expectation tied to Competencies."""

    description: LocalizedString
    competency_references: tuple[CompetencyReference, ...] = ()
    assessment_reference: AssessmentObjectReference | None = None
