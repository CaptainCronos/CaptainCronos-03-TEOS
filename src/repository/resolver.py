"""Exact and explicitly latest reference resolution helpers."""

from __future__ import annotations

from typing import TypeVar, cast

from src.models.base import TEOSObject
from src.models.references import Reference

from .exceptions import MissingReferenceError, VersionMismatchError, reference_details
from .registry import ObjectRegistry, object_type_for


ResolvedObject = TypeVar("ResolvedObject", bound=TEOSObject)


def resolve_reference(
    reference: Reference,
    registry: ObjectRegistry,
    expected_type: type[ResolvedObject] | None = None,
) -> ResolvedObject | TEOSObject:
    """Resolve the exact UUID, version, and object type in a reference."""
    details = reference_details(
        reference.identifier, reference.version, reference.object_type.value
    )
    try:
        target = registry.lookup(reference.identifier, reference.version)
    except KeyError as error:
        try:
            registry.all_versions(reference.identifier)
        except KeyError:
            raise MissingReferenceError(
                f"missing referenced {reference.object_type.value} "
                f"{reference.identifier}@{reference.version}",
                details=details,
            ) from error
        raise VersionMismatchError(
            f"no version {reference.version} exists for UUID {reference.identifier}",
            details=details,
        ) from error

    actual_type = object_type_for(target)
    if actual_type is not reference.object_type:
        from .exceptions import ReferenceValidationError

        raise ReferenceValidationError(
            f"reference declares {reference.object_type.value}, "
            f"but UUID {reference.identifier} is {actual_type.value}",
            details={**details, "actual_object_type": actual_type.value},
        )
    if expected_type is not None and not isinstance(target, expected_type):
        from .exceptions import ReferenceValidationError

        raise ReferenceValidationError(
            f"resolved object is {type(target).__name__}, "
            f"expected {expected_type.__name__}",
            details=details,
        )
    return cast(ResolvedObject | TEOSObject, target)


def resolve_latest_reference(
    reference: Reference,
    registry: ObjectRegistry,
    expected_type: type[ResolvedObject] | None = None,
) -> ResolvedObject | TEOSObject:
    """Resolve the latest version only when the caller explicitly requests it."""
    try:
        target = registry.latest(reference.identifier)
    except KeyError as error:
        raise MissingReferenceError(
            f"missing referenced {reference.object_type.value} {reference.identifier}",
            details=reference_details(
                reference.identifier, reference.version, reference.object_type.value
            ),
        ) from error
    if object_type_for(target) is not reference.object_type:
        from .exceptions import ReferenceValidationError

        raise ReferenceValidationError(
            f"reference type {reference.object_type.value} does not match "
            f"{object_type_for(target).value}"
        )
    if expected_type is not None and not isinstance(target, expected_type):
        from .exceptions import ReferenceValidationError

        raise ReferenceValidationError(
            f"resolved object is {type(target).__name__}, "
            f"expected {expected_type.__name__}"
        )
    return cast(ResolvedObject | TEOSObject, target)
