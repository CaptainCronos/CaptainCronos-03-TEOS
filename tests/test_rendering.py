"""Rendering framework registration, contracts, and immutability tests."""

from dataclasses import FrozenInstanceError
from datetime import datetime, timezone
from pathlib import PurePosixPath

import pytest

from src.models.lifecycle import ArtifactType, OutputFormat
from src.rendering import (
    Asset,
    AssetCatalog,
    AssetError,
    AssetKind,
    AssetReference,
    AssetRequirement,
    DocxRenderer,
    FormattingError,
    ImageStyle,
    InstitutionBranding,
    MarkdownRenderer,
    MissingAssetError,
    MissingBrandingError,
    RenderedDocument,
    RenderedPackage,
    RendererRegistry,
    RenderingContext,
    RenderingContextError,
    RenderOptions,
    Template,
    TemplateError,
    TemplateRegion,
    TemplateRegistry,
    Theme,
    UnsupportedOutputError,
    UnsupportedRendererError,
    UnsupportedTemplateError,
)
from src.scheduler import Scheduler, SchedulingContext
from tests.test_scheduler import compiled_fixture


GENERATED_AT = datetime(2026, 7, 25, 12, tzinfo=timezone.utc)


def scheduled_repository():
    """Create a real immutable ScheduledRepository fixture."""
    compiled, profile, calendar = compiled_fixture()
    return Scheduler().schedule_repository(
        compiled, (SchedulingContext(profile, calendar),)
    )


def template(
    *,
    formats: tuple[OutputFormat, ...] = (
        OutputFormat.DOCX,
        OutputFormat.PDF,
        OutputFormat.HTML,
        OutputFormat.MARKDOWN,
    ),
    required_assets: tuple[AssetRequirement, ...] = (),
    requires_branding: bool = False,
    required_context: tuple[str, ...] = (),
) -> Template:
    """Create a renderer-independent schedule template."""
    return Template(
        identifier="course-schedule",
        version="1.0.0",
        artifact_type=ArtifactType.SCHEDULE,
        supported_formats=formats,
        regions=(
            TemplateRegion("title", "heading"),
            TemplateRegion("schedule", "table"),
        ),
        required_assets=required_assets,
        requires_branding=requires_branding,
        required_context=required_context,
    )


def context(
    filename: str = "course-schedule.md",
    *,
    assets: AssetCatalog = AssetCatalog(),
    branding: InstitutionBranding | None = None,
    theme: Theme = Theme(),
) -> RenderingContext:
    """Create a fixed, reproducible presentation context."""
    return RenderingContext(
        options=RenderOptions(PurePosixPath(filename), GENERATED_AT),
        assets=assets,
        branding=branding,
        theme=theme,
    )


def test_default_renderer_registration_and_selection() -> None:
    """The registry selects all four framework formats."""
    registry = RendererRegistry.with_defaults()

    assert tuple(renderer.output_format for renderer in registry) == (
        OutputFormat.DOCX,
        OutputFormat.PDF,
        OutputFormat.HTML,
        OutputFormat.MARKDOWN,
    )
    assert registry.select("markdown").name == "markdown"
    assert registry.select(OutputFormat.PDF).content_type == "application/pdf"


def test_duplicate_and_unsupported_renderer_selection() -> None:
    """Registration and selection reject ambiguous or unknown formats."""
    registry = RendererRegistry((MarkdownRenderer(),))

    with pytest.raises(UnsupportedRendererError):
        registry.register(MarkdownRenderer())
    with pytest.raises(UnsupportedRendererError):
        registry.select(OutputFormat.JSON)
    with pytest.raises(UnsupportedRendererError):
        registry.select("epub")


def test_template_loading_is_exact_and_duplicate_safe() -> None:
    """Template loading resolves an exact identity and version in memory."""
    selected = template()
    registry = TemplateRegistry((selected,))

    assert registry.load("course-schedule", "1.0.0") is selected
    with pytest.raises(TemplateError):
        registry.load("course-schedule", "2.0.0")
    with pytest.raises(TemplateError):
        registry.register(selected)


def test_asset_resolution_and_media_type_contract() -> None:
    """Assets resolve by reference without embedding or loading content."""
    logo = Asset(
        "logo",
        "assets/logo.svg",
        "image/svg+xml",
        AssetKind.LOGO,
    )
    catalog = AssetCatalog((logo,))
    requirement = AssetRequirement(
        AssetReference("logo"), ("image/svg+xml",)
    )

    assert catalog.resolve(AssetReference("logo")) is logo
    assert catalog.require(requirement) is logo
    with pytest.raises(MissingAssetError):
        catalog.resolve(AssetReference("missing"))
    with pytest.raises(AssetError):
        catalog.require(
            AssetRequirement(AssetReference("logo"), ("image/png",))
        )


