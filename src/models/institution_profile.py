"""Institution Profile domain object and institution-owned value objects.

An Institution Profile owns presentation, meeting-pattern, export, and local
policy context.  It does not own curriculum, assign Sessions to occurrences,
store secrets, render artifacts, or perform scheduling.
"""

from dataclasses import dataclass
from datetime import time
from uuid import UUID

from .base import TEOSObject, require_identity, require_version
from .duration import Duration
from .lifecycle import (
    ArtifactType,
    LifecycleStatus,
    OutputFormat,
    SessionType,
    Weekday,
)
from .metadata import ExtensionItems, LocalizedString, Metadata, Organization
from .references import (
    AcademicCalendarReference,
    AssetReference,
    DestinationReference,
    DocumentReference,
    InstitutionProfileReference,
    TemplateReference,
)


@dataclass(frozen=True, slots=True)
class InstitutionInformation:
    """Authoritative institution identity and operating context."""

    institution_identifier: str
    display_name: LocalizedString
    owner: Organization
    time_zone: str
    legal_name: LocalizedString | None = None
    abbreviations: tuple[str, ...] = ()
    contact_information: LocalizedString | None = None

    def __post_init__(self) -> None:
        """Require institution identity and time-zone names."""
        if not self.institution_identifier:
            raise ValueError("institution identifier cannot be empty")
        if not self.time_zone:
            raise ValueError("institution time zone cannot be empty")


@dataclass(frozen=True, slots=True)
class CampusInformation:
    """Optional campus or site context subordinate to an institution."""

    campus_identifier: str
    display_name: LocalizedString
    address: LocalizedString | None = None

    def __post_init__(self) -> None:
        """Require the institution-governed campus identifier."""
        if not self.campus_identifier:
            raise ValueError("campus identifier cannot be empty")


@dataclass(frozen=True, slots=True)
class Branding:
    """Approved brand guidance without binary assets or templates."""

    colors: tuple[tuple[str, str], ...] = ()
    typography: tuple[LocalizedString, ...] = ()
    usage_guidance: LocalizedString | None = None
    accessibility_guidance: LocalizedString | None = None


@dataclass(frozen=True, slots=True)
class MeetingPattern:
    """A permitted recurring institutional delivery container."""

    meeting_pattern_id: str
    title: LocalizedString
    time_zone: str
    eligible_weekdays: tuple[Weekday, ...]
    start_time: time
    end_time: time
    recurrence: LocalizedString
    instructional_duration: Duration | None = None
    compatible_session_types: tuple[SessionType, ...] = ()

    def __post_init__(self) -> None:
        """Require the local identity and time-zone name."""
        if not self.meeting_pattern_id:
            raise ValueError("meeting pattern identifier cannot be empty")
        if not self.time_zone:
            raise ValueError("meeting pattern time zone cannot be empty")


@dataclass(frozen=True, slots=True)
class InstructionalTimeConventions:
    """Local rules for interpreting meeting time during later scheduling."""

    breaks_count_as_instructional_time: bool | None = None
    rounding_increment: Duration | None = None
    theory_convention: LocalizedString | None = None
    lab_convention: LocalizedString | None = None


@dataclass(frozen=True, slots=True)
class TemplateSelection:
    """A version-bound template and its institution-approved context."""

    template_reference: TemplateReference
    artifact_type: ArtifactType
    audience: str | None = None
    destination: str | None = None


@dataclass(frozen=True, slots=True)
class TerminologyOverride:
    """A presentation-only mapping from a canonical term to a display label."""

    canonical_term: str
    display_label: LocalizedString
    audience: str | None = None

    def __post_init__(self) -> None:
        """Require the unchanged canonical TEOS term."""
        if not self.canonical_term:
            raise ValueError("canonical term cannot be empty")


@dataclass(frozen=True, slots=True)
class LMSSettings:
    """Non-secret LMS compatibility and content-placement configuration."""

    destination_reference: DestinationReference
    compatibility_version: str
    course_shell_convention: LocalizedString | None = None
    packaging_profile: str | None = None
    identifier_mappings: tuple[tuple[str, str], ...] = ()
    content_placement_rules: tuple[LocalizedString, ...] = ()

    def __post_init__(self) -> None:
        """Require the destination compatibility version."""
        require_version(self.compatibility_version)


@dataclass(frozen=True, slots=True)
class ExportSettings:
    """Approved artifact formats and non-secret destination configuration."""

    artifact_types: tuple[ArtifactType, ...]
    output_formats: tuple[OutputFormat, ...]
    destination_reference: DestinationReference | None = None
    naming_convention: LocalizedString | None = None
    packaging_options: ExtensionItems = ()
    accessibility_requirements: tuple[DocumentReference, ...] = ()


@dataclass(frozen=True, slots=True)
class ProfileComposition:
    """Profile components and their deterministic low-to-high precedence."""

    profile_references: tuple[InstitutionProfileReference, ...]
    precedence: tuple[UUID, ...]


@dataclass(frozen=True, slots=True, kw_only=True)
class InstitutionProfile(TEOSObject):
    """Versioned institution-owned presentation and operating context."""

    institution_profile_id: UUID
    version: str
    institution_information: InstitutionInformation
    academic_calendar_references: tuple[AcademicCalendarReference, ...]
    meeting_patterns: tuple[MeetingPattern, ...]
    lifecycle_status: LifecycleStatus
    campus_information: CampusInformation | None = None
    branding: Branding | None = None
    logo_references: tuple[AssetReference, ...] = ()
    template_references: tuple[TemplateSelection, ...] = ()
    instructional_time_conventions: InstructionalTimeConventions | None = None
    holiday_references: tuple[DocumentReference, ...] = ()
    header_definitions: tuple[LocalizedString, ...] = ()
    footer_definitions: tuple[LocalizedString, ...] = ()
    terminology_overrides: tuple[TerminologyOverride, ...] = ()
    lms_settings: LMSSettings | None = None
    export_settings: ExportSettings | None = None
    local_policy_references: tuple[DocumentReference, ...] = ()
    composition: ProfileComposition | None = None
    maintainer: Organization | None = None
    revision_notes: str | None = None
    metadata: Metadata | None = None

    def __post_init__(self) -> None:
        """Check the object's identity and version invariants."""
        require_identity(self.institution_profile_id)
        require_version(self.version)

    @property
    def teos_id(self) -> UUID:
        """Return the Institution Profile identity."""
        return self.institution_profile_id

    @property
    def teos_version(self) -> str:
        """Return the Institution Profile version."""
        return self.version

    @property
    def lifecycle(self) -> LifecycleStatus:
        """Return the Institution Profile lifecycle."""
        return self.lifecycle_status

    @property
    def object_metadata(self) -> Metadata | None:
        """Return non-authoritative Institution Profile metadata."""
        return self.metadata

    def display_name(self) -> str:
        """Return the institution's default approved display name."""
        return self.institution_information.display_name.default
