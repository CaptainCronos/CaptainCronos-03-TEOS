# TEOS Plugin and Extension Framework

The plugin framework lets an embedding application discover and activate local
extensions without changing the TEOS engine or pipeline. Its architectural
boundary is defined by
[0011: Plugin and Extension Framework](architecture/0011-plugin-and-extension-framework.md).

## Extension lifecycle

1. Discovery reads manifests from configured directories, installed
   `teos.plugins` entry points, and optional injected discovery providers.
2. Validation rejects malformed manifests, duplicate identifiers, unsupported
   TEOS versions, missing or incompatible dependencies, and cycles.
3. The manager orders plugins so dependencies load first.
4. Permission policy rejects a plugin before import when its declarations are
   not granted by the host.
5. The loader imports the entry point and constructs a `Plugin`.
6. `activate(context)` registers extensions through the scoped registrar.
7. Activation becomes atomic: a callback failure removes every registration
   from that plugin and leaves unrelated plugins available.
8. `deactivate(context)` runs during reverse dependency-order unloading.
   Registrations and framework-owned module references are removed even when
   deactivation fails.

Statuses are immutable and inspectable through `PluginManager.statuses`.
Runtime failures are attached to only the affected plugin. A dependent is
skipped when its dependency is not active.

## Manifest format

Each plugin directory contains `teos-plugin.json`:

```json
{
  "id": "org.example.plain-theme",
  "version": "1.0.0",
  "name": "Plain Theme",
  "author": "Example Institution",
  "license": "MIT",
  "teos": ">=1.1.0,<2.0.0",
  "capabilities": ["theme"],
  "dependencies": [],
  "permissions": ["template.access", "asset.access"],
  "entry_point": "plugin.py:PlainThemePlugin"
}
```

All fields are required and unknown fields are rejected. `id` is a lowercase
stable identifier. `version` is strict SemVer. `teos` and dependency versions
are comma-separated comparisons using `==`, `!=`, `<`, `<=`, `>`, or `>=`;
`*` accepts every version. Dependencies contain only `id` and `version`.
Capabilities use lowercase category names. The entry point is either
`module:attribute` for an installed package or `file.py:attribute` relative to
the manifest directory.

Installed packages expose an entry point in the `teos.plugins` group and place
`teos-plugin.json` at the distribution root. The package entry-point value
overrides the manifest loading location while the manifest remains the source
of plugin metadata.

## Discovery model

Configured roots may be a single plugin directory or a parent whose immediate
children are plugin directories. Discovery does not recurse beyond that
boundary, execute code, install packages, or contact remote repositories.
Candidates are ordered by identifier, semantic version, source kind, and
source location. An injected `DiscoveryProvider` can represent a future
read-only repository index without redesigning manager or registry contracts.

## Registration model

The registrar accepts a category, extension object, and optional stable name:

```python
context.registrar.register("theme", theme, name="plain")
```

If `name` is omitted, the extension must expose a string `name` attribute.
The plugin must declare the category in its manifest. A `(category, name)` pair
is unique across the manager. Registration descriptors retain their owner and
are returned in deterministic order.

Built-in constants cover:

- `renderer`
- `generator`
- `validator`
- `importer`
- `exporter`
- `theme`
- `institution-template`
- `localization`

Categories are open strings, so future categories are additive. Registered
objects should implement the stable public interface expected by the embedding
application. The framework stores them without importing frozen engine
registries or inserting them into a core pipeline.

## Permission model

Manifests may declare `filesystem.read`, `filesystem.write`,
`network.access`, `template.access`, and `asset.access`. The host constructs a
`PermissionSet` and grants it to `PluginManager`. Every requested permission
must be granted before plugin code is imported. Plugins can use
`context.require_permission(...)` before accessing a host-supplied capability.

Declarations are explicit policy and capability checks. They do not prevent
malicious installed Python from using process APIs directly. Only trusted
in-process plugins should be loaded; hostile-code isolation requires a
separate process or container.

## Version compatibility

The host passes its TEOS version explicitly:

```python
manager = PluginManager(teos_version="1.1.0")
```

The manifest's `teos` constraint must accept that version. Every dependency
must be present once and its discovered version must satisfy the declaring
plugin's constraint. The manager rejects the complete set before importing
code when compatibility or dependency validation fails.

## Extension guidelines

- Import only from `src.plugins` and the stable public interface associated
  with the extension category.
- Treat every TEOS object supplied by a host as immutable.
- Keep curriculum, institution, calendar, and generated artifact data out of
  plugin manifests.
- Declare only capabilities and permissions actually used.
- Perform registration in `activate` and release plugin-owned resources in
  `deactivate`.
- Do not alter global registries, CLI handlers, core pipeline stages, or source
  data.
- Keep callbacks deterministic and raise a precise exception on failure.
- Use new category names for genuinely new extension contracts rather than
  overloading an existing category.

The working example is under `examples/plugins/plain-theme/`.
