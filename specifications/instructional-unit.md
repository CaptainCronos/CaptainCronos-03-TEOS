# Instructional Unit Specification

## Purpose

An Instructional Unit groups related Competencies into a coherent, teachable
unit and defines the ordered instructional work used to address them.

## Responsibilities

An Instructional Unit:

- states its instructional purpose and unit-level learning objectives;
- identifies the Competencies included;
- sequences one or more Sessions;
- consolidates unit-level resource, equipment, and safety context without
  weakening Session requirements;
- defines a unit-level assessment strategy; and
- remains reusable across Courses and independent of institutional delivery.

## Identity

- `instructional_unit_id` — stable identity unique within the Instructional
  Unit namespace.
- `version` — version of the unit contract.

The identity MUST NOT be derived from a Course position, Week, Day, term, or
rendered heading.

## Required Fields

- `instructional_unit_id`
- `version`
- `owner`
- `title`
- `description`
- `included_competency_references`
- `learning_objectives`
- `session_references`
- `estimated_duration`
- `assessment_strategy`
- `lifecycle_status`

At least one Competency and one Session MUST be referenced. Session references
MUST be ordered. Learning objectives MUST describe the intended result of the
unit and align with its included Competencies.

## Optional Fields

- `required_resources`
- `required_equipment`
- `required_safety_controls`
- `prerequisite_competency_references`
- `prerequisite_instructional_unit_references`
- `references`
- `tags`
- `maintainer`
- `revision_notes`

Unit-level requirements MAY summarize or add constraints, but MUST NOT imply
that omitted Session-specific requirements no longer apply.

## Relationships

An Instructional Unit references one or more
[Competencies](competency.md) and sequences one or more
[Sessions](session.md). It MAY depend on earlier Units or prerequisite
Competencies. One or more [Courses](course.md) MAY reuse the same Unit version.

Every Session in the ordered sequence MUST contribute to the Unit purpose,
learning objectives, included Competencies, or assessment strategy.

## Validation Rules

A conforming Instructional Unit MUST:

- resolve all Competency, Session, and prerequisite references;
- declare a deterministic Session order;
- ensure its learning objectives are covered by referenced Sessions;
- ensure referenced Sessions address only compatible Unit scope;
- reject self-dependencies and impossible Unit or Session dependency cycles;
- keep estimated duration consistent with the aggregation rules and referenced
  Session durations;
- ensure unit requirements do not weaken Session resource or safety controls;
- connect its assessment strategy to included Competencies; and
- contain no institution- or calendar-owned values.

Duration variance caused by an explicit aggregation rule MUST be explainable
rather than silently accepted.

## Versioning

A change to purpose, learning objectives, included Competencies, required
Sessions, meaningful order, prerequisites, assessment strategy, duration
meaning, or safety requirements requires a new version. Updating a referenced
object to a semantically changed version requires an intentional Unit revision.

## Lifecycle

An Instructional Unit follows the shared lifecycle. Approval requires all
required referenced objects to be approved and compatible. Deprecation SHOULD
name a replacement when Courses need to migrate. Retirement MUST preserve
historical references and order for provenance.

## Prohibited Content

An Instructional Unit MUST NOT contain:

- assigned dates, holidays, term boundaries, Week or Day structure;
- institution meeting patterns, campus identity, branding, or local templates;
- instructor, room, or learner assignments;
- copied authoritative Competency or Session definitions; or
- renderer layout and destination-specific export configuration.

## Future Schema Mapping

A future schema will need ordered, non-empty Session references; non-empty
Competency and objective collections; normalized durations; structured
resource, equipment, safety, and assessment values; and typed prerequisites.
Coverage, aggregate-duration consistency, and dependency acyclicity require
cross-object validation.

## Cross References

- [Competency Specification](competency.md)
- [Session Specification](session.md)
- [Course Specification](course.md)
- [Curriculum Model](../docs/architecture/0002-curriculum-model.md#instructional-unit)
