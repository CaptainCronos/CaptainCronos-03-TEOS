# Repository Conventions

TEOS uses strict ownership boundaries:

- Python application and engine code belongs under `src/`.
- Machine-readable data contracts belong under `schemas/`.
- Curriculum, institution, and calendar data belongs only in its matching
  top-level directory.
- Templates describe presentation and must not become curriculum stores.
- Generated documents and packages belong under `output/` and are never
  source inputs.

Curriculum is the single source of truth for instructional meaning. Sessions
are the scheduling primitive; Week and Day values are derived aliases.
Institutional presentation and scheduling remain outside curriculum, and
academic calendars contain no curriculum.

Public modules require module docstrings. New public behavior requires tests
and documentation. Keep changes small enough to review as one coherent unit,
and do not combine cleanup with behavioral redesign.

Names use `snake_case` for Python modules, functions, and variables;
`PascalCase` for classes; and lowercase hyphenated names for documentation and
serialized resource filenames unless an established contract requires another
form.

Before requesting review, inspect:

```bash
git diff --check
git diff --stat
git status --short
```

Do not commit generated artifacts, secrets, local environments, caches, or
build products.
