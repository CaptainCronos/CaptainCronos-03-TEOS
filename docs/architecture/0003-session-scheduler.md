# 0003: Session Scheduler

- Status: Proposed
- Scope: Define session-based scheduling and the boundary between curriculum,
  institution constraints, and Academic Calendars.

## Scheduling Principle

Session is the scheduling primitive because it is the smallest curriculum
object that represents a coherent instructional event and carries the
information needed for placement: purpose, type, estimated duration,
allocation, prerequisites, dependencies, resources, and safety requirements.

Instructional Units and Courses are too broad to place without losing the
constraints of their constituent instruction. Smaller activities may exist
inside a Session, but they are not independently schedulable unless the
curriculum models them as Sessions. This rule is recorded in
[ADR 0001](adr/0001-session-is-the-scheduling-primitive.md).

This document defines the scheduling contract and expected results. It does not
select data structures, optimization techniques, or implementation algorithms.

## Session Scheduling Contract

### Session Identity

Each Session has a stable curriculum identity and version. A scheduled
occurrence references that identity and version and adds placement information;
it does not replace or redefine the Session. Dates, meeting numbers, Week
labels, and Day labels are never Session identities.

If a Session is explicitly permitted to span more than one meeting, all
scheduled parts retain a relationship to the same Session identity and expose
their occurrence order. Splitting must not be inferred when the curriculum or
local policy prohibits it.

### Session Types

A Session type communicates the instructional mode relevant to delivery and
scheduling. Common conceptual types include:

- theory or classroom instruction;
- laboratory or shop practice;
- demonstration;
- guided practice;
- assessment;
- project or applied work; and
- review, orientation, or safety briefing.

The vocabulary may be extended through an approved curriculum convention, but
a type must have defined scheduling meaning. Institution terminology may
change how a type is displayed, not what the curriculum requires.

### Estimated Duration

Each Session declares an estimated instructional duration using a consistent,
unambiguous unit. Duration describes curriculum scope and provides the basis
for placement; it is not an assigned start or end time.

A scheduling context must define how estimated duration relates to local
instructional periods and whether a Session may be split, combined within a
meeting, or extended across occurrences. The schedule must preserve both the
source estimate and the duration actually allocated so variance can be
validated.

### Theory and Lab Allocation

A Session declares its required or expected division among theory, lab, or
other recognized instructional modes when that distinction matters. The
Institution Profile supplies local conventions such as period lengths,
permitted block structures, and terminology.

Scheduling may adapt placement to those conventions but must not silently
change the curriculum allocation. A mismatch is reported for review or handled
by an explicitly approved policy.

### Prerequisites and Dependencies

Prerequisites identify capabilities or instructional work that must be
completed before a Session can begin. Dependencies express ordering or
coordination relationships among Sessions, such as:

- must occur before or after another Session;
- must occur immediately before or after another Session;
- must occur in the same meeting or instructional period;
- may occur only after required Competency evidence is available; or
- must not overlap with a related Session.

Dependencies must reference stable identities, have defined meaning, and avoid
cycles that make placement impossible. The Scheduler preserves declared order
from Instructional Units and Courses unless the curriculum explicitly permits
flexibility.

### Required Resources

A Session identifies resource capabilities necessary for safe and effective
delivery, such as tools, equipment, facilities, consumables, technology, or
capacity. Curriculum states the requirement; institutional systems or profiles
may identify locally available capabilities.

The Scheduler must not assume availability merely because a Session fits in
time. When resource availability is part of the scheduling input, the result
must respect it. When it is unavailable or outside the scheduling scope, the
result must carry an unresolved requirement or validation finding rather than
claiming confirmed allocation.

### Safety Requirements

Safety requirements are hard constraints unless the curriculum or an
authorized local policy explicitly classifies them otherwise. They may include
required prior instruction, supervision, facility capabilities, personal
protective equipment, environmental conditions, or limits on group size.

Scheduling must preserve the source safety requirement and identify which
institutional condition satisfies it. A Session must remain unscheduled when a
required safety condition cannot be established.

### Sequencing Constraints

Sequencing is derived from Course and Instructional Unit order plus explicit
Session prerequisites and dependencies. Constraints may be strict or may
permit a documented range or interchangeable order. The scheduling result must
be traceable to the constraint that caused each non-obvious placement
restriction.

An Institution Profile can restrict eligible meeting patterns but cannot
reorder curriculum in a way that violates curriculum sequencing.

## Calendar and Meeting Conditions

### Holidays and Closures

Academic Calendars identify holidays and closures as unavailable or specially
classified dates. A Session is not assigned to an unavailable date unless the
calendar and Institution Profile explicitly define that date as eligible for
the applicable instructional purpose.

Holidays shift placement opportunities; they do not remove, rename, or
renumber Sessions in curriculum. Derived Week or Day views may therefore
contain fewer meetings or span different date ranges.

