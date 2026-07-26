"""Dependency-aware plugin validation, activation, and clean unloading."""

from __future__ import annotations

from collections.abc import Iterable

from .discovery import PluginCandidate, PluginDiscovery
from .exceptions import (
    DuplicatePluginError,
    PluginCompatibilityError,
    PluginDependencyError,
    PluginLifecycleError,
    PluginPermissionError,
)
from .interfaces import PluginContext
from .lifecycle import PluginState, PluginStatus
from .loader import LoadedPlugin, PluginLoader
from .metadata import SemanticVersion
from .permissions import PermissionSet
from .registry import ExtensionRegistry
from .sandbox import PluginSandbox


class PluginManager:
    """Coordinate a deterministic set of isolated plugin lifecycles."""

    def __init__(
        self,
        *,
        teos_version: str,
        discovery: PluginDiscovery | None = None,
        registry: ExtensionRegistry | None = None,
        granted_permissions: PermissionSet = PermissionSet(),
        loader: PluginLoader | None = None,
        sandbox: PluginSandbox | None = None,
    ) -> None:
        self.teos_version = SemanticVersion.parse(teos_version)
        self.discovery = discovery or PluginDiscovery()
        self.registry = registry or ExtensionRegistry()
        self.granted_permissions = granted_permissions
        self.loader = loader or PluginLoader()
        self.sandbox = sandbox or PluginSandbox()
        self._candidates: dict[str, PluginCandidate] = {}
        self._order: tuple[str, ...] = ()
        self._loaded: dict[str, LoadedPlugin] = {}
        self._contexts: dict[str, PluginContext] = {}
        self._statuses: dict[str, PluginStatus] = {}

    def discover(self) -> tuple[PluginCandidate, ...]:
        """Discover candidates and mark them for later validation."""
        candidates = self.discovery.discover()
        self._statuses = {
            candidate.metadata.identifier: PluginStatus(
                candidate.metadata.identifier, PluginState.DISCOVERED
            )
            for candidate in candidates
        }
        return candidates

    def validate(
        self, candidates: Iterable[PluginCandidate] | None = None
    ) -> tuple[PluginCandidate, ...]:
        """Validate identity, host compatibility, dependencies, and cycles."""
        selected = tuple(candidates) if candidates is not None else self.discover()
        by_identifier: dict[str, PluginCandidate] = {}
        duplicates: set[str] = set()
        for candidate in selected:
            identifier = candidate.metadata.identifier
            if identifier in by_identifier:
                duplicates.add(identifier)
            by_identifier[identifier] = candidate
        if duplicates:
            raise DuplicatePluginError(
                "duplicate plugin identifiers: " + ", ".join(sorted(duplicates))
            )
        for identifier, candidate in sorted(by_identifier.items()):
            metadata = candidate.metadata
            if not metadata.supported_teos.accepts(self.teos_version):
                raise PluginCompatibilityError(
                    f"plugin {identifier!r} {metadata.version} does not support "
                    f"TEOS {self.teos_version}"
                )
            for dependency in metadata.dependencies:
                target = by_identifier.get(dependency.identifier)
                if target is None:
                    raise PluginDependencyError(
                        f"plugin {identifier!r} requires missing plugin "
                        f"{dependency.identifier!r}"
                    )
                if not dependency.versions.accepts(target.metadata.version):
                    raise PluginDependencyError(
                        f"plugin {identifier!r} requires {dependency.identifier!r} "
                        f"{dependency.versions}, found {target.metadata.version}"
                    )
        order = self._dependency_order(by_identifier)
        self._candidates = by_identifier
        self._order = order
        self._statuses = {
            identifier: PluginStatus(identifier, PluginState.VALIDATED)
            for identifier in order
        }
        return tuple(by_identifier[identifier] for identifier in order)

    def load_all(
        self, candidates: Iterable[PluginCandidate] | None = None
    ) -> tuple[PluginStatus, ...]:
        """Validate and activate plugins while isolating runtime failures."""
        self.validate(candidates)
        for identifier in self._order:
            candidate = self._candidates[identifier]
            failed_dependencies = tuple(
                dependency.identifier
                for dependency in candidate.metadata.dependencies
                if self._statuses[dependency.identifier].state is not PluginState.ACTIVE
            )
            if failed_dependencies:
                error = PluginDependencyError(
                    f"plugin {identifier!r} skipped because dependencies are not "
                    f"active: {', '.join(failed_dependencies)}"
                )
                self._statuses[identifier] = PluginStatus(
                    identifier, PluginState.SKIPPED, error
                )
                continue
            missing = candidate.metadata.permissions.missing_from(
                self.granted_permissions
            )
            if missing:
                error = PluginPermissionError(
                    f"plugin {identifier!r} requires ungranted permissions: "
                    + ", ".join(permission.value for permission in missing)
                )
                self._statuses[identifier] = PluginStatus(
                    identifier, PluginState.FAILED, error
                )
                continue
            try:
                loaded = self.loader.load(candidate)
            except Exception as error:
                self._statuses[identifier] = PluginStatus(
                    identifier, PluginState.FAILED, error
                )
                continue
            self._loaded[identifier] = loaded
            self._statuses[identifier] = PluginStatus(
                identifier, PluginState.LOADED
            )
            registrar = self.registry.registrar(
                identifier, candidate.metadata.capabilities
            )
            context = PluginContext(
                metadata=candidate.metadata,
                permissions=candidate.metadata.permissions,
                registrar=registrar,
            )
            self._contexts[identifier] = context
            self._statuses[identifier] = PluginStatus(
                identifier, PluginState.ACTIVATING
            )
            result = self.sandbox.execute(
                lambda loaded=loaded, context=context: loaded.instance.activate(
                    context
                )
            )
            if not result.succeeded:
                self.registry.unregister_plugin(identifier)
                self.loader.unload(loaded)
                del self._loaded[identifier]
                del self._contexts[identifier]
                error = PluginLifecycleError(
                    f"plugin {identifier!r} activation failed"
                )
                error.__cause__ = result.error
                self._statuses[identifier] = PluginStatus(
                    identifier, PluginState.FAILED, error
                )
                continue
            self._statuses[identifier] = PluginStatus(
                identifier, PluginState.ACTIVE
            )
        return self.statuses

    def unload(self, plugin_id: str) -> PluginStatus:
        """Unload an active plugin and any active dependents first."""
        if plugin_id not in self._statuses:
            raise PluginLifecycleError(f"unknown plugin: {plugin_id}")
        dependents = [
            identifier
            for identifier in reversed(self._order)
            if identifier in self._loaded
            and any(
                dependency.identifier == plugin_id
                for dependency in self._candidates[identifier].metadata.dependencies
            )
        ]
        for dependent in dependents:
            self.unload(dependent)
        return self._unload_one(plugin_id)

    def unload_all(self) -> tuple[PluginStatus, ...]:
        """Unload active plugins in reverse dependency order."""
        for identifier in reversed(self._order):
            if identifier in self._loaded:
                self._unload_one(identifier)
        return self.statuses

    def status(self, plugin_id: str) -> PluginStatus:
        """Return current status for one managed plugin."""
        try:
            return self._statuses[plugin_id]
        except KeyError as error:
            raise PluginLifecycleError(f"unknown plugin: {plugin_id}") from error

    @property
    def statuses(self) -> tuple[PluginStatus, ...]:
        """Return statuses in deterministic dependency order."""
        return tuple(
            self._statuses[identifier]
            for identifier in self._order
            if identifier in self._statuses
        )

    def _unload_one(self, identifier: str) -> PluginStatus:
        loaded = self._loaded.get(identifier)
        if loaded is None:
            return self._statuses[identifier]
        context = self._contexts[identifier]
        self._statuses[identifier] = PluginStatus(
            identifier, PluginState.DEACTIVATING
        )
        result = self.sandbox.execute(
            lambda: loaded.instance.deactivate(context)
        )
        self.registry.unregister_plugin(identifier)
        self.loader.unload(loaded)
        del self._loaded[identifier]
        del self._contexts[identifier]
        if result.succeeded:
            status = PluginStatus(identifier, PluginState.UNLOADED)
        else:
            error = PluginLifecycleError(
                f"plugin {identifier!r} deactivation failed"
            )
            error.__cause__ = result.error
            status = PluginStatus(identifier, PluginState.FAILED, error)
        self._statuses[identifier] = status
        return status

    @staticmethod
    def _dependency_order(
        candidates: dict[str, PluginCandidate]
    ) -> tuple[str, ...]:
        visiting: list[str] = []
        complete: set[str] = set()
        order: list[str] = []

        def visit(identifier: str) -> None:
            if identifier in complete:
                return
            if identifier in visiting:
                start = visiting.index(identifier)
                cycle = visiting[start:] + [identifier]
                raise PluginDependencyError(
                    "plugin dependency cycle: " + " -> ".join(cycle)
                )
            visiting.append(identifier)
            dependencies = candidates[identifier].metadata.dependencies
            for dependency in dependencies:
                visit(dependency.identifier)
            visiting.pop()
            complete.add(identifier)
            order.append(identifier)

        for identifier in sorted(candidates):
            visit(identifier)
        return tuple(order)
