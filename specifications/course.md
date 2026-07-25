# Course Specification

## Purpose

A Course organizes Instructional Units into a complete curriculum offering and
defines curriculum-level scope, alignment, and completion expectations.

## Responsibilities

A Course:

- identifies and describes the complete offering;
- records catalog information without making institutional presentation
  authoritative;
- identifies governing Standards;
- orders Instructional Units;
- defines prerequisites and completion requirements;
- declares credit hours and estimated instructional hours with explicit
  meanings; and
- exposes traceability through Units, Sessions, Competencies, and Standards.

## Identity

- `course_id` — stable identity unique within the Course namespace.
- `version` — version of the Course contract.

An external catalog code supplements `course_id` unless its authority,
namespace, and uniqueness are explicit. Identity MUST NOT depend on an
institution, campus, term, schedule, Week, or Day.

## Required Fields

- `course_id`
- `version`
- `owner`
- `title`
- `description`
- `instructional_unit_references`
- `completion_requirements`
- `estimated_instructional_hours`
- `lifecycle_status`

The Unit references MUST be a non-empty ordered collection. Completion
requirements MUST be evaluable from curriculum-defined evidence or completion
conditions without embedding learner records.

## Optional Fields

- `catalog_information`
- `standard_references`
- `prerequisite_competency_references`
- `prerequisite_course_references`
- `credit_hours`
- `references`
- `tags`
- `maintainer`
- `revision_notes`

Catalog information MAY include a catalog title, external code, subject,
number, level, or approved summary and MUST identify the governing namespace
when ambiguity is possible.

Credit hours and estimated instructional hours are distinct. When present,
credit hours MUST identify the applicable definition or authority. Estimated
instructional hours MUST use an explicit aggregation rule and MUST NOT represent
assigned dates or local meeting containers.

## Relationships

A Course references an ordered set of one or more
[Instructional Units](instructional-unit.md) and MAY reference governing
[Standards](standard.md). Competency and Session coverage is resolved through
the Units rather than copied into the Course.

An [Institution Profile](institution-profile.md) MAY select an approved Course
version for an operation, and a Scheduler MAY place its Sessions against an
[Academic Calendar](academic-calendar.md). The Course owns neither object nor
the resulting schedule.

## Validation Rules

A conforming Course MUST:

- resolve every Unit, Standard, Course, and Competency reference;
- declare deterministic Unit order;
- reject prerequisite cycles and order that contradicts dependencies;
- ensure completion requirements align with referenced curriculum;
- ensure required Standard coverage is traceable through mapped Competencies;
- keep estimated hours consistent with the selected Unit and Session versions;
- distinguish credit hours from estimated instructional hours; and
- contain no institution, calendar, schedule, or renderer-owned values.

If aggregate Competency or Session coverage is exposed, it MUST be derived and
MUST NOT override the referenced sources.

## Versioning

A change to purpose, scope, governing Standards, ordered Units, prerequisites,
completion requirements, credit-hour meaning, or expected instructional scope
requires a new version. Selecting a semantically changed Unit version requires
an intentional Course revision. Catalog-only corrections MAY remain compatible
when they do not change identity, educational meaning, or reference semantics.

## Lifecycle

A Course follows the shared lifecycle. Approval requires its referenced Units
and required Standards to be approved and compatible. Deprecation SHOULD name
the intended replacement. Retired versions remain resolvable for schedules,
artifacts, and institutional records but are not eligible for new production
selection.

## Prohibited Content

A Course MUST NOT contain:

- institutional dates, holidays, term boundaries, or meeting patterns;
- Weeks or Days as curriculum components;
- campus, instructor, learner, room, or resource assignments;
- institutional branding, templates, headers, footers, or terminology
  overrides;
- copied Unit, Session, Competency, or Standard definitions;
- enrollment, attendance, grades, or credentials; or
- rendered schedules and documents as authoritative data.

## Future Schema Mapping

A future schema will need ordered, non-empty Unit references; typed Standard
and prerequisite references; structured completion requirements; distinct
credit and instructional-hour quantities; catalog namespace support; and
controlled lifecycle values. Traceability, graph acyclicity, order consistency,
and aggregate-hour validation require cross-object rules.

## Cross References

- [Standard Specification](standard.md)
- [Instructional Unit Specification](instructional-unit.md)
- [Session Specification](session.md)
- [Institution Profile Specification](institution-profile.md)
- [Curriculum Model](../docs/architecture/0002-curriculum-model.md#course)
