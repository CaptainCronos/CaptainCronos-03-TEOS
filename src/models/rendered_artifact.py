"""Rendered Artifact domain object and generation-record value objects.

A Rendered Artifact records a generated output as a non-authoritative,
reproducible artifact.  It does not render content, validate sources, read or
write files, or become a source of curriculum truth.
"""

from dataclasses import dataclass
from datetime import datetime
from pathlib import PurePosixPath
from uuid import UUID

from .base import TEOSObject, require_identity, require_version
from .lifecycle import (
    ArtifactLifecycleStatus,
    ArtifactType,
    OutputFormat,
    ValidationStatus,
)
from .metadata import ExtensionItems, LocalizedString, Metadata
from .references import (
    AcademicCalendarReference,
    AssetReference,
    DestinationReference,
    DocumentReference,
    InstitutionProfileReference,
    PolicyReference,
    Reference,
    RenderedArtifactReference,
    ScheduleReference,
    TemplateReference,
)


@dataclass(frozen=True, slots=True)
class VersionedComponent:
    """The stable identity and exact semantic version of a component."""

    identity: str
    version: str

    def __post_init__(self) -> None:
        """Require component identity and version."""
        if not self.identity:
            raise ValueError("component identity cannot be empty")
        require_version(self.version)


@dataclass(frozen=True, slots=True)
class ArtifactValidation:
    """The recorded validation outcome for a generated artifact."""

    status: ValidationStatus
    complete: bool
    report_reference: RenderedArtifactReference | None = None
    notes: LocalizedString | None = None


@dataclass(frozen=True, slots=True)
class ReproducibilityRecord:
    """Source and generation context needed to reproduce equivalent output."""

    source_references: tuple[Reference, ...]
    generator: VersionedComponent
    locale: str
    time_zone: str
    deterministic_ordering: LocalizedString
    equivalence_rule: LocalizedString
    source_digests: tuple[tuple[str, str], ...] = ()
    template_reference: TemplateReference | None = None
    asset_references: tuple[AssetReference, ...] = ()
    policy_references: tuple[PolicyReference, ...] = ()
    renderer: VersionedComponent | None = None
    destination_contract: DestinationReference | None = None
    generation_options: ExtensionItems = ()
    random_seed: int | str | None = None
    toolchain_versions: tuple[tuple[str, str], ...] = ()
    non_deterministic_values: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        """Require the generation locale and time-zone names."""
        if not self.locale or not self.time_zone:
            raise ValueError("reproducibility locale and time zone cannot be empty")


@dataclass(frozen=True, slots=True)
class PackageEntry:
    """A constituent file, role, and optional digest in a package artifact."""

    path: PurePosixPath
    role: str
    content_digest: str | None = None

    def __post_init__(self) -> None:
        """Require a relative artifact path and meaningful role."""
        if self.path.is_absolute() or ".." in self.path.parts:
            raise ValueError("package entry path must remain within the artifact")
        if not self.role:
            raise ValueError("package entry role cannot be empty")


@dataclass(frozen=True, slots=True, kw_only=True)
class RenderedArtifact(TEOSObject):
    """A versioned, generated TEOS output and its reproducibility record."""

    artifact_id: UUID
    artifact_type: ArtifactType
    artifact_version: str
    format: OutputFormat
    generation_timestamp: datetime
    generator_identity: str
    generator_version: str
    source_references: tuple[Reference, ...]
    validation_status: ArtifactValidation
    reproducibility_record: ReproducibilityRecord
    lifecycle_status: ArtifactLifecycleStatus
    renderer: VersionedComponent | None = None
    template_reference: TemplateReference | None = None
    title: LocalizedString | None = None
    audience: str | None = None
    language: str | None = None
    institution_profile_reference: InstitutionProfileReference | None = None
    academic_calendar_reference: AcademicCalendarReference | None = None
    schedule_reference: ScheduleReference | None = None
    destination_profile: DestinationReference | None = None
    accessibility_conformance: tuple[DocumentReference, ...] = ()
    content_digest: str | None = None
    package_manifest: tuple[PackageEntry, ...] = ()
    generation_notes: LocalizedString | None = None
    supersedes_artifact_reference: RenderedArtifactReference | None = None
    creation_metadata: Metadata | None = None

    def __post_init__(self) -> None:
        """Check identity and component version invariants."""
        require_identity(self.artifact_id)
        require_version(self.artifact_version)
        require_version(self.generator_version)
        if not self.generator_identity:
            raise ValueError("generator identity cannot be empty")

    @property
    def teos_id(self) -> UUID:
        """Return the Rendered Artifact identity."""
        return self.artifact_id

    @property
    def teos_version(self) -> str:
        """Return the Rendered Artifact version."""
        return self.artifact_version

    @property
    def lifecycle(self) -> ArtifactLifecycleStatus:
        """Return the Rendered Artifact lifecycle."""
        return self.lifecycle_status

    @property
    def object_metadata(self) -> Metadata | None:
        """Return artifact creation metadata."""
        return self.creation_metadata

    def display_name(self) -> str:
        """Return the title or the artifact's canonical type label."""
        return self.title.default if self.title is not None else self.artifact_type.value
