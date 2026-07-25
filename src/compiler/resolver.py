"""Contract-aware exact reference resolution into dependency graph edges."""

from __future__ import annotations

from dataclasses import fields, is_dataclass
from typing import Iterable

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
from src.models.lifecycle import ReferenceObjectType
from src.models.references import DocumentReference, Reference
from src.repository import ObjectRegistry, resolve_reference
from src.repository.exceptions import RepositoryError

from .edges import DependencyEdge, EdgeKind
from .exceptions import ResolutionError
from .node import NodeKey


_MANAGED_TYPES = frozenset(
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


def resolve_exact(
    reference: Reference,
    registry: ObjectRegistry,
    expected_type: type[TEOSObject] | None = None,
) -> TEOSObject:
    """Resolve a repository-managed reference without version substitution."""
    try:
        return resolve_reference(reference, registry, expected_type)
    except RepositoryError as error:
        raise ResolutionError(
            f"could not resolve {reference.object_type.value}:"
            f"{reference.identifier}@{reference.version}: {error.message}"
        ) from error


def _target_key(reference: Reference, registry: ObjectRegistry) -> NodeKey:
    target = resolve_exact(reference, registry)
    return NodeKey(reference.object_type, target.teos_id, target.teos_version)


def _declared_edges(
    source: NodeKey,
    references: Iterable[Reference],
    kind: EdgeKind,
    registry: ObjectRegistry,
) -> list[DependencyEdge]:
    return [
        DependencyEdge(
            source=source,
            target=_target_key(reference, registry),
            kind=kind,
            ordinal=ordinal,
        )
        for ordinal, reference in enumerate(references)
    ]


def _document_target_references(value: object) -> tuple[Reference, ...]:
    references: list[Reference] = []

    def inspect(candidate: object) -> None:
        if isinstance(candidate, DocumentReference):
            if (
                candidate.reference is not None
                and candidate.reference.object_type in _MANAGED_TYPES
            ):
                references.append(candidate.reference)
            return
        if isinstance(candidate, tuple):
            for item in candidate:
                inspect(item)
            return
        if is_dataclass(candidate):
            for item in fields(candidate):
                inspect(getattr(candidate, item.name))

    inspect(value)
    return tuple(references)


def dependency_edges_for(
    obj: TEOSObject, registry: ObjectRegistry
) -> tuple[DependencyEdge, ...]:
    """Resolve all contract-defined relationships declared by one object."""
    source = NodeKey(
        object_type=_object_type(obj),
        identifier=obj.teos_id,
        version=obj.teos_version,
    )
    edges: list[DependencyEdge] = []

    if isinstance(obj, Course):
        edges += _declared_edges(
            source,
            obj.instructional_unit_references,
            EdgeKind.COURSE_INSTRUCTIONAL_UNIT,
            registry,
        )
        edges += _declared_edges(
            source, obj.standard_references, EdgeKind.COURSE_STANDARD, registry
        )
        edges += _declared_edges(
            source,
            obj.prerequisite_competency_references,
            EdgeKind.COURSE_PREREQUISITE_COMPETENCY,
            registry,
        )
        edges += _declared_edges(
            source,
            obj.prerequisite_course_references,
            EdgeKind.COURSE_PREREQUISITE_COURSE,
            registry,
        )
    elif isinstance(obj, InstructionalUnit):
        edges += _declared_edges(
            source,
            obj.included_competency_references,
            EdgeKind.UNIT_COMPETENCY,
            registry,
        )
        edges += _declared_edges(
            source, obj.session_references, EdgeKind.UNIT_SESSION, registry
        )
        edges += _declared_edges(
            source,
            obj.prerequisite_competency_references,
            EdgeKind.UNIT_PREREQUISITE_COMPETENCY,
            registry,
        )
        edges += _declared_edges(
            source,
            obj.prerequisite_instructional_unit_references,
            EdgeKind.UNIT_PREREQUISITE_UNIT,
            registry,
        )
    elif isinstance(obj, Session):
        edges += _declared_edges(
            source,
            obj.competency_references,
            EdgeKind.SESSION_COMPETENCY,
            registry,
        )
        edges += _declared_edges(
            source,
            (
                dependency.session_reference
                for dependency in obj.prerequisite_session_references
            ),
            EdgeKind.SESSION_PREREQUISITE_SESSION,
            registry,
        )
        for ordinal, dependency in enumerate(
            obj.dependent_session_references
        ):
            dependent = _target_key(dependency.session_reference, registry)
            edges.append(
                DependencyEdge(
                    source=dependent,
                    target=source,
                    kind=EdgeKind.SESSION_PREREQUISITE_SESSION,
                    ordinal=ordinal,
                )
            )
        edges += _declared_edges(
            source,
            obj.prerequisite_competency_references,
            EdgeKind.SESSION_PREREQUISITE_COMPETENCY,
            registry,
        )
    elif isinstance(obj, Competency):
        edges += _declared_edges(
            source,
            obj.prerequisite_competency_references,
            EdgeKind.COMPETENCY_PREREQUISITE_COMPETENCY,
            registry,
        )
        edges += _declared_edges(
            source,
            obj.standard_references,
            EdgeKind.COMPETENCY_STANDARD,
            registry,
        )
    elif isinstance(obj, Standard):
        edges += _declared_edges(
            source,
            obj.competency_references,
            EdgeKind.STANDARD_COMPETENCY_TRACE,
            registry,
        )
    elif isinstance(obj, InstitutionProfile):
        edges += _declared_edges(
            source,
            obj.academic_calendar_references,
            EdgeKind.PROFILE_CALENDAR,
            registry,
        )
        if obj.composition is not None:
            edges += _declared_edges(
                source,
                obj.composition.profile_references,
                EdgeKind.PROFILE_COMPOSITION,
                registry,
            )
    elif isinstance(obj, RenderedArtifact):
        edges += _declared_edges(
            source,
            (
                reference
                for reference in obj.source_references
                if reference.object_type in _MANAGED_TYPES
            ),
            EdgeKind.ARTIFACT_SOURCE,
            registry,
        )
        if obj.institution_profile_reference is not None:
            edges += _declared_edges(
                source,
                (obj.institution_profile_reference,),
                EdgeKind.ARTIFACT_PROFILE,
                registry,
            )
        if obj.academic_calendar_reference is not None:
            edges += _declared_edges(
                source,
                (obj.academic_calendar_reference,),
                EdgeKind.ARTIFACT_CALENDAR,
                registry,
            )
        if obj.supersedes_artifact_reference is not None:
            edges += _declared_edges(
                source,
                (obj.supersedes_artifact_reference,),
                EdgeKind.ARTIFACT_SUPERSEDES,
                registry,
            )
    elif not isinstance(obj, AcademicCalendar):
        raise ResolutionError(
            f"unsupported maintained object type {type(obj).__name__}"
        )

    document_references = _document_target_references(obj)
    if isinstance(obj, InstitutionProfile):
        course_references = tuple(
            reference
            for reference in document_references
            if reference.object_type is ReferenceObjectType.COURSE
        )
        edges += _declared_edges(
            source, course_references, EdgeKind.PROFILE_COURSE, registry
        )
        document_references = tuple(
            reference
            for reference in document_references
            if reference.object_type is not ReferenceObjectType.COURSE
        )
    edges += _declared_edges(
        source,
        document_references,
        EdgeKind.DOCUMENT_REFERENCE,
        registry,
    )
    return tuple(edges)


def _object_type(obj: TEOSObject) -> ReferenceObjectType:
    from src.repository.registry import object_type_for

    return object_type_for(obj)
