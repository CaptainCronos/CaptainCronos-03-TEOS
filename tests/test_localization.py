"""Localization loading, resolution, formatting, and integration tests."""

from __future__ import annotations

import json
from dataclasses import FrozenInstanceError
from datetime import date, datetime, timezone
from pathlib import Path

import pytest

from src.localization import (
    BUILTIN_ENGLISH,
    FallbackResolutionError,
    FormattingError,
    Language,
    Locale,
    LocaleError,
    LocalizationManager,
    LocalizationRegistry,
    LocalizationResource,
    LocalizationResourceLoader,
    ResourceCompatibilityError,
    ResourceLayer,
    ResourceLoadError,
    ResourceMetadata,
    ResourceRegistrationError,
    Terminology,
    Translation,
)
from src.plugins import LOCALIZATION, ExtensionRegistry


ROOT = Path(__file__).resolve().parents[1]
SPANISH = ROOT / "examples/localization/es-ES.teos-locale.json"


def manager_with_spanish() -> LocalizationManager:
    """Return a manager containing the complete example Spanish pack."""
    manager = LocalizationManager()
    manager.load((SPANISH,))
    return manager


def resource(
    identifier: str,
    locale_id: str = "en-US",
    *,
    layer: ResourceLayer = ResourceLayer.PLUGIN,
    translations: tuple[Translation, ...] = (),
    terminology: tuple[Terminology, ...] = (),
    locale: Locale | None = None,
) -> LocalizationResource:
    """Create one minimal test resource."""
    return LocalizationResource(
        ResourceMetadata(identifier, "1.0.0"),
        locale_id,
        layer,
        translations,
        terminology,
        locale=locale,
    )


def test_language_loading_produces_immutable_resource_graph() -> None:
    """A data pack loads language, region, locale, and immutable mappings."""
    loaded = LocalizationResourceLoader().load(SPANISH)

    assert loaded.language == Language("es", "Spanish", "Español")
    assert loaded.locale is not None
    assert loaded.locale.region is not None
    assert loaded.locale.region.code == "ES"
    assert loaded.locale.conventions.paper_size == "a4"
    with pytest.raises(FrozenInstanceError):
        loaded.locale_id = "fr-FR"  # type: ignore[misc]


def test_locale_resolution_normalizes_identifiers_and_rejects_unknown() -> None:
    """Locale selection is normalized, exact, and explicit."""
    manager = manager_with_spanish()

    assert manager.registry.locale("es_es").identifier == "es-ES"
    assert manager.registry.language("es").native_name == "Español"
    with pytest.raises(LocaleError, match="unsupported locale"):
        manager.formatter("fr-FR")


def test_translation_lookup_pluralization_and_interpolation() -> None:
    """Translations select locale plural rules and named parameters."""
    manager = manager_with_spanish()

    assert manager.translate(
        "document.generated_on",
        locale="es-ES",
        parameters={"date": "26/07/2026"},
    ) == "Generado el 26/07/2026"
    assert manager.translate("count.sessions", locale="es-ES", count=1) == "1 sesión"
    assert manager.translate("count.sessions", locale="es-ES", count=3) == "3 sesiones"


def test_fallback_behavior_reaches_english_and_missing_keys_are_nonfatal() -> None:
    """Declared fallback reaches English and absent content records a warning."""
    manager = manager_with_spanish()

    fallback_only = resource(
        "plugin.fallback-only",
        translations=(Translation.singular("plugin.fallback", "English fallback"),),
    )
    manager.register(fallback_only)
    assert manager.translate("plugin.fallback", locale="es-ES") == "English fallback"
    assert manager.translate(
        "unknown.presentation.key", locale="es-ES"
    ) == "unknown.presentation.key"
    assert manager.resolver.diagnostics[-1].code == "localization.translation.missing"


def test_formatting_rules_cover_dates_numbers_percent_currency_and_pages() -> None:
    """Formatting uses resource conventions without process-global locale state."""
    formatter = manager_with_spanish().formatter("es-ES")

    assert formatter.format_date(date(2026, 7, 26)) == "26/07/2026"
    assert formatter.format_time(datetime(2026, 7, 26, 16, 5)) == "16:05"
    assert formatter.format_number("12345.678", decimal_places=2) == "12.345,68"
    assert formatter.format_percentage("0.256", decimal_places=1) == "25,6%"
    assert formatter.format_currency("1234.5") == "1.234,50 €"
    assert formatter.format_page_number(14, style="roman") == "xiv"
    assert formatter.format_measurement(12, "centimeter") == "12 cm"
    assert formatter.quote("Curso") == "«Curso»"


