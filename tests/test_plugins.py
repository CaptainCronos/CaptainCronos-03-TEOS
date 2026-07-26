"""Plugin framework discovery, validation, isolation, and lifecycle tests."""

from __future__ import annotations

import json
from dataclasses import FrozenInstanceError
from pathlib import Path
from types import SimpleNamespace

import pytest

from src.plugins import (
    DuplicatePluginError,
    ExtensionRegistry,
    Permission,
    PermissionSet,
    PluginCompatibilityError,
    PluginDependencyError,
    PluginDiscovery,
    PluginLoadError,
    PluginManager,
    PluginManifestError,
    PluginPermissionError,
    PluginRegistrationError,
    PluginState,
    SemanticVersion,
    VersionConstraint,
    load_manifest,
)


PLUGIN_SOURCE = """\
from dataclasses import dataclass
from src.plugins import Plugin

@dataclass(frozen=True)
class Value:
    name: str

class ExamplePlugin(Plugin):
    def activate(self, context):
        context.registrar.register(CATEGORY, Value(NAME))

    def deactivate(self, context):
        return None
"""


def write_plugin(
    root: Path,
    identifier: str,
    *,
    version: str = "1.0.0",
    teos: str = ">=1.1.0,<2.0.0",
    category: str = "theme",
    dependencies: list[dict[str, str]] | None = None,
    permissions: list[str] | None = None,
    source: str | None = None,
    entry_point: str = "plugin.py:ExamplePlugin",
) -> Path:
    """Create one complete local plugin fixture."""
    plugin_root = root / identifier
    plugin_root.mkdir()
    manifest = {
        "id": identifier,
        "version": version,
        "name": identifier,
        "author": "TEOS tests",
        "license": "MIT",
        "teos": teos,
        "capabilities": [category],
        "dependencies": dependencies or [],
        "permissions": permissions or [],
        "entry_point": entry_point,
    }
    (plugin_root / "teos-plugin.json").write_text(
        json.dumps(manifest), encoding="utf-8"
    )
    if source is not None or entry_point.startswith("plugin.py:"):
        selected_source = source if source is not None else PLUGIN_SOURCE
        selected_source = (
            f"CATEGORY = {category!r}\nNAME = {identifier!r}\n" + selected_source
        )
        (plugin_root / "plugin.py").write_text(selected_source, encoding="utf-8")
    return plugin_root


def local_discovery(root: Path) -> PluginDiscovery:
    """Return directory-only discovery for a test root."""
    return PluginDiscovery(directories=(root,), include_installed=False)


def test_manifest_is_strict_validated_and_immutable(tmp_path: Path) -> None:
    """Manifest parsing rejects drift and produces frozen metadata."""
    plugin_root = write_plugin(tmp_path, "org.example.theme")
    metadata = load_manifest(plugin_root / "teos-plugin.json")

    assert metadata.identifier == "org.example.theme"
    assert str(metadata.version) == "1.0.0"
    assert metadata.supported_teos.accepts("1.1.0")
    with pytest.raises(FrozenInstanceError):
        metadata.author = "changed"  # type: ignore[misc]

    document = json.loads((plugin_root / "teos-plugin.json").read_text())
    document["unexpected"] = True
    (plugin_root / "teos-plugin.json").write_text(json.dumps(document))
    with pytest.raises(PluginManifestError, match="unknown fields"):
        load_manifest(plugin_root / "teos-plugin.json")


def test_semantic_version_and_constraints() -> None:
    """Compatibility comparisons follow semantic-version precedence."""
    stable = SemanticVersion.parse("1.1.0")

    assert SemanticVersion.parse("1.1.0-rc.1") < stable
    assert stable > SemanticVersion.parse("1.1.0-rc.1")
    assert VersionConstraint.parse(">=1.1.0,<2.0.0").accepts(stable)
    assert not VersionConstraint.parse(">=1.2.0").accepts(stable)
    with pytest.raises(PluginManifestError):
        SemanticVersion.parse("1.1")


def test_directory_discovery_is_deterministic_and_does_not_import(
    tmp_path: Path,
) -> None:
    """Directory discovery sorts manifests and never executes entry points."""
    marker = tmp_path / "imported"
    source = f"""\
from pathlib import Path
Path({str(marker)!r}).write_text("imported")
""" + PLUGIN_SOURCE
    write_plugin(tmp_path, "org.example.zeta", source=source)
    write_plugin(tmp_path, "org.example.alpha")

    candidates = local_discovery(tmp_path).discover()

    assert [item.metadata.identifier for item in candidates] == [
        "org.example.alpha",
        "org.example.zeta",
    ]
    assert not marker.exists()


