"""Immutable rendering-result descriptors."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import PurePosixPath
from uuid import UUID

from src.models.lifecycle import OutputFormat
from src.scheduler import ScheduledRepository


@dataclass(frozen=True, slots=True)
class RenderedArtifact:
    """Metadata for a deterministic rendering result."""

    identifier: UUID
    renderer: str
    source_schedule: ScheduledRepository
    source_fingerprint: str
    generation_timestamp: datetime
    content_type: str
    output_filename: PurePosixPath
    output_format: OutputFormat
    template_identifier: str
    template_version: str


@dataclass(frozen=True, slots=True)
class RenderedDocument(RenderedArtifact):
    """Descriptor for one human-readable document output."""


@dataclass(frozen=True, slots=True)
class RenderedPackageEntry:
    """Descriptor for one relative entry in a rendered package."""

    filename: PurePosixPath
    content_type: str

    def __post_init__(self) -> None:
        """Keep package paths inside the package."""
        path = PurePosixPath(self.filename)
        object.__setattr__(self, "filename", path)
        if path.is_absolute() or ".." in path.parts:
            raise ValueError("package entry filename must be relative")


@dataclass(frozen=True, slots=True)
class RenderedPackage(RenderedArtifact):
    """Descriptor for a multi-entry rendering result."""

    entries: tuple[RenderedPackageEntry, ...] = ()
