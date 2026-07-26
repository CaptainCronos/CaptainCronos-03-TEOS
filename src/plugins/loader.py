"""Import plugin entry points without coupling them to TEOS core modules."""

from __future__ import annotations

import importlib
import importlib.util
import sys
from dataclasses import dataclass
from pathlib import Path
from types import ModuleType
from typing import Any

from .discovery import PluginCandidate
from .exceptions import PluginLoadError
from .interfaces import Plugin


@dataclass(frozen=True)
class LoadedPlugin:
    """A constructed plugin and framework-owned module reference."""

    candidate: PluginCandidate
    instance: Plugin
    module_name: str
    module: ModuleType
    framework_owned_module: bool


class PluginLoader:
    """Load directory files or installed Python module entry points."""

    def load(self, candidate: PluginCandidate) -> LoadedPlugin:
        """Import and construct one validated plugin entry point."""
        module_reference, separator, attribute_path = (
            candidate.effective_entry_point.partition(":")
        )
        if not separator or not module_reference or not attribute_path:
            raise PluginLoadError(
                f"plugin {candidate.metadata.identifier!r} entry point must use "
                "module:attribute or file.py:attribute"
            )
        try:
            if module_reference.endswith(".py"):
                module, module_name = self._load_file(candidate, module_reference)
                framework_owned = True
            else:
                module = importlib.import_module(module_reference)
                module_name = module.__name__
                framework_owned = False
            target: Any = module
            for part in attribute_path.split("."):
                target = getattr(target, part)
            instance = target() if isinstance(target, type) else target
        except PluginLoadError:
            raise
        except BaseException as error:
            raise PluginLoadError(
                f"cannot load plugin {candidate.metadata.identifier!r} from "
                f"{candidate.effective_entry_point!r}"
            ) from error
        if not isinstance(instance, Plugin):
            if framework_owned:
                sys.modules.pop(module_name, None)
            raise PluginLoadError(
                f"plugin {candidate.metadata.identifier!r} entry point must "
                "construct a Plugin"
            )
        return LoadedPlugin(
            candidate=candidate,
            instance=instance,
            module_name=module_name,
            module=module,
            framework_owned_module=framework_owned,
        )

    @staticmethod
    def _load_file(
        candidate: PluginCandidate, module_reference: str
    ) -> tuple[ModuleType, str]:
        if candidate.base_path is None:
            raise PluginLoadError(
                f"file entry point for {candidate.metadata.identifier!r} "
                "requires a plugin base directory"
            )
        base = candidate.base_path.resolve()
        file_path = (base / module_reference).resolve()
        if file_path != base and base not in file_path.parents:
            raise PluginLoadError("plugin entry point must remain in its directory")
        if not file_path.is_file():
            raise PluginLoadError(f"plugin entry point does not exist: {file_path}")
        safe_identifier = candidate.metadata.identifier.replace(".", "_").replace(
            "-", "_"
        )
        version = str(candidate.metadata.version).replace(".", "_").replace("-", "_")
        module_name = f"_teos_plugin_{safe_identifier}_{version}"
        spec = importlib.util.spec_from_file_location(module_name, file_path)
        if spec is None or spec.loader is None:
            raise PluginLoadError(f"cannot create module spec for {file_path}")
        module = importlib.util.module_from_spec(spec)
        sys.modules[module_name] = module
        try:
            spec.loader.exec_module(module)
        except BaseException:
            sys.modules.pop(module_name, None)
            raise
        return module, module_name

    @staticmethod
    def unload(plugin: LoadedPlugin) -> None:
        """Release framework-owned import references."""
        if plugin.framework_owned_module:
            sys.modules.pop(plugin.module_name, None)
