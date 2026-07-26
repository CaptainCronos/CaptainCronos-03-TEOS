"""Immutable plugin identity, compatibility, and dependency metadata."""

from __future__ import annotations

import re
from dataclasses import dataclass
from functools import total_ordering

from .exceptions import PluginManifestError
from .permissions import PermissionSet


_IDENTIFIER = re.compile(r"[a-z0-9](?:[a-z0-9._-]*[a-z0-9])?")
_CATEGORY = re.compile(r"[a-z][a-z0-9]*(?:[._-][a-z0-9]+)*")
_SEMVER = re.compile(
    r"(?P<major>0|[1-9]\d*)\.(?P<minor>0|[1-9]\d*)\."
    r"(?P<patch>0|[1-9]\d*)"
    r"(?:-(?P<prerelease>[0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*))?"
    r"(?:\+[0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*)?"
)
_CONSTRAINT = re.compile(r"(<=|>=|==|!=|<|>)?\s*(\S+)")


@total_ordering
@dataclass(frozen=True)
class SemanticVersion:
    """A SemVer 2.0 version suitable for deterministic compatibility checks."""

    major: int
    minor: int
    patch: int
    prerelease: tuple[str, ...] = ()

    @classmethod
    def parse(cls, value: str) -> "SemanticVersion":
        """Parse a strict semantic version."""
        if not isinstance(value, str):
            raise PluginManifestError("semantic version must be a string")
        match = _SEMVER.fullmatch(value)
        if match is None:
            raise PluginManifestError(f"invalid semantic version: {value!r}")
        prerelease = match.group("prerelease")
        parts = tuple(prerelease.split(".")) if prerelease else ()
        for part in parts:
            if part.isdigit() and len(part) > 1 and part.startswith("0"):
                raise PluginManifestError(
                    f"invalid semantic version: {value!r}"
                )
        return cls(
            int(match.group("major")),
            int(match.group("minor")),
            int(match.group("patch")),
            parts,
        )

    def __str__(self) -> str:
        base = f"{self.major}.{self.minor}.{self.patch}"
        return base if not self.prerelease else base + "-" + ".".join(self.prerelease)

    def __lt__(self, other: object) -> bool:
        if not isinstance(other, SemanticVersion):
            return NotImplemented
        core = (self.major, self.minor, self.patch)
        other_core = (other.major, other.minor, other.patch)
        if core != other_core:
            return core < other_core
        if not self.prerelease:
            return False
        if not other.prerelease:
            return True
        for left, right in zip(self.prerelease, other.prerelease):
            if left == right:
                continue
            if left.isdigit() and right.isdigit():
                return int(left) < int(right)
            if left.isdigit() != right.isdigit():
                return left.isdigit()
            return left < right
        return len(self.prerelease) < len(other.prerelease)


@dataclass(frozen=True)
class VersionConstraint:
    """A comma-separated conjunction of semantic-version comparisons."""

    clauses: tuple[tuple[str, SemanticVersion], ...] = ()

    @classmethod
    def parse(cls, value: str) -> "VersionConstraint":
        """Parse comparison clauses such as ``>=1.1.0,<2.0.0``."""
        if not isinstance(value, str) or not value.strip():
            raise PluginManifestError("version constraint must be a non-empty string")
        if value.strip() == "*":
            return cls()
        clauses: list[tuple[str, SemanticVersion]] = []
        for raw_clause in value.split(","):
            match = _CONSTRAINT.fullmatch(raw_clause.strip())
            if match is None:
                raise PluginManifestError(
                    f"invalid version constraint: {value!r}"
                )
            operator = match.group(1) or "=="
            clauses.append((operator, SemanticVersion.parse(match.group(2))))
        return cls(tuple(clauses))

    def accepts(self, version: SemanticVersion | str) -> bool:
        """Return whether a version satisfies every clause."""
        candidate = (
            SemanticVersion.parse(version)
            if isinstance(version, str)
            else version
        )
        comparisons = {
            "==": lambda expected: candidate == expected,
            "!=": lambda expected: candidate != expected,
            ">": lambda expected: candidate > expected,
            ">=": lambda expected: candidate >= expected,
            "<": lambda expected: candidate < expected,
            "<=": lambda expected: candidate <= expected,
        }
        return all(
            comparisons[operator](expected)
            for operator, expected in self.clauses
        )

    def __str__(self) -> str:
        if not self.clauses:
            return "*"
        return ",".join(f"{operator}{version}" for operator, version in self.clauses)


@dataclass(frozen=True)
class PluginDependency:
    """One exact plugin identity and its acceptable version range."""

    identifier: str
    versions: VersionConstraint

    def __post_init__(self) -> None:
        _validate_identifier(self.identifier, "dependency identifier")


@dataclass(frozen=True)
class PluginMetadata:
    """Validated immutable contents of one plugin manifest."""

    identifier: str
    version: SemanticVersion
    name: str
    author: str
    license: str
    supported_teos: VersionConstraint
    capabilities: tuple[str, ...]
    dependencies: tuple[PluginDependency, ...]
    permissions: PermissionSet
    entry_point: str

    def __post_init__(self) -> None:
        _validate_identifier(self.identifier, "plugin identifier")
        for field_name in ("name", "author", "license", "entry_point"):
            value = getattr(self, field_name)
            if not isinstance(value, str) or not value.strip():
                raise PluginManifestError(f"{field_name} must be a non-empty string")
        capabilities = tuple(sorted(set(self.capabilities)))
        if not capabilities:
            raise PluginManifestError("capabilities must contain at least one category")
        for capability in capabilities:
            if not isinstance(capability, str) or not _CATEGORY.fullmatch(capability):
                raise PluginManifestError(
                    f"invalid plugin capability: {capability!r}"
                )
        if len(self.dependencies) != len(
            {dependency.identifier for dependency in self.dependencies}
        ):
            raise PluginManifestError(
                "plugin dependencies contain duplicate identifiers"
            )
        if any(
            dependency.identifier == self.identifier
            for dependency in self.dependencies
        ):
            raise PluginManifestError("plugin cannot depend on itself")
        object.__setattr__(self, "capabilities", capabilities)
        object.__setattr__(
            self,
            "dependencies",
            tuple(sorted(self.dependencies, key=lambda item: item.identifier)),
        )


def _validate_identifier(value: str, label: str) -> None:
    if not isinstance(value, str) or not _IDENTIFIER.fullmatch(value):
        raise PluginManifestError(f"invalid {label}: {value!r}")
