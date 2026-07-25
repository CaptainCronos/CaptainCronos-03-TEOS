# ADR 0002: Curriculum Is Calendar Independent

## Status

Accepted

## Context

The same technical curriculum may be delivered in terms of different lengths,
on different weekdays, across different holiday patterns, and at institutions
using different instructional-day conventions. Embedding dates or calendar
positions in curriculum would create local copies, obscure educational
changes, and make curriculum versions depend on operational scheduling.

TEOS needs a clear ownership boundary between educational intent and the dates
available for its delivery.

## Decision

Canonical curriculum is independent of Academic Calendars.

Standards, Competencies, Instructional Units, Sessions, and Courses may define
educational sequence, estimated duration, prerequisites, completion
requirements, and other curriculum constraints. They must not contain
institutional dates, holidays, closures, term boundaries, or assigned Week and
Day positions.

Academic Calendars own instructional periods, date availability, holidays, and
closures. They contain no curriculum, Competencies, Sessions, or Course
sequence. The Scheduler combines curriculum constraints with a referenced
calendar only when producing a schedule.

## Consequences

- One curriculum version can be scheduled in multiple institutions and terms.
- Calendar changes do not create curriculum revisions.
- Curriculum and calendar sources can be validated and versioned
  independently.
- Schedules must retain references to both the curriculum and calendar versions
  used.
- Date-dependent views are derived artifacts and must be regenerated when a
  calendar changes.
- Curriculum authors cannot rely on Week numbers or specific dates to express
  instructional order; they must use explicit Unit and Session sequencing.
- Calendar maintainers cannot add or remove curriculum to resolve capacity
  problems.

## Alternatives Considered

### Embed a Default Calendar in Each Course

Rejected because even a default would encourage date-based curriculum
assumptions and create ambiguity over which source is authoritative.

### Maintain a Curriculum Copy per Term

Rejected because operational calendar changes would produce unnecessary
curriculum forks and make educational differences hard to distinguish.

### Put Session References in Academic Calendars

Rejected because the calendar would acquire curriculum ownership and could no
longer be reused or governed independently.

### Treat Week Numbers as Calendar-Neutral

Rejected because Week numbering still depends on a start date, holiday policy,
and meeting pattern. Explicit Session sequence expresses curriculum order
without those dependencies.
