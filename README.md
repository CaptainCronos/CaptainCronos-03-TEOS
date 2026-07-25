# Technical Education Operating System (TEOS)

A session-based curriculum orchestration platform that separates instructional
content from calendars, institutions, and document generation.

TEOS is currently architecture-first. The initial architecture records live in
[`docs/architecture/`](docs/architecture/), and implementation will begin only
after those boundaries are documented and approved.

## Core model

- Curriculum is the single source of truth.
- Standards define competencies.
- Competencies become Instructional Units.
- Instructional Units are delivered through Sessions.
- Sessions are the scheduling primitive.
- Weeks and Days are scheduling aliases, not curriculum objects.
- Institution Profiles own presentation and scheduling, not curriculum.
- Academic Calendars never contain curriculum.
- Lesson plans, guides, assessments, LMS packages, and reports are rendered
  artifacts.

## Repository layout

- `docs/architecture/` — architecture decision and design records
- `src/` — future compiler, scheduler, renderer, and validator engine code
- `schemas/` — future contracts for TEOS data
- `curriculum/` — curriculum source data
- `institutions/` — institution profiles
- `calendars/` — academic calendar data
- `templates/` — artifact templates
- `examples/` — example projects and data
- `tests/` — automated tests
- `scripts/` — development and maintenance scripts
- `output/` — generated artifacts

## Project status

Version 0.1.0 establishes the repository scaffold. No engine or curriculum
logic has been implemented.
