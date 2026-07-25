# 0007: Scheduling Engine

- Status: Accepted
- Scope: Define the implemented execution boundary from immutable compiled
  curriculum to immutable institution schedules.

## Architectural boundary

The Scheduling Engine is the first TEOS layer that introduces time:

```text
Repository
    → Validation
    → Compilation
    → Scheduling
    → Scheduled Repository
    → Rendering
```

It consumes a complete `CompiledRepository` and institution/calendar objects
from that compilation. It never loads source files, repeats schema validation,
changes curriculum or dependency relationships, renders output, serializes or
persists results, allocates resources, or optimizes institutional operations.

Compiled curriculum remains authoritative. Scheduled objects are immutable
execution views whose `source` fields retain the exact compiled objects from
which they derive.

## Execution lifecycle

For each requested `SchedulingContext`, the engine:

1. confirms that the Institution Profile and Academic Calendar are exact
   objects from the supplied compilation;
2. confirms that the profile references the selected calendar by exact
   identity and version;
3. validates calendar identifiers, ranges, periods, time zones, and special
   schedule precedence;
4. derives curriculum precedence from compiled Session prerequisites,
   Course prerequisites, Unit declarations, and Session declarations;
5. derives eligible institution/calendar slots;
6. places each Session in the earliest unused compatible slot;
7. publishes immutable Course, Unit, Session, and repository schedule views;
8. exposes deterministic post-placement constraint validation.

One compilation may be scheduled for multiple independent contexts. Each
context produces an `InstitutionSchedule`; `ScheduledRepository` groups those
results without merging their institutional facts.

## Placement algorithm

The algorithm is a stable serial placement algorithm, not an optimizer.

Calendar dates are considered chronologically. Within a date, instructional
period identifiers and meeting-pattern identifiers provide stable ordering.
Closures are always excluded. Unavailable holidays are excluded unless the
effective special schedule explicitly restores availability. The
highest-precedence special schedule for a date controls availability and
period selection.

Curriculum Sessions are stably topologically ordered using the frozen
prerequisite relationships plus declared Course, Unit, and Session sequence.
Each Session receives the earliest remaining slot whose meeting pattern
accepts its Session type and whose instructional capacity fits its duration.
A used slot is never shared. When no slot is available, or when an unscheduled
predecessor blocks placement, the Session is explicitly retained in
`unscheduled_sessions`.

This behavior favors reproducibility and traceability over packing efficiency.
It does not split Sessions, combine Sessions, or infer permission to do so.

## Calendar integration

`SchedulingCalendar` is a read-only adapter over an `InstitutionProfile` and
`AcademicCalendar`. It checks:

- exact profile-to-calendar references;
- matching institutional time zones;
- unique term, period, meeting-pattern, and special-schedule identifiers;
- instructional dates and term ranges within the academic year;
- valid date-to-term and date-to-period references;
- forward-moving period and meeting-pattern times; and
- unambiguous special-schedule precedence.

Eligible slots retain the source Academic Year, Term, Instructional Period,
Meeting Pattern, Holiday, Closure, and effective Special Schedule values.
Weeks and Days remain derivable aliases and are not written into curriculum.

## Constraint engine

Constraints implement one read-only `ScheduleConstraint` protocol and return
immutable `ConstraintViolation` values. The default deterministic constraint
sequence evaluates:

1. duplicate Sessions and duplicate time containers;
2. instructional dates, periods, availability, holidays, closures, and
   special-schedule precedence;
3. institution calendar references, meeting patterns, weekdays, Session types,
   and period capacity;
4. compiled Session prerequisites;
5. declared Unit and Course sequence; and
6. required Sessions left unscheduled.

Constraints never repair a result or weaken an authoritative requirement.
Callers may inspect all findings or request one aggregate
`ScheduleValidationError`.

## Scheduled object model

```text
ScheduledRepository
├── source: CompiledRepository
└── institution_schedules
    └── InstitutionSchedule
        ├── source: CompiledRepository
        ├── institution_profile: InstitutionProfile
        ├── academic_calendar: AcademicCalendar
        ├── courses
        │   └── ScheduledCourse
        │       ├── source: CompiledCourse
        │       └── instructional_units
        │           └── ScheduledInstructionalUnit
        │               ├── source: CompiledInstructionalUnit
        │               └── sessions
        │                   └── ScheduledSession
        │                       ├── source: CompiledSession
        │                       └── placement: Placement
        ├── sessions
        └── unscheduled_sessions: CompiledSession
```

The flattened Session view supports execution and validation. The nested view
preserves declared Course and Unit context. Both views reference the same
immutable `ScheduledSession` values.

## Validation pipeline

Input validation rejects invalid scheduling contexts before placement.
Post-placement validation can then evaluate both engine output and schedules
constructed by another in-process caller. Findings include duplicate
placements, invalid dates or periods, holiday and closure violations, invalid
institutional references, missing or reversed prerequisites, sequence
violations, and unscheduled required Sessions.

Incomplete schedules are valid immutable results but do not pass the default
validator. This preserves every requested Session without pretending that
insufficient calendar capacity is success.

## Failure model

```text
SchedulerError
├── SchedulingInputError
│   ├── CalendarConfigurationError
│   └── CalendarReferenceError
└── ScheduleValidationError
```

Ordinary capacity exhaustion is represented as an incomplete schedule rather
than an exception. Exceptions identify invalid inputs, unrepresentable
placements, or an explicit request to reject validation findings.

## Future extension points

Future approved layers may supply additional read-only constraints or consume
the scheduled model for optimization. Room, equipment, instructor, student,
vehicle, load, travel, and utilization decisions remain outside this engine.
An optimizer must treat the scheduled result and compiled curriculum as input;
it may not add scheduling behavior to curriculum or mutate dependency
relationships.
