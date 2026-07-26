"""Strict JSON manifest parsing for plugins."""

from __future__ import annotations

import json
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from .exceptions import PluginManifestError
from .metadata import (
    PluginDependency,
    PluginMetadata,
    SemanticVersion,
    VersionConstraint,
)
from .permissions import PermissionSet


MANIFEST_FILENAME = "teos-plugin.json"
_FIELDS = {
    "id",
    "version",
    "name",
    "author",
    "license",
    "teos",
    "capabilities",
    "dependencies",
    "permissions",
    "entry_point",
}


def load_manifest(path: str | Path) -> PluginMetadata:
    """Read and validate one UTF-8 JSON plugin manifest."""
    source = Path(path)
    try:
        document = json.loads(source.read_text(encoding="utf-8"))
    except OSError as error:
        raise PluginManifestError(f"cannot read plugin manifest: {source}") from error
    except (UnicodeError, json.JSONDecodeError) as error:
        raise PluginManifestError(f"invalid JSON plugin manifest: {source}") from error
    try:
        return parse_manifest(document)
    except PluginManifestError as error:
        raise PluginManifestError(f"{source}: {error}") from error


def parse_manifest(document: Any) -> PluginMetadata:
    """Validate a decoded manifest and return immutable metadata."""
    if not isinstance(document, Mapping):
        raise PluginManifestError("manifest must be a JSON object")
    keys = set(document)
    missing = _FIELDS - keys
    unknown = keys - _FIELDS
    if missing:
        raise PluginManifestError(
            "manifest is missing fields: " + ", ".join(sorted(missing))
        )
    if unknown:
        raise PluginManifestError(
            "manifest has unknown fields: " + ", ".join(sorted(unknown))
        )
    capabilities = _string_list(document["capabilities"], "capabilities")
    permissions = _string_list(document["permissions"], "permissions")
    dependencies_value = document["dependencies"]
    if not isinstance(dependencies_value, list):
        raise PluginManifestError("dependencies must be a JSON array")
    dependencies: list[PluginDependency] = []
    for index, dependency in enumerate(dependencies_value):
        if not isinstance(dependency, Mapping) or set(dependency) != {"id", "version"}:
            raise PluginManifestError(
                f"dependencies[{index}] must contain only id and version"
            )
        dependencies.append(
            PluginDependency(
                identifier=_string(dependency["id"], f"dependencies[{index}].id"),
                versions=VersionConstraint.parse(
                    _string(
                        dependency["version"],
                        f"dependencies[{index}].version",
                    )
                ),
            )
        )
    return PluginMetadata(
        identifier=_string(document["id"], "id"),
        version=SemanticVersion.parse(_string(document["version"], "version")),
        name=_string(document["name"], "name"),
        author=_string(document["author"], "author"),
        license=_string(document["license"], "license"),
        supported_teos=VersionConstraint.parse(_string(document["teos"], "teos")),
        capabilities=capabilities,
        dependencies=tuple(dependencies),
        permissions=PermissionSet.from_values(permissions),
        entry_point=_string(document["entry_point"], "entry_point"),
    )


def _string(value: Any, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise PluginManifestError(f"{label} must be a non-empty string")
    return value


def _string_list(value: Any, label: str) -> tuple[str, ...]:
    if not isinstance(value, list):
        raise PluginManifestError(f"{label} must be a JSON array")
    result = tuple(_string(item, f"{label} item") for item in value)
    if len(result) != len(set(result)):
        raise PluginManifestError(f"{label} must not contain duplicates")
    return result
