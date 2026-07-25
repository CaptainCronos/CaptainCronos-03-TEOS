# Session Specification

## Purpose

A Session is the smallest schedulable instructional event and the sole
canonical scheduling primitive in TEOS. It describes a coherent unit of
instruction with enough curriculum-owned information for a Scheduler to
evaluate placement against separate institutional and calendar constraints.

## Responsibilities

A Session:

- states a single instructional purpose and its learning objectives;
- identifies its Session type and theory, lab, review, or assessment
  characteristics;
- defines estimated instructional duration and preparation effort;
- identifies the Competencies it addresses;
- declares instructional resources, materials, equipment, and safety controls;
- expresses prerequisites, dependencies, and scheduling-relevant constraints;
- supplies curriculum source data for rendering; and
- remains independent of every institution-specific date.

## Unique Identifier

- `session_id` — stable identity unique within the Session namespace.
- `version` — version of the Session contract.

The identifier MUST remain stable across institutions, calendars, schedules,
and artifacts. It MUST NOT be derived from a date, meeting number, Week, Day,
Course position, Unit position, or rendered heading. A scheduled occurrence
references `session_id` and `version`; it does not replace either.

## Required Fields

- `session_id`
- `version`
- `owner`
- `session_title`
- `session_type`
- `duration`
- `learning_objectives`
- `competency_references`
- `lifecycle_status`

At least one learning objective and one Competency reference MUST be present.
Duration MUST be a positive estimated instructional quantity with an
unambiguous unit. The title MUST identify the instructional event for people
without being used as its identity.

## Session Type

`session_type` communicates the instructional mode relevant to curriculum,
delivery, and scheduling. The canonical vocabulary MUST support:

- `theory` — concepts, principles, or classroom-oriented instruction;
- `lab` — laboratory, shop, clinical, or hands-on technical work;
- `review` — reinforcement or synthesis of previously introduced instruction;
  and
- `assessment` — collection of evidence used to judge learning.

An approved vocabulary MAY also define demonstration, guided practice,
project, applied work, orientation, or safety briefing. Each value MUST have a
documented scheduling meaning. Institution terminology MAY change its display
label but MUST NOT change its canonical meaning.

When a Session intentionally combines modes, the type and any mode allocation
MUST make that combination explicit. A Session MUST NOT be classified only from
the location in which it happens.

## Duration

`duration` represents estimated instructional effort, not an assigned start,
end, date, or local period count. It MUST:

- state a quantity and unit;
- distinguish instructional time from breaks and preparation time;
- remain traceable when a schedule records a different allocated duration; and
- support explicit aggregation by an Instructional Unit and Course.

Optional mode allocations MAY divide the duration among theory, lab, review,
assessment, or another approved mode. Allocations MUST use compatible units and
MUST NOT exceed the Session duration. Whether a Session may span occurrences,
share a meeting, or require one uninterrupted occurrence MUST be expressed by
optional scheduling constraints rather than inferred.

## Optional Fields

- `description`
- `mode_allocations`
- `required_resources`
- `required_instructor_materials`
- `required_student_materials`
- `required_equipment`
- `required_safety_controls`
- `prerequisite_session_references`
- `dependent_session_references`
- `prerequisite_competency_references`
- `notes`
- `estimated_preparation_time`
- `rendering_metadata`
- `scheduling_constraints`
- `references`
- `tags`
- `maintainer`
- `revision_notes`

Optional fields become normative parts of the Session when present.

## Learning Objectives and Competencies Addressed

Each learning objective MUST describe an observable or assessable result for
the Session. `competency_references` identify the
[Competencies](competency.md) the Session addresses; they do not copy the
authoritative Competency definition.

Every referenced Competency MUST connect to at least one Session objective.
Coverage MAY be partial, but its intended scope SHOULD be explicit when the
Session does not address the full Competency.

## Resources, Materials, and Equipment

- `required_resources` identifies facilities, technology, consumables,
  references, services, or capabilities necessary for delivery.
- `required_instructor_materials` identifies curriculum-owned materials an
  instructor must have to prepare or conduct the Session.
- `required_student_materials` identifies curriculum-owned materials learners
  must receive or supply.
- `required_equipment` identifies equipment or tool capabilities required for
  instruction.

Requirements MUST describe capabilities or materials, not institution-specific
inventory assignments, room bookings, purchasing records, or personnel. When
quantity, capacity, accessibility, or configuration is educationally
significant, the requirement MUST state it explicitly.

## Required Safety Controls

`required_safety_controls` identifies controls necessary before or during the
Session, including prerequisite instruction, supervision, personal protective
equipment, facility capabilities, environmental conditions, operating
procedures, or group-size limits.

Safety controls are hard curriculum constraints unless an explicitly
authorized rule classifies a control otherwise. Omission MUST NOT be interpreted
as permission to ignore applicable external law or institution-owned policy.
Scheduling cannot claim a Session is placeable when a required control is known
to be unsatisfied.

## Prerequisite and Dependent Sessions

`prerequisite_session_references` identify Sessions that must be completed
before this Session can begin. `dependent_session_references` identify Sessions
whose sequencing or coordination is constrained by this Session.

Each dependency MUST:

- identify a Session and version;
- declare a defined relationship, such as before, immediately before, same
  meeting, non-overlap, or evidence-gated;
- agree with the ordering established by the containing Instructional Unit; and
- avoid cycles that make completion or placement impossible.

Dependencies SHOULD be declared from one authoritative direction and derived
in the reverse direction when possible. If both directions are stored, they
MUST be mutually consistent.

## Notes

