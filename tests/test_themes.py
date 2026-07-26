"""Theme loading, validation, resolution, and integration tests."""

from __future__ import annotations

from dataclasses import FrozenInstanceError
from pathlib import Path

import pytest

from src.plugins import THEME, ExtensionRegistry
from src.themes import (
    AssetError,
    AssetKind,
    Branding,
    BrandingError,
    DocumentTemplate,
    LayoutDefinition,
    LayoutError,
    StyleDefinition,
    StyleResolutionError,
    TemplateError,
    Theme,
    ThemeAsset,
    ThemeAssets,
    ThemeCompatibilityError,
    ThemeLayer,
    ThemeLayout,
    ThemeLoadError,
    ThemeLoader,
    ThemeManager,
    ThemeMetadata,
    ThemePalette,
    ThemeRegistrationError,
    ThemeRegistry,
    ThemeStyles,
    ThemeTemplates,
)


ROOT = Path(__file__).resolve().parents[1]
EXAMPLE = ROOT / "examples/themes/example-technical-college.theme.json"
BRANDING = ROOT / "examples/themes/example-department-branding.theme.yaml"


def minimal_theme(
    identifier: str,
    *,
    layer: ThemeLayer = ThemeLayer.THEME,
    extends: str | None = None,
    assets: tuple[ThemeAsset, ...] = (),
    branding: Branding = Branding(),
    styles: tuple[StyleDefinition, ...] = (),
    layouts: tuple[LayoutDefinition, ...] = (),
    templates: tuple[DocumentTemplate, ...] = (),
) -> Theme:
    """Construct one compact immutable theme for tests."""
    return Theme(
        ThemeMetadata(identifier, "1.0.0", layer),
        extends,
        branding,
        palette=ThemePalette(),
        assets=ThemeAssets(assets),
        styles=ThemeStyles(styles),
        layout=ThemeLayout(layouts),
        templates=ThemeTemplates(templates),
    )


def example_manager() -> ThemeManager:
    """Load the complete theme and its institution branding override."""
    manager = ThemeManager(default_theme_id="example.technical-college")
    manager.load((EXAMPLE, BRANDING))
    return manager


def test_theme_loading_produces_complete_immutable_resource_graph() -> None:
    """JSON loading constructs every presentation model without asset I/O."""
    loaded = ThemeLoader().load(EXAMPLE)

    assert loaded.name == "example.technical-college"
    assert loaded.branding.institution_name == "Example Technical College"
    assert loaded.assets.require("institution.logo").kind is AssetKind.LOGO
    assert loaded.typography.body is not None
    assert loaded.palette.primary == "#17365D"
    assert len(loaded.layout.items) == 9
    with pytest.raises(FrozenInstanceError):
        loaded.extends = "other"  # type: ignore[misc]


def test_theme_resolution_applies_documented_precedence_without_mutation() -> None:
    """Institution values override a theme while absent fields fall back."""
    manager = example_manager()
    original = manager.registry.require("example.technical-college")

    resolved = manager.resolve(
        "example.technical-college",
        institution_override="example.technical-college.engineering",
    )

    assert resolved.branding.department_name == "Engineering Technologies"
    assert resolved.branding.institution_name == "Example Technical College"
    assert resolved.branding.contact.email == "engineering@example.edu"
    assert resolved.branding.contact.phone == "+1-555-0100"
    assert resolved.asset("department.engineering.logo").kind is AssetKind.LOGO
    assert original.branding.department_name == ""


def test_asset_lookup_and_broken_branding_references_are_typed() -> None:
    """Exact lookup succeeds and unresolved branding assets fail validation."""
    theme = minimal_theme(
        "example.assets",
        assets=(ThemeAsset("logo.main", AssetKind.LOGO, "assets/logo.svg"),),
        branding=Branding(logo="logo.main"),
    )
    registry = ThemeRegistry((theme,))

    assert registry.require("example.assets").assets.require("logo.main").uri.endswith(
        "logo.svg"
    )
    with pytest.raises(AssetError, match="missing"):
        theme.assets.require("unknown")
    with pytest.raises(BrandingError, match="missing"):
        ThemeRegistry(
            (
                minimal_theme(
                    "example.broken", branding=Branding(logo="nope")
                ),
            )
        )


def test_style_inheritance_merges_properties_and_rejects_invalid_graphs() -> None:
    """Child properties override parents and style graphs must be closed."""
    styles = ThemeStyles(
        (
            StyleDefinition("base", {"color": "primary", "weight": 400}),
            StyleDefinition("strong", {"weight": 700}, "base"),
        )
    )

    assert dict(styles.resolve("strong")) == {"color": "primary", "weight": 700}
    with pytest.raises(StyleResolutionError, match="missing"):
        ThemeRegistry(
            (
                minimal_theme(
                    "example.missing-style",
                    styles=(StyleDefinition("child", {}, "absent"),),
                ),
            )
        )
    with pytest.raises(StyleResolutionError, match="cycle"):
        ThemeRegistry(
            (
                minimal_theme(
                    "example.style-cycle",
                    styles=(
                        StyleDefinition("one", {}, "two"),
                        StyleDefinition("two", {}, "one"),
                    ),
                ),
            )
        )


