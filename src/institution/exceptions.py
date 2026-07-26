"""Exception hierarchy for institution profile configuration."""


class InstitutionError(Exception):
    """Base error for all Institutional Profile Framework failures."""


class ProfileLoadError(InstitutionError):
    """Raised when a profile document cannot be read or constructed."""


class ProfileValidationError(InstitutionError):
    """Raised when an assembled profile is internally inconsistent."""

    def __init__(self, message: str, *, findings: tuple[str, ...] = ()) -> None:
        super().__init__(message)
        self.findings = findings


class ProfileRegistrationError(InstitutionError):
    """Raised for duplicate, missing, or ambiguous profile registrations."""


class ProfileCompatibilityError(InstitutionError):
    """Raised when a profile cannot run with the selected TEOS version."""


class BrandingError(ProfileValidationError):
    """Raised when required institution branding is unavailable or invalid."""


class CalendarConfigurationError(ProfileValidationError):
    """Raised when institution-owned calendar configuration is inconsistent."""


class GradingConfigurationError(ProfileValidationError):
    """Raised when an institution grading system is inconsistent."""


class TemplateConfigurationError(ProfileValidationError):
    """Raised when an institution template selection cannot be satisfied."""
