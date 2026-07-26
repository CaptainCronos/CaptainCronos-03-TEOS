# 0009: Document Generation Layer

- Status: Accepted
- Scope: Define the physical-file boundary from immutable rendering
  descriptors to replaceable generated deliverables.

## Architectural boundary

```text
Repository
    → Validation
    → Compilation
    → Scheduling
    → Rendering
    → RenderedArtifact
    → Document Generation
    → GeneratedFile
```

Document generation accepts an immutable
`src.rendering.RenderedArtifact`. It may also receive the exact immutable
`Template` and `RenderingContext` used by rendering so it can translate
approved regions, formatting, branding, and asset references into a native
document format. It never loads a repository, changes curriculum or schedule
objects, performs placement, selects curriculum content, or changes a rendered
descriptor.

The rendering framework currently records an artifact descriptor rather than
document bytes. Generation therefore uses a single, format-neutral projection
of that descriptor and its retained scheduled source. This projection is a
mechanical representation of already-rendered provenance and schedule values;
format generators may encode and style it but may not add facts or make
scheduling decisions.

## Generator lifecycle

1. A caller resolves a generator from `GeneratorRegistry`.
2. The generator verifies the artifact format, safe output location, template
   identity and compatibility, and referenced assets.
3. It creates an immutable format-neutral output projection.
4. A format-specific encoder creates bytes with stable ordering and metadata.
5. Assets are resolved from the rendering catalog and embedded where the
   native format supports embedding.
6. The bytes are written atomically beneath the requested output directory.
7. A frozen `GeneratedFile` descriptor records the path, media type,
   artifact-supplied generation timestamp, size, and SHA-256 checksum.

The output directory and file are operational artifacts, not authoritative
storage. Generated files belong under `output/` in repository workflows and
must not be committed.

## Common interface and registry

`Generator` exposes stable generator identity, version, output format, media
type, extension, and one `generate` operation. `GeneratorRegistry` resolves
one implementation by canonical `OutputFormat`. Registration rejects
ambiguous formats and does not mutate a generator.

The common operation accepts a `RenderedArtifact`, output directory, and the
optional exact `Template` and `RenderingContext` used by rendering. Supplying
one of the latter without the other is invalid. When supplied, their identity,
format declarations, required resources, and asset references are checked
before file creation.

## Output and file model

`GeneratedFile`, `GeneratedDirectory`, and `GeneratedPackage` are immutable
descriptors. Paths are concrete resolved paths, checksums use the
`sha256:<hex>` form, and package members remain ordered. The descriptors do
not provide mutation, upload, publication, or persistence behavior.

Atomic replacement uses a temporary sibling file and `os.replace`, so a
failed encoder cannot leave a partially written target. Directory traversal,
absolute artifact filenames, symlink escapes, and non-directory output roots
are rejected.

## Asset embedding

Assets remain rendering-owned metadata and references. Generation resolves
only local `file` or relative URIs against an explicit asset root, verifies
that a regular file exists, and checks its declared media type where a native
encoder has restrictions. Network fetching and repository discovery are
outside this layer.

DOCX and PDF embed supported raster images. HTML embeds asset bytes as data
URIs. Markdown emits deterministic data-URI images so the result remains a
single downloadable deliverable. Missing, unreadable, incompatible, or
unsupported assets fail before a successful descriptor is returned.

## Format implementations

- DOCX uses `python-docx` for sections, headers, footers, tables, lists,
  styles, numbering, and images. Package timestamps and volatile properties
  are normalized after encoding.
- PDF uses ReportLab platypus flowables for text, tables, headers, footers,
  pagination, fonts, layout, and images. Invariant output mode removes
  run-specific identifiers and timestamps.
- HTML emits semantic, responsive HTML with an embedded CSS theme, navigation,
  and data-URI assets.
- Markdown emits GitHub-compatible headings, tables, lists, links, and
  embedded data-URI assets with stable line endings and ordering.

## Failure model

```text
GenerationError
├── UnsupportedGeneratorError
├── OutputError
│   └── FileCreationError
├── AssetEmbeddingError
├── TemplateMismatchError
└── MissingResourceError
```

Validation errors are generation-boundary failures. They do not repeat schema,
repository, compiler, scheduling, or rendering validation.

## Determinism

Equivalent immutable inputs, dependency versions, and asset bytes produce
equivalent file bytes. Stable ordering, explicit UTF-8 and LF text encoding,
artifact-supplied timestamps, normalized DOCX ZIP metadata, and invariant PDF
mode prevent wall-clock or platform state from entering output. The resulting
SHA-256 checksum is calculated from the exact bytes written.

## Extension points and exclusions

New generators register against a new or supported `OutputFormat` without
editing existing implementations. Native style, font, layout, image, table,
and numbering helpers are independently testable.

LMS export, CLI behavior, publication, persistence, remote asset fetching,
optimization, repository loading, rendering decisions, and scheduling are
outside this layer.
