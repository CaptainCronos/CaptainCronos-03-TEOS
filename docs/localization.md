# Localization and Internationalization

The localization framework is a presentation-only service. It loads immutable
resource packs, validates their compatibility and fallback graph, and exposes
translation, terminology, pluralization, and formatting operations.

## Architecture

```text
JSON/YAML resources + plugin packs + institution overrides
                         ↓
              LocalizationManager
                         ↓
       immutable registry → resolver → formatter
                         ↓
         presentation values supplied by an application
```

No localization object owns curriculum, a repository, a schedule, a renderer,
or a generated document.

## Language and resource model

`Language` describes a language code, names, script, and direction. `Region`
describes a region. `Locale` combines them with document conventions and an
optional fallback. `LocalizationResource` packages those values with
translations, terminology, plural rules, metadata, and a precedence layer.

All public value objects are frozen. Mapping-shaped input is converted to
sorted tuples or read-only mappings. A registry snapshot can therefore be
shared without exposing mutable resource state.

## Translation lifecycle

1. The loader decodes a UTF-8 JSON or YAML mapping.
2. Contract, identifier, locale, compatibility, and field validation run.
3. The manager builds a replacement registry and validates the fallback graph.
4. The resolver searches the requested locale and fallback chain by layer.
5. A plural category is selected when a count is supplied.
6. Named parameters are interpolated after a value is selected.
7. Missing content returns the caller's default or key and records a warning.

## Fallback strategy

For each requested locale, resource precedence is:

```text
institution → plugin → language → default → built-in
```

Locale traversal is:

```text
requested locale → declared locale fallback → configured default → en-US
```

Each locale is visited once. The registry rejects declared cycles. Built-in
English guarantees a stable last presentation layer, while an unknown key
still degrades safely to the key.

## Formatting model

`LocaleFormatter` uses resource-owned patterns and symbols. It formats dates,
times, numbers, percentages, currency, measurements, page numbers, and aware
date-times converted through `zoneinfo`. Decimal rounding uses
`ROUND_HALF_UP`. The formatter never calls `locale.setlocale`, so results do
not depend on host process settings.

Document conventions also expose paper size, measurement system, date order,
hour cycle, page direction, decimal and grouping separators, quotation marks,
default time zone, and numbering digits.

## Terminology resolution

Terminology keys are canonical presentation terms such as `Course`, `Lesson`,
`Module`, `Lab`, `Workshop`, `Instructor`, `Student`, `Assessment`, `Quiz`,
and `Certificate`. Lookup uses the same locale and resource precedence as
translations. Institution overrides win without changing canonical model data.

## Plugin integration

A plugin registers one `LocalizationResource`, or an iterable of resources,
under the existing `localization` category. After plugin activation:

```python
manager.register_plugin_extensions(plugin_manager.registry)
```

The resources are copied into a new validated registry. Plugin lifecycle and
ownership remain with `src.plugins`.

## Institution integration

An embedding application creates a presentation-only institution resource:

```python
override = manager.institution_override(
    "example-college",
    "es-ES",
    terminology={"Course": "Asignatura"},
)
manager.register(override)
```

This does not modify an `InstitutionProfile`; an application may derive the
mapping from its profile at the public boundary.

## Example workflow

```python
from pathlib import Path
from src.localization import LocalizationManager

manager = LocalizationManager(default_locale="en-US")
manager.load([Path("examples/localization/es-ES.teos-locale.json")])

title = manager.translate("document.course_title", locale="es-ES")
course = manager.term("Course", locale="es-ES")
date = manager.formatter("es-ES").format_date(today)
```

Machine translation, cloud services, and OCR are intentionally out of scope.
