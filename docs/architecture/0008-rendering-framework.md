# 0008: Rendering Framework

- Status: Accepted
- Scope: Define the presentation boundary from immutable scheduled repositories
  to immutable rendered-artifact descriptors.

## Architectural boundary

```text
Repository
    → Validation
    → Compilation
    → Scheduling
    → Scheduled Repository
    → Rendering
    → Rendered Artifacts
```

Rendering accepts only an immutable `ScheduledRepository`. It reads scheduled,
compiled, curriculum, institution, and calendar values through that aggregate
and retains the exact aggregate as artifact provenance. It never loads a
repository, validates source data, schedules or optimizes Sessions, changes a
source object, or persists output.

The first framework release describes render requests and results. Its DOCX,
PDF, HTML, and Markdown renderers intentionally produce immutable descriptors,
not document bytes or files. Format-specific generation can be added behind
the same interface after its output contracts are approved.

## Renderer lifecycle

1. A caller resolves a renderer from `RendererRegistry`.
2. The renderer verifies that the template supports its output format.
3. It verifies the requested filename, required presentation context,
   branding, and referenced assets.
4. It derives a deterministic source fingerprint and artifact identifier from
   the schedule, template, renderer, and presentation context.
5. It returns an immutable `RenderedDocument` descriptor that retains the
   original `ScheduledRepository` by identity.

The caller supplies the generation timestamp. Consequently the same schedule,
template, context, filename, and timestamp produce equal descriptors.

## Renderer interface and registry

`Renderer` is an abstract interface with stable renderer name, output format,
content type, filename extension, and one `render` operation. Concrete
renderers share request checking and descriptor construction but do not depend
on one another. `RendererRegistry` selects implementations by canonical
`OutputFormat`; registering a future renderer does not require edits to an
existing renderer.

Registry mutation configures an application service. It never mutates a
renderer or a scheduled source.

## Context model

`RenderingContext` composes immutable, presentation-only values:

- `RenderOptions` controls filename and declared generation timestamp;
- `InstitutionBranding` selects display names and asset references;
- `Theme` selects named colors, typography, and theme assets;
- `Localization` selects locale, language, time zone, and display labels;
- `PageSettings` selects page size, orientation, and margins; and
- `AssetCatalog` resolves referenced logos, images, icons, and theme assets.

Context does not contain curriculum selection, dependency, scheduling, or
placement rules.

## Template system

`Template` is renderer-independent. It declares identity and version, artifact
kind, compatible output formats, ordered presentation regions, formatting,
required context fields, required assets, and whether branding is mandatory.
`TemplateRegistry` resolves exact identity/version pairs. No built-in
institution-specific templates are supplied.

Templates arrange source values but may not add curriculum facts, calendar
facts, dependencies, or scheduling decisions.

## Asset management

`Asset` values contain metadata and a URI; they do not embed binary data in
business objects. `AssetReference` and `AssetRequirement` identify assets
without performing I/O. An immutable `AssetCatalog` resolves exact references
and checks declared media-type requirements. Loading files or fetching remote
assets belongs to a later, separately approved integration layer.

## Formatting pipeline

Formatting is represented independently by immutable page-layout, typography,
header/footer, table, image, caption, list, and branding-placement values. A
template owns a `FormattingProfile`; renderers translate that profile into
format-native behavior in future implementations. Formatting contains no
business rules and cannot alter source data.

## Artifact model

`RenderedArtifact` records a deterministic identifier, renderer identity,
exact source schedule, source fingerprint, timestamp, content type, output
filename, output format, and exact template identity/version.
`RenderedDocument` and `RenderedPackage` distinguish single-document and
multi-entry results. Package entries remain descriptors and do not imply
persistence.

This presentation result is distinct from the frozen provenance-rich
`src.models.RenderedArtifact` domain contract. A future artifact-production
layer may map a rendering descriptor into that canonical envelope without
changing either source schedules or this renderer interface.

## Failure model

```text
RenderingError
├── RenderingContextError
│   └── MissingBrandingError
├── UnsupportedRendererError
├── UnsupportedOutputError
├── TemplateError
│   └── UnsupportedTemplateError
├── AssetError
│   └── MissingAssetError
└── FormattingError
```

Failures are raised before a descriptor is returned. They report presentation
request problems only; they do not repeat repository, curriculum, or schedule
validation.

## Extension points and supported formats

DOCX, PDF, HTML, and Markdown are registered framework formats. Production
encoders may later subclass or compose the common renderer behavior, while new
templates and assets are registered as data. LMS export, persistence,
institution-specific templates, lesson-plan generation, and CLI behavior are
outside this layer.
