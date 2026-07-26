# Development Setup

## Requirements

- Python 3.11 or newer
- Git
- A virtual environment tool provided by Python or an equivalent environment
  manager

## Editable installation

From the repository root:

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
```

On Windows, activate the environment with `.venv\Scripts\activate`.

The editable install exposes `teos` while keeping imports connected to the
working tree. The `dev` extra installs pytest, coverage support, Ruff, and the
standard Python build frontend.

## Readiness checks

```bash
teos version
teos doctor
pytest
python scripts/validate_schemas.py
ruff check .
```

`teos doctor` expects to run against a TEOS repository. By default it checks
the current directory and its `schemas/` contracts.

Application output belongs beneath `output/`. Local environments, caches,
coverage reports, wheels, and editable-install metadata are ignored by Git.
