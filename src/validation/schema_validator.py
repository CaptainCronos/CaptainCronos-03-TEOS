"""Draft 2020-12 validation using the approved local TEOS schemas."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping

from jsonschema import Draft202012Validator, FormatChecker
from referencing import Registry, Resource

from src.repository.exceptions import SchemaValidationError

from .validator import Validator


class SchemaValidator(Validator[Mapping[str, Any]]):
    """Validate raw objects without duplicating schema constraints in Python."""

    def __init__(self, schema_directory: Path | None = None) -> None:
        self.schema_directory = (
            schema_directory
            if schema_directory is not None
            else Path(__file__).resolve().parents[2] / "schemas"
        )
        self._schemas: dict[str, Mapping[str, Any]] = {}
        resources: list[tuple[str, Resource[Any]]] = []
        for path in sorted(self.schema_directory.glob("*.schema.json")):
            with path.open(encoding="utf-8") as stream:
                schema = json.load(stream)
            Draft202012Validator.check_schema(schema)
            self._schemas[path.name] = schema
            resources.append((schema["$id"], Resource.from_contents(schema)))
        self._registry = Registry().with_resources(resources)

    def validate(
        self,
        value: Mapping[str, Any],
        schema_name: str | None = None,
        *,
        source: Path | None = None,
    ) -> None:
        """Validate one document against its authoritative object schema."""
        if schema_name is None:
            schema_name = schema_name_for(value)
        try:
            schema = self._schemas[schema_name]
        except KeyError as error:
            raise SchemaValidationError(
                f"approved schema {schema_name!r} is unavailable", source=source
            ) from error
        validator = Draft202012Validator(
            schema, registry=self._registry, format_checker=FormatChecker()
        )
        errors = sorted(validator.iter_errors(value), key=lambda item: list(item.path))
        if errors:
            error = errors[0]
            raise SchemaValidationError(
                error.message,
                source=source,
                path=tuple(error.absolute_path),
                details={
                    "schema": schema_name,
                    "validator": str(error.validator),
                    "error_count": len(errors),
                },
            )


IDENTITY_SCHEMA_NAMES = {
    "standard_id": "standard.schema.json",
    "competency_id": "competency.schema.json",
    "instructional_unit_id": "instructional-unit.schema.json",
    "session_id": "session.schema.json",
    "course_id": "course.schema.json",
    "institution_profile_id": "institution-profile.schema.json",
    "academic_calendar_id": "academic-calendar.schema.json",
    "artifact_id": "rendered-artifact.schema.json",
}


def schema_name_for(value: Mapping[str, Any]) -> str:
    """Infer the one approved schema from a document's identity field."""
    matches = [name for field, name in IDENTITY_SCHEMA_NAMES.items() if field in value]
    if len(matches) != 1:
        raise SchemaValidationError(
            "document must contain exactly one recognized TEOS identity field"
        )
    return matches[0]
