"""Immutable, exact-version node identities for maintained TEOS objects."""

from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from src.models.base import TEOSObject
from src.models.lifecycle import ReferenceObjectType
from src.repository.registry import object_type_for


@dataclass(frozen=True, slots=True, order=True)
class NodeKey:
    """Identify one maintained object version without version substitution."""

    object_type: ReferenceObjectType
    identifier: UUID
    version: str

    def __post_init__(self) -> None:
        """Require exact typed identity fields."""
        if not isinstance(self.object_type, ReferenceObjectType):
            raise TypeError("node object type must be a ReferenceObjectType")
        if not isinstance(self.identifier, UUID):
            raise TypeError("node identifier must be a UUID")
        if not self.version:
            raise ValueError("node version cannot be empty")

    def __str__(self) -> str:
        """Return the stable diagnostic form of the node identity."""
        return f"{self.object_type.value}:{self.identifier}@{self.version}"


@dataclass(frozen=True, slots=True)
class GraphNode:
    """Pair an exact node identity with its immutable source domain object."""

    key: NodeKey
    value: TEOSObject

    def __post_init__(self) -> None:
        """Require the key to agree with the retained source object."""
        expected = NodeKey(
            object_type_for(self.value),
            self.value.teos_id,
            self.value.teos_version,
        )
        if self.key != expected:
            raise ValueError(f"node key {self.key} does not identify its value")

    @classmethod
    def from_object(cls, value: TEOSObject) -> GraphNode:
        """Create the exact graph node for one maintained domain object."""
        return cls(
            key=NodeKey(
                object_type_for(value), value.teos_id, value.teos_version
            ),
            value=value,
        )
