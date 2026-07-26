"""Immutable descriptors for generated files, directories, and packages."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from .metadata import GenerationMetadata


def _validate_checksum(value: str) -> None:
    algorithm, separator, digest = value.partition(":")
    if (
        separator != ":"
        or algorithm != "sha256"
        or len(digest) != 64
        or any(character not in "0123456789abcdef" for character in digest)
    ):
        raise ValueError("checksum must be a lowercase sha256 digest")


@dataclass(frozen=True, slots=True)
class GeneratedFile:
    """Descriptor for one successfully written physical file."""

    filename: str
    path: Path
    mime_type: str
    generation_timestamp: datetime
    checksum: str
    size_bytes: int
    metadata: GenerationMetadata

    def __post_init__(self) -> None:
        """Validate descriptor identity without touching the file system."""
        path = Path(self.path)
        object.__setattr__(self, "path", path)
        if not self.filename or Path(self.filename).name != self.filename:
            raise ValueError("generated filename must be a basename")
        if path.name != self.filename:
            raise ValueError("generated path and filename must agree")
        if "/" not in self.mime_type:
            raise ValueError("mime type is invalid")
        if self.size_bytes < 0:
            raise ValueError("file size cannot be negative")
        _validate_checksum(self.checksum)


@dataclass(frozen=True, slots=True)
class GeneratedDirectory:
    """Descriptor for an ordered collection of generated files."""

    filename: str
    path: Path
    mime_type: str
    checksum: str
    files: tuple[GeneratedFile, ...]
    generation_timestamp: datetime

    def __post_init__(self) -> None:
        """Validate directory naming and manifest checksum."""
        path = Path(self.path)
        object.__setattr__(self, "path", path)
        if path.name != self.filename:
            raise ValueError("generated directory path and filename must agree")
        if self.mime_type != "inode/directory":
            raise ValueError("generated directory mime type is invalid")
        _validate_checksum(self.checksum)


@dataclass(frozen=True, slots=True)
class GeneratedPackage:
    """Descriptor for an ordered downloadable deliverable."""

    filename: str
    path: Path
    mime_type: str
    generation_timestamp: datetime
    checksum: str
    files: tuple[GeneratedFile, ...]
    metadata: GenerationMetadata

    def __post_init__(self) -> None:
        """Validate package naming and checksum."""
        path = Path(self.path)
        object.__setattr__(self, "path", path)
        if path.name != self.filename:
            raise ValueError("generated package path and filename must agree")
        if "/" not in self.mime_type:
            raise ValueError("mime type is invalid")
        _validate_checksum(self.checksum)
