# Testing Workflow

The default pytest configuration is stored in `pyproject.toml`. It discovers
tests beneath `tests/`, treats unknown configuration and markers as errors,
and makes the repository package importable from a checkout.

Run the full suite:

```bash
pytest
```

Run one module or test while iterating:

```bash
pytest tests/test_cli.py
pytest tests/test_cli.py::test_invalid_command_help_and_version_output
```

Measure executable-code coverage:

```bash
pytest --cov=src --cov-report=term-missing
```

Validate schema contracts and examples independently:

```bash
python scripts/validate_schemas.py
```

Changes to packaging or the command adapter also require an isolated
installation check:

```bash
python -m build
python -m venv /tmp/teos-validation
/tmp/teos-validation/bin/python -m pip install dist/*.whl
/tmp/teos-validation/bin/teos --help
/tmp/teos-validation/bin/teos version
```

Tests must not depend on files in `output/` from an earlier run. Use pytest
temporary directories for generated content and keep fixtures deterministic.
CI should run the full suite, schema validation, lint checks, and a wheel
installation smoke test.
