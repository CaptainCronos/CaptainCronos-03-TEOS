"""Physical document generation, determinism, assets, and failures."""

from __future__ import annotations

import base64
import hashlib
from dataclasses import FrozenInstanceError
from pathlib import Path
from zipfile import ZipFile

import pytest

from src.generators import (
    AssetEmbeddingError,
    DocxGenerator,
    GeneratedFile,
    GeneratorRegistry,
    HtmlGenerator,
    MarkdownGenerator,
    OutputError,
    PdfGenerator,
    TemplateMismatchError,
    UnsupportedGeneratorError,
)
from src.models.lifecycle import OutputFormat
from src.rendering import (
    Asset,
    AssetCatalog,
    AssetKind,
    AssetReference,
    InstitutionBranding,
    RendererRegistry,
)
from tests.test_rendering import context, scheduled_repository, template


PNG = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR4n"
    "GNgYAAAAAMAASsJTYQAAAAASUVORK5CYII="
)


def rendered(output_format: OutputFormat, filename: str, **context_values):
    """Create an immutable descriptor and its exact approved inputs."""
    selected_template = template()
    selected_context = context(filename, **context_values)
    artifact = RendererRegistry.with_defaults().select(output_format).render(
        scheduled_repository(), selected_template, selected_context
    )
    return artifact, selected_template, selected_context


def assert_checksum(generated: GeneratedFile) -> None:
    """Verify a descriptor against the exact physical bytes."""
    expected = "sha256:" + hashlib.sha256(generated.path.read_bytes()).hexdigest()
    assert generated.checksum == expected
    assert generated.size_bytes == generated.path.stat().st_size


def test_default_registry_and_unsupported_selection() -> None:
    """The registry exposes exactly the four approved document formats."""
    registry = GeneratorRegistry.with_defaults()

    assert tuple(generator.output_format for generator in registry) == (
        OutputFormat.DOCX,
        OutputFormat.PDF,
        OutputFormat.HTML,
        OutputFormat.MARKDOWN,
    )
    assert registry.select("html").name == "html"
    with pytest.raises(UnsupportedGeneratorError):
        registry.select(OutputFormat.JSON)
    with pytest.raises(UnsupportedGeneratorError):
        registry.register(HtmlGenerator())


@pytest.mark.parametrize(
    ("output_format", "filename", "signature"),
    (
        (OutputFormat.DOCX, "schedule.docx", b"PK"),
        (OutputFormat.PDF, "schedule.pdf", b"%PDF-"),
        (OutputFormat.HTML, "schedule.html", b"<!doctype html>"),
        (OutputFormat.MARKDOWN, "schedule.md", b"# "),
    ),
)
@pytest.mark.integration
def test_all_formats_create_files_with_verified_checksums(
    tmp_path: Path,
    output_format: OutputFormat,
    filename: str,
    signature: bytes,
) -> None:
    """Every approved generator creates a native physical deliverable."""
    artifact, selected_template, selected_context = rendered(
        output_format, filename
    )

    result = GeneratorRegistry.with_defaults().select(output_format).generate(
        artifact,
        tmp_path,
        template=selected_template,
        context=selected_context,
    )

    assert result.path.read_bytes().startswith(signature)
    assert result.filename == filename
    assert result.generation_timestamp is artifact.generation_timestamp
    assert_checksum(result)
    with pytest.raises(FrozenInstanceError):
        result.checksum = "changed"  # type: ignore[misc]


@pytest.mark.parametrize(
    ("generator", "output_format", "filename"),
    (
        (DocxGenerator(), OutputFormat.DOCX, "schedule.docx"),
        (PdfGenerator(), OutputFormat.PDF, "schedule.pdf"),
        (HtmlGenerator(), OutputFormat.HTML, "schedule.html"),
        (MarkdownGenerator(), OutputFormat.MARKDOWN, "schedule.md"),
    ),
)
def test_output_is_deterministic(
    tmp_path: Path, generator, output_format: OutputFormat, filename: str
) -> None:
    """Equivalent inputs produce byte-identical files and checksums."""
    artifact, selected_template, selected_context = rendered(
        output_format, filename
    )

    first = generator.generate(
        artifact,
        tmp_path / "first",
        template=selected_template,
        context=selected_context,
    )
    second = generator.generate(
        artifact,
        tmp_path / "second",
        template=selected_template,
        context=selected_context,
    )

    assert first.path.read_bytes() == second.path.read_bytes()
    assert first.checksum == second.checksum


def test_assets_are_embedded_in_all_formats(tmp_path: Path) -> None:
    """An approved local logo becomes part of every generated deliverable."""
    asset_path = tmp_path / "logo.png"
    asset_path.write_bytes(PNG)
    logo = Asset("logo", "logo.png", "image/png", AssetKind.LOGO, "TEOS logo")
    assets = AssetCatalog((logo,))
    branding = InstitutionBranding("Example Institute", AssetReference("logo"))

    for output_format, filename in (
        (OutputFormat.DOCX, "branded.docx"),
        (OutputFormat.PDF, "branded.pdf"),
        (OutputFormat.HTML, "branded.html"),
        (OutputFormat.MARKDOWN, "branded.md"),
    ):
        artifact, selected_template, selected_context = rendered(
            output_format,
            filename,
            assets=assets,
            branding=branding,
        )
        result = GeneratorRegistry.with_defaults().select(output_format).generate(
            artifact,
            tmp_path / output_format.value,
            template=selected_template,
            context=selected_context,
            asset_root=tmp_path,
        )
        assert result.size_bytes > len(PNG)
        if output_format is OutputFormat.DOCX:
            with ZipFile(result.path) as archive:
                assert any(
                    name.startswith("word/media/")
                    for name in archive.namelist()
                )
        if output_format in {OutputFormat.HTML, OutputFormat.MARKDOWN}:
            assert b"data:image/png;base64," in result.path.read_bytes()


def test_generation_rejects_mismatches_and_invalid_output(tmp_path: Path) -> None:
    """Failures are raised before a successful output descriptor is returned."""
    artifact, selected_template, selected_context = rendered(
        OutputFormat.MARKDOWN, "schedule.md"
    )

    with pytest.raises(TemplateMismatchError):
        HtmlGenerator().generate(artifact, tmp_path)
    with pytest.raises(TemplateMismatchError):
        MarkdownGenerator().generate(
            artifact, tmp_path, template=selected_template
        )
    output_file = tmp_path / "not-a-directory"
    output_file.write_text("occupied", encoding="utf-8")
    with pytest.raises(OutputError):
        MarkdownGenerator().generate(artifact, output_file)


def test_missing_asset_file_raises_embedding_error(tmp_path: Path) -> None:
    """Catalog presence cannot conceal a missing physical resource."""
    logo = Asset("logo", "missing.png", "image/png", AssetKind.LOGO)
    artifact, selected_template, selected_context = rendered(
        OutputFormat.HTML,
        "branded.html",
        assets=AssetCatalog((logo,)),
        branding=InstitutionBranding("Example", AssetReference("logo")),
    )

    with pytest.raises(AssetEmbeddingError):
        HtmlGenerator().generate(
            artifact,
            tmp_path / "output",
            template=selected_template,
            context=selected_context,
            asset_root=tmp_path,
        )
