"""Repository loading, immutable indexing, and typed reference resolution."""

from .exceptions import (
    CircularReferenceError,
    ConstructionError,
    DuplicateIdentifierError,
    DuplicateVersionError,
    MissingReferenceError,
    ReferenceValidationError,
    RepositoryError,
    SchemaValidationError,
    VersionMismatchError,
)
from .registry import ObjectRegistry
from .repository import Repository
from .resolver import resolve_latest_reference, resolve_reference

__all__ = [
    "CircularReferenceError",
    "ConstructionError",
    "DuplicateIdentifierError",
    "DuplicateVersionError",
    "MissingReferenceError",
    "ObjectRegistry",
    "ReferenceValidationError",
    "Repository",
    "RepositoryError",
    "RepositoryLoader",
    "SchemaValidationError",
    "VersionMismatchError",
    "load_repository",
    "resolve_latest_reference",
    "resolve_reference",
]


def __getattr__(name: str):
    """Load the repository loader lazily to keep validation imports acyclic."""
    if name in {"RepositoryLoader", "load_repository"}:
        from .loader import RepositoryLoader, load_repository

        return {
            "RepositoryLoader": RepositoryLoader,
            "load_repository": load_repository,
        }[name]
    raise AttributeError(name)