def test_context_and_formatting_invariants() -> None:
    """Context and formatting values reject unsafe presentation settings."""
    valid = context()

    assert valid.options.output_filename == PurePosixPath(
        "course-schedule.md"
    )
    with pytest.raises(RenderingContextError):
        RenderOptions(PurePosixPath("../outside.md"), GENERATED_AT)
    with pytest.raises(RenderingContextError):
        RenderOptions(
            PurePosixPath("schedule.md"), datetime(2026, 7, 25)
        )
    with pytest.raises(FormattingError):
        ImageStyle(max_width_percent=101)


def test_rendered_descriptor_is_immutable_and_preserves_source_identity() -> None:
    """A result retains the exact source and cannot be edited."""
    source = scheduled_repository()
    result = MarkdownRenderer().render(source, template(), context())

    assert isinstance(result, RenderedDocument)
    assert result.source_schedule is source
    assert result.output_format is OutputFormat.MARKDOWN
    assert result.content_type == "text/markdown; charset=utf-8"
    assert result.generation_timestamp is GENERATED_AT
    with pytest.raises(FrozenInstanceError):
        result.renderer = "changed"  # type: ignore[misc]


def test_descriptor_generation_is_deterministic() -> None:
    """Equivalent requests yield the same identifier and source digest."""
    source = scheduled_repository()
    renderer = MarkdownRenderer()

    first = renderer.render(source, template(), context())
    second = renderer.render(source, template(), context())

    assert first == second
    assert first.identifier == second.identifier
    assert first.source_fingerprint == second.source_fingerprint
    assert first.source_fingerprint.startswith("sha256:")


@pytest.mark.parametrize(
    ("output_format", "filename", "content_type"),
    (
        (
            OutputFormat.DOCX,
            "schedule.docx",
            "application/vnd.openxmlformats-officedocument."
            "wordprocessingml.document",
        ),
        (OutputFormat.PDF, "schedule.pdf", "application/pdf"),
        (OutputFormat.HTML, "schedule.html", "text/html; charset=utf-8"),
        (
            OutputFormat.MARKDOWN,
            "schedule.md",
            "text/markdown; charset=utf-8",
        ),
    ),
)
def test_all_formats_return_descriptors_only(
    output_format: OutputFormat, filename: str, content_type: str
) -> None:
    """Each framework renderer returns metadata without producing files."""
    renderer = RendererRegistry.with_defaults().select(output_format)

    result = renderer.render(
        scheduled_repository(), template(), context(filename)
    )

    assert result.content_type == content_type
    assert result.output_filename == PurePosixPath(filename)
    assert not hasattr(result, "content")


def test_template_format_and_filename_are_checked() -> None:
    """Incompatible templates and output filenames fail before rendering."""
    source = scheduled_repository()
    renderer = DocxRenderer()

    with pytest.raises(UnsupportedTemplateError):
        renderer.render(
            source,
            template(formats=(OutputFormat.MARKDOWN,)),
            context("schedule.docx"),
        )
    with pytest.raises(UnsupportedOutputError):
        renderer.render(source, template(), context("schedule.pdf"))


def test_required_assets_context_and_branding_are_checked() -> None:
    """Template presentation dependencies must be explicitly supplied."""
    source = scheduled_repository()
    logo_reference = AssetReference("logo")
    selected = template(
        required_assets=(AssetRequirement(logo_reference),),
        requires_branding=True,
        required_context=("theme",),
    )

    with pytest.raises(MissingBrandingError):
        MarkdownRenderer().render(source, selected, context())
    with pytest.raises(MissingAssetError):
        MarkdownRenderer().render(
            source,
            selected,
            context(
                branding=InstitutionBranding("Example", logo_reference)
            ),
        )

    assets = AssetCatalog(
        (
            Asset(
                "logo",
                "assets/logo.svg",
                "image/svg+xml",
                AssetKind.LOGO,
            ),
        )
    )
    result = MarkdownRenderer().render(
        source,
        selected,
        context(
            assets=assets,
            branding=InstitutionBranding("Example", logo_reference),
        ),
    )
    assert result.template_identifier == "course-schedule"


def test_referenced_theme_assets_are_resolved() -> None:
    """Theme asset references participate in request checking."""
    with pytest.raises(MissingAssetError):
        MarkdownRenderer().render(
            scheduled_repository(),
            template(),
            context(theme=Theme(assets=(AssetReference("icon"),))),
        )


def test_rendered_package_is_an_immutable_descriptor() -> None:
    """Package results remain descriptors and contain no persistence API."""
    document = MarkdownRenderer().render(
        scheduled_repository(), template(), context()
    )
    package = RenderedPackage(
        identifier=document.identifier,
        renderer=document.renderer,
        source_schedule=document.source_schedule,
        source_fingerprint=document.source_fingerprint,
        generation_timestamp=document.generation_timestamp,
        content_type="application/zip",
        output_filename=PurePosixPath("schedule.zip"),
        output_format=document.output_format,
        template_identifier=document.template_identifier,
        template_version=document.template_version,
    )

    assert package.entries == ()
    with pytest.raises(FrozenInstanceError):
        package.entries = ()  # type: ignore[misc]
