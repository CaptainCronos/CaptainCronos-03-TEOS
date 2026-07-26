# 0010: Command Line Interface

- Status: Accepted
- Scope: Define the local user-facing orchestration boundary over the completed
  TEOS curriculum and document-generation pipeline.

> Integration update: architecture 0012 moves pipeline assembly into the
> Public Application API. The CLI responsibilities and terminal behavior in
> this record remain accepted; the CLI application now delegates equivalent
> operations to `TEOSApplication`.

## Architectural boundary

```text
Command arguments + configuration
    → CLI application → Public Application API
    → Repository loading and validation
    → Compilation
    → Scheduling
    → Rendering
    → Document generation
    → CLI output
```

The CLI coordinates existing public engine interfaces. It owns command
parsing, operational configuration, stage sequencing, progress, diagnostics,
logging, and process exit status. It does not own repository validation,
curriculum rules, reference resolution, compilation, scheduling, rendering,
generation, optimization, or persistence.

Every pipeline command executes the minimum ordered prefix needed for its
result. `validate` loads the repository, `compile` continues through
compilation, `schedule` continues through scheduling, `render` continues
through rendering, and `generate` and `build` continue through physical file
generation. A failed stage stops later stages and is reported with its stage
name and original cause.

## Command lifecycle

1. Parse command arguments without reading or changing a repository.
2. Load immutable configuration from defaults, an optional JSON file,
   environment variables, and explicit arguments, in increasing precedence.
3. Configure structured logging and progress reporting.
4. Dispatch one immutable command request.
5. Execute the required engine stages in fixed order.
6. Present a result or diagnostic and return a stable process exit status.

Informational commands (`info`, `version`, `doctor`, and `list`) do not execute
unneeded pipeline stages. `doctor` performs local read-only readiness checks.

## Configuration model

CLI configuration is an immutable value containing repository and output
locations, renderer and generator selections, institution profile and
academic calendar identities, logging level, verbosity, debug mode, timing,
and preserved extension values. Paths are operational locations; configuration
never becomes curriculum or calendar data.

Configuration precedence is:

```text
built-in defaults < configuration file < TEOS_* environment < CLI arguments
```

Unknown configuration-file keys are retained as immutable extension entries so
future versions can add options without changing the core value contract.
Unknown command-line options remain user-input errors.

Profile and calendar selection is explicit by UUID, with optional exact
versions. If an identity is omitted, the CLI may select the sole object of that
type; zero or multiple candidates require explicit input. This is operational
input selection, not scheduling.

## Rendering request

The rendering framework requires an immutable template and rendering context.
The default CLI application supplies a minimal schedule template and context
whose output format, filename, timestamp, and optional institution display
name are operational presentation inputs. Applications may inject another
template provider without changing pipeline orchestration. Renderers retain
all rendering rules and document generators retain all encoding and file
creation behavior.

## Logging and progress

Logging records have a level, event name, message, and ordered fields. The
default text sink emits one deterministic structured line per record. Verbose
and debug flags lower the logging threshold; optional timing adds elapsed
duration only to stage-completion records.

Progress is a separate user-facing event stream with `started`, `completed`,
and `failed` states for repository loading, validation, compilation,
scheduling, rendering, generation, and overall completion. Progress reporters
observe orchestration and never influence engine results.

## Failure model

```text
CliError
├── ConfigurationError
├── CommandError
├── PipelineError
├── OutputError
└── UserInputError
```

`PipelineError` records the failed stage and chains the original engine
exception. The CLI translates its own failures to stable nonzero exit statuses
and presents engine diagnostics without changing the engine exception
hierarchies.

## Extension points

- Register or inject additional command handlers at the application boundary.
- Inject repository, compiler, scheduler, renderer, generator, clock, and
  template providers for alternate local applications and tests.
- Add logging sinks and progress reporters through their small interfaces.
- Add configuration keys through immutable extension values before promoting
  them to typed fields.

Network services, publication, persistence, repository mutation, curriculum
mutation, optimization, and duplicated engine rules remain outside the CLI.
