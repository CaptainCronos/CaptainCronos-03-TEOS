# 0000: Guiding Principles

- Status: Proposed
- Scope: Define the durable principles and decision criteria that govern TEOS.

## Problem Statement

Technical-education programs must turn standards and learner capabilities into
coherent instruction, schedule that instruction within local operating
constraints, and produce materials for instructors, learners, administrators,
and external systems. When curriculum, dates, institutional policy, branding,
and document layout are maintained together, the curriculum becomes difficult
to reuse, changes are hard to trace, and generated documents can become
competing sources of truth.

TEOS solves this problem by keeping canonical curriculum independent from the
institutions that deliver it and from the calendars on which it is scheduled.
It provides an architectural path from standards through schedulable
instruction to validated, institution-specific artifacts without changing the
meaning of the source curriculum.

## Primary Design Goals

TEOS is designed to:

- represent technical-education curriculum in a durable, reviewable form;
- preserve traceability from Standards through Competencies, Instructional
  Units, Sessions, and Courses;
- make curriculum reusable across institutions, campuses, calendar years, and
  presentation formats;
- schedule instruction from explicit Session requirements and institutional
  constraints;
- validate source data, relationships, schedules, and rendered results at
  appropriate boundaries;
- generate consistent documents and integration packages from canonical
  sources;
- make ownership, provenance, and version compatibility explicit; and
- allow each subsystem to evolve without taking ownership of another
  subsystem's data.

## Explicit Non-Goals

TEOS does not:

- replace an institution's student information system, learning management
  system, human-resources system, or facilities system;
- manage enrollment, attendance, grades, credentials, instructor assignments,
  or room reservations as canonical curriculum;
- prescribe a single institutional calendar, meeting pattern, brand, teaching
  method, or document format;
- treat generated documents or export packages as editable curriculum sources;
- infer or silently rewrite the educational intent of curriculum;
- guarantee that every local policy can be satisfied without an explicit
  scheduling or validation decision; or
- make Weeks or Days part of the canonical curriculum hierarchy.

## Core Terminology

TEOS uses the following terms consistently:

- **Standard:** an external or internal body of requirements, identified by its
  issuer, official identity, and version.
- **Competency:** an observable learner capability that can be taught or
  assessed and traced to applicable Standards.
- **Instructional Unit:** a coherent, teachable grouping of related
  Competencies and its ordered instructional work.
- **Session:** the smallest schedulable instructional event and the unit that
  carries duration, delivery, resource, safety, and sequencing needs.
- **Course:** a complete curriculum offering that organizes Instructional Units
  and defines curriculum-level completion expectations.
- **Institution Profile:** institution-owned configuration for identity,
  presentation, scheduling conventions, local policy references, templates,
  and integrations.
- **Academic Calendar:** institution-specific operating dates, instructional
  periods, holidays, closures, and other date availability information.
- **Schedule:** a mapping of curriculum Sessions to calendar occurrences under
  an Institution Profile's constraints.
- **Week and Day:** derived labels or views over scheduled dates. They are
  scheduling aliases, not curriculum objects and not scheduling primitives.
- **Rendered artifact:** a generated document, package, feed, or other output
  produced from versioned source data and configuration.

Capitalized curriculum terms refer to the conceptual objects defined in
[0002: Curriculum Model](0002-curriculum-model.md).

## Separation of Concerns

### Curriculum

Curriculum owns educational intent: Standards, Competencies, Instructional
Units, Sessions, Courses, their relationships, and their curriculum-level
requirements. Curriculum is the single source of truth for what is taught,
why it is taught, how instructional elements relate, and what completion
requires.

Curriculum must not contain institutional dates, campus identity, branding,
local meeting patterns, template selection, or document-layout rules.

### Institution

Institution Profiles own the local context in which curriculum is delivered:
institution and campus identity, presentation, scheduling conventions,
calendar references, local terminology, policy references, template choices,
and integration settings. An Institution Profile may constrain or present
curriculum, but it must not redefine curriculum content or Competencies.

### Academic Calendar

Academic Calendars own date availability and institution-specific time
structure, including instructional periods, holidays, and closures. A calendar
must contain no curriculum, Session sequence, Competency, or Course content.

### Rendered Artifacts

Rendered documents and packages are reproducible outputs, not authoritative
inputs. They must be written under `output/`, must not be committed, and must
retain enough provenance to identify the source curriculum, Institution
Profile, Academic Calendar, templates, and relevant versions used to produce
them.

