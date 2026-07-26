"""High-level loading and deterministic selection of institution profiles."""

from __future__ import annotations

from pathlib import Path
from typing import Iterable

from .exceptions import ProfileRegistrationError
from .loader import InstitutionProfileLoader
from .profile import InstitutionProfile
from .registry import InstitutionProfileRegistry


class InstitutionProfileManager:
    """Build an immutable registry and expose host-compatible selections."""

    def __init__(
        self,
        *,
        teos_version: str,
        loader: InstitutionProfileLoader | None = None,
    ) -> None:
        self.teos_version = teos_version
        self.loader = loader or InstitutionProfileLoader()
        self._registry = InstitutionProfileRegistry()

    @property
    def registry(self) -> InstitutionProfileRegistry:
        """Return the current immutable registry snapshot."""
        return self._registry

    def load(
        self,
        sources: Iterable[str | Path],
        *,
        resource_root: str | Path | None = None,
        default: tuple[str, str] | None = None,
    ) -> InstitutionProfileRegistry:
        """Atomically replace the registry from deterministically sorted sources."""
        ordered = tuple(sorted((Path(item) for item in sources), key=lambda item: str(item)))
        profiles = tuple(
            self.loader.load(
                item,
                teos_version=self.teos_version,
                resource_root=resource_root,
            )
            for item in ordered
        )
        registry = InstitutionProfileRegistry(profiles, default=default)
        self._registry = registry
        return registry

    def select(
        self, profile_id: str | None = None, *, version: str | None = None
    ) -> InstitutionProfile:
        """Select an exact profile, or use the configured default."""
        if profile_id is None:
            selected = self._registry.default
            if selected is None:
                raise ProfileRegistrationError("no default profile is configured")
            return selected
        return self._registry.lookup(profile_id, version)
