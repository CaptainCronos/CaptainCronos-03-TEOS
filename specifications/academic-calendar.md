# Academic Calendar Specification

## Purpose

An Academic Calendar is the versioned, institution-owned source of operating
dates, instructional periods, date availability, holidays, closures, and
special schedules. It supplies date constraints independently of curriculum.

## Responsibilities

An Academic Calendar:

- identifies its owning institution and academic-year context;
- defines terms and other instructional periods;
- classifies holidays, closures, and instructional days;
- represents special schedules and exceptions;
- supplies availability facts to Institution Profiles and the Scheduler; and
- preserves enough provenance to explain and reproduce date decisions.

## Calendar Identity

- `academic_calendar_id` — stable identity unique within the Academic Calendar
  namespace.
- `version` — version of the calendar data set.
- `owner` — institution or governing authority responsible for the dates.

Calendar identity MUST NOT be derived solely from a year label or Course. A
calendar version represents one coherent set of date facts.

## Required Fields

- `academic_calendar_id`
- `version`
- `owner`
- `academic_year`
- `terms`
- `instructional_days`
- `time_zone`
- `lifecycle_status`

`academic_year` MUST have an unambiguous label and bounded date range. Each term
MUST have a stable term identity, title, start date, end date, and classification.
Instructional days MUST state date availability and any applicable
instructional-period context.

## Optional Fields

- `holidays`
- `closures`
- `special_schedules`
- `instructional_periods`
- `date_annotations`
- `source`
- `maintainer`
- `revision_notes`

Absence of an optional collection means that the calendar declares no entries
of that kind within its scope; it MUST NOT be used to mean that calendar data
is unknown.

## Terms

Terms define institution-owned academic periods such as semesters, quarters,
modules, or approved equivalents. Term ranges MAY overlap only when the
institution explicitly permits and classifies the relationship. A term
organizes dates; it MUST NOT organize curriculum objects.

## Holidays and Closures

A holiday identifies a named or classified date condition and whether the date
is ordinarily instructional, non-instructional, or subject to policy. A closure
identifies a date or interval on which specified institutional operations are
unavailable.

The calendar owns the date and classification. The
[Institution Profile](institution-profile.md) owns policy for how a
classification affects a particular scheduling operation. Cancellations or
emergency changes require a traceable calendar revision or schedule event; they
do not delete curriculum.

## Instructional Days

Instructional days identify dates and periods available, unavailable, or
conditionally available for instruction. Availability MUST be explicit within
the calendar's stated scope and time zone. Instructional-day records MAY
reference a term or special schedule but MUST NOT reference a Session,
Instructional Unit, Competency, or Course.

## Special Schedules

Special schedules represent date-specific changes to ordinary availability or
operating periods, such as shortened days, examination operating periods,
make-up availability, or emergency patterns. They define calendar conditions,
not the curriculum scheduled into those conditions.

If a special schedule conflicts with a general term or instructional-day rule,
precedence MUST be explicit and deterministic.

## Relationships

An Academic Calendar is referenced by one or more Institution Profiles. The
Scheduler combines it with a profile's meeting and policy constraints and the
requirements of [Sessions](session.md) to produce a schedule.

The resulting schedule references the exact calendar identity and version used.
It is a derived artifact or intermediate result, not part of the Academic
Calendar.

## Validation Rules

A conforming Academic Calendar MUST:

- have unambiguous identity, owner, version, date scope, and time zone;
- contain valid, bounded academic-year and term ranges;
- ensure every included date belongs to the declared scope;
- resolve overlaps and precedence among terms, holidays, closures,
  instructional days, and special schedules;
- avoid contradictory availability classifications;
- distinguish facts from institution-owned handling policies;
- provide provenance for published and revised dates; and
- contain no curriculum references or content.

Validation MUST reject a calendar that attempts to resolve capacity or
scheduling problems by adding, removing, renaming, or sequencing curriculum.

## Versioning

Changing a term boundary, date classification, instructional availability,
holiday, closure, special schedule, time zone, or precedence rule requires a
new calendar version or traceable revision. Published versions MUST remain
resolvable because schedules and artifacts depend on their exact date facts.

A calendar revision does not create a curriculum version. Affected schedules
MUST be revalidated or regenerated against the new calendar version.

## Lifecycle

An Academic Calendar follows the shared lifecycle. Draft calendars MAY be used
for planning only when outputs clearly identify that status. Approval confirms
the authoritative date set. Deprecation or retirement preserves historical
resolution for schedules and artifacts; new scheduling uses an approved
calendar version.

## Prohibited Content

Academic Calendars never contain curriculum. An Academic Calendar MUST NOT
contain:

- Standards, Competencies, Instructional Units, Sessions, or Courses;
- curriculum sequence, learning objectives, assessments, or completion rules;
- Session references or assigned instructional content;
- institution branding, templates, headers, footers, or LMS mappings;
- instructor, learner, room, or equipment assignments; or
- Weeks or Days presented as canonical curriculum objects.

## Future Schema Mapping

A future schema will need typed calendar, term, and classification identities;
normalized dates, intervals, and time zones; explicit availability states;
structured recurrence or exception rules where approved; and deterministic
precedence. Overlap, completeness, and curriculum-boundary checks will require
validation across calendar entries and referenced profile policies.

## Cross References

- [Institution Profile Specification](institution-profile.md)
- [Session Specification](session.md)
- [Rendered Artifact Specification](rendered-artifacts.md)
- [Session Scheduler](../docs/architecture/0003-session-scheduler.md)
- [ADR 0002: Curriculum Is Calendar Independent](../docs/architecture/adr/0002-curriculum-is-calendar-independent.md)
