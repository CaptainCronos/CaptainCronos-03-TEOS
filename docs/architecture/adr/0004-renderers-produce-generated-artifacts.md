# ADR 0004: Renderers Produce Generated Artifacts

## Status

Accepted

## Context

TEOS must produce documents, schedules, packages, feeds, and other outputs for
different audiences and systems. If those outputs are edited and maintained as
source data, they can diverge from curriculum, institutional configuration,
calendars, templates, and one another. Committing generated files also obscures
meaningful source changes and creates uncertainty about which representation is
authoritative.

The architecture needs a one-way boundary between maintained sources and their
presented or exported forms.

## Decision

Renderers and export integrations produce generated artifacts from validated,
versioned inputs. Generated artifacts are not authoritative source data.

Artifacts are written under `output/`, are not committed, and are safe to
replace by regeneration. Their provenance identifies the relevant curriculum,
Institution Profile, Academic Calendar, template, and rendering or export
context versions.

Corrections are made in the source owned by the relevant subsystem or in
rendering behavior and templates. Generated files are then regenerated; edits
to an artifact are never used as the canonical change path.

## Consequences

- Curriculum, institution, calendar, and template sources remain authoritative.
- Outputs can be reproduced and compared from declared versions.
- Multiple artifact formats can coexist without becoming competing curriculum
  models.
- Generated-file churn is kept out of version control.
- Delivery workflows must generate or retrieve artifacts rather than assume
  they are stored as source.
- Rendering and export validation must detect missing data or incompatible
  targets before an artifact is presented as complete.
- Provenance is required to explain which sources produced an artifact.
- Manual changes to a delivered artifact are outside the canonical workflow
  and will be lost on regeneration.

## Alternatives Considered

### Commit Generated Artifacts

Rejected because generated changes obscure source reviews, create repository
churn, and risk stale outputs appearing authoritative.

### Treat Rendered Documents as Editable Curriculum

Rejected because layout-oriented representations cannot reliably preserve
identity, relationships, ownership, and validation semantics across formats.

### Maintain a Separate Hand-Edited Output per Institution

Rejected because institutional variations belong in profiles and templates,
and hand-maintained copies would drift from shared curriculum.

### Allow Two-Way Synchronization from Artifacts

Rejected at this architectural layer because reverse mapping is ambiguous
across layouts and export formats and would undermine single ownership.
