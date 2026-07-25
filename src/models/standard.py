"""Standard domain object.

A Standard preserves requirement authority and provenance.  It does not own
curriculum delivery, institutional schedules, or rendered presentation.
"""

from dataclasses import dataclass
from datetime import date
from uuid import UUID

from .base import TEOSObject, require_identity, require_version
from .lifecycle import LifecycleStatus
from .metadata import LocalizedString, Metadata, Organization
from .references import CompetencyReference, DocumentReference


@dataclass(frozen=True, slots=True, kw_only=True)
class Standard(TEOSObject):
    """A versioned external or internal body of education requirements."""

    standard_id: UUID
    version: str
    title: LocalizedString
    issuer: Organization
    source: DocumentReference
    requirements_scope: LocalizedString
    lifecycle_status: LifecycleStatus
    official_identifier: str | None = None
    official_version: str | None = None
    description: LocalizedString | None = None
    publication_date: date | None = None
    effective_context: LocalizedString | None = None
    source_uri: str | None = None
    competency_references: tuple[CompetencyReference, ...] = ()
    references: tuple[DocumentReference, ...] = ()
    revision: str | None = None
    tags: tuple[str, ...] = ()
    owner: Organization | None = None
    maintainer: Organization | None = None
    revision_notes: str | None = None
    metadata: Metadata | None = None

    def __post_init__(self) -> None:
        """Check the object's identity and version invariants."""
        require_identity(self.standard_id)
        require_version(self.version)

    @property
    def teos_id(self) -> UUID:
        """Return the Standard identity."""
        return self.standard_id

    @property
    def teos_version(self) -> str:
        """Return the Standard version."""
        return self.version

    @property
    def lifecycle(self) -> LifecycleStatus:
        """Return the Standard lifecycle."""
        return self.lifecycle_status

    @property
    def object_metadata(self) -> Metadata | None:
        """Return non-authoritative Standard metadata."""
        return self.metadata

    def display_name(self) -> str:
        """Return the default approved title."""
        return self.title.default
