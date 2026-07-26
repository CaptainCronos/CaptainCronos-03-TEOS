# Document Generation

The Document Generation Layer turns immutable rendering descriptors into
downloadable files. Its accepted architecture is
[`0009-document-generation-layer.md`](architecture/0009-document-generation-layer.md).

## Supported formats

| Format | Generator | Media type | Native support |
| --- | --- | --- | --- |
| DOCX | `DocxGenerator` | Office Open XML document | `python-docx` |
| PDF | `PdfGenerator` | `application/pdf` | ReportLab |
| HTML | `HtmlGenerator` | UTF-8 HTML | Python standard library |
| Markdown | `MarkdownGenerator` | UTF-8 Markdown | Python standard library |

All generators implement `Generator.generate`. The operation accepts an
immutable rendering `RenderedArtifact`, an output directory, and optionally
the exact `Template` and `RenderingContext` used to create the descriptor.
Template and context must be supplied together.

```python
generated = GeneratorRegistry.with_defaults().select(
    artifact.output_format
).generate(
    artifact,
    "output",
    template=template,
    context=context,
    asset_root=".",
)
```

## Output lifecycle

Generation validates the format, media type, extension, template identity,
timestamp, filename, output containment, and asset references. It then creates
native bytes, writes a temporary sibling file, atomically replaces the target,
and calculates the SHA-256 checksum from the exact written bytes.

The returned `GeneratedFile` is immutable and records filename, resolved path,
media type, generation timestamp, checksum, byte size, artifact identity, and
generator version. `GeneratedDirectory` and `GeneratedPackage` describe
ordered multi-file results without adding persistence or publication behavior.

Generated files are replaceable artifacts. Repository workflows place them
under `output/` and do not commit them.

## Asset embedding

Asset bytes remain external to rendering objects. Generation resolves catalog
URIs against the explicit `asset_root`. Relative paths and local `file:` URIs
are supported; remote retrieval is not.

DOCX and PDF accept common raster formats. HTML and Markdown embed declared
logo bytes as data URIs, keeping each deliverable self-contained. Unsupported
media types, absent files, and unreadable resources raise
`AssetEmbeddingError`.

## Extension points

Add a generator by subclassing `Generator`, declaring its stable identity,
format, media type, and extension, and implementing `_encode`. Register the
instance in `GeneratorRegistry`; no existing generator needs to change.

Format helpers are separated by responsibility: DOCX tables, styles, images,
and numbering; PDF layout and fonts. New helpers must remain native encoding
concerns and must not select curriculum, alter schedules, or make rendering
decisions.
