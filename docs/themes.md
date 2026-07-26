# Theme and Branding Framework

The Theme and Branding Framework is TEOS's immutable presentation-resource
layer. It separates visual identity from curriculum, institutional policy,
document structure, rendering logic, and generator behavior. Its accepted
architecture is recorded in
`docs/architecture/0015-theme-and-branding-framework.md`.

## Theme architecture

Applications load JSON or YAML packages through `ThemeLoader`, collect them in
an immutable `ThemeRegistry`, and resolve them through `ThemeManager` or
`ThemeResolver`. Loading and registration construct a complete replacement
registry before publication, so a failed update leaves the active registry
unchanged.

A `Theme` aggregates `ThemeMetadata`, `Branding`, `ThemeTypography`,
`ThemePalette`, `ThemeLayout`, `ThemeAssets`, `ThemeStyles`, and
`ThemeTemplates`. Every public model is a frozen, slotted dataclass. Registries,
resolved mappings, and recursive style properties are immutable.

The framework reads theme package files only. Asset and template URIs are
opaque references; the framework never opens, edits, downloads, copies, or
embeds their targets.

## Branding model

`Branding` supports institution and department display names, contact
information, and references for logos, department logos, seals, watermarks,
cover pages, headers, footers, and revision blocks. Each reference must resolve
to a named `ThemeAsset` in the effective theme. Branding contains no
institutional policy or curriculum data.

An institution may select a registered theme identifier or supply a
presentation-only `Theme` with the `institution` source layer. The resolver
merges that value without importing or mutating `src.institution`.

## Typography model

`ThemeTypography` owns named `FontFamily` values and logical `TextStyle` values
for body text, headings, captions, code, and tables. A text style declares its
font-family reference, point size, weight, italics, optional semantic color,
line spacing, and paragraph spacing. Font references are validated within the
effective typography catalog. No font files are loaded or embedded.

## Color palette model

`ThemePalette` exposes primary, secondary, accent, warning, success, error, and
neutral colors. It also supports named print-safe and high-contrast variants.
Colors use six- or eight-digit hexadecimal notation. Semantic color names are
presentation tokens; this layer does not translate them into PDF, CSS, DOCX,
or other format-native instructions.

## Layout model

`LayoutDefinition` identifies an artifact kind, logical page size,
orientation, margins, ordered regions, and referenced styles.
`ThemeLayout` can hold reusable layouts for lesson plans, assessments, labs,
quizzes, worksheets, reports, certificates, attendance forms, grade sheets,
and future artifact kinds. It does not decide document content or implement
page composition.

## Asset management

`ThemeAsset` holds a stable identifier, kind, URI, media type, and description.
Supported kinds cover logos, icons, backgrounds, banners, watermarks, seals,
illustrations, and custom graphics. `ThemeAssets.require()` provides exact
lookup. URI existence and binary manipulation remain responsibilities of the
host or a separately approved integration layer.

The validator detects empty URIs, malformed media types, duplicate asset
identifiers, and asset identifiers referenced by branding or templates but
absent from the effective catalog.

## Style inheritance and resolution

`StyleDefinition` is a named immutable property mapping with an optional parent
style. Parent properties merge first and child properties override matching
keys. Missing parents and cycles are rejected. Recursive JSON-shaped property
values are frozen.

Overall theme resolution applies resources from low to high precedence:

```text
Built-in → Configured Default → Selected Theme → Institution Override
```

Explicit ancestors are applied before their child. Named assets, styles,
layouts, templates, font families, and headings merge by stable identifier.
Higher layers replace matching identifiers. Branding uses the highest non-empty
field. The resolver returns a new `ResolvedTheme` and never modifies a source
theme.

## Template selection

`DocumentTemplate` references a URI, artifact kind, optional output format,
layout, styles, and required assets. Selection first chooses an exact output
format, then a format-neutral template, then stable template-identifier order.
A missing selection raises `TemplateError`; no renderer or generator is called.

## Validation and errors

The loader rejects unreadable files, unsupported extensions, invalid syntax,
duplicate mapping keys, unknown fields, and malformed values.
`ThemeRegistry` rejects duplicate theme identifiers, unsupported contract
versions, missing or cyclic parent themes, invalid or cyclic style inheritance,
and broken branding, layout, template, style, and asset references.

The exception root is `ThemeError`. Its typed branches are `ThemeLoadError`,
`ThemeCompatibilityError`, `ThemeRegistrationError`, `ThemeResolutionError`,
`StyleResolutionError`, `AssetError`, `LayoutError`, `BrandingError`, and
`TemplateError`.

## Plugin integration

Plugins register immutable `Theme` values through the existing `theme`
extension category. `ThemeManager.register_plugin_extensions()` copies those
values into a new registry and requires the `theme` source layer. It neither
discovers nor activates plugin code.

## Examples

- `examples/themes/example-technical-college.theme.json` is a complete reusable
  theme package.
- `examples/themes/example-department-branding.theme.yaml` is an institution
  branding override extending that package.

Both examples contain references only; no image assets, PDF styling, or
document-generation behavior is implemented.
