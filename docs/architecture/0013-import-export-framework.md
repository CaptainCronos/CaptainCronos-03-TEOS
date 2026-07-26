# 0013: Import / Export Framework

- Status: Accepted
- Scope: Define deterministic translation between external interchange formats
  and the TEOS Public Application API.

## Architectural boundary

```text
External representation
        ↓
Import / Export Framework
        ↓
Public Application API
        ↓
Repository → Validation → Compilation → Scheduling → Rendering → Generation
```

`src.interoperability` is a translation boundary. Importers decode external
representations into immutable request objects published by `src.api`.
`InteroperabilityManager.execute_import` is the only framework operation that
submits a translated request, and it does so through
`TEOSApplication.execute`. Exporters project immutable public API responses and
artifact descriptors into external representations.

The framework never constructs, mutates, or publishes repository, registry,
domain, compiled, scheduled, rendered, or generator implementation objects.
Because API version 1.0 contains no repository-write operation, import does not
persist curriculum. Adding such behavior requires a separately accepted public
API contract.

## Translation contracts

An importer receives text or bytes and an immutable `ImportContext`. It
validates syntax, checks an explicit format version, identifies one public API
operation, validates the operation's request fields, and returns an immutable
`ImportResult`. A successful result contains exactly one public request and
preserves source location and SHA-256 attribution.

An exporter receives one immutable `OperationResponse` and an immutable
`ExportContext`. It checks the requested format version, creates a stable
public-response projection, and returns an immutable `ExportResult`. It does
not write a file; an embedding application owns persistence and transport.

## Context and options

Contexts contain only input configuration. `FormatOptions` controls encoding,
line endings, CSV delimiter, indentation, and deterministic key ordering.
`ConversionOptions` controls strict unknown-field handling and whether
diagnostics are included in exports. Nested option mappings are frozen into
sorted tuples.

## Registry

The registry stores importer and exporter capabilities independently. A
capability declares a stable name, kind, supported format versions, filename
extensions, and media types. Registration rejects duplicate names and
capability/implementation mismatches. Lookups use exact normalized names and
exact declared versions; discovery by extension or media type is sorted and
rejects ambiguity.

Built-ins are registered in a fixed order by the default manager. Plugin
extensions registered in the existing `importer` and `exporter` categories can
be copied into the interoperability registry. Plugin ownership and lifecycle
remain with `src.plugins`; this framework does not load plugin code.

## Diagnostics and failures

Translation diagnostics are immutable and ordered. Stable kinds cover
unsupported fields, data truncation, unknown values, missing mandatory fields,
version mismatch, and unsupported features. A diagnostic records severity,
message, optional source, field path, and source position.

`ImportExportError` is the root exception. `ImportError` and `ExportError`
separate translation direction; `FormatError`, `CompatibilityError`, and
`TranslationError` identify invalid syntax, unsupported versions, and failed
semantic translation. Invalid syntax and unsupported capabilities raise;
representable source problems are returned as diagnostics.

## Versioning

Framework contract version `1.0` identifies the Python interoperability
contracts. Every external document independently declares format version
`1.0`. Compatibility is exact and capability-specific. Additive formats or
versions may be registered without changing existing behavior. A changed
field meaning, request mapping, or serialized response shape requires a new
format version; a breaking Python contract change requires a new framework
major version.

## Built-in formats

- JSON and YAML imports use an envelope containing `format_version`,
  `operation`, and `request`.
- CSV imports use one header row and one request row. Complex values use
  canonical JSON within a cell.
- Markdown imports use YAML front matter with the same envelope followed by
  optional human-readable content.
- JSON, YAML, CSV, and Markdown exporters publish the same stable response
  information in representations appropriate to each format.

## Exclusions

The framework does not implement REST, cloud synchronization, databases,
remote repositories, LMS integrations, curriculum rules, scheduling,
rendering, generation, API mutation, repository persistence, or transport.
