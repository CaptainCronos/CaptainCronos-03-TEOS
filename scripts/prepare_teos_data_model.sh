#!/usr/bin/env bash
set -euo pipefail

REPO_NAME="CaptainCronos-03-TEOS"

die() {
    printf 'ERROR: %s\n' "$*" >&2
    exit 1
}

info() {
    printf '\n==> %s\n' "$*"
}

create_file_if_missing() {
    local path="$1"
    local body="$2"

    if [[ -e "$path" ]]; then
        printf 'KEEP   %s\n' "$path"
        return 0
    fi

    mkdir -p "$(dirname "$path")"
    printf '%s\n' "$body" > "$path"
    printf 'CREATE %s\n' "$path"
}

[[ -d .git ]] || die "Run this script from the repository root."
[[ "$(basename "$PWD")" == "$REPO_NAME" ]] || die "Expected repository directory: $REPO_NAME"

info "Creating TEOS conceptual model structure"

mkdir -p models schemas/courses docs/architecture/diagrams

create_file_if_missing "models/README.md" "# TEOS Conceptual Models

This directory defines TEOS domain concepts independently of programming language or serialization format.

Conceptual models explain what each object means, what it owns, and how it relates to other objects.

Machine-validation formats belong in \`schemas/\`.
Implementation code belongs in \`src/\`."

create_file_if_missing "models/standard.md" "# Standard

## Purpose

Represents an externally or internally defined body of technical-education requirements.

## Initial responsibilities

- Identify the issuing organization.
- Preserve the official identifier and version.
- Group related competency requirements.
- Retain source and revision metadata.
- Remain independent of calendars and document templates.

## Relationships

A Standard defines or references one or more Competencies."

create_file_if_missing "models/competency.md" "# Competency

## Purpose

Represents an observable technical capability that a learner must demonstrate.

## Initial responsibilities

- State the required capability using measurable language.
- Reference the governing Standard when applicable.
- Define prerequisite competencies.
- Define evidence and assessment criteria.
- Support instructional and assessment tagging.

## Relationships

Competencies are grouped into Instructional Units and may appear in multiple Courses."

create_file_if_missing "models/instructional-unit.md" "# Instructional Unit

## Purpose

Groups related competencies into a coherent teachable unit.

## Initial responsibilities

- Define learning outcomes.
- Identify included competencies.
- Define prerequisite knowledge.
- Identify required tools, equipment, resources, and safety controls.
- Define the Session sequence needed for delivery.
- Remain independent of dates and institutional meeting patterns.

## Relationships

An Instructional Unit contains one or more Sessions."

create_file_if_missing "models/session.md" "# Session

## Purpose

Represents the smallest schedulable instructional event in TEOS.

## Initial responsibilities

- Define instructional purpose and delivery type.
- Define estimated duration.
- Reference competencies and learning outcomes.
- Identify required resources and safety controls.
- Define dependencies on earlier Sessions.
- Provide source data for rendered artifacts.

## Canonical rule

Sessions are the scheduling primitive. Weeks and days are calendar aliases, not curriculum objects."

create_file_if_missing "models/course.md" "# Course

## Purpose

Organizes Instructional Units into a complete curriculum offering.

## Initial responsibilities

- Define course identity and description.
- Reference governing Standards.
- Sequence Instructional Units.
- Define completion requirements.
- Define expected instructional hours without embedding dates.
- Remain independent of any Institution Profile.

## Relationships

A Course contains ordered Instructional Units, which contain Sessions."

create_file_if_missing "schemas/courses/README.md" "# Course Schemas

Machine-readable validation schemas for Course data belong here.

No schema format has been selected yet. Do not add JSON Schema, YAML Schema, or implementation-specific validation models until the conceptual Course model is approved."

for schema_dir in standards competencies instructional_units sessions institutions calendars; do
    title="${schema_dir//_/ }"
    create_file_if_missing "schemas/${schema_dir}/README.md" "# ${title^} Schemas

Machine-readable validation schemas for this TEOS object belong here.

The conceptual definition must be approved before an implementation schema is added."
done

create_file_if_missing "docs/architecture/diagrams/README.md" "# Architecture Diagrams

Store source-controlled TEOS architecture diagrams here.

Prefer text-based formats such as Mermaid when practical so changes remain reviewable in Git."

info "TEOS data-model scaffold complete"

if command -v lstree >/dev/null 2>&1; then
    lstree .
elif command -v tree >/dev/null 2>&1; then
    tree -a -I '.git'
else
    find . -path './.git' -prune -o -print | sort
fi

cat <<'EOF'

Next review:
  1. Review models/*.md.
  2. Revise object responsibilities and relationships.
  3. Do not implement schemas or engine code until the conceptual models are approved.

Suggested commit:
  git add models schemas docs/architecture/diagrams
  git commit -m "Add initial TEOS conceptual data models"
EOF
