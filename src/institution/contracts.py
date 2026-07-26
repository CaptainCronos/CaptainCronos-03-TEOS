"""Shared immutable contracts for institution profile configuration."""

from __future__ import annotations

import re
from dataclasses import dataclass
from enum import StrEnum
from functools import total_ordering
from pathlib import PurePosixPath
from types import MappingProxyType
from typing import Any, Mapping

from .exceptions import ProfileCompatibilityError, ProfileLoadError


FRAMEWORK_VERSION = "1.0.0"
SUPPORTED_CONTRACT_VERSION = "1.0"

_SEMVER = re.compile(
    r"(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)"
    r"(?:-([0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*))?"
)
_CONSTRAINT = re.compile(r"(<=|>=|==|!=|<|>)?\s*(\S+)")


@total_ordering
@dataclass(frozen=True, slots=True)
class SemanticVersion:
    """Strict semantic version used for deterministic profile selection."""

    major: int
    minor: int
    patch: int
    prerelease: tuple[str, ...] = ()

    @classmethod
    def parse(cls, value: str) -> "SemanticVersion":
        """Parse a SemVer 2.0 version without accepting abbreviated forms."""
        if not isinstance(value, str):
            raise ProfileLoadError("semantic version must be a string")
        match = _SEMVER.fullmatch(value)
        if match is None:
            raise ProfileLoadError(f"invalid semantic version: {value!r}")
        prerelease = tuple(match.group(4).split(".")) if match.group(4) else ()
        if any(
            part.isdigit() and len(part) > 1 and part.startswith("0")
            for part in prerelease
        ):
            raise ProfileLoadError(f"invalid semantic version: {value!r}")
        return cls(
            int(match.group(1)),
            int(match.group(2)),
            int(match.group(3)),
            prerelease,
        )

    def __str__(self) -> str:
        core = f"{self.major}.{self.minor}.{self.patch}"
        return core if not self.prerelease else core + "-" + ".".join(self.prerelease)

    def __lt__(self, other: object) -> bool:
        if not isinstance(other, SemanticVersion):
            return NotImplemented
        left_core = (self.major, self.minor, self.patch)
        right_core = (other.major, other.minor, other.patch)
        if left_core != right_core:
            return left_core < right_core
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


@dataclass(frozen=True, slots=True)
class VersionCompatibility:
    """Conjunction of TEOS semantic-version compatibility clauses."""

    clauses: tuple[tuple[str, SemanticVersion], ...] = ()

    @classmethod
    def parse(cls, value: str) -> "VersionCompatibility":
        """Parse constraints such as ``>=1.1.0,<2.0.0`` or ``*``."""
        if not isinstance(value, str) or not value.strip():
            raise ProfileLoadError("compatibility must be a non-empty string")
        if value.strip() == "*":
            return cls()
        clauses: list[tuple[str, SemanticVersion]] = []
        for raw_clause in value.split(","):
            match = _CONSTRAINT.fullmatch(raw_clause.strip())
            if match is None:
                raise ProfileLoadError(f"invalid compatibility: {value!r}")
            clauses.append(
                (match.group(1) or "==", SemanticVersion.parse(match.group(2)))
            )
        return cls(tuple(clauses))

    def accepts(self, version: SemanticVersion | str) -> bool:
        """Return whether the candidate satisfies every compatibility clause."""
        candidate = (
            SemanticVersion.parse(version) if isinstance(version, str) else version
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
            comparisons[operator](expected) for operator, expected in self.clauses
        )

    def require(self, version: str) -> None:
        """Raise when a TEOS version does not satisfy this contract."""
        if not self.accepts(version):
            raise ProfileCompatibilityError(
                f"TEOS {version} is incompatible with profile requirement {self}"
            )

    def __str__(self) -> str:
        return (
            "*"
            if not self.clauses
            else ",".join(f"{operator}{version}" for operator, version in self.clauses)
        )


class AssetKind(StrEnum):
    """Institution-owned external asset categories."""

    LOGO = "logo"
    WATERMARK = "watermark"
    FONT = "font"


@dataclass(frozen=True, slots=True)
class ResourceReference:
    """Versioned reference to a separately owned configuration resource."""

    identifier: str
    path: PurePosixPath
    version: str | None = None
    required: bool = True

    def __post_init__(self) -> None:
        if not self.identifier:
            raise ValueError("resource identifier cannot be empty")
        if self.path.is_absolute() or ".." in self.path.parts:
            raise ValueError("resource path must be a safe relative path")


def immutable_mapping(values: Mapping[str, Any]) -> Mapping[str, Any]:
    """Return a stable read-only shallow mapping."""
    return MappingProxyType(dict(sorted(values.items())))
