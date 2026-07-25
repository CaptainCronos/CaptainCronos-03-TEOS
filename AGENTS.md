# Repository Instructions

TEOS follows an architecture-first development process.

## Working rules

- Do not implement features until the relevant architecture is documented and
  approved.
- Keep changes small and reviewable.
- Favor readability over cleverness.
- Document every public module.
- Preserve a strict separation between engine code and curriculum data.
- Do not add placeholder code that cannot evolve into production code.
- Treat curriculum as the single source of truth.
- Treat Sessions as the scheduling primitive; Weeks and Days are aliases.
- Keep institutional presentation and scheduling outside curriculum.
- Keep curriculum out of academic calendars.
- Treat generated documents and packages as rendered artifacts.

## Directory boundaries

- Place engine code under `src/`.
- Place data contracts under `schemas/`.
- Place curriculum, institution, and calendar data only in their corresponding
  top-level directories.
- Place generated artifacts under `output/`; do not commit them.
