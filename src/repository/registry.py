"""Immutable indexes over loaded TEOS domain objects."""

from __future__ import annotations

import re
from collections import defaultdict
from enum import Enum
from types import MappingProxyType
from typing import Iterable, Mapping, TypeVar
from uuid import UUID

from src.models.base import TEOSObject
from src.models.lifecycle import ReferenceObjectType
from src.models.metadata import Organization

from .exceptions import DuplicateIdentifierError, DuplicateVersionError


DomainObject = TypeVar("DomainObject", bound=TEOSObject)

_CLASS_TO_OBJECT_TYPE: Mapping[type[TEOSObject], ReferenceObjectType]


def object_type_for(value: TEOSObject | type[TEOSObject]) -> ReferenceObjectType:
    """Return the reference vocabulary member for a supported domain type."""
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

    mapping: Mapping[type[TEOSObject], ReferenceObjectType] = {
        Standard: ReferenceObjectType.STANDARD,
        Competency: ReferenceObjectType.COMPETENCY,
        InstructionalUnit: ReferenceObjectType.INSTRUCTIONAL_UNIT,
        Session: ReferenceObjectType.SESSION,
        Course: ReferenceObjectType.COURSE,
        InstitutionProfile: ReferenceObjectType.INSTITUTION_PROFILE,
        AcademicCalendar: ReferenceObjectType.ACADEMIC_CALENDAR,
        RenderedArtifact: ReferenceObjectType.RENDERED_ARTIFACT,
    }
    value_type = value if isinstance(value, type) else type(value)
    try:
        return mapping[value_type]
    except KeyError as error:
        raise TypeError(f"unsupported TEOS object type: {value_type.__name__}") from error


def _owner_of(obj: TEOSObject) -> Organization | None:
    owner = getattr(obj, "owner", None)
    if isinstance(owner, Organization):
        return owner
    institution_information = getattr(obj, "institution_information", None)
    institution_owner = getattr(institution_information, "owner", None)
    return institution_owner if isinstance(institution_owner, Organization) else None


_SEMVER = re.compile(
    r"^(?P<major>0|[1-9]\d*)\.(?P<minor>0|[1-9]\d*)\."
    r"(?P<patch>0|[1-9]\d*)(?:-(?P<pre>[0-9A-Za-z.-]+))?"
    r"(?:\+[0-9A-Za-z.-]+)?$"
)


def _semver_key(version: str) -> tuple[object, ...]:
    match = _SEMVER.fullmatch(version)
    if match is None:
        return (0, version)
    prerelease = match.group("pre")
    pre_key: tuple[tuple[int, object], ...]
    if prerelease is None:
        pre_key = ((2, ""),)
    else:
        pre_key = tuple(
            (0, int(part)) if part.isdigit() else (1, part)
            for part in prerelease.split(".")
        )
    return (
        1,
        int(match.group("major")),
        int(match.group("minor")),
        int(match.group("patch")),
        pre_key,
    )


