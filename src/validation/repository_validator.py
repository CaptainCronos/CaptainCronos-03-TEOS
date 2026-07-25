"""Repository-wide validation orchestration before object construction."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping
from uuid import UUID

from src.models.lifecycle import ReferenceObjectType
from src.repository.exceptions import SchemaValidationError

from .reference_validator import DocumentInput, ReferenceValidator
from .validator import Validator


IDENTITY_FIELDS: dict[ReferenceObjectType, tuple[str, str]] = {
    ReferenceObjectType.STANDARD: ("standard_id", "version"),
    ReferenceObjectType.COMPETENCY: ("competency_id", "version"),
    ReferenceObjectType.INSTRUCTIONAL_UNIT: ("instructional_unit_id", "version"),
    ReferenceObjectType.SESSION: ("session_id", "version"),
    ReferenceObjectType.COURSE: ("course_id", "version"),
    ReferenceObjectType.INSTITUTION_PROFILE: ("institution_profile_id", "version"),
    ReferenceObjectType.ACADEMIC_CALENDAR: ("academic_calendar_id", "version"),
    ReferenceObjectType.RENDERED_ARTIFACT: ("artifact_id", "artifact_version"),
}


SCHEMA_OBJECT_TYPES = {
    "standard.schema.json": ReferenceObjectType.STANDARD,
    "competency.schema.json": ReferenceObjectType.COMPETENCY,
    "instructional-unit.schema.json": ReferenceObjectType.INSTRUCTIONAL_UNIT,
    "session.schema.json": ReferenceObjectType.SESSION,
    "course.schema.json": ReferenceObjectType.COURSE,
    "institution-profile.schema.json": ReferenceObjectType.INSTITUTION_PROFILE,
    "academic-calendar.schema.json": ReferenceObjectType.ACADEMIC_CALENDAR,
    "rendered-artifact.schema.json": ReferenceObjectType.RENDERED_ARTIFACT,
}


RepositoryValidationInput = tuple[
    tuple[Path, Mapping[str, Any], str],
    ...,
]


class RepositoryValidator(Validator[RepositoryValidationInput]):
    """Apply cross-file identity, reference, and composition validation."""

    def __init__(self, reference_validator: ReferenceValidator | None = None) -> None:
        self.reference_validator = reference_validator or ReferenceValidator()

    def validate(self, value: RepositoryValidationInput) -> None:
        """Validate all schema-conforming documents as one repository."""
        self.reference_validator.validate(self.describe(value))

    @staticmethod
    def describe(value: RepositoryValidationInput) -> tuple[DocumentInput, ...]:
        """Extract typed identity descriptors from schema-valid documents."""
        described: list[DocumentInput] = []
        for source, document, schema_name in value:
            try:
                object_type = SCHEMA_OBJECT_TYPES[schema_name]
                identity_field, version_field = IDENTITY_FIELDS[object_type]
                identifier = UUID(document[identity_field])
                version = document[version_field]
            except (KeyError, TypeError, ValueError) as error:
                raise SchemaValidationError(
                    "could not extract validated TEOS identity", source=source
                ) from error
            described.append((source, document, object_type, identifier, version))
        return tuple(described)
