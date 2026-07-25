"""Validate TEOS JSON Schema contracts, examples, references, and type guards."""

from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator, FormatChecker, ValidationError
from referencing import Registry, Resource


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
SCHEMA_DIRECTORY = REPOSITORY_ROOT / "schemas"


def load_json_files() -> dict[Path, Any]:
    """Parse and return every maintained JSON file in the repository."""
    json_files = sorted(
        path
        for path in REPOSITORY_ROOT.rglob("*.json")
        if ".git" not in path.parts and "output" not in path.parts
    )
    return {
        path: json.loads(path.read_text(encoding="utf-8")) for path in json_files
    }


def load_schemas(parsed_json: dict[Path, Any]) -> dict[str, dict[str, Any]]:
    """Return schema documents keyed by their local relative identifiers."""
    return {
        path.name: document
        for path, document in parsed_json.items()
        if path.parent == SCHEMA_DIRECTORY and path.name.endswith(".schema.json")
    }


def decode_json_pointer(document: Any, fragment: str) -> Any:
    """Resolve a JSON Pointer fragment within a parsed schema document."""
    if fragment in ("", "#"):
        return document
    if not fragment.startswith("#/"):
        raise ValueError(f"unsupported local fragment: {fragment}")

    current = document
    for encoded_part in fragment[2:].split("/"):
        part = encoded_part.replace("~1", "/").replace("~0", "~")
        if isinstance(current, list):
            current = current[int(part)]
        else:
            current = current[part]
    return current


def iter_references(value: Any) -> list[str]:
    """Collect every `$ref` string in a JSON-compatible value."""
    references: list[str] = []
    if isinstance(value, dict):
        reference = value.get("$ref")
        if isinstance(reference, str):
            references.append(reference)
        for nested_value in value.values():
            references.extend(iter_references(nested_value))
    elif isinstance(value, list):
        for nested_value in value:
            references.extend(iter_references(nested_value))
    return references


def validate_local_references(schemas: dict[str, dict[str, Any]]) -> int:
    """Resolve every local schema reference and return the number checked."""
    checked = 0
    for schema_name, schema in schemas.items():
        for reference in iter_references(schema):
            if reference.startswith(("http://", "https://")):
                continue
            target_name, separator, fragment_text = reference.partition("#")
            target_schema = schemas[target_name or schema_name]
            fragment = f"#{fragment_text}" if separator else ""
            decode_json_pointer(target_schema, fragment)
            checked += 1
    return checked


def build_registry(schemas: dict[str, dict[str, Any]]) -> Registry:
    """Build a local registry for relative schema identifiers."""
    return Registry().with_resources(
        (schema_name, Resource.from_contents(schema))
        for schema_name, schema in schemas.items()
    )


def validate_examples(
    schemas: dict[str, dict[str, Any]], registry: Registry
) -> int:
    """Validate every embedded positive example and return the number checked."""
    checked = 0
    format_checker = FormatChecker()
    for schema_name, schema in schemas.items():
        validator = Draft202012Validator(
            schema, registry=registry, format_checker=format_checker
        )
        for example in schema.get("examples", []):
            validator.validate(example)
            checked += 1
    return checked


def wrong_type_cases(
    schemas: dict[str, dict[str, Any]]
) -> list[tuple[str, str, dict[str, Any]]]:
    """Build the required invalid examples using existing positive examples."""
    reference_id = "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa"

    session_with_course_competency = copy.deepcopy(
        schemas["session.schema.json"]["examples"][0]
    )
    session_with_course_competency["competency_references"][0][
        "object_type"
    ] = "course"

    session_with_competency_dependency = copy.deepcopy(
        schemas["session.schema.json"]["examples"][0]
    )
    session_with_competency_dependency["prerequisite_session_references"] = [
        {
            "session_reference": {
                "object_type": "competency",
                "identifier": reference_id,
                "version": "1.0.0",
            },
            "relationship": "before",
        }
    ]

    course_with_calendar_unit = copy.deepcopy(
        schemas["course.schema.json"]["examples"][0]
    )
    course_with_calendar_unit["instructional_unit_references"][0][
        "object_type"
    ] = "academic-calendar"

    profile_with_session_calendar = copy.deepcopy(
        schemas["institution-profile.schema.json"]["examples"][0]
    )
    profile_with_session_calendar["academic_calendar_references"][0][
        "object_type"
    ] = "session"

    return [
        (
            "Course reference in session.competency_references",
            "session.schema.json",
            session_with_course_competency,
        ),
        (
            "Competency reference in sessionDependency.session_reference",
            "session.schema.json",
            session_with_competency_dependency,
        ),
        (
            "Academic Calendar reference in course.instructional_unit_references",
            "course.schema.json",
            course_with_calendar_unit,
        ),
        (
            "Session reference in institution-profile.academic_calendar_references",
            "institution-profile.schema.json",
            profile_with_session_calendar,
        ),
    ]


def validate_negative_cases(
    schemas: dict[str, dict[str, Any]], registry: Registry
) -> list[str]:
    """Confirm every wrong-target-type case is rejected."""
    passed: list[str] = []
    format_checker = FormatChecker()
    for case_name, schema_name, instance in wrong_type_cases(schemas):
        validator = Draft202012Validator(
            schemas[schema_name],
            registry=registry,
            format_checker=format_checker,
        )
        try:
            validator.validate(instance)
        except ValidationError:
            passed.append(case_name)
        else:
            raise AssertionError(f"negative case was accepted: {case_name}")
    return passed


def main() -> None:
    """Run all schema-contract validation checks and print concise results."""
    parsed_json = load_json_files()
    schemas = load_schemas(parsed_json)
    registry = build_registry(schemas)

    for schema in schemas.values():
        Draft202012Validator.check_schema(schema)

    reference_count = validate_local_references(schemas)
    example_count = validate_examples(schemas, registry)
    negative_results = validate_negative_cases(schemas, registry)

    print(f"JSON parsing: PASS ({len(parsed_json)} files)")
    print(f"Draft 2020-12 metaschema: PASS ({len(schemas)} schemas)")
    print(f"Local $ref resolution: PASS ({reference_count} references)")
    print(f"Embedded examples: PASS ({example_count} examples)")
    print(f"Wrong-type negative cases: PASS ({len(negative_results)} cases)")
    for case_name in negative_results:
        print(f"  - {case_name}")


if __name__ == "__main__":
    main()
