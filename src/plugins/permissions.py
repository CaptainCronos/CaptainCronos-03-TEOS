"""Immutable permission declarations for plugin capability boundaries."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Iterable, Iterator

from .exceptions import PluginManifestError, PluginPermissionError


class Permission(str, Enum):
    """Permissions understood by the TEOS plugin framework."""

    FILESYSTEM_READ = "filesystem.read"
    FILESYSTEM_WRITE = "filesystem.write"
    NETWORK_ACCESS = "network.access"
    TEMPLATE_ACCESS = "template.access"
    ASSET_ACCESS = "asset.access"


@dataclass(frozen=True)
class PermissionSet:
    """An ordered, duplicate-free collection of explicit permissions."""

    permissions: tuple[Permission, ...] = ()

    def __post_init__(self) -> None:
        normalized = tuple(sorted(set(self.permissions), key=lambda item: item.value))
        object.__setattr__(self, "permissions", normalized)

    @classmethod
    def from_values(cls, values: Iterable[str]) -> "PermissionSet":
        """Parse manifest permission strings."""
        parsed: list[Permission] = []
        for value in values:
            try:
                parsed.append(Permission(value))
            except (TypeError, ValueError) as error:
                raise PluginManifestError(
                    f"unknown plugin permission: {value!r}"
                ) from error
        return cls(tuple(parsed))

    def allows(self, permission: Permission) -> bool:
        """Return whether this set grants one permission."""
        return permission in self.permissions

    def require(self, permission: Permission, *, plugin_id: str) -> None:
        """Raise when a plugin attempts to use an ungranted capability."""
        if not self.allows(permission):
            raise PluginPermissionError(
                f"plugin {plugin_id!r} does not have {permission.value!r}"
            )

    def missing_from(self, granted: "PermissionSet") -> tuple[Permission, ...]:
        """Return declared permissions absent from the host grant."""
        return tuple(
            permission
            for permission in self.permissions
            if not granted.allows(permission)
        )

    def __contains__(self, permission: object) -> bool:
        return permission in self.permissions

    def __iter__(self) -> Iterator[Permission]:
        return iter(self.permissions)

    def __len__(self) -> int:
        return len(self.permissions)
