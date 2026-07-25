# ADR 0001: Session Is the Scheduling Primitive

## Status

Accepted

## Context

TEOS must schedule reusable curriculum across institutions with different term
dates, holidays, instructional-day lengths, and meeting patterns. Course and
Instructional Unit are useful organizational levels, but each can contain
instruction with different durations, delivery modes, prerequisites, resource
needs, and safety constraints. Week and Day are familiar presentation concepts,
but their meaning changes with a calendar and local meeting pattern.

The architecture needs one stable curriculum object at which schedulable
requirements can be expressed without embedding institutional dates in
curriculum.

## Decision

Session is the smallest schedulable instructional event and the only canonical
scheduling primitive in TEOS.

Each Session has a stable curriculum identity and version and carries the
duration, delivery type, theory or lab allocation, prerequisites, dependencies,
resource needs, safety requirements, and sequencing constraints needed for
placement. The Scheduler maps Session references to calendar occurrences.

Week and Day are derived scheduling aliases used for navigation and
presentation. They are not curriculum objects, Session identities, or
scheduling primitives.

## Consequences

- A Session remains identifiable when dates or local meeting patterns change.
- Courses can be reused across institutions without Week- or Day-based forks.
- Holidays, closures, and cancellations change placements rather than
  curriculum identity.
- Scheduling validation can report conflicts against the smallest event that
  owns the relevant requirement.
- Instruction that must be scheduled independently must be modeled as a
  Session, which requires curriculum authors to choose meaningful boundaries.
- Multi-meeting delivery must preserve one Session identity or be modeled as
  multiple Sessions according to explicit curriculum intent.
- Renderers may display Week and Day groupings, but those labels cannot be
  written back as canonical curriculum structure.

## Alternatives Considered

### Course as the Scheduling Primitive

Rejected because a Course is too coarse to express the differing durations,
resources, prerequisites, and safety requirements of its instructional events.

### Instructional Unit as the Scheduling Primitive

Rejected because a Unit can contain heterogeneous theory, lab, assessment, and
practice Sessions that require separate placement.

### Week or Day as the Scheduling Primitive

Rejected because Week and Day depend on institutional calendars and meeting
patterns. Making them canonical would couple curriculum to one delivery
context.

### Individual Learning Activities as the Primitive

Rejected as the universal rule because activities below Session level do not
always need independent placement. If an activity needs its own scheduling
contract, it should be represented as a Session.
