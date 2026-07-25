"""Shared abstraction for maintained TEOS domain objects.

The base offers uniform read-only access to identity, version, lifecycle, and
metadata while allowing each approved contract to retain its native field
names.  It performs no serialization, persistence, reference resolution,
validation orchestration, scheduling, or rendering.
"""

from abc import ABC, abstractmethod
from uuid import UUID

from .lifecycle import ArtifactLifecycleStatus, LifecycleStatus
from .metadata import Metadata


Lifecycle = LifecycleStatus | ArtifactLifecycleStatus


def require_identity(identifier: UUID) -> None:
    """Enforce the local invariant that a maintained object has a UUID."""
    if not isinstance(identifier, UUID):
        raise TypeError("TEOS object identity must be a UUID")


def require_version(version: str) -> None:
    """Enforce the local invariant that a maintained object has a version."""
    if not version:
        raise ValueError("TEOS object version cannot be empty")


class TEOSObject(ABC):
    """Common immutable-domain interface for every maintained TEOS object."""

    __slots__ = ()

    @property
    @abstractmethod
    def teos_id(self) -> UUID:
        """Return the object's stable TEOS identity."""

    @property
    @abstractmethod
    def teos_version(self) -> str:
        """Return the object's schema-native semantic version."""

    @property
    @abstractmethod
    def lifecycle(self) -> Lifecycle:
        """Return the object's source or artifact lifecycle."""

    @property
    @abstractmethod
    def object_metadata(self) -> Metadata | None:
        """Return the object's schema-native optional metadata."""

    def identifier(self) -> UUID:
        """Return the stable TEOS identity."""
        return self.teos_id

    def is_draft(self) -> bool:
        """Return whether this is a draft source object."""
        return self.lifecycle is LifecycleStatus.DRAFT

    def is_approved(self) -> bool:
        """Return whether this is an approved source object."""
        return self.lifecycle is LifecycleStatus.APPROVED
