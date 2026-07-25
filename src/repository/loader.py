"""Atomic JSON loading, validation, and immutable object construction."""

from __future__ import annotations

import json
import sys
import types
from dataclasses import fields, is_dataclass
from datetime import date, datetime, time
from decimal import Decimal
from enum import Enum
from pathlib import Path, PurePosixPath
from typing import Any, Mapping, Union, get_args, get_origin, get_type_hints
from uuid import UUID

from src.models import (
    AcademicCalendar,
    Competency,
    Course,
    InstitutionProfile,
    InstructionalUnit,
    RenderedArtifact,
    Session,
    Standard,
)
from src.models.base import TEOSObject
from src.models.metadata import ImmutableValue
from src.validation.repository_validator import RepositoryValidator
from src.validation.schema_validator import SchemaValidator, schema_name_for

from .exceptions import ConstructionError, RepositoryError, SchemaValidationError
from .registry import ObjectRegistry
from .repository import Repository


SCHEMA_MODEL_TYPES: Mapping[str, type[TEOSObject]] = {
    "standard.schema.json": Standard,
    "competency.schema.json": Competency,
    "instructional-unit.schema.json": InstructionalUnit,
    "session.schema.json": Session,
    "course.schema.json": Course,
    "institution-profile.schema.json": InstitutionProfile,
    "academic-calendar.schema.json": AcademicCalendar,
    "rendered-artifact.schema.json": RenderedArtifact,
}

_EXCLUDED_DIRECTORIES = frozenset(
    {".git", ".agents", ".codex", ".pytest_cache", "schemas", "output"}
)


def _freeze_json(value: Any) -> Any:
    if isinstance(value, Mapping):
        return tuple((key, _freeze_json(child)) for key, child in value.items())
    if isinstance(value, list):
        return tuple(_freeze_json(child) for child in value)
    return value


def _convert_union(value: Any, annotation: Any) -> Any:
    choices = get_args(annotation)
    if value is None and type(None) in choices:
        return None
    for choice in choices:
        if choice is type(None):
            continue
        if isinstance(choice, type) and isinstance(value, choice):
            return value
    errors: list[Exception] = []
    for choice in choices:
        if choice is type(None):
            continue
        try:
            return _convert(value, choice)
        except (TypeError, ValueError) as error:
            errors.append(error)
    if errors:
        raise TypeError(f"value does not match {annotation!r}") from errors[-1]
    return value


def _convert(value: Any, annotation: Any) -> Any:
    if annotation is Any:
        return _freeze_json(value)
    origin = get_origin(annotation)
    if origin in (Union, types.UnionType):
        return _convert_union(value, annotation)
    if origin is tuple:
        arguments = get_args(annotation)
        item_type = arguments[0] if arguments else Any
        if isinstance(value, Mapping):
            return tuple(
                (str(key), _freeze_json(child)) for key, child in value.items()
            )
        if len(arguments) > 1 and arguments[-1] is not Ellipsis:
            return tuple(
                _convert(child, child_type)
                for child, child_type in zip(value, arguments, strict=True)
            )
        return tuple(_convert(child, item_type) for child in value)
    if isinstance(annotation, type) and issubclass(annotation, Enum):
        return annotation(value)
    if annotation is UUID:
        return UUID(value)
    if annotation is datetime:
        return datetime.fromisoformat(value)
    if annotation is date:
        return date.fromisoformat(value)
    if annotation is time:
        return time.fromisoformat(value)
    if annotation is PurePosixPath:
        return PurePosixPath(value)
    if annotation is Decimal:
        return Decimal(str(value))
    if isinstance(annotation, type) and is_dataclass(annotation):
        if not isinstance(value, Mapping):
            raise TypeError(f"{annotation.__name__} requires an object")
        module_globals = dict(vars(sys.modules[annotation.__module__]))
        module_globals.setdefault("ImmutableValue", ImmutableValue)
        hints = get_type_hints(annotation, globalns=module_globals)
        keywords = {
            field.name: _convert(value[field.name], hints[field.name])
            for field in fields(annotation)
            if field.init and field.name in value
        }
        return annotation(**keywords)
    if annotation in (str, int, float, bool):
        if not isinstance(value, annotation):
            raise TypeError(f"expected {annotation.__name__}")
        return value
    return value


def construct_object(
    document: Mapping[str, Any],
    schema_name: str,
    *,
    source: Path | None = None,
) -> TEOSObject:
    """Construct one immutable domain object from schema-valid JSON."""
    try:
        model_type = SCHEMA_MODEL_TYPES[schema_name]
        return _convert(document, model_type)
    except (KeyError, TypeError, ValueError) as error:
        raise ConstructionError(
            f"could not construct {schema_name}: {error}",
            source=source,
            details={"schema": schema_name, "cause": type(error).__name__},
        ) from error


class RepositoryLoader:
    """Execute the repository loading pipeline atomically."""

    def __init__(
        self,
        *,
        schema_validator: SchemaValidator | None = None,
        repository_validator: RepositoryValidator | None = None,
    ) -> None:
        self.schema_validator = schema_validator or SchemaValidator()
        self.repository_validator = repository_validator or RepositoryValidator()

    def load(self, location: str | Path) -> Repository:
        """Load a file or directory, aborting on the first validation failure."""
        sources = self.locate(location)
        documents: list[tuple[Path, Mapping[str, Any], str]] = []
        for source in sources:
            document = self._read(source)
            try:
                schema_name = schema_name_for(document)
            except SchemaValidationError as error:
                raise SchemaValidationError(
                    error.message,
                    source=source,
                    path=error.path,
                    details=error.details,
                ) from error
            self.schema_validator.validate(
                document, schema_name=schema_name, source=source
            )
            documents.append((source, document, schema_name))

        validated_documents = tuple(documents)
        self.repository_validator.validate(validated_documents)
        objects = tuple(
            construct_object(document, schema_name, source=source)
            for source, document, schema_name in validated_documents
        )
        registry = ObjectRegistry(objects)
        return Repository(registry, sources)

    @staticmethod
    def locate(location: str | Path) -> tuple[Path, ...]:
        """Locate candidate JSON object documents in deterministic order."""
        root = Path(location)
        if not root.exists():
            raise RepositoryError("repository location does not exist", source=root)
        if root.is_file():
            if root.suffix.lower() != ".json":
                raise RepositoryError("repository document must be JSON", source=root)
            return (root.resolve(),)
        candidates = (
            path
            for path in root.rglob("*.json")
            if not any(part in _EXCLUDED_DIRECTORIES for part in path.relative_to(root).parts)
        )
        return tuple(sorted(path.resolve() for path in candidates))

    @staticmethod
    def _read(source: Path) -> Mapping[str, Any]:
        try:
            with source.open(encoding="utf-8") as stream:
                value = json.load(stream)
        except (OSError, UnicodeError, json.JSONDecodeError) as error:
            raise SchemaValidationError(
                f"could not parse JSON: {error}", source=source
            ) from error
        if not isinstance(value, Mapping):
            raise SchemaValidationError(
                "a repository document must contain a JSON object", source=source
            )
        return value


def load_repository(location: str | Path) -> Repository:
    """Load one repository using the default authoritative validators."""
    return RepositoryLoader().load(location)
