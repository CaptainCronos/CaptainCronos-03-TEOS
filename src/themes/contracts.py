"""Shared contracts, identifiers, and immutable helpers for themes."""

from __future__ import annotations

import re
from enum import IntEnum, StrEnum
from types import MappingProxyType
from typing import Any, Mapping


FRAMEWORK_VERSION = "1.0.0"
THEME_CONTRACT_VERSION = "1.0"

_IDENTIFIER = re.compile(r"[a-z0-9](?:[a-z0-9._-]*[a-z0-9])?")
_NAME = re.compile(r"[A-Za-z][A-Za-z0-9_.-]*")
_SEMVER = re.compile(r"\d+\.\d+\.\d+(?:-[A-Za-z0-9.-]+)?")


class ThemeLayer(IntEnum):
    """Stable precedence of theme resource sources."""

    BUILTIN = 10
    DEFAULT = 20
    THEME = 30
    INSTITUTION = 40


class AssetKind(StrEnum):
    """Supported classes of externally managed presentation assets."""

    LOGO = "logo"
    ICON = "icon"
    BACKGROUND = "background"
    BANNER = "banner"
    WATERMARK = "watermark"
    SEAL = "seal"
    ILLUSTRATION = "illustration"
    GRAPHIC = "graphic"


class Orientation(StrEnum):
    """Supported logical page orientations."""

    PORTRAIT = "portrait"
    LANDSCAPE = "landscape"


def require_identifier(value: str, *, label: str = "identifier") -> str:
    """Require one stable lowercase identifier."""
    if not isinstance(value, str) or _IDENTIFIER.fullmatch(value) is None:
        raise ValueError(f"invalid {label}: {value!r}")
    return value


def require_name(value: str, *, label: str = "name") -> str:
    """Require one stable case-sensitive resource name."""
    if not isinstance(value, str) or _NAME.fullmatch(value) is None:
        raise ValueError(f"invalid {label}: {value!r}")
    return value


def require_semver(value: str) -> str:
    """Require a semantic version accepted by the theme contract."""
    if not isinstance(value, str) or _SEMVER.fullmatch(value) is None:
        raise ValueError(f"invalid semantic version: {value!r}")
    return value


def frozen_mapping(
    values: Mapping[str, Any] | tuple[tuple[str, Any], ...] = (),
) -> Mapping[str, Any]:
    """Return a sorted, recursively immutable mapping."""
    source = dict(values)
    return MappingProxyType(
        {str(key): freeze_value(value) for key, value in sorted(source.items())}
    )


def freeze_value(value: Any) -> Any:
    """Recursively freeze JSON-shaped style property values."""
    if isinstance(value, Mapping):
        return frozen_mapping(value)
    if isinstance(value, (list, tuple)):
        return tuple(freeze_value(item) for item in value)
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    raise TypeError(f"theme property is not immutable JSON data: {value!r}")
