# Institution Profile Specification

## Purpose

An Institution Profile is the versioned, authoritative description of the
local context in which an institution schedules, presents, renders, and exports
TEOS curriculum. It supplies institutional configuration without creating an
institution-specific curriculum fork.

## Responsibilities

An Institution Profile:

- identifies the institution and optional campus context;
- references branding assets, logos, templates, calendars, and policies;
- defines meeting patterns and local instructional-time conventions;
- defines approved headers, footers, and presentation terminology;
- configures LMS and export mappings; and
- composes institution-wide and campus-specific configuration with explicit
  precedence and provenance.

## Identity

- `institution_profile_id` — stable identity unique within the Institution
  Profile namespace.
- `version` — version of the coherent configuration set.
- `institution_identifier` — authoritative identifier for the institution.

An optional campus identity MUST remain subordinate to the institution identity
and MUST NOT replace curriculum object identities.

## Required Fields

- `institution_profile_id`
- `version`
- `institution_information`
- `academic_calendar_references`
- `meeting_patterns`
- `lifecycle_status`

`institution_information` MUST include the authoritative institution identity,
approved display name, owner, and applicable time zone. Calendar references
MUST identify compatible [Academic Calendar](academic-calendar.md) versions or
an unambiguous rule for selecting among them.

## Optional Fields

- `campus_information`
- `branding`
- `logo_references`
- `template_references`
- `instructional_time_conventions`
- `holiday_references`
- `header_definitions`
- `footer_definitions`
- `terminology_overrides`
- `lms_settings`
- `export_settings`
- `local_policy_references`
- `composition`
- `maintainer`
- `revision_notes`

Only configuration needed for a requested operation is required at application
time, but missing authoritative values MUST NOT be inferred silently.

## Institution Information

Institution information MAY include legal and approved display names,
recognized abbreviations, institutional identifiers, contact information, time
zone, and campus or site descriptors. These values are institutional facts for
presentation and integration. They MUST NOT redefine a Course or become part of
a curriculum identity.

## Branding and Logos

`branding` defines approved brand characteristics such as color, typography,
usage, and accessibility conventions. `logo_references` identify versioned
brand assets and their allowed contexts. Full binary assets remain separately
owned resources; references MUST be resolvable and MUST preserve asset
provenance.

Brand configuration MUST NOT embed curriculum or generated documents.

## Templates

`template_references` select or constrain compatible, versioned templates by
artifact type, audience, campus, or destination. Templates remain separate
resources under `templates/`; a profile MUST NOT copy full template bodies or
use a template to store curriculum.

## Meeting Patterns

`meeting_patterns` define locally permitted delivery containers, such as
eligible weekdays, recurring blocks, alternating patterns, intensive formats,
evening delivery, and instructional-day or period lengths.

Meeting patterns constrain Session placement. They MUST have unambiguous time
zones, recurrence semantics, instructional-time treatment, and compatibility
with local theory and lab conventions. They MUST NOT become Course, Unit,
Session, Week, or Day structure.

## Academic Calendar and Holiday References

Academic calendar references identify independently maintained calendars and
versions. `holiday_references` MAY identify calendar classifications and
versioned institution-owned policies for handling holidays, closures, make-up
instruction, or special eligibility.

Holiday references MUST NOT duplicate specific holiday dates. Dates and
availability remain owned by the Academic Calendar; handling policy remains
owned by the Institution Profile.

## Header and Footer Definitions

Header and footer definitions MAY include required institutional text,
document identifiers, revision statements, approval lines, accessibility
notices, page conventions, and other presentation requirements. They MUST be
applied through compatible templates and renderers and MUST NOT replace
artifact provenance or curriculum content.

## Terminology Overrides

Terminology overrides map canonical TEOS terms to approved display labels,
abbreviations, or audience-specific language. Every override MUST retain its
canonical term internally and MUST affect presentation only.

