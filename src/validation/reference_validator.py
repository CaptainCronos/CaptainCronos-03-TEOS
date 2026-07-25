"""Cross-document validation for exact typed TEOS references."""

from __future__ import annotations

from collections import defaultdict
from pathlib import Path
from typing import Any, Iterable, Mapping
from uuid import UUID

from src.models.lifecycle import ReferenceObjectType
from src.repository.exceptions import (
    CircularReferenceError,
    DuplicateIdentifierError,
    DuplicateVersionError,
    MissingReferenceError,
    ReferenceValidationError,
    VersionMismatchError,
    reference_details,
)

from .validator import Validator


IdentityKey = tuple[UUID, str, ReferenceObjectType]
DocumentInput = tuple[Path, Mapping[str, Any], ReferenceObjectType, UUID, str]

LOADABLE_REFERENCE_TYPES = frozenset(
    {
        ReferenceObjectType.STANDARD,
        ReferenceObjectType.COMPETENCY,
        ReferenceObjectType.INSTRUCTIONAL_UNIT,
        ReferenceObjectType.SESSION,
        ReferenceObjectType.COURSE,
        ReferenceObjectType.INSTITUTION_PROFILE,
        ReferenceObjectType.ACADEMIC_CALENDAR,
        ReferenceObjectType.RENDERED_ARTIFACT,
    }
)


def _references(
    value: Any, path: tuple[str | int, ...] = ()
) -> Iterable[tuple[tuple[str | int, ...], Mapping[str, Any]]]:
    if isinstance(value, Mapping):
        if {"object_type", "identifier", "version"} <= value.keys():
            yield path, value
        for key, child in value.items():
            yield from _references(child, (*path, key))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            yield from _references(child, (*path, index))


class ReferenceValidator(Validator[tuple[DocumentInput, ...]]):
    """Validate identities, versions, types, and resolvable cross-file links."""

    def validate(self, value: tuple[DocumentInput, ...]) -> None:
        """Validate repository-wide exact reference integrity."""
        by_identity: dict[UUID, set[ReferenceObjectType]] = defaultdict(set)
        by_key: dict[IdentityKey, Path] = {}
        by_identity_versions: dict[UUID, set[str]] = defaultdict(set)

        for source, _, object_type, identifier, version in value:
            by_identity[identifier].add(object_type)
            if len(by_identity[identifier]) > 1:
                raise DuplicateIdentifierError(
                    f"UUID {identifier} is used by multiple object types",
                    source=source,
                    details={"identifier": str(identifier)},
                )
            key = (identifier, version, object_type)
            if key in by_key:
                raise DuplicateVersionError(
                    f"duplicate version {version} for UUID {identifier}",
                    source=source,
                    details={
                        "identifier": str(identifier),
                        "version": version,
                        "first_source": str(by_key[key]),
                    },
                )
            by_key[key] = source
            by_identity_versions[identifier].add(version)

        for source, document, _, _, _ in value:
            for path, raw_reference in _references(document):
                try:
                    target_type = ReferenceObjectType(raw_reference["object_type"])
                    identifier = UUID(raw_reference["identifier"])
                    version = raw_reference["version"]
                except (ValueError, TypeError) as error:
                    raise ReferenceValidationError(
                        "reference envelope contains invalid typed identity data",
                        source=source,
                        path=path,
                    ) from error
                if target_type not in LOADABLE_REFERENCE_TYPES:
                    continue
                details = reference_details(identifier, version, target_type.value)
                if identifier not in by_identity:
                    raise MissingReferenceError(
                        f"missing referenced {target_type.value} "
                        f"{identifier}@{version}",
                        source=source,
                        path=path,
                        details=details,
                    )
                actual_type = next(iter(by_identity[identifier]))
                if actual_type is not target_type:
                    raise ReferenceValidationError(
                        f"reference declares {target_type.value}, but UUID "
                        f"{identifier} is {actual_type.value}",
                        source=source,
                        path=path,
                        details={**details, "actual_object_type": actual_type.value},
                    )
                if version not in by_identity_versions[identifier]:
                    raise VersionMismatchError(
                        f"no version {version} exists for UUID {identifier}",
                        source=source,
                        path=path,
                        details=details,
                    )

        self._validate_profile_composition(value)

    @staticmethod
    def _validate_profile_composition(value: tuple[DocumentInput, ...]) -> None:
        graph: dict[IdentityKey, set[IdentityKey]] = defaultdict(set)
        sources: dict[IdentityKey, Path] = {}
        for source, document, object_type, identifier, version in value:
            if object_type is not ReferenceObjectType.INSTITUTION_PROFILE:
                continue
            key = (identifier, version, object_type)
            sources[key] = source
            composition = document.get("composition")
            if not isinstance(composition, Mapping):
                continue
            for reference in composition.get("profile_references", []):
                graph[key].add(
                    (
                        UUID(reference["identifier"]),
                        reference["version"],
                        ReferenceObjectType.INSTITUTION_PROFILE,
                    )
                )

        visiting: set[IdentityKey] = set()
        visited: set[IdentityKey] = set()

        def visit(node: IdentityKey) -> None:
            if node in visiting:
                raise CircularReferenceError(
                    f"circular Institution Profile composition at "
                    f"{node[0]}@{node[1]}",
                    source=sources.get(node),
                    details={"identifier": str(node[0]), "version": node[1]},
                )
            if node in visited:
                return
            visiting.add(node)
            for child in graph.get(node, ()):
                visit(child)
            visiting.remove(node)
            visited.add(node)

        for node in graph:
            visit(node)
