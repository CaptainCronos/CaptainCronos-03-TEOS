"""Institutional Profile Framework public application configuration API.

The package loads, validates, registers, and selects immutable institution
configuration. It deliberately performs no curriculum, scheduling, rendering,
generation, authentication, LMS, cloud, or institution-specific business logic.
"""

from .branding import BrandAsset, InstitutionBrand
from .calendars import (
    AcademicCalendarProfile,
    AcademicPeriod,
    CalendarDay,
    CalendarDayKind,
    CalendarSystem,
)
from .contracts import (
    FRAMEWORK_VERSION,
    SUPPORTED_CONTRACT_VERSION,
    AssetKind,
    SemanticVersion,
    VersionCompatibility,
)
from .exceptions import (
    BrandingError,
    CalendarConfigurationError,
    GradingConfigurationError,
    InstitutionError,
    ProfileCompatibilityError,
    ProfileLoadError,
    ProfileRegistrationError,
    ProfileValidationError,
    TemplateConfigurationError,
)
from .grading import GradeBand, GradingPolicy, GradingSystem, WeightedCategory
from .loader import InstitutionProfileLoader
from .manager import InstitutionProfileManager
from .metadata import ContactInformation, InstitutionMetadata
from .policies import OperationalPolicy
from .profile import InstitutionProfile
from .registry import InstitutionProfileRegistry
from .templates import TemplateKind, TemplateProfile, TemplateSelection
from .terminology import CANONICAL_TERMS, TerminologyProfile
from .validator import InstitutionProfileValidator

__all__ = [
    "FRAMEWORK_VERSION",
    "SUPPORTED_CONTRACT_VERSION",
    "AcademicCalendarProfile",
    "AcademicPeriod",
    "AssetKind",
    "BrandAsset",
    "BrandingError",
    "CANONICAL_TERMS",
    "CalendarConfigurationError",
    "CalendarDay",
    "CalendarDayKind",
    "CalendarSystem",
    "ContactInformation",
    "GradeBand",
    "GradingConfigurationError",
    "GradingPolicy",
    "GradingSystem",
    "InstitutionBrand",
    "InstitutionError",
    "InstitutionMetadata",
    "InstitutionProfile",
    "InstitutionProfileLoader",
    "InstitutionProfileManager",
    "InstitutionProfileRegistry",
    "InstitutionProfileValidator",
    "OperationalPolicy",
    "ProfileCompatibilityError",
    "ProfileLoadError",
    "ProfileRegistrationError",
    "ProfileValidationError",
    "SemanticVersion",
    "TemplateConfigurationError",
    "TemplateKind",
    "TemplateProfile",
    "TemplateSelection",
    "TerminologyProfile",
    "VersionCompatibility",
    "WeightedCategory",
]
