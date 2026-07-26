# ADR 0005: Plugins Use an Isolated Public Extension Boundary

## Status

Accepted

## Context

Institutions and third parties need to add renderers, generators, importers,
exporters, validators, themes, institution templates, localization, and future
categories without changing the completed TEOS engine. Direct imports from
core components to third-party packages would reverse dependency direction,
make plugin failures engine failures, and allow extensions to assume ownership
of immutable TEOS values.

The framework also needs deterministic discovery, version compatibility,
explicit permissions, dependency ordering, and clean unloading without
implementing a marketplace or remote installer.

## Decision

Plugins sit above the application and depend only on stable public plugin
interfaces. Core engine, pipeline, and CLI modules never depend on plugins.

Each plugin supplies an immutable JSON manifest. Discovery reads manifests
without importing plugin code. A manager validates the complete candidate set,
orders dependencies, checks host-granted permissions, loads entry points,
activates plugin-scoped registrations transactionally, isolates failures, and
unloads in reverse dependency order.

Extension categories are strings rather than a closed enumeration so new
categories are additive. Registrations are immutable descriptors keyed by
category and name. Plugins receive an immutable context and scoped registrar;
they do not receive mutable framework registries.

Permission enforcement is an activation gate and a boundary for host-supplied
capabilities. The framework is an in-process isolation mechanism, not a
security boundary against arbitrary malicious Python.

## Consequences

- The core architecture and pipeline remain independent of third-party code.
- Invalid or incompatible manifests are rejected before plugin import.
- One failed plugin does not terminate activation of unrelated plugins.
- Partial registrations are rolled back and unloading removes registrations.
- Dependency failures prevent dependent activation without affecting unrelated
  plugins.
- Hosts can inspect requested and granted permissions.
- Adding a category does not require changing registry internals.
- Installed plugin code must be trusted at the Python-process level.
- Strong isolation for untrusted code would require a future process protocol.
- The application embedding TEOS must explicitly connect registered extension
  values to the appropriate stable engine interfaces.

## Alternatives Considered

### Core-owned plugin hooks in every subsystem

Rejected because it would make frozen core components depend on plugins and
spread lifecycle and failure handling across the pipeline.

### A closed plugin-type enumeration

Rejected because every future category would require a framework contract
change.

### Automatic package installation

Rejected because discovery and execution do not need to own remote repository,
dependency-resolution, or installation policy.

### Claiming in-process Python is a security sandbox

Rejected because arbitrary imported Python can access process facilities.
Permission declarations remain useful and enforceable at public capability
boundaries, while hostile-code isolation requires a separate process design.