An override MUST NOT change identity, relationship meaning, validation
semantics, Session type, curriculum requirements, or the rule that Week and Day
are scheduling aliases.

## LMS Settings

LMS settings MAY define destination references, stable identifier mappings,
course-shell conventions, packaging profiles, content placement rules, naming,
and supported compatibility versions.

Credentials, secrets, learner data, grades, enrollment, and mutable LMS state
MUST remain in secure operational systems. An LMS package or mapping MUST NOT
become authoritative curriculum.

## Export Settings

Export settings MAY define approved artifact types, target formats, destination
mappings, naming conventions, packaging options, accessibility constraints, and
compatibility requirements. They control transformation and delivery, not
canonical source meaning.

## Relationships

An Institution Profile references Academic Calendars, templates, brand assets,
policies, and integration destinations. It MAY select an approved
[Course](course.md) version for a requested operation but does not own or
modify it.

The Scheduler combines profile constraints with Sessions and an Academic
Calendar. Renderers combine profile presentation settings with validated
curriculum, optional schedules, and templates to produce
[Rendered Artifacts](rendered-artifacts.md).

Composition of institution-wide and campus-specific profiles MUST have explicit
precedence and retain provenance for every contributing version.

## Validation Rules

A conforming Institution Profile MUST:

- have unambiguous identity, ownership, version, time zone, and composition;
- resolve compatible calendars, templates, policies, logos, brand assets, and
  destination mappings;
- ensure campus settings do not contradict institution-wide hard constraints;
- define meeting patterns and instructional-time conventions sufficiently for
  requested scheduling operations;
- keep holiday policy separate from calendar dates;
- preserve canonical semantics in terminology overrides;
- provide applicable header, footer, accessibility, LMS, and export settings
  for requested outputs; and
- reject copied or modified curriculum content.

Validation findings MUST identify whether correction belongs to the profile,
calendar, template, asset, integration, or curriculum source.

## Versioning

A change to identity, composition, scheduling eligibility, instructional-time
meaning, policy interpretation, presentation meaning, template or asset
compatibility, terminology mapping, or integration contract requires a new
profile version. Independently versioned references MUST NOT silently advance.

Profile changes do not create curriculum versions unless curriculum meaning is
changed through the approved curriculum process.

## Lifecycle

An Institution Profile follows the shared lifecycle. Approval establishes a
coherent, resolvable configuration set. Deprecation SHOULD identify its
replacement and affected calendar, template, or integration compatibility.
Retired profiles remain available for schedule and artifact provenance but are
not eligible for new production application.

## Prohibited Content

An Institution Profile MUST NOT:

- modify, replace, add, remove, or rewrite curriculum;
- change Standard provenance, Competency capability, Unit outcomes, Session
  purpose or sequence, or Course completion requirements;
- store copied curriculum as a local override;
- store holiday, closure, term, or instructional dates as a competing calendar;
- assign dates directly to Sessions;
- promote Weeks or Days to curriculum objects;
- embed full templates or generated artifacts;
- store credentials, secrets, learner records, grades, or mutable external
  system state; or
- treat export mappings as authoritative curriculum.

If an institution needs a substantive educational difference, that difference
MUST be approved and versioned in curriculum. The profile is explicitly
prohibited from modifying curriculum.

## Future Schema Mapping

A future schema will need typed, version-bound references; structured identity
and campus composition; explicit precedence; normalized time zones and meeting
patterns; presentation-safe branding and terminology structures; and
destination-specific LMS and export settings. Secret-bearing fields MUST be
excluded. Cross-reference compatibility, composition, and curriculum-boundary
checks require validation beyond one object schema.

## Cross References

- [Course Specification](course.md)
- [Academic Calendar Specification](academic-calendar.md)
- [Rendered Artifact Specification](rendered-artifacts.md)
- [Institution Profiles Architecture](../docs/architecture/0004-institution-profiles.md)
- [ADR 0003: Institution Profile Abstraction](../docs/architecture/adr/0003-institution-profile-abstraction.md)
