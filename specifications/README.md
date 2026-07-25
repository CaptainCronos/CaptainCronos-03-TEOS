# TEOS Specifications

## Purpose

The Specifications layer defines the canonical, serialization-independent
contract for every TEOS object. It translates the meaning and ownership
established by the architecture and conceptual models into explicit fields,
relationships, invariants, lifecycle rules, and validation expectations.

Specifications are authoritative for contract design. Machine-readable schemas
are derived from these documents and must not introduce meanings, fields, or
ownership rules that the applicable specification does not support.

## Repository Layers

TEOS progresses from intent to generated output through these layers:

```text
Architecture
    ↓
Conceptual Models
    ↓
Specifications
    ↓
Schemas
    ↓
Engine
    ↓
Renderers
```

- **Architecture** establishes system boundaries, ownership, and durable design
  decisions.
- **Conceptual Models** define the domain objects and their meaning without
  choosing a representation.
- **Specifications** define the canonical contracts for those objects.
- **Schemas** encode approved specifications in machine-readable validation
  formats.
- **Engine** loads, resolves, validates, schedules, and transforms conforming
  objects without taking ownership of their data.
- **Renderers** produce reproducible artifacts from validated, versioned inputs.

A lower layer MUST conform to the approved layers above it. When a proposed
schema or behavior requires a contract change, the specification and any
affected architecture MUST be reviewed first.

## Responsibilities

This layer:

- defines canonical fields and whether they are required or optional;
- defines identity, reference, relationship, and ordering semantics;
- states object-level and cross-object validation expectations;
- establishes versioning and lifecycle rules;
- preserves the boundaries among curriculum, institution, calendar, and
  rendered artifacts; and
- identifies considerations for later schema design without selecting a schema
  language.

This layer does not contain schemas, implementation code, source data,
scheduling algorithms, renderer behavior, or generated artifacts.

## Shared Contract Conventions

The key words **MUST**, **MUST NOT**, **SHOULD**, **SHOULD NOT**, and **MAY**
express normative requirements.

All independently maintained source objects MUST have:

- a stable TEOS identity that is unique within its object type and governing
  namespace;
- a meaningful version or revision;
- an identifiable owner or authoritative source; and
- enough provenance to resolve references and evaluate compatibility.

References MUST identify the target object type, stable identity, and intended
version or compatible version constraint. A reference does not copy ownership
of the target. Ordering MUST be explicit wherever order conveys educational or
operational meaning.

Durations represent quantities of instructional or preparation time, never
assigned dates or clock times unless a scheduling result explicitly owns those
values. Units, allowed precision, and aggregation behavior remain decisions for
the derived schemas.

Optional fields are optional only when omitted. When present, they MUST be
well-formed and meaningful; empty values MUST NOT be used as substitutes for
absence.

## Shared Validation Expectations

Validation MUST:

- distinguish object, relationship, boundary, scheduling, and artifact
  findings;
- report actionable failures without silently repairing authoritative data;
- confirm that references resolve to compatible object versions;
- reject dependency cycles that make completion or scheduling impossible;
- preserve declared ordering and ownership boundaries; and
- identify the source that must be corrected.

Local-policy validation MUST be identified as institution-owned rather than
presented as a universal curriculum rule.

## Shared Versioning Rules

Versions communicate compatibility, not merely edit history. A new version is
required when educational meaning, reference semantics, required behavior, or
owned constraints change. Editorial corrections MAY remain compatible only
when they do not change meaning.

Additive changes are preferred. A breaking contract change requires an
approved Architecture Decision Record, an explicit version boundary, migration
expectations, compatibility validation, and coordinated updates to affected
layers. References MUST NOT silently move to a later version.

## Shared Lifecycle

Unless an object specification narrows the rule, source objects move through:

1. **Draft** — editable and not available as an approved dependency.
2. **Approved** — reviewed and eligible for use by compatible references.
3. **Deprecated** — still identifiable and resolvable, but not recommended for
   new references; a replacement SHOULD be identified.
4. **Retired** — preserved for provenance and historical resolution but not
   eligible for new production use.

Published versions are immutable in meaning. A substantive correction produces
a new version rather than rewriting the published version. Lifecycle state
does not replace version identity.

## Future Schema Mapping

Derived schemas SHOULD map canonical fields directly, use explicit typed
references, constrain controlled vocabularies where the specification defines
closed meanings, and preserve extension points only where this layer permits
them. Schemas MUST distinguish absent optional values from invalid empty
values, and MUST support boundary validation that a single object schema
cannot express on its own.

No serialization syntax, schema technology, identifier encoding, date format,
duration format, or version syntax is selected by these documents.

## Prohibited Content

Specifications MUST NOT:

- contain institution-specific curriculum variants;
- promote Weeks or Days to curriculum objects or scheduling primitives;
- place institutional dates in curriculum objects;
- place curriculum in Academic Calendars or Institution Profiles;
- treat templates or generated artifacts as authoritative sources; or
- prescribe implementation classes, algorithms, commands, or renderer code.

## Specification Index

- [Standard](standard.md)
- [Competency](competency.md)
- [Instructional Unit](instructional-unit.md)
- [Session](session.md)
- [Course](course.md)
- [Institution Profile](institution-profile.md)
- [Academic Calendar](academic-calendar.md)
- [Rendered Artifacts](rendered-artifacts.md)

## Cross References

- [Guiding Principles](../docs/architecture/0000-guiding-principles.md)
- [System Overview](../docs/architecture/0001-system-overview.md)
- [Curriculum Model](../docs/architecture/0002-curriculum-model.md)
- [Conceptual Models](../models/README.md)