`notes` MAY retain curriculum-owned authoring or delivery guidance that does
not fit another field. Notes MUST NOT carry requirements that should be
validated as objectives, resources, safety controls, dependencies, or
materials. Institution-specific operational instructions belong in the
Institution Profile or a schedule context, not in Session notes.

## Estimated Preparation Time

`estimated_preparation_time` represents the estimated instructor preparation
effort attributable to the Session. It MUST use an unambiguous duration unit
and MUST remain distinct from instructional duration. It is not a staffing
assignment, payroll value, or scheduled work time.

## Rendering Metadata

`rendering_metadata` MAY provide presentation-neutral hints needed to select or
organize Session content in artifacts, such as audience applicability,
content-section availability, or a stable display label.

Rendering metadata MUST NOT contain:

- template bodies, layout coordinates, page breaks, or style instructions;
- institution branding, headers, footers, or terminology overrides;
- output paths or committed generated content; or
- values that override the Session's canonical title, objectives,
  Competencies, duration, materials, or safety controls.

Artifact-specific presentation belongs to templates, Institution Profiles, and
renderers.

## Relationships

A Session MUST be sequenced by at least one
[Instructional Unit](instructional-unit.md) before it contributes to a Course.
It MUST address one or more Competencies and MAY depend on other Sessions or
prerequisite Competencies. A [Course](course.md) includes Sessions through its
ordered Units.

The Scheduler combines a Session with an
[Institution Profile](institution-profile.md) and
[Academic Calendar](academic-calendar.md) to produce occurrences. Those
objects never become children of the Session.

## Validation Rules

Object validation MUST confirm:

- complete and stable identity, version, title, type, and lifecycle status;
- positive, unambiguous instructional and preparation durations;
- non-empty objectives and Competency references;
- alignment among objectives, type, Competencies, and any assessment intent;
- internally consistent mode allocations;
- well-defined resources, materials, equipment, and safety controls; and
- separation of requirements from unstructured notes and rendering metadata.

Relationship validation MUST confirm:

- all Competency, Session, and reference targets resolve to compatible versions;
- Session prerequisites and dependents agree with Unit and Course order;
- self-dependencies and impossible dependency cycles are rejected;
- the containing Unit does not weaken Session-specific requirements; and
- every dependency has explicit scheduling semantics.

Boundary validation MUST reject institutional dates, local assignments,
branding, calendar classifications, Week or Day identities, and renderer-owned
layout in the Session.

## Versioning

A new Session version is required when any of these change meaning:

- instructional purpose, title scope, type, or learning objectives;
- Competency coverage;
- instructional duration, mode allocation, or split/grouping constraints;
- prerequisite or dependency semantics;
- required resources, materials, equipment, or safety controls;
- assessment intent or preparation expectations; or
- rendering metadata that changes the substantive content exposed.

Editorial changes MAY remain compatible only when instructional, scheduling,
safety, and rendering meaning is unchanged. Every scheduled occurrence and
artifact provenance record MUST identify the exact Session version used.

## Lifecycle

A Session follows the shared lifecycle. It MUST NOT become Approved until all
required references resolve and the containing curriculum can validate its
sequence. Deprecation SHOULD identify a replacement and the affected Units.
Retirement prevents new production scheduling but preserves historical
schedule and artifact resolution.

## Scheduler Considerations

A Scheduler consumes, but does not own or modify, Session requirements. It MUST
preserve:

- Session identity and version;
- source duration and any mode allocation;
- prerequisite and dependency semantics;
- resource, equipment, and safety requirements; and
- explicit split, grouping, continuity, or non-overlap constraints.

A scheduled occurrence adds date, start or end information, allocated duration,
meeting context, placement status, and derived Week or Day aliases. Those
values belong to the schedule. Every requested Session MUST be scheduled or
reported explicitly as unscheduled; hard constraints MUST NOT be weakened
silently.

**Sessions never contain institution-specific dates.** Holidays, closures,
terms, meeting dates, cancellations, and assigned occurrences belong to
Academic Calendars or schedules. Calendar changes affect placement, never
Session identity or curriculum meaning.

## Prohibited Content

A Session MUST NOT contain:

- institution-specific dates, start or end times, holidays, or term boundaries;
- canonical Week or Day numbers, labels, or structure;
- campus, instructor, learner, room, or inventory assignments;
- institution branding, local terminology, meeting patterns, or calendar
  policy;
- copied authoritative Competency definitions;
- grades, attendance, enrollment, or learner records;
- template bodies, document layout, export credentials, or LMS state; or
- generated schedules or rendered artifacts as editable source.

## Future Schema Mapping

A future schema will need:

- strongly typed identity, version, lifecycle, and reference values;
- a controlled and extensible Session-type vocabulary;
- normalized duration quantities and mode-allocation constraints;
- structured resource, material, equipment, and safety requirements;
- typed dependency relationships and split/grouping constraints;
- distinct instructional and preparation durations; and
- bounded, presentation-neutral rendering metadata.

A schema for one Session cannot enforce graph acyclicity, Unit ordering,
Competency coverage, schedule placement, or institutional boundary rules by
itself. Those checks require graph and boundary validation.

## Cross References

- [Competency Specification](competency.md)
- [Instructional Unit Specification](instructional-unit.md)
- [Institution Profile Specification](institution-profile.md)
- [Academic Calendar Specification](academic-calendar.md)
- [Rendered Artifact Specification](rendered-artifacts.md)
- [Session Scheduler](../docs/architecture/0003-session-scheduler.md)
- [ADR 0001: Session Is the Scheduling Primitive](../docs/architecture/adr/0001-session-is-the-scheduling-primitive.md)
- [ADR 0002: Curriculum Is Calendar Independent](../docs/architecture/adr/0002-curriculum-is-calendar-independent.md)
