# Repository Loading and Validation

## Status

Implemented against the certified TEOS schemas and immutable domain model.

## Purpose and boundary

The repository loading layer is the only boundary at which maintained TEOS
JSON becomes immutable Python domain objects. Its lifecycle is:

```text
locate JSON documents
    → parse JSON
    → validate each approved Draft 2020-12 schema
    → validate repository-wide identity and references
    → construct immutable domain objects
    → publish a frozen object registry
```

Every stage is fail-fast. A failure prevents publication of a partial
repository. Callers receive either a complete `Repository` or a diagnostic
`RepositoryError`; raw JSON is not exposed above this boundary.

This layer does not schedule Sessions, assign institutional resources, compile
curriculum, render artifacts, serialize domain objects, or persist changes.
External target categories without maintained TEOS domain contracts, such as
assets and templates, retain their typed reference envelopes but are not
invented as repository objects by this layer.

## Validation pipeline

`SchemaValidator` selects the approved object schema from the document's
identity field and delegates all object-local shape, format, vocabulary, and
required-field rules to that schema. Schema behavior is not copied into Python.

`RepositoryValidator` runs after every document passes schema validation. It
enforces:

- one domain object type per stable UUID;
- one document per `(UUID, version)` pair;
- existence of repository-managed referenced UUIDs;
- exact referenced versions;
- agreement between declared and actual reference types; and
- acyclic Institution Profile composition.

Multiple versions of the same UUID and object type are valid. UUID reuse by a
different object type is a `DuplicateIdentifierError`; repeating the same
version is a `DuplicateVersionError`.

## Registry responsibilities

`ObjectRegistry` copies constructed objects into private indexes and exposes
only read operations. It supports exact UUID/version lookup, unambiguous
single-version UUID lookup, type lookup, global version lookup, SemVer latest
lookup, all-version lookup, owner lookup, lifecycle lookup, stable iteration,
and size.

The registry performs no scheduling, graph optimization, persistence, or
serialization. `Repository` exposes the registry and immutable source paths,
not parsed documents.

## Reference resolution

`resolve_reference` resolves the UUID and exact version encoded by a typed
domain `Reference`, confirms the registered object type, and can additionally
enforce a caller-provided Python domain type. It never falls forward or
backward to another version.

Latest-version behavior is available only through the separately named
`resolve_latest_reference`, making non-exact resolution an explicit caller
decision.

## Failure behavior

All load failures derive from `RepositoryError` and carry a message plus
optional source path, object path, and structured diagnostic details:

```text
RepositoryError
├── SchemaValidationError
├── ReferenceValidationError
│   ├── DuplicateIdentifierError
│   ├── DuplicateVersionError
│   ├── MissingReferenceError
│   ├── VersionMismatchError
│   └── CircularReferenceError
└── ConstructionError
```

JSON parsing and schema selection failures are schema diagnostics. Cross-file
identity and exact-reference failures are reference diagnostics. A mismatch
between schema-valid data and the certified Python model is a construction
diagnostic and indicates a contract or implementation defect.
