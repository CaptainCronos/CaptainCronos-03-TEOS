# Rendered Artifact Specification

## Purpose

Rendered Artifacts are the canonical output categories produced by TEOS from
validated, versioned sources. They include human-readable documents,
machine-consumable packages, schedules, feeds, and reports. An artifact is a
reproducible result, never an authoritative curriculum, institution, calendar,
or template source.

## Responsibilities

The Rendered Artifact contract:

- defines the supported logical artifact types and output formats;
- identifies required source inputs and generated outputs;
- requires provenance, validation status, and compatibility metadata;
- makes version and reproducibility expectations explicit; and
- preserves a one-way boundary from maintained sources to replaceable outputs.

Renderers own transformation behavior. They do not own or modify the facts they
render.

## Required Fields

Every artifact instance MUST record:

- `artifact_id`
- `artifact_type`
- `artifact_version`
- `format`
- `generation_timestamp`
- `generator_identity`
- `generator_version`
- `source_references`
- `template_reference`, when a template is used
- `validation_status`
- `reproducibility_record`

`source_references` MUST identify every curriculum, Institution Profile,
Academic Calendar, schedule, policy, and other authoritative version that
materially affected the output.

## Optional Fields

- `title`
- `audience`
- `language`
- `institution_profile_reference`
- `academic_calendar_reference`
- `schedule_reference`
- `destination_profile`
- `accessibility_conformance`
- `content_digest`
- `package_manifest`
- `generation_notes`
- `supersedes_artifact_reference`

Optional source references become required when their data or configuration
affects the artifact. A schedule reference is not required for a rendering that
has no date-dependent content.

## Artifact Types

Each artifact type has the following canonical contract:

| Artifact type | Purpose | Required inputs | Generated outputs | Required metadata | Versioning | Reproducibility |
| --- | --- | --- | --- | --- | --- | --- |
| Lesson Plans | Give instructors a Session-level plan for preparation and delivery. | Session; related Competencies and Unit context; applicable instructor materials; template and Institution Profile when institutionally presented; schedule when dates are shown. | A structured plan containing objectives, sequence, duration, resources, equipment, safety controls, assessment intent, and applicable occurrence information. | Session and curriculum versions, audience, template and profile versions when used, schedule and calendar versions when date-dependent. | Changes follow source, template, and renderer versions; a materially changed plan is a new artifact version. | Regeneration from the recorded inputs and generation context MUST reproduce equivalent instructional content and presentation. |
| Instructor Guides | Provide instructor-facing guidance across one or more Units or a Course. | Course or Unit graph; Sessions; Competencies; instructor materials; applicable profile, template, and optional schedule. | An ordered guide with delivery guidance, preparation needs, resources, safety controls, assessment strategy, and traceability. | Curriculum graph versions, scope, audience, profile, template, renderer, and optional schedule provenance. | The artifact version changes when scope, source meaning, guidance, template contract, or renderer output changes materially. | Ordered content and all source-derived requirements MUST be reproducible from the recorded graph and context. |
| Student Guides | Provide learner-facing objectives, materials, activities, safety expectations, and completion guidance. | Course, Unit, or Session scope; applicable Competencies; student materials; profile and template when institutionally presented; optional schedule. | An audience-appropriate guide that preserves curriculum meaning without exposing restricted instructor or answer content. | Scope, audience, curriculum versions, content-selection policy, profile, template, and optional schedule provenance. | Changes in learner-facing meaning, selection policy, or source versions require a new artifact version. | The same sources and selection policy MUST reproduce equivalent learner content with restricted content consistently excluded. |
| Assessments | Collect evidence against defined Competencies and performance criteria. | Competencies; performance criteria; assessment evidence expectations; applicable Sessions or Units; assessment template and generation policy. | Assessment instructions, items or tasks, evidence requirements, criteria, and traceability mappings. | Competency and curriculum versions, assessment policy, form or variant identity, security classification, template, and generator version. | Each materially distinct form or changed criterion mapping requires an identifiable artifact version or variant. | The precise form MUST be reproducible when policy permits; randomized generation MUST record seed or equivalent deterministic inputs. |
| Answer Keys | Provide controlled expected responses, scoring guidance, or evaluator evidence for a specific Assessment. | Exact Assessment version; Competencies; performance criteria; scoring or evaluation policy. | A restricted key, rubric, scoring guide, or expected-evidence guide linked to the Assessment. | Assessment identity and version, competency versions, access classification, scoring-policy version, template, and generator version. | A key MUST version with the Assessment or any change to correct responses, evidence, or scoring meaning. | Regeneration MUST retain an exact, unambiguous link to the Assessment form and reproduce equivalent scoring meaning. |
| Slide Decks | Support visual delivery of Session, Unit, or Course instruction. | Selected curriculum scope; rendering metadata; media references; profile branding; slide template. | Ordered slides and associated presentation metadata or speaker guidance. | Curriculum scope and versions, audience, asset, brand, profile, template, and renderer versions. | Changes to source meaning, slide selection, assets, template contract, or renderer output require a new artifact version. | Slide order, content selection, and asset resolution MUST be repeatable from recorded inputs. |
| LMS Packages | Transfer curriculum-derived content and structure to a compatible LMS destination. | Validated curriculum graph; selected artifacts and assets; Institution Profile LMS/export settings; destination compatibility contract. | A destination-compatible package with manifest, identifiers, content, mappings, and validation report. | All source versions, destination profile and compatibility version, identifier mappings, packaging options, generator version, and digest. | A changed destination contract, mapping, package content, or source version requires a new package version. | The package manifest and file digests MUST be reproducible from the same source set and packaging context, excluding declared non-deterministic envelope values. |
| Reports | Present traceability, coverage, validation, effort, completion design, or other derived TEOS information. | The authoritative objects and validated derived results required by the report definition. | A labeled report with scope, findings, derivation basis, and completeness status. | Report definition and version, source scope and versions, filters, derivation rules, validation status, and generator version. | Changes to report definition, derivation semantics, filters, or sources require a new artifact version. | Re-running the recorded query and derivation context MUST reproduce equivalent findings and totals. |
| Schedules | Map Session identities and versions to calendar occurrences under institutional constraints. | Validated Course graph; Session constraints; Institution Profile; Academic Calendar; applicable resources, policies, and scheduling context. | Ordered occurrences, allocated durations and modes, conflicts, unscheduled Sessions, completeness status, and derived Week or Day aliases. | Curriculum, profile, calendar, policy, scheduler, and context versions; placement status; conflicts; completeness. | Any changed source, placement, constraint, or scheduling decision produces a new schedule artifact version. | Reproduction MUST use the recorded source versions and scheduling context; if multiple valid solutions exist, the decision policy and seed or selected result MUST be retained. |

