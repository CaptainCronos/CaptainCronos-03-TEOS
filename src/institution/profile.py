"""Immutable aggregate root for effective institutional configuration."""

from dataclasses import dataclass

from .branding import InstitutionBrand
from .calendars import AcademicCalendarProfile
from .contracts import SUPPORTED_CONTRACT_VERSION, VersionCompatibility
from .grading import GradingPolicy
from .metadata import InstitutionMetadata
from .policies import OperationalPolicy
from .templates import TemplateProfile
from .terminology import TerminologyProfile


@dataclass(frozen=True, slots=True, kw_only=True)
class InstitutionProfile:
    """Versioned configuration consumed by TEOS application operations."""

    profile_id: str
    version: str
    compatibility: VersionCompatibility
    metadata: InstitutionMetadata
    branding: InstitutionBrand
    calendars: tuple[AcademicCalendarProfile, ...]
    grading: GradingPolicy
    terminology: TerminologyProfile
    templates: TemplateProfile
    policies: OperationalPolicy
    contract_version: str = SUPPORTED_CONTRACT_VERSION

    def __post_init__(self) -> None:
        if not self.profile_id or not self.version:
            raise ValueError("profile identifier and version are required")
        if not self.calendars:
            raise ValueError("an institution profile requires at least one calendar")

    @property
    def institution_id(self) -> str:
        """Return the authoritative institution identifier."""
        return self.metadata.institution_id

    def calendar(
        self, calendar_id: str, version: str | None = None
    ) -> AcademicCalendarProfile:
        """Return one exact or unambiguous configured academic calendar."""
        matches = tuple(
            item
            for item in self.calendars
            if item.calendar_id == calendar_id
            and (version is None or item.version == version)
        )
        if len(matches) != 1:
            raise KeyError(
                f"calendar {calendar_id!r} does not resolve unambiguously"
            )
        return matches[0]
