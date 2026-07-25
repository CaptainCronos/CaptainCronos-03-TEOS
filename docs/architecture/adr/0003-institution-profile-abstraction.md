# ADR 0003: Institution Profile Abstraction

## Status

Accepted

## Context

Institutions differ in identity, campus configuration, branding, calendars,
meeting patterns, instructional-day lengths, theory and lab conventions,
templates, terminology, local policies, and integration targets. Placing these
differences in curriculum would create institution-specific curriculum forks.
Distributing the settings independently among schedulers, renderers, and
exporters would make configuration inconsistent and difficult to trace.

TEOS needs a versioned institutional boundary that supplies local context while
preserving canonical curriculum.

## Decision

TEOS uses an Institution Profile as the authoritative abstraction for
institution-owned presentation, scheduling conventions, local policy
references, and integration configuration.

An Institution Profile identifies the institution and optional campus context;
references Academic Calendars, templates, brand resources, and policies; and
provides meeting patterns, instructional-day conventions, terminology, and
export settings to the appropriate engines.

Profiles may select an approved curriculum version but must not redefine
Standards, Competencies, Instructional Units, Sessions, Course content,
educational sequence, or completion requirements.

## Consequences

- Canonical curriculum can be applied consistently at multiple institutions.
- Schedulers, renderers, and exporters share one traceable institutional
  context.
- Profile and curriculum versions can evolve independently.
- Campus-specific composition must have explicit precedence and provenance.
- Referenced calendars and templates remain independently owned and versioned.
- Local policy validation can be distinguished from universal curriculum
  validation.
- A substantive local curriculum difference requires an approved curriculum
  version rather than a hidden profile override.
- Profile validation must prevent copied calendar data and curriculum
  redefinition.

## Alternatives Considered

### Institution-Specific Curriculum Forks

Rejected because institutional presentation and scheduling differences would
become indistinguishable from changes to educational meaning.

### Configuration Embedded Separately in Each Engine

Rejected because scheduling, rendering, and export could apply inconsistent
institutional identity, terminology, and policy.

### Put All Institutional Data in the Academic Calendar

Rejected because calendars own date availability, not branding, templates,
meeting conventions, policy references, or integration configuration.

### Global Configuration Only

Rejected because it cannot represent multiple institutions, campuses, or
versioned local contexts in a reproducible way.
