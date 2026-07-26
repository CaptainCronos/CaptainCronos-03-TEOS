"""Strict JSON loading and assembly for institution profile configuration."""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path, PurePosixPath
from typing import Any, Mapping

from .branding import BrandAsset, InstitutionBrand
from .calendars import (
    AcademicCalendarProfile,
    AcademicPeriod,
    CalendarDay,
    CalendarDayKind,
    CalendarSystem,
)
from .contracts import AssetKind, VersionCompatibility
from .exceptions import ProfileLoadError
from .grading import GradeBand, GradingPolicy, GradingSystem, WeightedCategory
from .metadata import ContactInformation, InstitutionMetadata
from .policies import OperationalPolicy
from .profile import InstitutionProfile
from .templates import TemplateKind, TemplateProfile, TemplateSelection
from .terminology import TerminologyProfile
from .validator import InstitutionProfileValidator


def _mapping(value: Any, label: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise ProfileLoadError(f"{label} must be an object")
    return value


def _sequence(value: Any, label: str) -> list[Any]:
    if not isinstance(value, list):
        raise ProfileLoadError(f"{label} must be an array")
    return value


def _strict(
    value: Mapping[str, Any],
    label: str,
    *,
    required: frozenset[str] = frozenset(),
    optional: frozenset[str] = frozenset(),
) -> None:
    missing = sorted(required - value.keys())
    unknown = sorted(value.keys() - required - optional)
    if missing:
        raise ProfileLoadError(f"{label} is missing fields: {', '.join(missing)}")
    if unknown:
        raise ProfileLoadError(f"{label} has unknown fields: {', '.join(unknown)}")


def _text(value: Any, label: str) -> str:
    if not isinstance(value, str) or not value:
        raise ProfileLoadError(f"{label} must be a non-empty string")
    return value


def _path(value: Any, label: str) -> PurePosixPath:
    selected = PurePosixPath(_text(value, label))
    if selected.is_absolute() or ".." in selected.parts:
        raise ProfileLoadError(f"{label} must be a safe repository-relative path")
    return selected


def _read_json(path: Path, label: str) -> Mapping[str, Any]:
    try:
        with path.open(encoding="utf-8") as stream:
            value = json.load(stream)
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise ProfileLoadError(f"could not read {label} {path}: {error}") from error
    return _mapping(value, label)


class InstitutionProfileLoader:
    """Load, assemble, and validate one immutable institution profile."""

    def __init__(
        self, validator: InstitutionProfileValidator | None = None
    ) -> None:
        self.validator = validator or InstitutionProfileValidator()

    def load(
        self,
        source: str | Path,
        *,
        teos_version: str,
        resource_root: str | Path | None = None,
    ) -> InstitutionProfile:
        """Load a profile and its separately owned calendar sources."""
        source_path = Path(source).resolve()
        root = (
            Path(resource_root).resolve()
            if resource_root is not None
            else source_path.parent
        )
        document = _read_json(source_path, "institution profile")
        try:
            profile = self._construct(document, root)
            self.validator.validate(
                profile, teos_version=teos_version, resource_root=root
            )
            return profile
        except ProfileLoadError:
            raise
        except Exception as error:
            if isinstance(error, ProfileLoadError):
                raise
            if error.__class__.__module__.startswith("src.institution"):
                raise
            raise ProfileLoadError(
                f"could not construct institution profile: {error}"
            ) from error

    def loads(
        self,
        content: str,
        *,
        teos_version: str,
        resource_root: str | Path | None = None,
    ) -> InstitutionProfile:
        """Load profile JSON text, using no calendar files unless configured."""
        try:
            value = json.loads(content)
        except json.JSONDecodeError as error:
            raise ProfileLoadError(f"could not parse institution profile: {error}") from error
        root = Path(resource_root or ".").resolve()
        profile = self._construct(_mapping(value, "institution profile"), root)
        self.validator.validate(
            profile, teos_version=teos_version, resource_root=root
        )
        return profile

    def _construct(
        self, document: Mapping[str, Any], root: Path
    ) -> InstitutionProfile:
        required = frozenset(
            {
                "profile_id",
                "version",
                "teos_compatibility",
                "metadata",
                "branding",
                "calendar_sources",
                "grading",
                "terminology",
                "templates",
                "policies",
            }
        )
        _strict(
            document,
            "institution profile",
            required=required,
            optional=frozenset({"contract_version"}),
        )
        calendar_sources = _sequence(
            document["calendar_sources"], "calendar_sources"
        )
        calendars = tuple(
            self._calendar(
                _read_json(root / _path(item, "calendar source"), "academic calendar")
            )
            for item in calendar_sources
        )
        return InstitutionProfile(
            profile_id=_text(document["profile_id"], "profile_id"),
            version=_text(document["version"], "version"),
            compatibility=VersionCompatibility.parse(
                _text(document["teos_compatibility"], "teos_compatibility")
            ),
            contract_version=str(document.get("contract_version", "1.0")),
            metadata=self._metadata(_mapping(document["metadata"], "metadata")),
            branding=self._branding(_mapping(document["branding"], "branding")),
            calendars=calendars,
            grading=self._grading(_mapping(document["grading"], "grading")),
            terminology=self._terminology(
                _mapping(document["terminology"], "terminology")
            ),
            templates=self._templates(
                _mapping(document["templates"], "templates")
            ),
            policies=self._policies(_mapping(document["policies"], "policies")),
        )

    @staticmethod
    def _metadata(value: Mapping[str, Any]) -> InstitutionMetadata:
        _strict(
            value,
            "metadata",
            required=frozenset({"institution_id", "name", "time_zone"}),
            optional=frozenset(
                {"legal_name", "abbreviations", "identifiers", "contact"}
            ),
        )
        contact = value.get("contact")
        contact_value = None
        if contact is not None:
            contact_data = _mapping(contact, "contact")
            _strict(
                contact_data,
                "contact",
                optional=frozenset({"address", "phone", "email", "website"}),
            )
            contact_value = ContactInformation(**contact_data)
        identifiers = _mapping(value.get("identifiers", {}), "identifiers")
        return InstitutionMetadata(
            institution_id=_text(value["institution_id"], "institution_id"),
            name=_text(value["name"], "institution name"),
            time_zone=_text(value["time_zone"], "time_zone"),
            legal_name=value.get("legal_name"),
            abbreviations=tuple(
                _sequence(value.get("abbreviations", []), "abbreviations")
            ),
            identifiers=tuple(
                sorted((str(key), str(child)) for key, child in identifiers.items())
            ),
            contact=contact_value,
        )

    @staticmethod
    def _branding(value: Mapping[str, Any]) -> InstitutionBrand:
        _strict(
            value,
            "branding",
            required=frozenset({"display_name"}),
            optional=frozenset(
                {
                    "assets",
                    "colors",
                    "fonts",
                    "headers",
                    "footers",
                    "copyright_text",
                    "revision_text",
                }
            ),
        )
        assets = []
        for raw in _sequence(value.get("assets", []), "branding assets"):
            item = _mapping(raw, "brand asset")
            _strict(
                item,
                "brand asset",
                required=frozenset({"id", "kind", "path"}),
                optional=frozenset({"required", "alt_text"}),
            )
            assets.append(
                BrandAsset(
                    identifier=_text(item["id"], "brand asset id"),
                    kind=AssetKind(item["kind"]),
                    path=_path(item["path"], "brand asset path"),
                    required=bool(item.get("required", True)),
                    alt_text=item.get("alt_text"),
                )
            )
        colors = _mapping(value.get("colors", {}), "brand colors")
        return InstitutionBrand(
            display_name=_text(value["display_name"], "brand display name"),
            assets=tuple(assets),
            colors=tuple(sorted((str(key), str(child)) for key, child in colors.items())),
            fonts=tuple(_sequence(value.get("fonts", []), "fonts")),
            headers=tuple(_sequence(value.get("headers", []), "headers")),
            footers=tuple(_sequence(value.get("footers", []), "footers")),
            copyright_text=value.get("copyright_text"),
            revision_text=value.get("revision_text"),
        )

    @staticmethod
    def _calendar(value: Mapping[str, Any]) -> AcademicCalendarProfile:
        _strict(
            value,
            "academic calendar",
            required=frozenset({"calendar_id", "version", "system", "periods"}),
            optional=frozenset({"days", "metadata"}),
        )
        periods = []
        for raw in _sequence(value["periods"], "calendar periods"):
            item = _mapping(raw, "calendar period")
            _strict(
                item,
                "calendar period",
                required=frozenset({"id", "name", "start_date", "end_date"}),
            )
            periods.append(
                AcademicPeriod(
                    identifier=_text(item["id"], "period id"),
                    name=_text(item["name"], "period name"),
                    start_date=date.fromisoformat(item["start_date"]),
                    end_date=date.fromisoformat(item["end_date"]),
                )
            )
        days = []
        for raw in _sequence(value.get("days", []), "calendar days"):
            item = _mapping(raw, "calendar day")
            _strict(
                item,
                "calendar day",
                required=frozenset({"date", "kind"}),
                optional=frozenset({"name"}),
            )
            days.append(
                CalendarDay(
                    date=date.fromisoformat(item["date"]),
                    kind=CalendarDayKind(item["kind"]),
                    name=item.get("name"),
                )
            )
        metadata = _mapping(value.get("metadata", {}), "calendar metadata")
        return AcademicCalendarProfile(
            calendar_id=_text(value["calendar_id"], "calendar id"),
            version=_text(value["version"], "calendar version"),
            system=CalendarSystem(value["system"]),
            periods=tuple(periods),
            days=tuple(days),
            metadata=tuple(
                sorted((str(key), str(child)) for key, child in metadata.items())
            ),
        )

    @staticmethod
    def _grading(value: Mapping[str, Any]) -> GradingPolicy:
        _strict(
            value,
            "grading",
            required=frozenset({"system"}),
            optional=frozenset(
                {
                    "grade_bands",
                    "weighted_categories",
                    "attendance_policy",
                    "late_submission_policy",
                    "passing_threshold",
                }
            ),
        )
        bands = []
        for raw in _sequence(value.get("grade_bands", []), "grade bands"):
            item = _mapping(raw, "grade band")
            _strict(
                item,
                "grade band",
                required=frozenset({"label", "minimum"}),
            )
            bands.append(GradeBand(str(item["label"]), float(item["minimum"])))
        categories = []
        for raw in _sequence(
            value.get("weighted_categories", []), "weighted categories"
        ):
            item = _mapping(raw, "weighted category")
            _strict(
                item,
                "weighted category",
                required=frozenset({"id", "name", "weight"}),
            )
            categories.append(
                WeightedCategory(
                    str(item["id"]), str(item["name"]), float(item["weight"])
                )
            )
        threshold = value.get("passing_threshold")
        return GradingPolicy(
            system=GradingSystem(value["system"]),
            grade_bands=tuple(bands),
            weighted_categories=tuple(categories),
            attendance_policy=value.get("attendance_policy"),
            late_submission_policy=value.get("late_submission_policy"),
            passing_threshold=float(threshold) if threshold is not None else None,
        )

    @staticmethod
    def _terminology(value: Mapping[str, Any]) -> TerminologyProfile:
        _strict(
            value,
            "terminology",
            optional=frozenset({"overrides"}),
        )
        overrides = _mapping(value.get("overrides", {}), "terminology overrides")
        return TerminologyProfile(
            tuple(sorted((str(key), str(child)) for key, child in overrides.items()))
        )

    @staticmethod
    def _templates(value: Mapping[str, Any]) -> TemplateProfile:
        _strict(value, "templates", optional=frozenset({"selections"}))
        selections = []
        for raw in _sequence(value.get("selections", []), "template selections"):
            item = _mapping(raw, "template selection")
            _strict(
                item,
                "template selection",
                required=frozenset({"id", "kind", "path", "version", "format"}),
                optional=frozenset({"audience", "default"}),
            )
            selections.append(
                TemplateSelection(
                    identifier=_text(item["id"], "template id"),
                    kind=TemplateKind(item["kind"]),
                    path=_path(item["path"], "template path"),
                    version=_text(item["version"], "template version"),
                    format=_text(item["format"], "template format"),
                    audience=item.get("audience"),
                    is_default=bool(item.get("default", False)),
                )
            )
        return TemplateProfile(tuple(selections))

    @staticmethod
    def _policies(value: Mapping[str, Any]) -> OperationalPolicy:
        _strict(
            value,
            "policies",
            optional=frozenset(
                {
                    "revision_policy",
                    "document_numbering",
                    "approval_workflow",
                    "record_retention",
                    "naming_convention",
                    "output_directory_default",
                }
            ),
        )
        output = value.get("output_directory_default")
        return OperationalPolicy(
            revision_policy=value.get("revision_policy"),
            document_numbering=value.get("document_numbering"),
            approval_workflow=tuple(
                _sequence(value.get("approval_workflow", []), "approval workflow")
            ),
            record_retention=value.get("record_retention"),
            naming_convention=value.get("naming_convention"),
            output_directory_default=(
                _path(output, "output directory default") if output is not None else None
            ),
        )
