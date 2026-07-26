# Localization and Internationalization Specification

## Scope

The Localization Framework MUST provide deterministic, data-driven
presentation localization. It MUST NOT alter curriculum, repository,
validation, compilation, scheduling, rendering, generation, or immutable
domain behavior.

## Resource contract

Every resource MUST declare:

- `resource_id`, `version`, and contract compatibility;
- one normalized locale identifier;
- one source layer;
- immutable translations and terminology mappings.

A resource MAY declare its language, locale conventions, plural rule,
currencies, and unit labels. Unknown fields, duplicate identifiers, duplicate
keys at equal precedence, incompatible contracts, and inconsistent
language/locale declarations MUST be rejected.

## Lookup

Translation and terminology lookup MUST be deterministic. Resolution order is
institution, plugin, language, configured default, then built-in English.
Within locale resolution, explicit fallbacks precede the configured default
and built-in English. A fallback cycle MUST be rejected.

Missing display content MUST NOT terminate processing. The resolver MUST
return a supplied default or stable key and expose a diagnostic.

## Formatting

Formatting MUST use the selected locale resource for:

- dates and times;
- decimal numbers and percentages;
- currencies;
- page numbers and numbering digits;
- measurements and unit labels;
- time-zone conversion; and
- document conventions.

Formatting MUST NOT mutate process-global locale state. Unsupported values or
malformed format metadata MUST raise `FormattingError`.

## Extensions

Language and locale packs MUST be addable as data files. Plugin localization
MUST use the existing `localization` extension category. Institution
overrides MUST remain presentation-only and take highest precedence.

## Compatibility

The initial localization resource contract is `1.0`. A resource MUST declare
that contract version exactly. Additive translation keys and new resource
packages are compatible. Changed field meaning or resolution precedence
requires a new contract version.

## Related architecture

- [Localization Architecture](../docs/architecture/0014-localization-and-internationalization-framework.md)
- [Institution Profiles Architecture](../docs/architecture/0004-institution-profiles.md)
- [Plugin Architecture](../docs/architecture/0011-plugin-and-extension-framework.md)
