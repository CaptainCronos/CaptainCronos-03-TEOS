# TEOS Schema Layer

## Purpose

The schema layer provides machine-readable documentation and validation
contracts for TEOS source objects and rendered-artifact provenance. The
first-generation contracts use
[JSON Schema Draft 2020-12](https://json-schema.org/draft/2020-12/schema).

Schemas describe the permitted serialized shape of an object: required fields,
property types, controlled vocabularies, reusable values, reference envelopes,
and object-local constraints. They do not implement loading, relationship
resolution, graph validation, scheduling, rendering, exporting, or migration.
Rules such as dependency acyclicity, reference resolution, aggregate-duration
consistency, date-range ordering, and cross-object coverage require later
implementation against these contracts.

## Place in the design

TEOS develops from design authority toward executable behavior:

```text
Architecture
    ↓
Conceptual Models
    ↓
Specifications
    ↓
Schemas
    ↓
Implementation
```

- **Architecture** establishes system boundaries, ownership, and durable
  decisions.
- **Conceptual Models** define what each domain object means.
- **Specifications** define canonical fields, relationships, invariants,
  lifecycle rules, and validation expectations.
- **Schemas** encode the approved specifications as machine-readable
  contracts.
- **Implementation** may load, validate, schedule, transform, and render
  conforming objects without taking ownership of their meaning.

Schemas are derived contracts. They must never become the authoritative source
of TEOS design. If a schema needs meaning, ownership, or behavior not supported
by the architecture, models, and specifications, those authoritative documents
must be reviewed and approved before the schema changes.

## Contracts

- [`common.schema.json`](common.schema.json) — reusable identifiers, semantic
  versions, dates, times, durations, typed references, metadata, tags,
  localized strings, organizations, resources, documents, safety controls,
  assessment expectations, and shared enumerations.
- [`standard.schema.json`](standard.schema.json) — Standard identity, issuer,
  official provenance, represented scope, mappings, references, and lifecycle.
- [`competency.schema.json`](competency.schema.json) — observable learner
  capability, outcome, criteria, assessment evidence, prerequisites, and
  Standard traceability.
- [`instructional-unit.schema.json`](instructional-unit.schema.json) — coherent
  Competency grouping, ordered Sessions, objectives, duration, requirements,
  and assessment strategy.
- [`session.schema.json`](session.schema.json) — the sole canonical scheduling
  primitive, including instructional duration, objectives, requirements,
  materials, safety, predecessors, successors, and dependency semantics.
  Institutional dates and derived Week or Day aliases are intentionally
  absent.
- [`course.schema.json`](course.schema.json) — Course identity, catalog
  information, governing Standards, ordered Units, completion requirements,
  instructional scope, and credit hours.
- [`institution-profile.schema.json`](institution-profile.schema.json) —
  institution identity, branding, assets, templates, meeting conventions,
  calendar references, terminology, policies, and integration configuration.
- [`academic-calendar.schema.json`](academic-calendar.schema.json) —
  institution-owned academic years, terms, date availability, holidays,
  closures, instructional periods, and special schedules. Curriculum
  properties and references are intentionally absent.
- [`rendered-artifact.schema.json`](rendered-artifact.schema.json) — generated
  artifact identity, type, format, source provenance, generator and renderer
  versions, template, validation state, checksums, lifecycle, and
  reproducibility context.

## Conventions

Each independently maintained object carries a stable UUID, an explicit
semantic version, and its applicable lifecycle status. References preserve the
target type, UUID, and exact version. Ordered arrays are used where order has
educational or operational meaning.

The generic `reference` definition is used only when a relationship
intentionally accepts multiple target object types. Relationships with one
approved target type use a reusable typed reference definition. Each typed
reference preserves the generic reference envelope and constrains
`object_type` with `const`, so a structurally valid reference to the wrong
domain object is rejected.

Object schemas reject unknown properties with `additionalProperties: false`.
The only intentional general extension points are namespaced metadata or
generation options whose keys begin with `x-`. Optional collections, when
present, must be non-empty; omission is used instead of empty placeholder
values.

Every schema has its own relative `$id`. Relative references therefore resolve
within this directory without claiming an external schema registry. The
`x-teos-schema-version` annotation versions the schema contract independently
from the version of any TEOS object validated by it.

JSON Schema validates object-local structure. The architectural separations
among curriculum, institutions, calendars, schedules, and artifacts remain
normative even where a single schema cannot evaluate the full relationship
graph.

## Contract validation

Run `python scripts/validate_schemas.py` from the repository root to validate
the schema contracts. The check parses every repository JSON file, validates
each schema against the Draft 2020-12 metaschema, resolves every local `$ref`,
and validates every embedded positive example against its own schema.

The same check includes focused negative cases for wrong target object types.
These cases confirm that Course references are rejected from Session
Competency fields, Competency references are rejected from Session
dependencies, Academic Calendar references are rejected from Course
Instructional Unit fields, and Session references are rejected from
Institution Profile Academic Calendar fields.
