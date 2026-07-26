# Technical Education Operating System (TEOS)

TEOS is a session-based curriculum orchestration application. It compiles
standards-aligned curriculum, validates source contracts and relationships,
applies institution and academic-calendar context, schedules instructional
Sessions, and renders or generates reproducible documents.

Curriculum remains the single source of truth. Institution profiles own local
scheduling and presentation settings, academic calendars own date
availability, and generated documents are replaceable artifacts.

## Architecture overview

TEOS processes maintained data through a one-way application pipeline:

```text
repository loading → validation → compilation → scheduling → rendering → generation
```

The implementation preserves these boundaries:

- Standards define requirements and Competencies define observable outcomes.
- Instructional Units organize Competencies and contain ordered Sessions.
- Sessions are the scheduling primitive; Weeks and Days are derived aliases.
- Institution Profiles provide local policies, branding, templates, and
  scheduling conventions without changing curriculum.
- Academic Calendars provide institutional availability without containing
  curriculum.
- Renderers produce immutable artifact descriptions; generators produce
  physical files beneath `output/`.

The supported in-process application boundary is `src.api`. The `src.cli`
package adapts that API for terminal use. Engine packages remain independent
of curriculum, institution, and calendar data.

## Major components

- Repository loading and JSON Schema validation
- Immutable domain models and cross-object validation
- Curriculum dependency graph compilation
- Session scheduling against institution and calendar constraints
- Markdown, HTML, DOCX, and PDF rendering and generation
- Institution profiles, localization, themes, and branding
- Import and export adapters
- Plugin discovery and lifecycle management
- Public application API and command-line interface

## Repository layout

| Path | Purpose |
| --- | --- |
| `src/` | Application, engine, API, and CLI Python packages |
| `schemas/` | Authoritative machine-readable data contracts |
| `models/` | Serialization-independent conceptual models |
| `specifications/` | Canonical object and interoperability specifications |
| `institutions/` | Institution-owned profiles and assets |
| `calendars/` | Institution-owned academic calendars |
| `templates/` | Source-controlled artifact templates |
| `examples/` | Example plugins, themes, and localization resources |
| `docs/architecture/` | Architecture records, ADRs, and diagrams |
| `docs/development/` | Contributor setup, conventions, testing, and releases |
| `tests/` | Automated application and engine tests |
| `scripts/` | Repository maintenance and contract-validation utilities |
| `output/` | Ignored generated artifacts |

Curriculum data belongs only in a top-level `curriculum/` directory when a
curriculum repository is added. Generated artifacts must not be committed.

## Installation

TEOS requires Python 3.11 or newer. From the repository root:

```bash
python -m pip install .
```

For editable development:

```bash
python -m pip install -e .
python -m pip install -e ".[dev]"
```

The development extra installs the test, coverage, build, and lint tools used
by the documented workflow.

## CLI

Installation exposes the `teos` command:

```bash
teos --help
teos version
teos doctor
```

Pipeline commands execute only through their named stage:

```bash
teos validate
teos compile
teos schedule
teos --renderer markdown render
teos --renderer markdown --generator markdown generate
teos build
```

Use `teos info` to inspect effective settings and `teos list` to inspect
registered renderers and generators. Run `teos --help` for global options,
including repository, institution, calendar, output, logging, and JSON-output
configuration. See [the CLI guide](docs/cli.md) for configuration precedence,
diagnostics, and exit statuses.

## Development workflow

1. Create and activate a virtual environment.
2. Install `python -m pip install -e ".[dev]"`.
3. Keep architecture, curriculum, institution, calendar, and generated data
   within their documented boundaries.
4. Make a small, reviewable change and add or update tests.
5. Run `pytest`, `python scripts/validate_schemas.py`, and `ruff check .`.
6. Review `git diff` and confirm generated files remain under `output/`.

No new architectural capability should be implemented without an approved
architecture update. See the
[development documentation](docs/development/README.md) for the complete
workflow.

## Testing

Run the complete suite:

```bash
pytest
```

Run coverage when changing executable code:

```bash
pytest --cov=src --cov-report=term-missing
```

Validate the JSON Schema contracts separately:

```bash
python scripts/validate_schemas.py
```

## Architecture documents

The accepted system design is recorded in
[`docs/architecture/`](docs/architecture/). Numbered records describe the
system and its implemented layers; ADRs in
[`docs/architecture/adr/`](docs/architecture/adr/) capture durable decisions.
Start with the [guiding principles](docs/architecture/0000-guiding-principles.md)
and [system overview](docs/architecture/0001-system-overview.md).

The architecture is feature-complete. Current work focuses on application
quality, packaging, testing, documentation, and release readiness rather than
adding architectural layers.
