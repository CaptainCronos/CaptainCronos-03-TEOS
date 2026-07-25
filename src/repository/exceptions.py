"""Diagnostic exceptions raised by repository loading and validation."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping, Sequence
from uuid import UUID


class RepositoryError(Exception):
    """Base class for failures that abort repository loading."""

    def __init__(
        self,
        message: str,
        *,
        source: Path | None = None,
        path: Sequence[str | int] = (),
        details: Mapping[str, Any] | None = None,
    ) -> None:
        self.message = message
        self.source = source
        self.path = tuple(path)
        self.details = dict(details or {})
        location = str(source) if source is not None else "repository"
        if self.path:
            location = f"{location}:{'.'.join(map(str, self.path))}"
        super().__init__(f"{location}: {message}")


class SchemaValidationError(RepositoryError):
    """A JSON document does not satisfy its Draft 2020-12 schema."""


class ReferenceValidationError(RepositoryError):
    """Repository-wide reference integrity validation failed."""


class DuplicateIdentifierError(ReferenceValidationError):
    """A UUID is assigned to more than one TEOS object type."""


class DuplicateVersionError(ReferenceValidationError):
    """A repository contains the same UUID and version more than once."""


class MissingReferenceError(ReferenceValidationError):
    """An exact referenced UUID cannot be found in the repository."""


class VersionMismatchError(ReferenceValidationError):
    """A UUID exists, but the exact referenced version does not."""


class CircularReferenceError(ReferenceValidationError):
    """An ownership or composition relationship contains a cycle."""


class ConstructionError(RepositoryError):
    """Validated JSON could not be converted to its immutable domain object."""


def reference_details(
    identifier: UUID | str, version: str, object_type: str
) -> dict[str, str]:
    """Return consistent machine-readable details for a reference failure."""
    return {
        "identifier": str(identifier),
        "version": version,
        "object_type": object_type,
    }
