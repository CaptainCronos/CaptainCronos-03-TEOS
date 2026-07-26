"""Deterministic plugin discovery without importing plugin code."""

from __future__ import annotations

from dataclasses import dataclass
from importlib import metadata as importlib_metadata
from pathlib import Path
from typing import Iterable, Protocol

from .exceptions import PluginDiscoveryError, PluginManifestError
from .manifest import MANIFEST_FILENAME, load_manifest
from .metadata import PluginMetadata


@dataclass(frozen=True)
class PluginCandidate:
    """One discovered manifest and its local loading context."""

    metadata: PluginMetadata
    source_kind: str
    source: str
    base_path: Path | None = None
    entry_point: str | None = None

    @property
    def effective_entry_point(self) -> str:
        """Return a discovery override or the manifest entry point."""
        return self.entry_point or self.metadata.entry_point


class DiscoveryProvider(Protocol):
    """Interface for future local or repository-index discovery providers."""

    def discover(self) -> Iterable[PluginCandidate]:
        """Return candidates without importing or installing plugin code."""
        ...


class PluginDiscovery:
    """Discover configured-directory, installed, and injected candidates."""

    def __init__(
        self,
        directories: Iterable[str | Path] = (),
        providers: Iterable[DiscoveryProvider] = (),
        *,
        include_installed: bool = True,
    ) -> None:
        self._directories = tuple(Path(item) for item in directories)
        self._providers = tuple(providers)
        self._include_installed = include_installed

    def discover(self) -> tuple[PluginCandidate, ...]:
        """Return all valid candidates in a deterministic order."""
        candidates: list[PluginCandidate] = []
        candidates.extend(self._discover_directories())
        if self._include_installed:
            candidates.extend(self._discover_installed())
        for provider in self._providers:
            try:
                candidates.extend(provider.discover())
            except Exception as error:
                raise PluginDiscoveryError(
                    f"plugin discovery provider failed: {type(provider).__name__}"
                ) from error
        unique: dict[
            tuple[str, str, str, str], PluginCandidate
        ] = {}
        for candidate in candidates:
            key = (
                candidate.metadata.identifier,
                str(candidate.metadata.version),
                candidate.source_kind,
                candidate.source,
            )
            unique[key] = candidate
        return tuple(
            sorted(
                unique.values(),
                key=lambda item: (
                    item.metadata.identifier,
                    item.metadata.version,
                    item.source_kind,
                    item.source,
                ),
            )
        )

    def _discover_directories(self) -> list[PluginCandidate]:
        manifests: set[Path] = set()
        for configured in self._directories:
            root = configured.resolve()
            if not root.exists():
                raise PluginDiscoveryError(
                    f"configured plugin directory does not exist: {root}"
                )
            if not root.is_dir():
                raise PluginDiscoveryError(
                    f"configured plugin location is not a directory: {root}"
                )
            direct = root / MANIFEST_FILENAME
            if direct.is_file():
                manifests.add(direct)
            try:
                manifests.update(
                    child / MANIFEST_FILENAME
                    for child in root.iterdir()
                    if child.is_dir() and (child / MANIFEST_FILENAME).is_file()
                )
            except OSError as error:
                raise PluginDiscoveryError(
                    f"cannot search configured plugin directory: {root}"
                ) from error
        candidates: list[PluginCandidate] = []
        for manifest in sorted(manifests):
            metadata = load_manifest(manifest)
            candidates.append(
                PluginCandidate(
                    metadata=metadata,
                    source_kind="directory",
                    source=str(manifest),
                    base_path=manifest.parent,
                )
            )
        return candidates

    @staticmethod
    def _discover_installed() -> list[PluginCandidate]:
        try:
            entry_points = importlib_metadata.entry_points()
            selected = (
                entry_points.select(group="teos.plugins")
                if hasattr(entry_points, "select")
                else entry_points.get("teos.plugins", ())
            )
        except Exception as error:
            raise PluginDiscoveryError("cannot inspect installed plugins") from error
        candidates: list[PluginCandidate] = []
        for entry_point in sorted(selected, key=lambda item: (item.name, item.value)):
            distribution = entry_point.dist
            if distribution is None:
                raise PluginDiscoveryError(
                    f"installed plugin {entry_point.name!r} has no distribution"
                )
            manifest = Path(distribution.locate_file(MANIFEST_FILENAME))
            if not manifest.is_file():
                raise PluginManifestError(
                    f"installed plugin {entry_point.name!r} is missing "
                    f"{MANIFEST_FILENAME}"
                )
            candidates.append(
                PluginCandidate(
                    metadata=load_manifest(manifest),
                    source_kind="installed",
                    source=f"{distribution.metadata['Name']}:{entry_point.name}",
                    entry_point=entry_point.value,
                )
            )
        return candidates
