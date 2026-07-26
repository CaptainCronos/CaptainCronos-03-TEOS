"""Cross-section validation for assembled institution profiles."""

from __future__ import annotations

from collections import Counter
from pathlib import Path
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from .contracts import SUPPORTED_CONTRACT_VERSION, SemanticVersion
from .exceptions import (
    BrandingError,
    CalendarConfigurationError,
    GradingConfigurationError,
    ProfileCompatibilityError,
    ProfileValidationError,
    TemplateConfigurationError,
)
from .grading import GradingSystem
from .profile import InstitutionProfile


class InstitutionProfileValidator:
    """Validate institution configuration without repairing or applying it."""

    def validate(
        self,
        profile: InstitutionProfile,
        *,
        teos_version: str,
        resource_root: Path | None = None,
    ) -> None:
        """Validate one complete profile for a host and optional resource root."""
        try:
            SemanticVersion.parse(profile.version)
        except Exception as error:
            raise ProfileValidationError(str(error)) from error
        if profile.contract_version != SUPPORTED_CONTRACT_VERSION:
            raise ProfileCompatibilityError(
                f"profile contract {profile.contract_version!r} is not supported; "
                f"expected {SUPPORTED_CONTRACT_VERSION!r}"
            )
        profile.compatibility.require(teos_version)
        try:
            ZoneInfo(profile.metadata.time_zone)
        except ZoneInfoNotFoundError as error:
            raise ProfileValidationError(
                f"unknown institution time zone: {profile.metadata.time_zone!r}"
            ) from error
        self._validate_branding(profile, resource_root)
        self._validate_calendars(profile)
        self._validate_grading(profile)
        self._validate_templates(profile, resource_root)

    @staticmethod
    def _validate_branding(
        profile: InstitutionProfile, resource_root: Path | None
    ) -> None:
        assets = profile.branding.assets
        identifiers = [item.identifier for item in assets]
        if len(identifiers) != len(set(identifiers)):
            raise BrandingError("branding contains duplicate asset identifiers")
        color_names = [name for name, _ in profile.branding.colors]
        if len(color_names) != len(set(color_names)):
            raise BrandingError("branding contains duplicate color names")
        if resource_root is not None:
            missing = tuple(
                str(item.path)
                for item in assets
                if item.required and not (resource_root / item.path).is_file()
            )
            if missing:
                raise BrandingError(
                    "required branding assets are unavailable",
                    findings=missing,
                )

    @staticmethod
    def _validate_calendars(profile: InstitutionProfile) -> None:
        identities = [(item.calendar_id, item.version) for item in profile.calendars]
        if len(identities) != len(set(identities)):
            raise CalendarConfigurationError(
                "calendar identifiers and versions must be unique"
            )
        for calendar in profile.calendars:
            period_ids = [item.identifier for item in calendar.periods]
            if len(period_ids) != len(set(period_ids)):
                raise CalendarConfigurationError(
                    f"calendar {calendar.calendar_id!r} has duplicate period identifiers"
                )
            dates = [item.date for item in calendar.days]
            if len(dates) != len(set(dates)):
                raise CalendarConfigurationError(
                    f"calendar {calendar.calendar_id!r} classifies a date more than once"
                )
            outside = tuple(
                day.date
                for day in calendar.days
                if not any(
                    period.start_date <= day.date <= period.end_date
                    for period in calendar.periods
                )
            )
            if outside:
                raise CalendarConfigurationError(
                    f"calendar {calendar.calendar_id!r} has dates outside its periods",
                    findings=tuple(map(str, outside)),
                )

    @staticmethod
    def _validate_grading(profile: InstitutionProfile) -> None:
        grading = profile.grading
        if grading.system in {GradingSystem.LETTER, GradingSystem.NUMERIC} and not (
            grading.grade_bands
        ):
            raise GradingConfigurationError(
                f"{grading.system.value} grading requires grade bands"
            )
        labels = [item.label for item in grading.grade_bands]
        thresholds = [item.minimum for item in grading.grade_bands]
        if len(labels) != len(set(labels)) or len(thresholds) != len(set(thresholds)):
            raise GradingConfigurationError(
                "grade-band labels and thresholds must be unique"
            )
        categories = grading.weighted_categories
        identifiers = [item.identifier for item in categories]
        if len(identifiers) != len(set(identifiers)):
            raise GradingConfigurationError(
                "weighted categories contain duplicate identifiers"
            )
        if categories and abs(sum(item.weight for item in categories) - 100.0) > 1e-9:
            raise GradingConfigurationError(
                "weighted category percentages must total 100"
            )

    @staticmethod
    def _validate_templates(
        profile: InstitutionProfile, resource_root: Path | None
    ) -> None:
        selections = profile.templates.selections
        identifiers = [item.identifier for item in selections]
        if len(identifiers) != len(set(identifiers)):
            raise TemplateConfigurationError(
                "template identifiers must be unique within a profile"
            )
        default_counts = Counter(
            item.kind for item in selections if item.is_default
        )
        duplicates = tuple(
            kind.value for kind, count in default_counts.items() if count > 1
        )
        if duplicates:
            raise TemplateConfigurationError(
                "template kinds cannot have multiple defaults",
                findings=duplicates,
            )
        if resource_root is not None:
            missing = tuple(
                str(item.path)
                for item in selections
                if not (resource_root / item.path).is_file()
            )
            if missing:
                raise TemplateConfigurationError(
                    "configured templates are unavailable",
                    findings=missing,
                )
