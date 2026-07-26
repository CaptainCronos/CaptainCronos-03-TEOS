"""Common document-generator contract and physical output lifecycle."""

from __future__ import annotations

import hashlib
import os
import tempfile
from abc import ABC, abstractmethod
from pathlib import Path
from urllib.parse import unquote, urlparse

from src.models.lifecycle import OutputFormat
from src.rendering import (
    Asset,
    AssetError,
    AssetReference,
    RenderedArtifact,
    RenderingContext,
    Template,
)

from .exceptions import (
    AssetEmbeddingError,
    FileCreationError,
    OutputError,
    TemplateMismatchError,
)
from .files import GeneratedFile
from .metadata import GenerationMetadata
from .output import DocumentOutput, project_artifact


class Generator(ABC):
    """Abstract interface shared by all physical document generators."""

    version = "1.0.0"

    @property
    @abstractmethod
    def name(self) -> str:
        """Return the stable generator identity."""

    @property
    @abstractmethod
    def output_format(self) -> OutputFormat:
        """Return the canonical format produced by this generator."""

    @property
    @abstractmethod
    def mime_type(self) -> str:
        """Return the generated media type."""

    @property
    @abstractmethod
    def file_extension(self) -> str:
        """Return the required lowercase extension, including its dot."""

    def generate(
        self,
        artifact: RenderedArtifact,
        output_directory: str | Path,
        *,
        template: Template | None = None,
        context: RenderingContext | None = None,
        asset_root: str | Path | None = None,
    ) -> GeneratedFile:
        """Validate, encode, atomically write, and describe one artifact."""
        self._validate_inputs(artifact, template, context)
        root = self._validate_output_directory(output_directory)
        target = self._resolve_target(root, artifact)
        resolved_asset_root = (
            Path(asset_root).resolve()
            if asset_root is not None
            else Path.cwd().resolve()
        )
        output = project_artifact(artifact, template, context)
        payload = self._encode(
            artifact,
            output,
            template=template,
            context=context,
            asset_root=resolved_asset_root,
        )
        if not isinstance(payload, bytes):
            raise FileCreationError("generator encoder must return bytes")
        self._write_atomic(target, payload)
        checksum = "sha256:" + hashlib.sha256(payload).hexdigest()
        metadata = GenerationMetadata(
            artifact_identifier=artifact.identifier,
            generator_identity=self.name,
            generator_version=self.version,
            generation_timestamp=artifact.generation_timestamp,
        )
        return GeneratedFile(
            filename=target.name,
            path=target,
            mime_type=self.mime_type,
            generation_timestamp=artifact.generation_timestamp,
            checksum=checksum,
            size_bytes=len(payload),
            metadata=metadata,
        )

    @abstractmethod
    def _encode(
        self,
        artifact: RenderedArtifact,
        output: DocumentOutput,
        *,
        template: Template | None,
        context: RenderingContext | None,
        asset_root: Path,
    ) -> bytes:
        """Encode one validated output projection into native bytes."""

    def _validate_inputs(
        self,
        artifact: RenderedArtifact,
        template: Template | None,
        context: RenderingContext | None,
    ) -> None:
        if not isinstance(artifact, RenderedArtifact):
            raise TemplateMismatchError(
                "generator source must be a rendering RenderedArtifact"
            )
        if artifact.output_format is not self.output_format:
            raise TemplateMismatchError(
                f"{self.name} cannot generate {artifact.output_format.value}"
            )
        if artifact.content_type != self.mime_type:
            raise TemplateMismatchError(
                f"artifact content type does not match {self.name}"
            )
        if artifact.output_filename.suffix.lower() != self.file_extension:
            raise TemplateMismatchError(
                f"{self.name} output filename must end in {self.file_extension}"
            )
        if (template is None) != (context is None):
            raise TemplateMismatchError(
                "template and rendering context must be supplied together"
            )
        if template is None or context is None:
            return
        if not isinstance(template, Template) or not isinstance(
            context, RenderingContext
        ):
            raise TemplateMismatchError(
                "generation requires rendering Template and RenderingContext values"
            )
        if (
            template.identifier != artifact.template_identifier
            or template.version != artifact.template_version
        ):
            raise TemplateMismatchError(
                "template identity does not match rendered artifact"
            )
        if self.output_format not in template.supported_formats:
            raise TemplateMismatchError(
                f"template does not support {self.output_format.value}"
            )
        if context.options.output_filename != artifact.output_filename:
            raise TemplateMismatchError(
                "rendering context filename does not match artifact"
            )
        if (
            context.options.generation_timestamp
            != artifact.generation_timestamp
        ):
            raise TemplateMismatchError(
                "rendering context timestamp does not match artifact"
            )
        try:
            for requirement in template.required_assets:
                context.assets.require(requirement)
            references = list(context.theme.assets)
            if context.branding is not None:
                references.extend(context.branding.additional_assets)
                if context.branding.logo is not None:
                    references.append(context.branding.logo)
            for reference in references:
                context.assets.resolve(reference)
        except AssetError as error:
            raise AssetEmbeddingError(str(error)) from error

    @staticmethod
    def _validate_output_directory(value: str | Path) -> Path:
        root = Path(value)
        try:
            root.mkdir(parents=True, exist_ok=True)
            resolved = root.resolve(strict=True)
        except OSError as error:
            raise OutputError(f"cannot create output directory: {root}") from error
        if not resolved.is_dir():
            raise OutputError(f"output location is not a directory: {resolved}")
        return resolved

    @staticmethod
    def _resolve_target(root: Path, artifact: RenderedArtifact) -> Path:
        relative = Path(*artifact.output_filename.parts)
        if relative.is_absolute() or ".." in relative.parts:
            raise OutputError("artifact output filename must be relative")
        target = (root / relative).resolve(strict=False)
        if target != root and root not in target.parents:
            raise OutputError("generated file must remain inside output directory")
        try:
            target.parent.mkdir(parents=True, exist_ok=True)
        except OSError as error:
            raise OutputError(
                f"cannot create output parent: {target.parent}"
            ) from error
        return target

    @staticmethod
    def _write_atomic(target: Path, payload: bytes) -> None:
        temporary: Path | None = None
        try:
            descriptor, name = tempfile.mkstemp(
                prefix=f".{target.name}.", suffix=".tmp", dir=target.parent
            )
            temporary = Path(name)
            with os.fdopen(descriptor, "wb") as stream:
                stream.write(payload)
                stream.flush()
                os.fsync(stream.fileno())
            os.replace(temporary, target)
        except OSError as error:
            if temporary is not None:
                temporary.unlink(missing_ok=True)
            raise FileCreationError(
                f"cannot create generated file: {target}"
            ) from error

    @staticmethod
    def load_asset(asset: Asset, asset_root: Path) -> bytes:
        """Load one declared local asset while preventing root escape."""
        parsed = urlparse(asset.uri)
        if parsed.scheme not in {"", "file"}:
            raise AssetEmbeddingError(
                f"remote asset schemes are unsupported: {asset.identifier}"
            )
        candidate = Path(unquote(parsed.path))
        if not candidate.is_absolute():
            candidate = asset_root / candidate
        resolved = candidate.resolve(strict=False)
        if not resolved.is_file():
            raise AssetEmbeddingError(f"asset file not found: {asset.identifier}")
        try:
            return resolved.read_bytes()
        except OSError as error:
            raise AssetEmbeddingError(
                f"cannot read asset: {asset.identifier}"
            ) from error

    @staticmethod
    def logo_asset(context: RenderingContext | None) -> Asset | None:
        """Return the explicitly referenced branding logo, if any."""
        if (
            context is None
            or context.branding is None
            or context.branding.logo is None
        ):
            return None
        return context.assets.resolve(
            AssetReference(context.branding.logo.identifier)
        )
