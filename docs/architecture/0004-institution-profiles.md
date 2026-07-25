# 0004: Institution Profiles

- Status: Proposed
- Scope: Define institution-owned scheduling, presentation, policy, and
  integration configuration without embedding curriculum.

## Abstraction

An Institution Profile is the versioned, authoritative description of the
local context in which an institution presents, schedules, renders, and
exports TEOS curriculum. It allows the same canonical Course and Session
sequence to be used by different institutions or campuses without creating
institution-specific curriculum forks.

The profile is an input to profile application, scheduling, validation,
rendering, and export. It references an Academic Calendar and presentation
resources but does not absorb their owned data. The architectural decision is
recorded in
[ADR 0003](adr/0003-institution-profile-abstraction.md).

## Identity and Composition

Each Institution Profile requires a stable identity, human-readable name,
institution owner, and version or revision. A profile may represent an entire
institution or explicitly compose institution-wide configuration with a
campus-specific profile. Composition and precedence must be unambiguous, and
the effective profile must retain the provenance of every contributing source.

A profile version identifies a coherent set of institutional expectations.
Configuration that changes scheduling eligibility, presentation meaning,
policy interpretation, or integration compatibility requires an intentional
revision.

## Responsibilities

### Institution Identity

The profile identifies the legal or operational institution, approved display
name, recognized abbreviations, and any institution identifiers needed for
rendering or integration. These identifiers are institutional facts and must
not replace curriculum object identities.

### Campus Information

When delivery differs by location, the profile identifies the campus or site,
its display information, applicable time zone, and locally relevant contact or
facility context. Campus data may narrow institution-wide scheduling or
presentation settings but must not change the meaning of a Course,
Instructional Unit, Session, or Competency.

### Branding

The profile owns approved brand references such as names, logos, colors,
typography conventions, and accessibility requirements. Branding is applied by
templates and renderers. Brand resources must not embed curriculum as a way to
bypass curriculum ownership.

### Academic Calendar References

The profile identifies the Academic Calendar and version applicable to a
scheduling scope or term. It may declare how a campus selects among approved
calendars, but dates, holidays, instructional periods, and closures remain
owned by the referenced calendar.

The profile must not copy curriculum into a calendar or imply that a calendar
defines Session order.

### Course Meeting Patterns

The profile defines locally permitted meeting patterns, such as eligible
weekdays, recurring time blocks, alternating patterns, intensive formats, or
evening delivery. It may associate a Course delivery context with an approved
pattern, but it cannot place Week or Day labels inside canonical curriculum.

Meeting patterns constrain the Scheduler. They do not redefine the Course or
its required Sessions.

### Instructional-Day Lengths

The profile defines the institution's recognized instructional-day and period
lengths, including how breaks or non-instructional time are treated. These
values allow estimated Session duration to be mapped to local meeting
containers without changing the curriculum estimate.

### Theory and Lab Conventions

The profile defines local distinctions among theory, laboratory, shop,
clinical, project, or other recognized instructional modes. It may define
approved block lengths, conversion or reporting conventions, eligible
facilities, and display terminology.

Local conventions interpret and constrain curriculum allocations. They must
not silently recategorize or reduce a Session's theory, lab, resource, or safety
requirements.

### Holidays and Closures

The Academic Calendar owns specific holidays and closures. The Institution
Profile owns institutional policy for how those conditions affect instruction,
such as whether a classified date is unavailable, eligible for make-up
instruction, or subject to approval.

The profile references calendar classifications rather than maintaining a
competing list of dates. Changes to date availability are made in the calendar;
changes to institutional handling policy are made in the profile.

### Document Templates

The profile selects or constrains the versioned templates approved for artifact
types, audiences, campuses, or destinations. Templates remain separate
presentation resources under `templates/`. The profile must identify compatible
choices without embedding full template bodies or curriculum content.

### Footer and Header Standards

The profile defines required institutional header and footer content, document
identifiers, revision statements, approval lines, accessibility notices, page
conventions, and other presentation standards. Renderers apply these through
templates and must preserve the provenance and versions behind generated
documents.

### Terminology Overrides

The profile may map canonical TEOS terms to institution-approved display terms,
abbreviations, or audience-specific labels. An override changes presentation
only. It must retain the canonical term or concept internally and must not
change identity, ownership, relationships, validation meaning, or curriculum
requirements.

Week and Day terminology remains a scheduling or presentation alias and cannot
be promoted into curriculum.

### LMS and Export Settings

The profile defines approved destination references, identifier mappings,
packaging options, naming conventions, and compatibility settings for learning
management systems and other integrations. Credentials and mutable
external-system state should remain in an appropriate secure operational
system rather than in curriculum or a distributable profile.

Destination settings control mapping and delivery; they do not make an LMS
export authoritative curriculum.

### Local Policy References

The profile references versioned local policies relevant to scheduling,
safety, contact hours, accessibility, approval, retention, or presentation.
References must identify the governing authority and applicable version or
effective context.

Where a local policy affects validation, the resulting rule must be identified
as institution-owned. Policy references must not be used to overwrite a
curriculum requirement silently.

## Prohibited Responsibilities

Institution Profiles must not redefine curriculum content or Competencies.
Specifically, a profile must not:

- edit or replace Standard requirements or provenance;
- change the learner capability expressed by a Competency;
- add, remove, or rewrite Instructional Unit outcomes;
- change Session instructional purpose, Competency coverage, or curriculum
  sequence;
- change Course completion requirements or educational scope;
- assign canonical curriculum identities based on campus, term, Week, or Day;
- store Academic Calendar dates as a competing calendar source; or
- treat rendered documents, templates, or external-system mappings as
  authoritative curriculum.

If an institution requires a substantive curriculum difference, that
difference must be reviewed and versioned in curriculum under curriculum
ownership. A profile may select an approved Course version; it may not create a
hidden local variant.

## Application Rules

Applying a profile produces an effective institutional context for a specific
operation. Application must:

- resolve the profile identity, version, composition, and references;
- retain curriculum identity and version without mutation;
- resolve, rather than copy, the selected Academic Calendar and templates;
- distinguish universal curriculum validation from local policy validation;
- report incompatible or missing configuration explicitly; and
- preserve provenance for schedules, rendered artifacts, and exports.

A profile may be applied for scheduling, rendering, export, or a combination
of those operations. Only the relevant configuration should be required for a
given operation, but no operation may infer missing authoritative values
silently.

## Validation Expectations

Profile validation must confirm:

- identity, version, ownership, and composition are unambiguous;
- referenced calendars, templates, policies, brand resources, and destination
  mappings resolve to compatible versions;
- campus configuration does not contradict institution-wide hard constraints;
- meeting patterns and instructional-day lengths are sufficient for the
  requested scheduling context;
- theory and lab conventions have explicit meanings;
- terminology overrides preserve canonical semantics;
- required headers, footers, and accessibility standards are available for the
  requested artifact; and
- no profile field redefines curriculum or duplicates Academic Calendar
  ownership.

Validation findings must identify whether correction belongs to the profile,
the referenced calendar or template, or curriculum. Validators and renderers
must not repair ownership violations by copying or rewriting source data.

## Relationship to Other Architecture

- [0000: Guiding Principles](0000-guiding-principles.md) defines the ownership
  and separation rules.
- [0001: System Overview](0001-system-overview.md) describes profile application
  in the production pipeline.
- [0002: Curriculum Model](0002-curriculum-model.md) defines the curriculum
  objects a profile must not redefine.
- [0003: Session Scheduler](0003-session-scheduler.md) defines how profile
  scheduling conventions constrain placement.
