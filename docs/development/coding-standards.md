# Coding Standards

TEOS supports Python 3.11 and newer. Prefer direct, readable code with explicit
types at public boundaries. Preserve immutable domain values and do not
silently rewrite authoritative source data.

## Python

- Document every public module, class, function, and method.
- Use four spaces and an 88-character line length.
- Add `from __future__ import annotations` where deferred annotations improve
  clarity or avoid import coupling.
- Use specific exceptions and retain useful causes.
- Keep CLI presentation separate from application services and engine rules.
- Keep filesystem writes in generation and output boundaries.
- Avoid import-time side effects and dependency cycles.

Ruff provides fast static correctness checks:

```bash
ruff check .
```

Formatting should follow the repository `.editorconfig`. Mechanical formatting
must not obscure unrelated behavioral changes.

## Contracts and data

Schema changes must remain derived from approved specifications and
architecture. Domain model changes require explicit architecture review.
Tests should exercise public outcomes and invariants rather than private
implementation details where practical.

Do not add placeholders that cannot mature into production code.