def test_installed_package_discovery_uses_manifest_without_import(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Installed entry points provide loading locations, not metadata."""
    plugin_root = write_plugin(tmp_path, "org.example.installed")
    distribution = SimpleNamespace(
        metadata={"Name": "example-distribution"},
        locate_file=lambda name: plugin_root / name,
    )
    entry_point = SimpleNamespace(
        name="installed",
        value="example_package:plugin",
        dist=distribution,
    )

    class EntryPoints(tuple):
        def select(self, *, group: str):
            assert group == "teos.plugins"
            return self

    monkeypatch.setattr(
        "src.plugins.discovery.importlib_metadata.entry_points",
        lambda: EntryPoints((entry_point,)),
    )

    candidate = PluginDiscovery().discover()[0]

    assert candidate.metadata.identifier == "org.example.installed"
    assert candidate.effective_entry_point == "example_package:plugin"
    assert candidate.source_kind == "installed"


def test_registration_loading_and_clean_unloading(tmp_path: Path) -> None:
    """Activation registers one value and unloading removes it."""
    write_plugin(tmp_path, "org.example.theme")
    manager = PluginManager(
        teos_version="1.1.0", discovery=local_discovery(tmp_path)
    )

    statuses = manager.load_all()

    assert statuses[0].state is PluginState.ACTIVE
    assert manager.registry.resolve("theme", "org.example.theme").name == (
        "org.example.theme"
    )
    assert manager.unload_all()[0].state is PluginState.UNLOADED
    with pytest.raises(PluginRegistrationError):
        manager.registry.resolve("theme", "org.example.theme")


def test_registry_rejects_duplicate_and_undeclared_categories() -> None:
    """Registration is unique and limited to manifest capabilities."""
    registry = ExtensionRegistry()
    first = registry.registrar("org.example.first", ("theme",))
    second = registry.registrar("org.example.second", ("theme",))

    first.register("theme", object(), name="plain")
    with pytest.raises(PluginRegistrationError, match="already registered"):
        second.register("theme", object(), name="plain")
    with pytest.raises(PluginRegistrationError, match="did not declare"):
        first.register("renderer", object(), name="other")


def test_teos_version_compatibility_is_checked_before_import(
    tmp_path: Path,
) -> None:
    """An incompatible host constraint fails collection validation."""
    write_plugin(tmp_path, "org.example.future", teos=">=2.0.0")
    manager = PluginManager(
        teos_version="1.1.0", discovery=local_discovery(tmp_path)
    )

    with pytest.raises(PluginCompatibilityError, match="does not support"):
        manager.load_all()


def test_permission_policy_blocks_plugin_before_import(tmp_path: Path) -> None:
    """Every declared permission must be explicitly granted by the host."""
    marker = tmp_path / "imported"
    source = f"""\
from pathlib import Path
Path({str(marker)!r}).write_text("imported")
""" + PLUGIN_SOURCE
    write_plugin(
        tmp_path,
        "org.example.files",
        permissions=["filesystem.read"],
        source=source,
    )
    manager = PluginManager(
        teos_version="1.1.0", discovery=local_discovery(tmp_path)
    )

    status = manager.load_all()[0]

    assert status.state is PluginState.FAILED
    assert isinstance(status.error, PluginPermissionError)
    assert not marker.exists()

    granted = PluginManager(
        teos_version="1.1.0",
        discovery=local_discovery(tmp_path),
        granted_permissions=PermissionSet((Permission.FILESYSTEM_READ,)),
    )
    assert granted.load_all()[0].state is PluginState.ACTIVE
    assert marker.exists()


def test_dependencies_are_ordered_and_versions_are_enforced(tmp_path: Path) -> None:
    """Dependencies activate first and incompatible requirements fail."""
    write_plugin(tmp_path, "org.example.base")
    dependent = write_plugin(
        tmp_path,
        "org.example.dependent",
        dependencies=[{"id": "org.example.base", "version": ">=1.0.0,<2.0.0"}],
    )
    manager = PluginManager(
        teos_version="1.1.0", discovery=local_discovery(tmp_path)
    )

    assert [status.plugin_id for status in manager.load_all()] == [
        "org.example.base",
        "org.example.dependent",
    ]

    document = json.loads((dependent / "teos-plugin.json").read_text())
    document["dependencies"][0]["version"] = ">=2.0.0"
    (dependent / "teos-plugin.json").write_text(json.dumps(document))
    incompatible = PluginManager(
        teos_version="1.1.0", discovery=local_discovery(tmp_path)
    )
    with pytest.raises(PluginDependencyError, match="found 1.0.0"):
        incompatible.load_all()


def test_missing_dependency_and_cycle_detection(tmp_path: Path) -> None:
    """Dependency graph validation reports missing nodes and cycles."""
    missing_root = tmp_path / "missing"
    missing_root.mkdir()
    write_plugin(
        missing_root,
        "org.example.child",
        dependencies=[{"id": "org.example.absent", "version": "*"}],
    )
    with pytest.raises(PluginDependencyError, match="missing plugin"):
        PluginManager(
            teos_version="1.1.0", discovery=local_discovery(missing_root)
        ).load_all()

    cycle_root = tmp_path / "cycle"
    cycle_root.mkdir()
    write_plugin(
        cycle_root,
        "org.example.a",
        dependencies=[{"id": "org.example.b", "version": "*"}],
    )
    write_plugin(
        cycle_root,
        "org.example.b",
        dependencies=[{"id": "org.example.a", "version": "*"}],
    )
    with pytest.raises(PluginDependencyError, match="cycle"):
        PluginManager(
            teos_version="1.1.0", discovery=local_discovery(cycle_root)
        ).load_all()


def test_activation_failure_rolls_back_and_unrelated_plugin_continues(
    tmp_path: Path,
) -> None:
    """A failed callback loses partial registrations but not unrelated work."""
    failing_source = PLUGIN_SOURCE.replace(
        "context.registrar.register(CATEGORY, Value(NAME))",
        "context.registrar.register(CATEGORY, Value(NAME))"
        '\n        raise RuntimeError("boom")',
    )
    write_plugin(tmp_path, "org.example.failing", source=failing_source)
    write_plugin(tmp_path, "org.example.healthy")
    manager = PluginManager(
        teos_version="1.1.0", discovery=local_discovery(tmp_path)
    )

    statuses = {status.plugin_id: status for status in manager.load_all()}

    assert statuses["org.example.failing"].state is PluginState.FAILED
    assert statuses["org.example.healthy"].state is PluginState.ACTIVE
    with pytest.raises(PluginRegistrationError):
        manager.registry.resolve("theme", "org.example.failing")
    assert manager.registry.resolve("theme", "org.example.healthy").name == (
        "org.example.healthy"
    )


def test_failed_dependency_skips_dependent_but_not_unrelated(
    tmp_path: Path,
) -> None:
    """Runtime dependency failure is isolated to its dependent branch."""
    failing_source = PLUGIN_SOURCE.replace(
        "context.registrar.register(CATEGORY, Value(NAME))",
        'raise RuntimeError("boom")',
    )
    write_plugin(tmp_path, "org.example.base", source=failing_source)
    write_plugin(
        tmp_path,
        "org.example.child",
        dependencies=[{"id": "org.example.base", "version": "*"}],
    )
    write_plugin(tmp_path, "org.example.independent")
    manager = PluginManager(
        teos_version="1.1.0", discovery=local_discovery(tmp_path)
    )

    statuses = {status.plugin_id: status for status in manager.load_all()}

    assert statuses["org.example.base"].state is PluginState.FAILED
    assert statuses["org.example.child"].state is PluginState.SKIPPED
    assert statuses["org.example.independent"].state is PluginState.ACTIVE


def test_duplicate_identifiers_and_missing_entry_points(tmp_path: Path) -> None:
    """Duplicate identities fail validation and missing code fails only loading."""
    first = write_plugin(tmp_path, "org.example.duplicate")
    duplicate = tmp_path / "second"
    duplicate.mkdir()
    document = json.loads((first / "teos-plugin.json").read_text())
    (duplicate / "teos-plugin.json").write_text(json.dumps(document))
    (duplicate / "plugin.py").write_text(PLUGIN_SOURCE)
    with pytest.raises(DuplicatePluginError):
        PluginManager(
            teos_version="1.1.0", discovery=local_discovery(tmp_path)
        ).load_all()

    missing_root = tmp_path / "entry"
    missing_root.mkdir()
    write_plugin(
        missing_root,
        "org.example.missing-entry",
        entry_point="absent.py:ExamplePlugin",
    )
    status = PluginManager(
        teos_version="1.1.0", discovery=local_discovery(missing_root)
    ).load_all()[0]
    assert status.state is PluginState.FAILED
    assert isinstance(status.error, PluginLoadError)


def test_deactivation_failure_still_removes_registration(tmp_path: Path) -> None:
    """Unload cleanup runs even when plugin shutdown raises."""
    source = PLUGIN_SOURCE.replace(
        "return None",
        'raise RuntimeError("shutdown failed")',
    )
    write_plugin(tmp_path, "org.example.shutdown", source=source)
    manager = PluginManager(
        teos_version="1.1.0", discovery=local_discovery(tmp_path)
    )
    manager.load_all()

    status = manager.unload_all()[0]

    assert status.state is PluginState.FAILED
    with pytest.raises(PluginRegistrationError):
        manager.registry.resolve("theme", "org.example.shutdown")