def test_time_zone_formatting_converts_aware_values() -> None:
    """Time zones use deterministic IANA conversions and reject naive input."""
    formatter = manager_with_spanish().formatter("es-ES")
    instant = datetime(2026, 7, 26, 14, 0, tzinfo=timezone.utc)

    assert formatter.format_time(instant, time_zone="Europe/Madrid") == "16:00"
    with pytest.raises(FormattingError, match="aware"):
        formatter.convert_time_zone(datetime(2026, 7, 26, 14, 0), "UTC")


def test_terminology_and_institution_overrides_use_highest_precedence() -> None:
    """Institution labels override language terms without mutating the pack."""
    manager = manager_with_spanish()
    override = manager.institution_override(
        "example-college",
        "es-ES",
        translations={"document.course_title": "Asignatura"},
        terminology={"Course": "Asignatura"},
    )
    manager.register(override)

    assert manager.translate("document.course_title", locale="es-ES") == "Asignatura"
    assert manager.term("Course", locale="es-ES") == "Asignatura"
    assert LocalizationResourceLoader().load(SPANISH).term("Course") == "Curso"


def test_registry_rejects_duplicate_identifiers_and_ambiguous_keys() -> None:
    """Registration identity and same-precedence message ownership are unique."""
    first = resource(
        "plugin.first", translations=(Translation.singular("plugin.title", "First"),)
    )
    duplicate_key = resource(
        "plugin.second", translations=(Translation.singular("plugin.title", "Second"),)
    )

    with pytest.raises(ResourceRegistrationError, match="identifier"):
        LocalizationRegistry((BUILTIN_ENGLISH, first, first))
    with pytest.raises(ResourceRegistrationError, match="duplicate translation"):
        LocalizationRegistry((BUILTIN_ENGLISH, first, duplicate_key))


def test_plugin_localization_is_copied_from_existing_extension_boundary() -> None:
    """Active plugin localization resources integrate without plugin ownership."""
    extension_registry = ExtensionRegistry()
    registrar = extension_registry.registrar("example.plugin", (LOCALIZATION,))
    plugin_resource = resource(
        "plugin.example.en-us",
        translations=(Translation.singular("plugin.greeting", "Hello plugin"),),
    )
    registrar.register(LOCALIZATION, plugin_resource)
    manager = LocalizationManager()

    assert manager.register_plugin_extensions(extension_registry) == 1
    assert manager.translate("plugin.greeting") == "Hello plugin"


def test_missing_resources_and_atomic_manager_loading(tmp_path: Path) -> None:
    """Unreadable and invalid packs fail without replacing the active registry."""
    manager = manager_with_spanish()
    original = manager.registry

    with pytest.raises(ResourceLoadError, match="cannot read"):
        manager.load((tmp_path / "missing.json",))
    assert manager.registry is original

    malformed = tmp_path / "bad.json"
    malformed.write_text('{"resource_id":"bad","resource_id":"again"}', encoding="utf-8")
    with pytest.raises(ResourceLoadError, match="duplicate"):
        manager.load((malformed,))
    assert manager.registry is original


def test_validation_detects_broken_fallbacks_and_missing_translations() -> None:
    """Fallback graphs are closed and required-key gaps are diagnostics."""
    broken_locale = Locale(
        "fr-FR", "fr", "Français (France)", fallback="de-DE"
    )
    broken = resource(
        "language.fr-fr",
        "fr-FR",
        layer=ResourceLayer.LANGUAGE,
        locale=broken_locale,
    )
    with pytest.raises(FallbackResolutionError, match="unsupported"):
        LocalizationRegistry((BUILTIN_ENGLISH, broken))

    diagnostics = manager_with_spanish().registry.validate(
        required_translation_keys=("document.course_title", "missing.required")
    )
    assert any(item.key == "missing.required" for item in diagnostics)


def test_loader_rejects_invalid_definitions_and_compatibility(tmp_path: Path) -> None:
    """Strict loading rejects unsupported fields, locales, and contracts."""
    document = json.loads(SPANISH.read_text(encoding="utf-8"))
    document["unexpected"] = True
    invalid = tmp_path / "invalid.json"
    invalid.write_text(json.dumps(document), encoding="utf-8")
    with pytest.raises(ResourceLoadError, match="unsupported fields"):
        LocalizationResourceLoader().load(invalid)

    document.pop("unexpected")
    document["contract_version"] = "2.0"
    invalid.write_text(json.dumps(document), encoding="utf-8")
    with pytest.raises(ResourceCompatibilityError):
        LocalizationResourceLoader().load(invalid)


def test_yaml_language_pack_loading_and_non_english_default(tmp_path: Path) -> None:
    """YAML is equivalent to JSON and a future default can be selected at load."""
    import yaml

    document = json.loads(SPANISH.read_text(encoding="utf-8"))
    source = tmp_path / "es-ES.yaml"
    source.write_text(yaml.safe_dump(document, allow_unicode=True), encoding="utf-8")
    manager = LocalizationManager(default_locale="es-ES")

    manager.load((source,))

    assert manager.translate("document.course_title") == "Curso"
