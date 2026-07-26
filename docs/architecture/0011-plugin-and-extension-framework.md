# 0011: Plugin and Extension Framework

- Status: Accepted
- Scope: Define the isolated extension boundary above the standalone TEOS
  application.

> Integration update: architecture 0012 publishes `src.api` and
> `src.api.contracts` as an additional supported plugin-consumption boundary.
> Plugin lifecycle and isolation behavior in this record are unchanged.

## Architectural boundary

```text
Repository → Validation → Compilation → Scheduling → Rendering
    → Document Generation → Public Application API → CLI / Plugin Framework
```

The plugin framework consumes stable public interfaces and exposes extensions
to an embedding application. Core components never import plugin
implementations and plugins never become owners of TEOS data. The framework
does not insert itself into, or modify, the existing compilation, scheduling,
rendering, generation, or CLI pipelines.

Plugins may inspect values deliberately supplied by a host and may return new
values or services through extension points. They may not mutate curriculum,
repositories, schedules, compiled objects, rendered artifacts, generated
documents, or CLI logic. Immutable core values remain immutable across the
boundary.

## Manifest and identity

Every plugin has one immutable manifest containing:

- a globally stable plugin identifier and semantic version;
- display name, author, and license;
- a supported TEOS semantic-version constraint;
- one or more capability category names;
- exact plugin dependencies with semantic-version constraints;
- requested permissions; and
- one Python entry point in `module:attribute` or `file.py:attribute` form.

Unknown manifest fields are rejected. Identifiers, categories, dependency
identifiers, permissions, and entry points are validated before importing
plugin code. Duplicate identifiers are errors even when their versions differ;
one manager represents one deterministic resolved plugin set.

## Discovery

Discovery produces immutable candidates without importing plugin code.
Configured directories are searched one level deep for `teos-plugin.json`.
Installed packages are represented by the `teos.plugins` entry-point group and
must provide a distribution-level `teos-plugin.json`. Additional discovery
providers may be injected later for package-repository indexes, but discovery
does not download or install packages.

Candidates are sorted by plugin identifier, version, source kind, and source
location. Filesystem paths are resolved, duplicate paths are removed, and
directory order cannot affect the result.

## Registration

An extension is registered under an open category string and a stable local
name. Built-in category constants cover renderer, generator, validator,
importer, exporter, theme, institution template, and localization extensions.
Unknown future categories require no registry redesign.

Registration is scoped to the activating plugin. A plugin cannot replace an
existing `(category, name)` pair or register a category absent from its
declared capabilities. Activation uses a transaction: if registration or
startup fails, all registrations belonging to that plugin are removed.
Consumers receive immutable registration descriptors and never mutable
registry internals.

## Permissions

Permissions are explicit string values:

- `filesystem.read`
- `filesystem.write`
- `network.access`
- `template.access`
- `asset.access`

The host supplies the permissions it is willing to grant. A plugin is not
activated unless every requested permission is granted. The plugin context
allows a plugin to inspect its declaration and require a permission before
using a host-supplied capability.

This is an in-process capability and policy boundary, not an operating-system
sandbox. Python code installed into the host environment is trusted not to
bypass public interfaces. Untrusted code requires a separately designed
process or container boundary.

## Lifecycle and isolation

The lifecycle is:

```text
discovered → validated → loaded → activating → active
                                      ↓          ↓
                                    failed ← deactivating → unloaded
```

Dependencies are validated and topologically ordered before code is imported.
A dependency activates before its dependents and unloads after them. Cycles,
missing dependencies, incompatible versions, missing entry points, and
duplicate identifiers fail validation.

Loading constructs a plugin object implementing the public plugin interface.
Activation receives only an immutable context and a plugin-scoped registrar.
Exceptions are wrapped with plugin identity, recorded as a failure, and do not
stop unrelated plugins. Dependents of a failed plugin are skipped. Unloading
calls plugin shutdown, always removes its registrations, and releases
framework-owned module references.

## Exclusions

The framework does not implement a marketplace, remote package installation,
operating-system sandbox, dependency installer, pipeline interception,
repository mutation, curriculum mutation, scheduling decisions, rendering
decisions, generated-file rewriting, or new CLI commands.