## Scheduling Principles

Session is the scheduling primitive because it is the smallest curriculum
object with an instructional purpose, an estimated duration, and the
constraints needed to place it. Schedulers map Sessions to calendar
occurrences.

Weeks and Days are aliases applied after or during scheduling to help people
navigate dates. A Session does not belong intrinsically to "Week 2" or
"Day 10." Those labels may change when a holiday, closure, cancellation, or
meeting pattern changes, while the Session's identity and curriculum meaning
remain stable. See [0003: Session Scheduler](0003-session-scheduler.md).

## Architectural Boundaries

- Engine behavior belongs under `src/`; canonical curriculum does not.
- Data contracts belong under `schemas/`; conceptual meaning does not depend on
  a serialization format.
- Curriculum, institution, and calendar source data belong only in their
  corresponding top-level directories.
- Conceptual object definitions belong under `models/`; architecture records
  define system-wide boundaries and decisions.
- Presentation templates belong under `templates/` and must not embed canonical
  curriculum.
- Generated artifacts belong under `output/` and must not be treated as source
  data.
- A subsystem may reference data owned by another subsystem through an
  explicit identity and version, but it must not copy and independently own
  that data.
- Engines transform, validate, schedule, or render source data; they do not
  become its owner.

## Data Ownership Principles

Every authoritative field must have one clear owner. Ownership includes the
right and responsibility to define meaning, version changes, and validation
rules.

- Curriculum owners govern educational content and curriculum relationships.
- Standards owners or curriculum maintainers govern Standard provenance and
  mappings.
- Institutions govern profiles, calendars, local policies, branding,
  templates, and integration configuration.
- Schedulers own schedule results, not Sessions or calendars.
- Renderers own rendering behavior, not the source facts they display.
- Export integrations own destination mappings, not the canonical curriculum.

References must preserve the identity of the object referenced. Derived and
denormalized values must be identifiable as derived and must never silently
override their source.

## Validation Expectations

Validation is layered and must produce actionable findings without silently
repairing authoritative data:

1. **Object validation** confirms that each source object is complete and
   internally coherent.
2. **Relationship validation** confirms that references resolve, required
   ordering is consistent, and dependencies do not contradict one another.
3. **Boundary validation** prevents curriculum, institution, calendar,
   template, and artifact concerns from crossing ownership boundaries.
4. **Scheduling validation** confirms that placed Sessions satisfy duration,
   sequence, calendar availability, meeting-pattern, resource, and safety
   constraints, and reports Sessions that remain unscheduled.
5. **Rendering and export validation** confirms that required source values are
   represented and that an artifact or package meets its target contract.

Validation rules that depend on local policy belong to the institutional
context; they must not be presented as universal curriculum facts. Validation
results are diagnostics, not new sources of truth.

## Versioning and Compatibility

All independently maintained source objects and configuration sets must expose
a stable identity and a meaningful version or revision. Versions support
traceability, compatibility checks, reproducible rendering, and migration.
Artifact provenance must record the relevant source versions.

Backward compatibility is expected for:

- published identities and reference semantics;
- accepted meanings of existing fields and relationships;
- supported source versions that have not reached an announced end of support;
  and
- established subsystem boundaries and ownership rules.

Additive changes should be preferred when they preserve meaning. A change is
breaking when an existing valid source becomes invalid, an identity or
reference changes meaning, a required behavior changes, a field is removed or
reinterpreted, or an output contract changes incompatibly.

Breaking changes require:

1. an Architecture Decision Record describing the reason, scope, alternatives,
   and consequences;
2. an explicit version boundary rather than silent reinterpretation;
3. documented compatibility and migration expectations;
4. validation that detects incompatible inputs or configuration; and
5. coordinated updates to affected architecture, conceptual models, contracts,
   tests, templates, and integrations before release.

Versions must communicate compatibility, not merely edit history. Revisions
that change educational meaning must produce a new curriculum version.
Institution, calendar, template, and integration versions may evolve
independently when their changes do not alter canonical curriculum.

## Decision Rule

When a proposed design could place a fact in more than one subsystem, assign it
to the subsystem that is authoritative for that fact, reference it elsewhere,
and validate the boundary. If the ownership or compatibility consequence is
not clear, document and approve the architectural decision before
implementation.
