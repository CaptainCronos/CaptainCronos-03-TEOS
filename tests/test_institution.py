"""Institutional Profile Framework loading, validation, and registry tests."""

from __future__ import annotations

import json
from dataclasses import FrozenInstanceError
from pathlib import Path

import pytest

from src.institution import (
    BrandingError,
    CalendarConfigurationError,
    GradingConfigurationError,
    InstitutionProfileLoader,
    InstitutionProfileManager,
    InstitutionProfileRegistry,
    ProfileCompatibilityError,
    ProfileLoadError,
    ProfileRegistrationError,
    TemplateConfigurationError,
    TemplateKind,
)


ROOT = Path(__file__).resolve().parents[1]
EXAMPLE = ROOT / "institutions/example-technical-college/profile.teos-profile"
CALENDAR = ROOT / "calendars/example-technical-college-2026.teos-calendar"


def profile_document() -> dict[str, object]:
    """Return a mutable copy of the complete example profile document."""
    return json.loads(EXAMPLE.read_text(encoding="utf-8"))


def calendar_document() -> dict[str, object]:
    """Return a mutable copy of the complete example calendar document."""
    return json.loads(CALENDAR.read_text(encoding="utf-8"))


def write_package(
    root: Path,
    profile: dict[str, object],
    calendar: dict[str, object] | None = None,
) -> Path:
    """Write a profile package with its external calendar and resources."""
    profile_path = root / "institutions/example/profile.teos-profile"
    profile_path.parent.mkdir(parents=True)
    profile_path.write_text(json.dumps(profile), encoding="utf-8")
    calendar_path = root / "calendars/example-technical-college-2026.teos-calendar"
    calendar_path.parent.mkdir(parents=True)
    calendar_path.write_text(
        json.dumps(calendar or calendar_document()), encoding="utf-8"
    )
    for relative in (
        "institutions/example-technical-college/assets/primary-logo.svg",
        "templates/example-technical-college/lesson-plan.md",
    ):
        path = root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("fixture", encoding="utf-8")
    return profile_path


def load_example():
    """Load the repository example using the supported host version."""
    return InstitutionProfileLoader().load(
        EXAMPLE, teos_version="1.1.0", resource_root=ROOT
    )


def test_profile_loading_produces_immutable_configuration() -> None:
    """A complete profile and external calendar assemble immutably."""
    profile = load_example()

    assert profile.profile_id == "example-technical-college"
    assert profile.metadata.name == "Example Technical College"
    assert profile.calendars[0].periods[0].identifier == "fall-2026"
    with pytest.raises(FrozenInstanceError):
        profile.version = "2.0.0"  # type: ignore[misc]


def test_branding_and_required_asset_validation(tmp_path: Path) -> None:
    """Brand assets expose supported settings and required files must exist."""
    profile = profile_document()
    source = write_package(tmp_path, profile)
    loaded = InstitutionProfileLoader().load(
        source, teos_version="1.1.0", resource_root=tmp_path
    )

    assert dict(loaded.branding.colors)["primary"] == "#17365D"
    assert loaded.branding.assets[0].alt_text == "Example Technical College"
    (tmp_path / loaded.branding.assets[0].path).unlink()
    with pytest.raises(BrandingError, match="unavailable"):
        InstitutionProfileLoader().load(
            source, teos_version="1.1.0", resource_root=tmp_path
        )


def test_calendar_configuration_supports_periods_and_day_kinds() -> None:
    """Calendar configuration carries semester, holiday, break, and make-up facts."""
    calendar = load_example().calendars[0]

    assert calendar.system.value == "semester"
    assert {item.kind.value for item in calendar.days} == {
        "holiday",
        "break",
        "instructional",
        "make-up",
    }


def test_calendar_rejects_duplicate_and_out_of_period_dates(
    tmp_path: Path,
) -> None:
    """A calendar date is unique and belongs to a declared period."""
    calendar = calendar_document()
    days = calendar["days"]
    assert isinstance(days, list)
    days.append({"date": "2027-01-01", "kind": "instructional"})
    source = write_package(tmp_path, profile_document(), calendar)

    with pytest.raises(CalendarConfigurationError, match="outside"):
        InstitutionProfileLoader().load(
            source, teos_version="1.1.0", resource_root=tmp_path
        )