class ObjectRegistry:
    """A frozen, read-only registry of all validated object versions."""

    __slots__ = ("_by_identity", "_by_type", "_by_owner", "_by_lifecycle")

    def __init__(self, objects: Iterable[TEOSObject]) -> None:
        identities: dict[UUID, dict[str, TEOSObject]] = defaultdict(dict)
        identity_types: dict[UUID, ReferenceObjectType] = {}
        by_type: dict[ReferenceObjectType, list[TEOSObject]] = defaultdict(list)
        by_owner: dict[str, list[TEOSObject]] = defaultdict(list)
        by_lifecycle: dict[str, list[TEOSObject]] = defaultdict(list)

        for obj in objects:
            object_type = object_type_for(obj)
            previous_type = identity_types.setdefault(obj.teos_id, object_type)
            if previous_type is not object_type:
                raise DuplicateIdentifierError(
                    f"UUID {obj.teos_id} is used by both "
                    f"{previous_type.value} and {object_type.value}",
                    details={"identifier": str(obj.teos_id)},
                )
            if obj.teos_version in identities[obj.teos_id]:
                raise DuplicateVersionError(
                    f"duplicate version {obj.teos_version} for UUID {obj.teos_id}",
                    details={
                        "identifier": str(obj.teos_id),
                        "version": obj.teos_version,
                    },
                )
            identities[obj.teos_id][obj.teos_version] = obj
            by_type[object_type].append(obj)
            owner = _owner_of(obj)
            if owner is not None:
                by_owner[owner.identifier].append(obj)
            lifecycle = obj.lifecycle
            lifecycle_value = lifecycle.value if isinstance(lifecycle, Enum) else str(lifecycle)
            by_lifecycle[lifecycle_value].append(obj)

        self._by_identity = MappingProxyType(
            {
                identifier: MappingProxyType(dict(versions))
                for identifier, versions in identities.items()
            }
        )
        self._by_type = MappingProxyType(
            {key: self._ordered(value) for key, value in by_type.items()}
        )
        self._by_owner = MappingProxyType(
            {key: self._ordered(value) for key, value in by_owner.items()}
        )
        self._by_lifecycle = MappingProxyType(
            {key: self._ordered(value) for key, value in by_lifecycle.items()}
        )

    @staticmethod
    def _ordered(objects: Iterable[TEOSObject]) -> tuple[TEOSObject, ...]:
        return tuple(
            sorted(objects, key=lambda obj: (str(obj.teos_id), _semver_key(obj.teos_version)))
        )

    def lookup(self, identifier: UUID, version: str | None = None) -> TEOSObject:
        """Look up one UUID, requiring a version when several are present."""
        versions = self._by_identity[identifier]
        if version is not None:
            return versions[version]
        if len(versions) != 1:
            raise ValueError("version is required when an identity has multiple versions")
        return next(iter(versions.values()))

    def by_type(
        self, object_type: ReferenceObjectType | type[DomainObject]
    ) -> tuple[TEOSObject, ...]:
        """Return every version of a domain type in stable order."""
        resolved = (
            object_type_for(object_type)
            if isinstance(object_type, type)
            else object_type
        )
        return self._by_type.get(resolved, ())

    def by_version(self, version: str) -> tuple[TEOSObject, ...]:
        """Return all objects carrying an exact semantic version."""
        return self._ordered(
            obj
            for versions in self._by_identity.values()
            for candidate_version, obj in versions.items()
            if candidate_version == version
        )

    def latest(self, identifier: UUID) -> TEOSObject:
        """Return the highest SemVer version registered for one UUID."""
        versions = self._by_identity[identifier]
        return versions[max(versions, key=_semver_key)]

    def all_versions(self, identifier: UUID) -> tuple[TEOSObject, ...]:
        """Return every version of one UUID in semantic-version order."""
        versions = self._by_identity[identifier]
        return tuple(versions[key] for key in sorted(versions, key=_semver_key))

    def by_owner(
        self, owner: Organization | str
    ) -> tuple[TEOSObject, ...]:
        """Return objects owned by an organization identifier."""
        identifier = owner.identifier if isinstance(owner, Organization) else owner
        return self._by_owner.get(identifier, ())

    def by_lifecycle(self, lifecycle: Enum | str) -> tuple[TEOSObject, ...]:
        """Return objects with an exact source or artifact lifecycle."""
        value = lifecycle.value if isinstance(lifecycle, Enum) else lifecycle
        return self._by_lifecycle.get(value, ())

    def __iter__(self):
        """Iterate over all registered versions in stable order."""
        return iter(
            self._ordered(
                obj for versions in self._by_identity.values() for obj in versions.values()
            )
        )

    def __len__(self) -> int:
        """Return the number of registered object versions."""
        return sum(len(versions) for versions in self._by_identity.values())
