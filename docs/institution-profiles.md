# Institutional Profile Framework

## Purpose and Boundary

The Institutional Profile Framework provides immutable, configuration-driven
institution identity, branding, calendar, grading, terminology, template, and
operational-policy settings. The package is an application configuration
boundary. It does not contain curriculum, mutate domain objects, schedule
Sessions, render templates, generate documents, authenticate users, integrate
with an LMS, or call cloud services.

The implementation follows
[Architecture 0004](architecture/0004-institution-profiles.md) and
[ADR 0003](architecture/adr/0003-institution-profile-abstraction.md).
Institution data remains under `institutions/`, calendar facts remain under
`calendars/`, and template resources remain under `templates/`.

## Architecture

```text
institution profile JSON ─┐
                          ├─ InstitutionProfileLoader
calendar JSON sources ────┘             │
                                        ▼
                           InstitutionProfileValidator
                                        │
                                        ▼
                           immutable InstitutionProfile
                                        │
                                        ▼
                           InstitutionProfileRegistry
                                        │
                                        ▼
                            InstitutionProfileManager
                                        │
                                        ▼
                     public application operation context
```

`src.institution` exposes the public configuration API. Existing repository,
validation, compiler, scheduler, renderer, generator, plugin, and domain-model
implementations are unchanged. A consuming application resolves the requested
profile before invoking an operation and supplies only the relevant
configuration to the existing layer.

## Configuration Model

An `InstitutionProfile` is a frozen aggregate identified by `profile_id` and a
semantic `version`. `contract_version` identifies the configuration contract;
`teos_compatibility` constrains compatible TEOS host versions. The aggregate
contains:

- `InstitutionMetadata`
- `InstitutionBrand`
- one or more `AcademicCalendarProfile` values assembled from calendar sources
- `GradingPolicy`
- `TerminologyProfile`
- `TemplateProfile`
- `OperationalPolicy`

All collection fields become tuples and every public configuration object is a
frozen, slotted dataclass. The loader rejects unknown top-level and nested
fields instead of silently accepting configuration drift.

## Branding Model

`InstitutionBrand` provides the approved display name, external logo,
watermark, and font asset references, named six-digit RGB colors, font names,
header and footer text, copyright text, and revision text.

`BrandAsset` stores a repository-relative path and an asset kind. Logo
references require alternative text. Required assets must exist below the
resource root during validation. The framework neither reads image bytes nor
transforms assets.

## Calendar Model

Calendar facts live in independent JSON documents under `calendars/` and are
assembled through `calendar_sources`. `AcademicCalendarProfile` supports
semester, quarter, trimester, and block systems. `AcademicPeriod` defines
bounded institution-owned periods. `CalendarDay` classifies holidays, breaks,
instructional days, and make-up days.

Calendar validation rejects duplicate calendar versions, duplicate period
identifiers, duplicate date classifications, reversed periods, and classified
dates outside all declared periods. Calendar periods remain operating-date
containers and never become curriculum Weeks, Days, Courses, or Sessions.

## Grading Model

`GradingPolicy` supports letter, numeric, competency, and pass/fail systems.
Letter and numeric systems require grade bands. Optional weighted categories
must have unique identifiers and total exactly 100 percent. Passing thresholds
are bounded from zero through 100. Attendance and late-submission rules are
immutable policy text; the framework does not calculate grades or enforce
student behavior.

## Terminology Model

`TerminologyProfile` maps a fixed canonical TEOS vocabulary to
institution-approved presentation labels. `label()` returns the override when
one exists and the canonical term otherwise. Overrides cannot introduce an
unknown canonical key, redefine an identity, or change validation and
curriculum semantics.

## Template Configuration Model

`TemplateProfile` stores versioned `TemplateSelection` references for lesson
plans, assessments, quizzes, worksheets, certificates, reports, attendance
sheets, and grading exports. A selection may target an audience and one
selection per kind may be the default.

Selection is deterministic: an exact audience match wins, otherwise the unique
default is returned. Ambiguous or unavailable selections fail explicitly. The
framework selects external template metadata but never parses or renders a
template body.

## Policy Model

`OperationalPolicy` carries revision policy, document-numbering conventions,
approval workflow metadata, record-retention text, naming conventions, and a
safe repository-relative output-directory default. These are inputs for
authorized consumers, not executable business rules.

## Registry Lifecycle

`InstitutionProfileManager.load()` sorts input paths, loads and validates every
profile, constructs a new registry, and publishes it only after the whole set
succeeds. This makes replacement atomic.

`InstitutionProfileRegistry` supports multiple institutions and versions,
explicit defaults, exact lookup, unambiguous single-version lookup, greatest
semantic-version lookup, compatibility filtering, immutable snapshots, and
deterministic iteration. Duplicate identity/version pairs are rejected.
Future packaged profiles can be loaded by supplying their extracted profile
paths and resource root without changing registry semantics.

## Validation Strategy

Validation has four stages:

1. Strict JSON structure and safe repository-relative paths.
2. Immutable object construction and local value invariants.
3. Cross-section validation for assets, calendars, grading, templates,
   terminology, time zones, duplicates, and contract compatibility.
4. Deterministic registration and default resolution.

Validation reports ownership-specific exceptions and never repairs data,
changes curriculum, or substitutes a newer referenced resource silently.

## Exception Hierarchy

```text
InstitutionError
├── ProfileLoadError
├── ProfileValidationError
│   ├── BrandingError
│   ├── CalendarConfigurationError
│   ├── GradingConfigurationError
│   └── TemplateConfigurationError
├── ProfileRegistrationError
└── ProfileCompatibilityError
```

Validation exceptions may expose immutable `findings` with missing or
conflicting resource identifiers.

## Example

Profile and calendar configuration use the `.teos-profile` and
`.teos-calendar` suffixes so the frozen repository loader does not mistake
framework package manifests for canonical domain-object JSON. Their contents
are strict JSON.

The example profile is
[`institutions/example-technical-college/profile.teos-profile`](../institutions/example-technical-college/profile.teos-profile).
It references the separately owned
[`calendars/example-technical-college-2026.teos-calendar`](../calendars/example-technical-college-2026.teos-calendar)
and
[`templates/example-technical-college/lesson-plan.md`](../templates/example-technical-college/lesson-plan.md).

```python
from pathlib import Path

from src.institution import InstitutionProfileManager, TemplateKind

root = Path(".")
manager = InstitutionProfileManager(teos_version="1.1.0")
manager.load(
    (root / "institutions/example-technical-college/profile.teos-profile",),
    resource_root=root,
    default=("example-technical-college", "1.0.0"),
)
profile = manager.select()
lesson_plan = profile.templates.select(TemplateKind.LESSON_PLAN)
```