### Canceled Meetings

A canceled meeting is a change to schedule availability, not a deletion of
curriculum. Affected Session occurrences return to an unplaced state or are
rescheduled according to approved institutional policy. The result must retain
the cancellation and rescheduling relationship for traceability.

If no valid replacement exists, the Session remains explicitly unscheduled and
the schedule is incomplete. The Scheduler must not compress, omit, or merge
instruction silently.

### Different Institutional Meeting Patterns

Institution Profiles define eligible patterns such as fixed weekdays,
alternating days, block schedules, evening meetings, intensive delivery, or
variable instructional-day lengths. The same Course and Session sequence may
therefore produce different schedules at different institutions or in
different terms.

Meeting patterns supply available containers for Sessions. They do not become
curriculum structure and must not alter Session identity, Competency coverage,
or educational requirements.

### Mapping Sessions to Calendar Dates

A mapping connects a specific Session identity and version to one or more
eligible calendar occurrences. Each occurrence must identify its date,
applicable start and end or allocated duration, meeting context, placement
status, and the institutional and calendar context used.

Mapping must preserve source order and all hard constraints. When a Session may
validly fit more than one date, the selected placement is a schedule decision,
not a curriculum change.

### Week and Day Labels

Week and Day are derived scheduling aliases used for navigation, reporting,
and presentation. Their definition comes from the Institution Profile,
Academic Calendar, or selected rendering convention.

Labels must be derivable from the schedule and must not be written back into
canonical Sessions. A holiday or cancellation may change the label associated
with an occurrence without creating a new Session version. Ambiguous labels
must be accompanied by actual dates and Session identities.

## Scheduling Outcomes

### Conflicts

A conflict occurs when two or more requirements cannot be satisfied together
or when a proposed placement violates a constraint. Conflict categories
include:

- calendar or meeting-pattern conflicts;
- duration or allocation conflicts;
- prerequisite or sequence conflicts;
- resource or capacity conflicts;
- safety conflicts;
- overlapping placement conflicts; and
- incompatible local policy constraints.

Each conflict must identify the affected Session or occurrence, the violated
constraint and its owner, severity, and enough context for a reviewer to act.
The Scheduler must not resolve hard conflicts by silently weakening a source
requirement.

### Unscheduled Sessions

Every requested Session must be either scheduled or explicitly reported as
unscheduled. An unscheduled result identifies the Session identity and version,
the reason or blocking conflicts, and whether additional calendar capacity,
institutional configuration, resource information, or curriculum review is
needed.

Partial schedules are valid results only when clearly marked incomplete. They
must not be rendered or exported as complete schedules.

## Scheduler Inputs

The conceptual inputs are:

- a validated Course version and its ordered Instructional Units and Sessions;
- Session durations, allocations, prerequisites, dependencies, resources,
  safety requirements, and split or grouping constraints;
- a validated Institution Profile with meeting patterns, instructional-day
  lengths, conventions, policies, and calendar references;
- a validated Academic Calendar with instructional periods, eligible dates,
  holidays, and closures;
- relevant resource availability when resource assignment is in scope;
- an optional prior schedule or cancellation record when rescheduling; and
- the requested scheduling scope and policy selections.

All inputs retain ownership and version identity. Supplying them to the
Scheduler does not merge curriculum, institution, and calendar data.

## Scheduler Outputs

The conceptual outputs are:

- a schedule identifying its curriculum, Institution Profile, Academic
  Calendar, and scheduling-context versions;
- ordered Session occurrences mapped to calendar dates and local meeting
  contexts;
- source and allocated durations and theory or lab allocations;
- derived Week and Day aliases where requested;
- conflict and constraint findings;
- an explicit list of unscheduled Sessions;
- completeness and validation status; and
- provenance sufficient to reproduce or explain the result.

The schedule is a derived artifact or intermediate result. It does not become
canonical curriculum or an Academic Calendar.

## Validation Requirements

Before scheduling, validation must confirm:

- all requested object identities and versions resolve;
- Session duration, type, allocations, prerequisites, dependencies, resource
  needs, and safety requirements are coherent;
- Course, Unit, and Session order does not contradict dependencies;
- the Institution Profile and Academic Calendar are compatible and cover the
  requested scheduling scope; and
- applicable meeting patterns and local policies are unambiguous.

After scheduling, validation must confirm:

- every Session is scheduled or explicitly unscheduled;
- every occurrence refers to the intended Session identity and version;
- placements fall on eligible dates and within eligible meeting containers;
- duration, theory or lab allocation, sequence, prerequisites, resources, and
  safety constraints are satisfied or reported;
- no prohibited overlap or duplicate placement exists;
- Week and Day labels are derived consistently; and
- completeness and provenance are accurately reported.

Validation findings never rewrite curriculum, institution configuration, or
calendar availability. The owning source must be changed and the schedule
regenerated when correction is required.
