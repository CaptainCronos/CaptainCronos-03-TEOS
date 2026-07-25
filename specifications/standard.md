# Standard Specification

## Purpose

A Standard represents an external or internal body of technical-education
requirements against which curriculum is traced. It preserves the authority,
official identity, edition, and provenance of those requirements without
rewriting them as TEOS curriculum.

## Responsibilities

A Standard:

- identifies its issuing organization or internal governing owner;
- preserves its official identifier, title, edition, and source provenance;
- defines the scope of the requirements represented;
- provides stable targets for Competency and Course alignment; and
- distinguishes official requirement text from TEOS-maintained annotations.

## Identity Fields

- `standard_id` — stable TEOS identity, unique within the Standard namespace.
- `version` — TEOS contract version of this Standard object.
- `official_identifier` — identifier assigned by the issuer, when one exists.
- `issuer` — identifiable organization or internal governing owner.

`standard_id` MUST distinguish Standards that reuse an official identifier
across issuers. Neither `official_identifier` nor a title alone is a TEOS
identity.

## Required Fields

- `standard_id`
- `version`
- `title`
- `issuer`
- `source`
- `requirements_scope`
- `lifecycle_status`

`source` MUST identify an authoritative publication, repository, or controlled
internal source. `requirements_scope` MUST make clear which body or subset of
requirements the object represents.

## Optional Fields

- `official_identifier`
- `official_version`
- `publication_date`
- `effective_context`
- `source_uri`
- `revision_notes`
- `maintainer`
- `competency_references`
- `tags`

Official requirement excerpts MAY be retained only when provenance and usage
rights permit it. A reference to authoritative text is preferred when copying
would create a competing source.

## Relationships

A Standard MAY govern or inform zero or more
[Competencies](competency.md). A [Course](course.md) MAY declare direct
alignment to one or more Standards. All mappings MUST preserve the referenced
Standard identity and version and SHOULD identify the applicable requirement
location or scope.

A Standard has no ownership dependency on a Course, Institution Profile,
Academic Calendar, or rendered format.

## Validation Rules

A conforming Standard MUST:

- have a complete, unambiguous identity and issuer;
- have a resolvable authoritative source or named internal owner;
- distinguish the TEOS object version from an official edition;
- avoid duplicate mappings that claim different meanings for the same target;
- ensure that every Competency reference resolves to a compatible version; and
- retain provenance for corrections and official revisions.

Validation MUST report a missing source, ambiguous issuer, unresolved mapping,
or silent change of official edition as an error.

## Versioning

A new official edition, changed requirement meaning, changed represented scope,
or changed mapping semantics requires a new Standard version. A provenance-only
correction MAY be compatible if it does not alter the represented requirement
or any reference meaning.

Competency and Course mappings MUST NOT silently migrate to another Standard
version. The shared rules in [Specifications](README.md#shared-versioning-rules)
also apply.

## Lifecycle

A Standard follows the shared source-object lifecycle. Deprecation or
retirement MUST preserve the identity, issuer, official edition, provenance,
and historical mappings. Supersession SHOULD identify the replacing Standard
version without altering existing references.

## What the Object MUST Contain

The object MUST contain enough identity, authority, version, source, and scope
information to determine exactly which requirements it represents.

## Prohibited Content

A Standard MUST NOT contain:

- teaching schedules, Session occurrences, assigned dates, Weeks, or Days;
- institutional branding, campus policy, meeting patterns, or templates;
- instructor, learner, room, or equipment assignments;
- copied Competency definitions presented as Standard-owned content; or
- generated document layout and export settings.

It MUST NOT alter official requirements merely to fit a Course or local
calendar.

## Future Schema Mapping

A future schema will need separate fields for TEOS version and official
edition, a typed issuer identity, source provenance, controlled lifecycle
status, and version-bound references. Requirement-level mappings may require a
structured locator rather than a free-text citation. Schema design MUST allow
an official identifier to be absent without weakening `standard_id`.

## Cross References

- [Competency Specification](competency.md)
- [Course Specification](course.md)
- [Curriculum Model](../docs/architecture/0002-curriculum-model.md#standard)
- [Guiding Principles](../docs/architecture/0000-guiding-principles.md)
