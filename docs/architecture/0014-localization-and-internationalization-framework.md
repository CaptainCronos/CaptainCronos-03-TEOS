# 0014: Localization and Internationalization Framework

- Status: Accepted
- Scope: Define data-driven presentation localization without changing TEOS
  curriculum or execution semantics.

## Architectural boundary

```text
Localization resources
        ↓
Institution Profile
        ↓
Public Application API
        ↓
Repository → Validation → Compilation → Scheduling → Rendering → Generation
```

`src.localization` is a presentation-support boundary. It resolves immutable
language and locale resources into display strings and formatted values.
Callers may add its results to an institution or rendering context, but the
framework does not mutate those contexts or depend on engine objects.

Curriculum identity, references, validation, compilation, scheduling,
rendering, and generation remain language-independent. Localization changes
only human-facing presentation.

## Resource model

A localization resource has a stable identifier and version, a locale,
framework compatibility metadata, a declared source layer, and immutable
translation and terminology entries. It may additionally define a language,
locale conventions, currency metadata, unit labels, and plural rules.

The source layers, from highest to lowest precedence, are:

1. institution overrides;
2. plugin resources;
3. language packs;
4. the configured default language; and
5. built-in English.

Resources are loaded independently from JSON or YAML. The loader rejects
unknown fields, malformed identifiers, duplicate mapping keys, invalid locale
definitions, and incompatible contract versions. The registry rejects
duplicate resource identifiers and ambiguous keys at the same locale and
precedence.

## Language and locale model

A `Language` identifies a BCP 47 language subtag, English and native names,
script, and default page direction. A `Region` identifies an ISO-style region
code and name. A `Locale` combines language, optional script and region,
culture name, explicit fallback locale, and document conventions.

Locale identifiers use normalized BCP 47 syntax. This framework validates and
normalizes identifiers but does not claim to implement the entire Unicode
locale extension registry.

Document conventions contain date and time patterns, date order, hour cycle,
paper size, measurement system, page direction, separators, quotation marks,
numbering digits, default time zone, currencies, and unit labels. Formatting
uses only this data and Python's deterministic date, decimal, and zone-info
facilities; it never changes process-global locale state.

## Translation and terminology

Translation keys are stable dotted identifiers. Lookup searches resource
layers for the requested locale, then each explicitly declared locale
fallback, followed by the configured default locale and built-in `en-US`.
Repeated locales are ignored and cycles are rejected when a registry is
validated.

Plural translations use immutable category mappings and declarative operand
conditions. The framework selects a category from the locale's plural rule and
falls back to `other`. It performs no machine translation.

Terminology uses canonical TEOS display-term keys. Institution terminology
has the highest precedence, but canonical curriculum values and domain objects
are never modified. A missing translation or term returns the supplied
default, or the key itself, and records a diagnostic rather than terminating
processing.

## Registry and plugin integration

`LocalizationRegistry` owns deterministic registration and validation.
Snapshots and returned resources are immutable. Registration is additive;
manager loading is atomic.

Plugins continue to register through the existing `localization` extension
category. `LocalizationManager.register_plugin_extensions` copies immutable
resource values into the localization registry. The localization framework
does not discover, import, activate, unload, or execute plugin code.

Institution integration is similarly one-way: an application supplies
presentation-only translation or terminology overrides. This framework does
not import or modify the frozen Institution Profile implementation.

## Failures and diagnostics

Configuration defects raise a typed `LocalizationError`. Missing presentation
content is non-fatal and becomes an immutable validation diagnostic.
Validation covers duplicate identifiers and keys, invalid language and locale
definitions, unsupported locales, broken fallback chains, compatibility, and
missing translations relative to an optional required-key set.

## Exclusions

The framework does not implement automatic or cloud translation, OCR,
curriculum mutation, repository changes, scheduling rules, renderer behavior,
document-generator behavior, or institution-specific policy.