Artifact-type requirements apply independently of output format. For example, a
Lesson Plan remains a Lesson Plan whether rendered as DOCX, PDF, HTML, or
Markdown.

## Output Formats

TEOS recognizes these canonical output formats:

- **DOCX** — editable office-document delivery format. The file MUST preserve
  required structure, metadata, accessibility features, and template intent.
- **PDF** — fixed-layout delivery or archival format. The file MUST identify its
  source artifact and preserve required accessibility and provenance metadata.
- **HTML** — web-oriented structured content. Output MUST use valid,
  accessible markup and resolve or package its dependent assets explicitly.
- **Markdown** — portable text-source presentation. Output MUST retain
  meaningful hierarchy and identify any format limitations.
- **JSON** — machine-consumable output. It MUST conform to the applicable
  approved output contract and MUST NOT be confused with canonical source
  objects.

Slide Decks and LMS Packages MAY require additional container formats selected
by later approved specifications. A container format MUST identify its internal
manifest and files and MUST NOT weaken artifact provenance.

## Generated Output Rules

Generated outputs MUST be written under `output/`, MUST NOT be committed, and
MUST be safe to replace by regeneration. A multi-file artifact MUST include or
reference a manifest that identifies all constituent files, roles, and content
digests where supported.

An artifact MUST clearly identify incomplete, draft, conflicted, or
partially-generated status. A partial schedule MUST NOT be represented as
complete. Assessment and Answer Key outputs MUST preserve their distinct access
and audience classifications.

## Metadata

Metadata MUST make it possible to answer:

- what artifact type and format was generated;
- which exact sources, templates, policies, and derived inputs were used;
- which generator and renderer versions produced it;
- when and under what generation context it was produced;
- whether validation succeeded and whether the result is complete;
- what audience, destination, language, and security classification apply; and
- how the output can be verified or regenerated.

