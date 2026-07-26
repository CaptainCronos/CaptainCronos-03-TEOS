# Plain Theme Example Plugin

This plugin demonstrates a directory manifest, immutable extension value, and
one `theme` registration. It does not modify a TEOS renderer or pipeline.

```python
from pathlib import Path

from src.plugins import PluginDiscovery, PluginManager

discovery = PluginDiscovery(
    directories=(Path("examples/plugins/plain-theme"),),
    include_installed=False,
)
manager = PluginManager(teos_version="1.1.0", discovery=discovery)
manager.load_all()
theme = manager.registry.resolve("theme", "plain")
manager.unload_all()
```
