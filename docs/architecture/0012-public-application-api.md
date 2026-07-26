# 0012: Public Application API

- Status: Accepted
- Scope: Define the stable in-process application boundary over the complete
  TEOS processing pipeline and plugin framework.

## Architectural boundary

```text
Repository loading → Validation → Compilation → Scheduling → Rendering
    → Document Generation → Application Services → Public Application API
    → CLI / Plugins / Future Integrations
```

`src.application` contains the application-service implementation. It
coordinates existing engine interfaces, owns pipeline sequencing, retains
intermediate values during one operation, and translates internal failures.
It does not own curriculum, validation, compilation, scheduling, rendering,
generation, plugin, persistence, terminal, or transport rules.

`src.api` is the supported import boundary. It contains immutable request,
response, result, status, diagnostic, exception, facade, client, and service
contract types. Applications and plugins may import documented names from
`src.api` and `src.api.contracts`. They must not import `src.application`,
whose modules are private implementation details despite not using underscore
filenames.

## Facade lifecycle

`TEOSApplication` is a synchronous, reusable facade. Construction accepts an
optional immutable application configuration and optional implementations of
the public service contracts. A call:

1. validates and combines request input with application defaults;
2. creates an immutable operation context;
3. executes the minimum deterministic pipeline prefix;
4. stops after a fatal stage while retaining completed stage summaries;
5. translates exceptions to diagnostics and stable operation status; and
6. returns one immutable response without writing terminal output.

The facade supports repository validation, compilation, scheduling, rendering,
generation, complete builds, repository inspection, plugin listing, and local
readiness diagnostics. Calls share configured services but no mutable
operation state.

## Request and context model

Every operation has a frozen request value containing only inputs and
configuration. Common processing inputs are repository location, exact
institution profile and academic calendar selections, renderer, generator,
output directory, timing, and diagnostic verbosity. Requests normalize path
inputs but do not read them or contain execution state.

Internal immutable contexts carry normalized request input through application
services. Institution and calendar identities select existing repository
objects; they never become curriculum or calendar content. An aware timestamp
may be injected for deterministic rendering tests and embedding applications.

## Service model

Thin services adapt the existing layers:

- repository service locates and loads validated repositories;
- validation service reports successful authoritative loader validation;
- compilation service invokes the curriculum compiler;
- scheduling service selects exact context objects and invokes the scheduler;
- rendering service selects a renderer and supplies the default schedule
  template and presentation context;
- generation service selects the matching generator and writes the artifact;
- plugin service discovers plugin metadata without activating plugin code; and
- diagnostic service aggregates immutable diagnostics in stable order.

Public protocols in `src.api.contracts` permit compatible service injection.
The default implementations live in `src.application.services`.

## Pipeline orchestration

Pipeline stages have a fixed order:

```text
load → validate → compile → schedule → render → generate
```

An operation requests a terminal stage and executes only its ordered prefix.
`load` performs source discovery and `validate` performs the authoritative
repository load, including schema and cross-file validation. Later stages
consume internal values from the immediately preceding stages. Fatal failure
prevents later execution. Completed stages remain represented in the returned
pipeline result, but their engine values are not published by the API.

## Response and result model

Responses contain an operation identifier, status, optional result,
diagnostics, optional timing metadata, and source information. Convenience
views expose success, warnings, and errors. Status distinguishes success,
success with warnings, partial completion, validation failure, execution
failure, unsupported operation, and configuration failure.

Public results contain stable counts, identifiers, format names, checksums,
paths, and ordered stage summaries. They do not publish repositories,
registries, compiled objects, schedules, renderers, generators, plugin
managers, templates, or rendering contexts. Generated files and rendered
artifacts are projected into immutable public descriptors.

## Diagnostics and error translation

A diagnostic has a machine-readable code, severity, message, optional stage,
object identifier, file location, and field path. Collections preserve
insertion order and offer severity filtering.

Known repository, compiler, scheduler, rendering, generation, and plugin
exceptions are mapped to stable application diagnostics. Repository validation
failures retain source and field path. Unexpected exceptions become an
application service failure diagnostic containing the exception class but no
traceback. Normal facade calls return failure responses; explicit low-level
application misuse may raise the documented `ApplicationError` hierarchy.

## Versioning policy

The public package exports:

- `API_VERSION`, versioning this import and response contract;
- `ENGINE_VERSION`, versioning the coordinated TEOS engine; and
- `SUPPORTED_CONTRACT_VERSION`, identifying the service protocol contract.

The first public API supports one contract version. Compatible additions may
occur within an API major version. Removing or changing published fields,
statuses, diagnostic meaning, operation semantics, or protocols requires a new
API major version. Compatibility checks reject unsupported requested contract
versions before pipeline execution.

## CLI integration

The CLI remains responsible for parsing, configuration precedence, progress,
logging, presentation, and exit codes. Pipeline commands delegate to
`TEOSApplication` and project immutable API responses into existing terminal
messages. The CLI does not assemble engine stages. Its injectable service
bundle is adapted to public service contracts for compatibility with existing
embedders and tests.

## Plugin integration

Plugins may consume names explicitly exported by `src.api` and
`src.api.contracts`. The API plugin operation performs discovery and returns
metadata descriptors; it does not activate code. Existing plugin lifecycle
interfaces remain a separate published extension boundary. Plugins must not
import `src.application` or rely on engine values retained during an
operation.

## Exclusions

The API does not implement HTTP, REST, GraphQL, authentication, database
persistence, remote repositories, cloud services, background execution,
curriculum rules, scheduling decisions, rendering decisions, generation
behavior, terminal output, or CLI parsing.
