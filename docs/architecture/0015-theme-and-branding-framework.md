# 0015: Theme and Branding Framework

- Status: Accepted
- Scope: Define reusable, immutable presentation resources without changing
  document structure, curriculum, scheduling, rendering, or generation behavior.

## Architectural boundary

```text
Theme Resources
        ↓
Institution Profile
        ↓
Localization
        ↓
Rendering
        ↓
Document Generation
```

`src.themes` is a presentation-resource boundary. It loads, validates,
registers, and resolves immutable theme values. Applications may place resolved
values in presentation contexts, but this framework does not import or modify
the frozen institution, localization, rendering, or generation layers.

Themes never contain curriculum, calendar, scheduling, or institution business
rules. They do not render documents, manipulate binary assets, or translate
styles into format-specific PDF, DOCX, HTML, or Markdown behavior.

## Theme model

A `Theme` has stable metadata and immutable branding, typography, palette,
layout, asset, style, and template collections. Metadata includes a stable
identifier, semantic version, theme contract version, description, and source
layer. A theme may extend one other registered theme. Inheritance is explicit,
acyclic, and resolved by identifier.

Theme source layers describe ownership rather than execution:

1. built-in safety theme;
2. configured default themes;
3. selected themes, including plugin themes; and
4. institution overrides.

An institution override is itself presentation data. It cannot mutate an
Institution Profile or introduce institutional policy.

## Branding, typography, palettes, and layouts

Branding contains display identity, department identity, contact information,
and named references for logos, seals, watermarks, cover pages, headers,
footers, and revision blocks. All asset links are identifiers resolved against
the effective theme assets.

Typography declares font families and named text styles for body text,
headings, captions, code, and tables, plus paragraph and line spacing. Color
palettes contain semantic colors and optional print-safe and high-contrast
variants. Layouts are named page configurations selected by artifact kind; they
describe margins, orientation, regions, and style references without encoding
document-generation algorithms.

## Assets, styles, and templates

Assets are immutable metadata and URI references. This layer does not open,
copy, transform, inspect, download, or embed image files.

Styles are named immutable property collections with optional parent-style
references. A style parent must exist in the same effective theme. Style
inheritance is acyclic and merges parent properties before child properties.

Templates are immutable references selected by artifact kind and optional
output format. They may reference layouts, styles, and required assets.
Template selection prefers an exact output-format match over a format-neutral
template, with deterministic identity ordering as the final tie-breaker.

## Resolution

Resolution is deterministic and field-based. From highest to lowest
precedence:

1. institution override;
2. selected theme and its explicit ancestors;
3. configured default theme and its explicit ancestors;
4. built-in theme.

Lower-precedence resources are merged first, then overwritten by
higher-precedence named resources. Scalar branding and metadata selections use
the highest non-empty value. Collections merge by stable key. The result is a
new immutable `ResolvedTheme`; no registered theme is changed.

## Loading, validation, and integration

JSON and YAML loaders reject duplicate keys, unknown fields, malformed values,
and unsupported file formats. Registry construction rejects duplicate theme
identifiers, unsupported contract versions, missing or cyclic parents, missing
assets, invalid or cyclic style references, missing layouts and templates, and
broken template references.

Manager loading and registration are atomic. Plugins continue to register
through the existing `theme` extension category. The manager copies immutable
`Theme` values from active plugin registrations and requires the selected-theme
source layer. It does not discover, activate, or execute plugins.

Applications may construct an institution override or select a theme identifier
from profile data. The framework does not import, mutate, or reinterpret the
Institution Profile model.

## Failure model

```text
ThemeError
├── ThemeLoadError
├── ThemeCompatibilityError
├── ThemeRegistrationError
├── ThemeResolutionError
│   └── StyleResolutionError
├── AssetError
├── LayoutError
├── BrandingError
└── TemplateError
```

Configuration failures are fatal before a registry or resolved theme is
published. All errors describe presentation-resource defects only.

## Exclusions

The framework does not edit images, style PDFs, render documents, modify
rendering algorithms, change generation behavior, contain presentation-specific
business rules, mutate repository or curriculum objects, or influence
compilation and scheduling.