def test_grading_policy_and_weight_validation(tmp_path: Path) -> None:
    """Letter bands and weighted categories remain configuration-driven."""
    loaded = load_example()
    assert loaded.grading.grade_bands[0].label == "A"
    assert sum(item.weight for item in loaded.grading.weighted_categories) == 100

    document = profile_document()
    grading = document["grading"]
    assert isinstance(grading, dict)
    categories = grading["weighted_categories"]
    assert isinstance(categories, list)
    categories[0]["weight"] = 50
    source = write_package(tmp_path, document)
    with pytest.raises(GradingConfigurationError, match="total 100"):
        InstitutionProfileLoader().load(
            source, teos_version="1.1.0", resource_root=tmp_path
        )


def test_terminology_overrides_preserve_canonical_fallback() -> None:
    """Overrides affect presentation labels and leave other terms unchanged."""
    terminology = load_example().terminology

    assert terminology.label("Student") == "Learner"
    assert terminology.label("Course") == "Course"


def test_template_selection_and_availability(tmp_path: Path) -> None:
    """Template selection returns metadata but performs no rendering."""
    profile = load_example()
    selected = profile.templates.select(TemplateKind.LESSON_PLAN)

    assert selected.identifier == "default-lesson-plan"
    assert selected.format == "markdown"

    source = write_package(tmp_path, profile_document())
    (tmp_path / selected.path).unlink()
    with pytest.raises(TemplateConfigurationError, match="unavailable"):
        InstitutionProfileLoader().load(
            source, teos_version="1.1.0", resource_root=tmp_path
        )


def test_loader_rejects_unknown_profile_fields(tmp_path: Path) -> None:
    """Strict profile loading rejects silent configuration drift."""
    document = profile_document()
    document["business_logic"] = "not permitted"
    source = write_package(tmp_path, document)

    with pytest.raises(ProfileLoadError, match="unknown fields"):
        InstitutionProfileLoader().load(
            source, teos_version="1.1.0", resource_root=tmp_path
        )


def test_registry_handles_multiple_institutions_and_default() -> None:
    """Registration order is deterministic and defaults are explicit."""
    first = load_example()
    document = profile_document()
    document["profile_id"] = "second-college"
    metadata = document["metadata"]
    assert isinstance(metadata, dict)
    metadata["institution_id"] = "second-college"
    second = InstitutionProfileLoader().loads(
        json.dumps(document),
        teos_version="1.1.0",
        resource_root=ROOT,
    )
    registry = InstitutionProfileRegistry(
        (second, first), default=(first.profile_id, first.version)
    )

    assert [item.profile_id for item in registry] == [
        "example-technical-college",
        "second-college",
    ]
    assert registry.default is first
    assert registry.lookup("second-college") is second


def test_registry_rejects_duplicates_and_ambiguous_versions() -> None:
    """Duplicate registrations and implicit multi-version lookup are rejected."""
    profile = load_example()
    with pytest.raises(ProfileRegistrationError, match="duplicate"):
        InstitutionProfileRegistry((profile, profile))

    document = profile_document()
    document["version"] = "1.1.0"
    newer = InstitutionProfileLoader().loads(
        json.dumps(document), teos_version="1.1.0", resource_root=ROOT
    )
    registry = InstitutionProfileRegistry((profile, newer))
    assert registry.latest(profile.profile_id) is newer
    with pytest.raises(ProfileRegistrationError, match="version is required"):
        registry.lookup(profile.profile_id)


def test_version_compatibility_is_enforced() -> None:
    """Incompatible hosts are rejected before a profile is registered."""
    with pytest.raises(ProfileCompatibilityError, match="incompatible"):
        InstitutionProfileLoader().load(
            EXAMPLE, teos_version="2.0.0", resource_root=ROOT
        )


def test_manager_loads_atomically_and_selects_default(tmp_path: Path) -> None:
    """The manager publishes a new registry only after all sources load."""
    source = write_package(tmp_path, profile_document())
    manager = InstitutionProfileManager(teos_version="1.1.0")

    registry = manager.load(
        (source,),
        resource_root=tmp_path,
        default=("example-technical-college", "1.0.0"),
    )

    assert len(registry) == 1
    assert manager.select() is registry.default
