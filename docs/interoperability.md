# Import / Export Framework

The interoperability framework translates external documents at the stable
TEOS application boundary. It does not modify repositories or expose engine
objects.

## Architecture

```text
external bytes
    → importer
    → immutable ImportResult + src.api request
    → InteroperabilityManager.execute_import
    → TEOSApplication.execute
    → immutable src.api response
    → exporter
    → immutable ExportResult
```

Import translation and API execution are separate operations. Applications can
inspect diagnostics and source attribution before choosing to execute a
request. Exporters return text and never write files; the embedding application
chooses where to persist or transport it.

## Translation lifecycle

An import proceeds through:

1. exact capability and version lookup;
2. source decoding with the configured encoding;
3. syntax validation;
4. envelope and request-field validation;
5. construction of one immutable public API request;
6. diagnostic and SHA-256 source-attribution reporting; and, only when
   explicitly requested,
7. submission through `TEOSApplication.execute`.

An export proceeds through:

1. exact capability and version lookup;
2. projection of the immutable public response;
3. optional diagnostic inclusion;
4. deterministic format encoding; and
5. return of immutable content and media-type metadata.

## Supported formats

| Format | Import representation | Export representation |
| --- | --- | --- |
| CSV | One header and one request row | One response-summary row |
| Markdown | YAML request front matter | YAML response metadata and summary |
| JSON | Request envelope object | Public response object |
| YAML | Request envelope mapping | Public response mapping |

JSON, YAML, and Markdown request metadata use this envelope:

```yaml
format_version: "1.0"
operation: validate_repository
request:
  repository_path: .
  timing: false
```

CSV places `format_version`, `operation`, and request fields in columns.
Structured CSV values use canonical JSON within their cells.

## Registry model

`InteroperabilityRegistry` stores importer and exporter capabilities under
separate keys. A capability declares:

- normalized format name;
- importer or exporter direction;
- exact supported format versions;
- recognized filename extensions; and
- recognized media types.

Duplicate names within one direction are rejected. Registration inspection and
discovery results use stable sorting. `discover` selects by direction, exact
version, and optional extension/media type; zero or multiple matches are
compatibility errors.

The default `InteroperabilityManager` automatically registers the eight
built-in translators.

## Context model

`ImportContext` carries the selected format version, optional source path,
`FormatOptions`, and `ConversionOptions`. `ExportContext` carries the same
options without import source state. All context and option types are frozen.

`FormatOptions` controls encoding, newline, CSV delimiter, indentation, key
ordering, and immutable format-specific values. `ConversionOptions` controls
strict unknown-field handling, exported diagnostic inclusion, and immutable
conversion-specific values.

Strict import mode reports unsupported fields as errors. Permissive mode omits
them and reports warnings. Neither mode silently changes known values.

## Diagnostics

Translation diagnostics have a stable kind, severity, message, source, field
path, and optional source position. Kinds are:

- `unsupported_field`
- `data_truncation`
- `unknown_value`
- `missing_mandatory_field`
- `version_mismatch`
- `unsupported_feature`

Collections preserve translator order and expose `has_errors`. Syntax that
cannot be decoded raises `FormatError`; source issues that can be located in a
decoded document are returned as diagnostics.

## Exception hierarchy

```text
ImportExportError
├── ImportError
├── ExportError
├── FormatError
├── CompatibilityError
└── TranslationError
```

`CompatibilityError` covers unknown capabilities and unsupported versions.
`TranslationError` prevents execution when import diagnostics contain errors.

## Version compatibility

`FRAMEWORK_VERSION` versions the Python framework. The current public
interoperability contract is `SUPPORTED_FRAMEWORK_CONTRACT_VERSION == "1.0"`.
Every source and export independently declares format version `1.0`.

Lookup uses exact capability-declared versions. There is no implicit upgrade or
downgrade. New versions can coexist in a capability; a changed field meaning,
request mapping, or response shape requires a new format version.

## Plugin integration

Plugins implement `Importer` or `Exporter` and declare a `FormatCapability`.
They register instances through the existing plugin categories:

```python
from src.plugins import EXPORTER, IMPORTER


class ExamplePlugin:
    def activate(self, context):
        context.registrar.register(IMPORTER, ExampleImporter())
        context.registrar.register(EXPORTER, ExampleExporter())
```

After the normal plugin manager activates plugins, an application passes its
`ExtensionRegistry` to `InteroperabilityManager` or calls
`register_plugin_extensions`. The interoperability framework copies active
registrations but never imports, activates, unloads, or otherwise owns plugin
code.

## Sample import workflow

```python
from pathlib import Path

from src.interoperability import ImportContext, InteroperabilityManager

manager = InteroperabilityManager()
imported = manager.import_discovered(
    Path("request.json"),
    ImportContext(format_version="1.0"),
)

if imported.success:
    execution = manager.execute_import(
        "json",
        '{"format_version":"1.0","operation":"validate_repository",'
        '"request":{"repository_path":"."}}',
    )
    response = execution.response
```

Use `import_data` when content is already in memory.

## Sample export workflow

```python
from pathlib import Path

from src.api import TEOSApplication, ValidateRequest
from src.interoperability import ExportContext, InteroperabilityManager

application = TEOSApplication()
response = application.validate_repository(
    ValidateRequest(repository_path=Path("."))
)

manager = InteroperabilityManager(application=application)
exported = manager.export_data(
    "json", response, ExportContext(format_version="1.0")
)
Path("output/validation.json").write_text(exported.content, encoding="utf-8")
```

Writing the returned content is an application concern; the exporter itself is
side-effect free.