Metadata MAY be embedded, stored in a package manifest, or emitted in an
associated provenance record, but it MUST travel with or remain unambiguously
linked to the artifact.

## Relationships

Artifacts reference, but never own, [Standards](standard.md),
[Competencies](competency.md), [Instructional Units](instructional-unit.md),
[Sessions](session.md), [Courses](course.md),
[Institution Profiles](institution-profile.md), and
[Academic Calendars](academic-calendar.md) as applicable.

Lesson Plans and Schedules are normally Session-centered. Instructor and
Student Guides and Slide Decks MAY span Sessions, Units, or Courses.
Assessments trace to Competencies and their evidence expectations. Answer Keys
MUST reference an exact Assessment. LMS Packages and Reports MAY compose
multiple artifact types while preserving each source identity.

## Validation Rules

Before generation, validation MUST confirm:

- every required input and version resolves;
- source relationships and ownership boundaries are valid;
- the selected artifact type, format, template, and destination are compatible;
- required audience and access controls are defined; and
- date-dependent artifacts have a valid schedule and calendar context.

After generation, validation MUST confirm:

- required source values and traceability are represented;
- artifact-type and output-format contracts are satisfied;
- metadata and provenance are complete;
- manifests, links, assets, identifiers, and digests are internally consistent;
- accessibility and destination requirements are satisfied where applicable;
- incomplete or conflicted results are labeled accurately; and
- no output claims authority over its sources.

## Versioning

`artifact_version` identifies a particular logical output contract and result.
Artifact provenance MUST separately record versions of all inputs, templates,
generators, renderers, destination profiles, and policies. A source or context
change that can affect output requires regeneration and a new artifact version.

Artifact versions do not replace source versions. Manually editing a generated
file does not create an approved artifact version.

## Reproducibility Requirements

A reproducibility record MUST contain:

- exact source identities, versions, and content digests where available;
- exact template, asset, policy, profile, calendar, and schedule versions used;
- generator, renderer, and destination-contract versions;
- generation options, locale, time zone, and deterministic ordering rules;
- random seed or equivalent input for permitted variable generation;
- dependency or toolchain versions that materially affect output; and
- declared non-deterministic values and the equivalence rule used to compare
  regenerated output.

Reproducibility requires equivalent semantic and presentation output, not
necessarily identical file bytes when a format embeds timestamps or other
declared non-deterministic envelope data. Where byte-for-byte output is a
contract requirement, the generation process MUST normalize those values.

## Lifecycle

Artifacts move through **Generated**, **Validated**, **Published**,
**Superseded**, and **Withdrawn** states. This artifact lifecycle is distinct
from the source-object lifecycle.

- Generated artifacts are not publishable until applicable validation passes.
- Published artifacts MUST retain immutable provenance.
- Superseded and Withdrawn artifacts remain identifiable for audit but MUST NOT
  be presented as current.
- Regeneration creates a new artifact instance or version; it does not rewrite
  historical provenance.

## Prohibited Content

A Rendered Artifact MUST NOT:

- become an editable source of curriculum, institutional facts, or calendar
  dates;
- be committed as maintained repository source;
- hide missing inputs, conflicts, unscheduled Sessions, or failed validation;
- omit materially contributing source versions from provenance;
- contain secrets, credentials, or unauthorized learner information;
- merge Answer Keys into learner-facing Assessments or Student Guides; or
- write derived Week or Day labels back into canonical curriculum.

Corrections MUST be made in the authoritative source, template, policy, or
renderer and then regenerated.

## Future Schema Mapping

Future schemas will need a common artifact envelope plus type-specific payload
contracts, a controlled artifact-type and format vocabulary, typed provenance
references, manifests and digests, validation and completeness states,
audience/security classifications, and reproducibility records. Package and
format schemas MAY specialize the common contract but MUST preserve its
identity, provenance, lifecycle, and boundary rules.

## Cross References

- [Specifications](README.md)
- [Session Specification](session.md)
- [Institution Profile Specification](institution-profile.md)
- [Academic Calendar Specification](academic-calendar.md)
- [System Overview](../docs/architecture/0001-system-overview.md)
- [ADR 0004: Renderers Produce Generated Artifacts](../docs/architecture/adr/0004-renderers-produce-generated-artifacts.md)
