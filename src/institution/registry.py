"""Deterministic in-memory registry for immutable institution profiles."""

from __future__ import annotations

from collections import defaultdict
from types import MappingProxyType
from typing import Iterable, Mapping

from .contracts import SemanticVersion
from .exceptions import ProfileRegistrationError
from .profile import InstitutionProfile


class InstitutionProfileRegistry:
    """Register, select, and inspect multiple versioned institutions."""

    __slots__ = ("_profiles", "_default")

    def __init__(
        self,
        profiles: Iterable[InstitutionProfile] = (),
        *,
        default: tuple[str, str] | None = None,
    ) -> None:
        values: dict[str, dict[str, InstitutionProfile]] = defaultdict(dict)
        for profile in profiles:
            if profile.version in values[profile.profile_id]:
                raise ProfileRegistrationError(
                    f"duplicate profile {profile.profile_id!r} version "
                    f"{profile.version!r}"
                )
            values[profile.profile_id][profile.version] = profile
        if default is not None and (
            default[0] not in values or default[1] not in values[default[0]]
        ):
            raise ProfileRegistrationError("default profile is not registered")
        self._profiles = MappingProxyType(
            {
                identifier: MappingProxyType(dict(versions))
                for identifier, versions in sorted(values.items())
            }
        )
        self._default = default

    @property
    def default(self) -> InstitutionProfile | None:
        """Return the configured default profile, if any."""
        if self._default is None:
            return None
        return self._profiles[self._default[0]][self._default[1]]

    def lookup(
        self, profile_id: str, version: str | None = None
    ) -> InstitutionProfile:
        """Return an exact version or require an unambiguous identity."""
        try:
            versions = self._profiles[profile_id]
        except KeyError as error:
            raise ProfileRegistrationError(
                f"unknown institution profile: {profile_id!r}"
            ) from error
        if version is not None:
            try:
                return versions[version]
            except KeyError as error:
                raise ProfileRegistrationError(
                    f"unknown version {version!r} for profile {profile_id!r}"
                ) from error
        if len(versions) != 1:
            raise ProfileRegistrationError(
                f"version is required for profile {profile_id!r}"
            )
        return next(iter(versions.values()))

    def latest(self, profile_id: str) -> InstitutionProfile:
        """Return the greatest semantic version registered for an identity."""
        try:
            versions = self._profiles[profile_id]
        except KeyError as error:
            raise ProfileRegistrationError(
                f"unknown institution profile: {profile_id!r}"
            ) from error
        selected = max(versions, key=SemanticVersion.parse)
        return versions[selected]

    def compatible(
        self, teos_version: str, *, profile_id: str | None = None
    ) -> tuple[InstitutionProfile, ...]:
        """Return compatible profiles in deterministic identity/version order."""
        candidates = (
            self._profiles[profile_id].values()
            if profile_id in self._profiles
            else (
                profile
                for identifier in self._profiles
                for profile in self._profiles[identifier].values()
                if profile_id is None
            )
        )
        return tuple(
            sorted(
                (
                    profile
                    for profile in candidates
                    if profile.compatibility.accepts(teos_version)
                ),
                key=lambda item: (
                    item.profile_id,
                    SemanticVersion.parse(item.version),
                ),
            )
        )

    def snapshot(self) -> Mapping[str, Mapping[str, InstitutionProfile]]:
        """Return the immutable registration mapping."""
        return self._profiles

    def __iter__(self):
        """Iterate in deterministic identity and semantic-version order."""
        return iter(
            profile
            for identifier in self._profiles
            for profile in sorted(
                self._profiles[identifier].values(),
                key=lambda item: SemanticVersion.parse(item.version),
            )
        )

    def __len__(self) -> int:
        """Return the number of registered profile versions."""
        return sum(len(versions) for versions in self._profiles.values())
