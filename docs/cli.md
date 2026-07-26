# TEOS Command-Line Interface

The TEOS CLI is the local user-facing coordinator for the completed engine
pipeline. Its accepted boundary is documented in
[`architecture/0010-command-line-interface.md`](architecture/0010-command-line-interface.md).
It invokes existing components and contains no curriculum, validation,
compilation, scheduling, rendering, or generation rules.

## User workflow

Run the CLI from the repository root:

```bash
python -m src.cli.main --help
python -m src.cli.main validate
python -m src.cli.main compile
python -m src.cli.main schedule
python -m src.cli.main --renderer markdown render
python -m src.cli.main --renderer markdown --generator markdown generate
python -m src.cli.main build
```

`build` and `generate` execute the complete pipeline. Generated deliverables
are written beneath `output/` by default. The two selected formats must match
because a document generator consumes the immutable descriptor produced by
the corresponding renderer.

Commands execute these pipeline prefixes:

| Command | Last stage |
| --- | --- |
| `validate` | repository validation |
| `compile` | curriculum compilation |
| `schedule` | institutional scheduling |
| `render` | immutable artifact rendering |
| `generate` | physical document generation |
| `build` | physical document generation |

`info` displays effective operational settings. `version` displays the TEOS
version. `doctor` performs read-only local readiness checks. `list` reports
registered renderers and generators.

## Configuration

Use a JSON object for repeatable operational settings:

```json
{
  "repository": ".",
  "output_directory": "output",
  "renderer": "markdown",
  "generator": "markdown",
  "institution_profile": "00000000-0000-0000-0000-000000000000",
  "institution_profile_version": "1.0.0",
  "academic_calendar": "00000000-0000-0000-0000-000000000000",
  "academic_calendar_version": "1.0.0",
  "logging_level": "info",
  "timing": false
}
```

Load it with `--config path/to/teos.json`. Values may also be supplied through
`TEOS_REPOSITORY`, `TEOS_OUTPUT_DIRECTORY`, `TEOS_RENDERER`,
`TEOS_GENERATOR`, `TEOS_INSTITUTION_PROFILE`,
`TEOS_INSTITUTION_PROFILE_VERSION`, `TEOS_ACADEMIC_CALENDAR`,
`TEOS_ACADEMIC_CALENDAR_VERSION`, `TEOS_LOG_LEVEL`, `TEOS_VERBOSE`,
`TEOS_DEBUG`, `TEOS_TIMING`, `TEOS_PROGRESS`, and `TEOS_JSON`.

Precedence is defaults, configuration file, environment, then explicit CLI
arguments. Unknown file keys remain immutable extension values for future
configuration versions.

When the loaded repository contains exactly one institution profile and one
academic calendar, the CLI selects them automatically. Repositories with
multiple candidates must provide explicit UUIDs and may provide exact
versions.

## Logging and progress

Structured logging is written to standard error as stable key-value records.
`--log-level` sets the threshold, `--verbose` exposes informational records
when a stricter level was configured, and `--debug` enables debug records.
`--timing` adds elapsed seconds to successful stage records.

Progress is a separate standard-error stream of stage state changes. Use
`--no-progress` for scripts. `--json` makes command results and failure
diagnostics machine-readable; progress and logs remain on standard error.

## Failures and exit status

Configuration and input syntax failures return status 2, command failures
return 3, engine pipeline failures return 4, and CLI output failures return 5.
Pipeline diagnostics name the failed stage and preserve the original engine
exception as their cause.

## Extension points

`PipelineServices` accepts alternate implementations of each existing engine
interface for embedding and testing. `CliContext` accepts a clock, logger,
progress reporter, and output writer. Renderer and generator registries remain
the authority for supported formats; the CLI does not duplicate their work.
