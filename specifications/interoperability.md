# Interoperability Specification

## Purpose

The interoperability contract translates external documents to TEOS Public
Application API requests and public API responses to external documents
without taking ownership of curriculum or engine objects.

## Import envelope

JSON, YAML, and Markdown imports MUST represent one mapping with:

- `format_version` — an explicitly supported interchange version;
- `operation` — one operation published by `src.api.Operation`; and
- `request` — a mapping of constructor fields for that operation's published
  immutable request type.

CSV imports MUST contain the same values in one record. Request fields occupy
individual columns; structured cell values MUST use JSON. Multiple CSV records
are unsupported in contract version 1.0.

Unknown envelope and request fields MUST be diagnosed. Strict conversion MUST
reject them; permissive conversion MAY omit them only with an ordered
diagnostic. Missing mandatory fields MUST prevent request construction.

## Export document

An export MUST contain the format version, operation, status, success state,
public result projection, public diagnostics when requested, elapsed time, and
source attribution. Published artifact, generated-file, stage, and plugin
descriptors MUST be retained when present. Paths, timestamps, enumerations, and
diagnostic locations MUST have deterministic scalar representations.

An exporter MUST NOT inspect private application state or engine objects.

## Determinism

Object keys, diagnostic order, registry discovery results, and structured CSV
cell values MUST be stable. JSON MUST use stable separators and ordering. YAML
MUST use stable key ordering. Markdown and CSV MUST use the configured newline.

## Attribution and immutability

Import results MUST preserve an optional source path and a SHA-256 digest of
the exact imported bytes. Contexts, capabilities, diagnostics, results, and
registrations MUST be immutable public values. A translated public request
remains governed by the immutability guarantees of `src.api`.

## Compatibility

Format compatibility MUST be checked before semantic translation. Version
selection is exact; no importer or exporter may silently upgrade or downgrade
a document. Plugin capabilities MUST declare every version they implement.
