# Public Application API

The supported in-process TEOS boundary is `src.api`. It coordinates the
existing repository, validation, compilation, scheduling, rendering,
generation, and plugin-discovery layers without publishing their concrete
implementations.

## Basic usage

```python
from src.api import BuildRequest, TEOSApplication

application = TEOSApplication()
response = application.build(
    BuildRequest(
        repository_path="curriculum/",
        institution_profile_id="00000000-0000-0000-0000-000000000001",
        academic_calendar_id="00000000-0000-0000-0000-000000000002",
        renderer="markdown",
        generator="markdown",
        output_directory="output/",
    )
)

if response.success:
    for generated_file in response.generated_files:
        print(generated_file.path)
else:
    for diagnostic in response.diagnostics:
        print(diagnostic.code, diagnostic.message)
```

Facade operations are synchronous:

- `validate_repository(ValidateRequest(...))`
- `compile_repository(CompileRequest(...))`
- `schedule_curriculum(ScheduleRequest(...))`
- `render_schedule(RenderRequest(...))`
- `generate_documents(GenerateRequest(...))`
- `build(BuildRequest(...))`
- `inspect_repository(InspectRequest(...))`
- `list_plugins(ListPluginsRequest(...))`
- `doctor(DoctorRequest(...))`

Each pipeline operation executes only the minimum prefix required for its
result. Stages are always ordered `load`, `validate`, `compile`, `schedule`,
`render`, and `generate`.

## Requests, responses, and results

Requests are frozen values containing only operation input. Paths are
normalized to `Path`, names are normalized to lowercase, and plugin
configuration is retained as ordered immutable entries.

Every response exposes:

- `operation` and `status`;
- `success`;
- an optional stable public `result`;
- ordered `diagnostics`, plus `warnings` and `errors` views;
- optional `elapsed_seconds` when request timing is enabled; and
- repository and document source information.

Pipeline results expose ordered stage summaries, rendered artifact
descriptors, and generated file descriptors. They deliberately do not expose
repository registries, compiled objects, scheduled objects, renderer or
generator instances, templates, or application contexts.

## Diagnostics and failures

Diagnostics contain a namespaced code, severity, message, stage, and optional
source, object identifier, and field path. Severities are `information`,
`warning`, `error`, and `fatal`.

Expected engine failures become immutable failure responses. Source and field
locations are retained where an engine exception provides them. Unexpected
exceptions are translated to application execution diagnostics without
returning a traceback. Exceptions in `src.api.exceptions` are reserved for
explicit application-boundary misuse and service implementations.

## Service injection

Applications may implement the runtime-checkable protocols in
`src.api.contracts` and provide a complete immutable `ApplicationServices`
bundle to `TEOSApplication`. Services remain thin coordinators: business rules
belong to the completed engine layers.

The public service contracts use opaque intermediate values intentionally.
An implementation may pass those values between adjacent services, but
applications and plugins must not rely on their concrete types.

## Versions and compatibility

`src.api` exports `API_VERSION`, `ENGINE_VERSION`, and
`SUPPORTED_CONTRACT_VERSION`. A request may set `contract_version`; a mismatch
returns a configuration-failure response before any pipeline service runs.
Only contract version `1.0` is currently supported.

Compatible additions may be made within API major version 1. Removing or
changing published fields, statuses, diagnostic semantics, operation
semantics, or service protocols requires a new API major version.

## CLI and plugins

The CLI delegates equivalent pipeline and readiness operations to
`TEOSApplication`. It still owns argument parsing, configuration precedence,
progress and log presentation, terminal formatting, and exit codes.

Plugins may import documented exports from `src.api`,
`src.api.contracts`, and the existing `src.plugins` extension interfaces.
They must not import `src.application`; that package is the private facade
implementation. Plugin listing performs metadata discovery only and does not
import or activate plugin code.

HTTP endpoints, REST, GraphQL, authentication, persistence, remote
repositories, and cloud services are outside this API.