def test_template_selection_prefers_exact_format_then_neutral_fallback() -> None:
    """Template selection is deterministic and missing templates are typed."""
    resolved = example_manager().resolve("example.technical-college")

    assert resolved.template("lesson-plan", "docx").template_id == "lesson.docx"
    assert resolved.template("lesson-plan", "html").template_id == "lesson.default"
    with pytest.raises(TemplateError, match="missing template"):
        resolved.template("quiz", "pdf")


def test_layout_configuration_and_references_are_validated() -> None:
    """Layouts retain document kinds and reject broken style references."""
    resolved = example_manager().resolve("example.technical-college")

    certificate = resolved.layouts_for("certificate")
    assert len(certificate) == 1
    assert certificate[0].orientation.value == "landscape"
    with pytest.raises(LayoutError, match="missing style"):
        ThemeRegistry(
            (
                minimal_theme(
                    "example.layout-broken",
                    layouts=(
                        LayoutDefinition(
                            "lesson", "lesson-plan", style_refs=("absent",)
                        ),
                    ),
                ),
            )
        )


def test_builtin_and_default_theme_fallbacks_are_always_available() -> None:
    """A manager resolves a safe built-in theme and fills selected omissions."""
    manager = ThemeManager()
    builtin = manager.resolve()
    assert builtin.typography.body is not None

    manager.register(minimal_theme("example.sparse"))
    sparse = manager.resolve("example.sparse")
    assert sparse.typography.body is not None
    assert "teos.builtin" in sparse.source_theme_ids

    configured = ThemeManager(default_theme_id="example.default")
    configured.register(
        Theme(
            ThemeMetadata(
                "example.default", "1.0.0", ThemeLayer.DEFAULT
            ),
            palette=ThemePalette(primary="#123456"),
        )
    )
    configured.register(minimal_theme("example.child"))
    assert configured.resolve("example.child").palette.primary == "#123456"


def test_registry_rejects_duplicate_themes_and_parent_cycles() -> None:
    """Theme identity and inheritance graphs remain unambiguous."""
    first = minimal_theme("example.same")
    with pytest.raises(ThemeRegistrationError, match="duplicate"):
        ThemeRegistry((first, first))

    one = minimal_theme("example.one", extends="example.two")
    two = minimal_theme("example.two", extends="example.one")
    with pytest.raises(ThemeRegistrationError, match="cycle"):
        ThemeRegistry((one, two))


def test_version_compatibility_is_enforced() -> None:
    """Unsupported contract versions fail before registration."""
    with pytest.raises(ThemeCompatibilityError, match="supported contract"):
        Theme(
            ThemeMetadata(
                "example.future",
                "1.0.0",
                ThemeLayer.THEME,
                contract_version="2.0",
            )
        )


def test_plugin_themes_copy_through_the_existing_extension_boundary() -> None:
    """Plugin-owned immutable theme values register without plugin execution."""
    extensions = ExtensionRegistry()
    registrar = extensions.registrar("example.plugin", (THEME,))
    registrar.register(THEME, minimal_theme("plugin.accessible"))
    manager = ThemeManager()

    assert manager.register_plugin_extensions(extensions) == 1
    assert manager.resolve("plugin.accessible").theme_id == "plugin.accessible"


def test_loader_rejects_unknown_duplicate_and_invalid_input_atomically(
    tmp_path: Path,
) -> None:
    """Strict package failures do not replace the manager's active registry."""
    manager = example_manager()
    original = manager.registry
    duplicate = tmp_path / "duplicate.json"
    duplicate.write_text(
        '{"theme_id":"example.one","theme_id":"example.two","version":"1.0.0"}',
        encoding="utf-8",
    )
    with pytest.raises(ThemeLoadError, match="duplicate"):
        manager.load((duplicate,))
    assert manager.registry is original

    unknown = tmp_path / "unknown.yaml"
    unknown.write_text(
        "theme_id: example.unknown\nversion: 1.0.0\nmystery: true\n",
        encoding="utf-8",
    )
    with pytest.raises(ThemeLoadError, match="unsupported fields"):
        manager.load((unknown,))
    assert manager.registry is original


def test_template_asset_layout_and_style_references_must_resolve() -> None:
    """Templates cannot publish broken dependencies."""
    template = DocumentTemplate(
        "lesson",
        "lesson-plan",
        "templates/lesson",
        layout_ref="missing",
        style_refs=("unknown",),
        required_assets=("absent",),
    )
    with pytest.raises(TemplateError, match="missing layout"):
        ThemeRegistry(
            (
                minimal_theme(
                    "example.template-broken", templates=(template,)
                ),
            )
        )

    with pytest.raises(TemplateError, match="missing required template"):
        ThemeRegistry((minimal_theme("example.no-report"),)).validate(
            required_template_kinds=("report",)
        )

    manager = ThemeManager(default_theme_id="example.technical-college")
    manager.load((EXAMPLE, BRANDING), required_template_kinds=("report",))
