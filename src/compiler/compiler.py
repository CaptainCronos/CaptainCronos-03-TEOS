"""Compile a validated Repository into immutable dependency-aware views."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TypeVar, cast

from src.models import (
    Competency,
    Course,
    InstructionalUnit,
    Session,
    Standard,
)
from src.models.base import TEOSObject
from src.models.references import Reference
from src.repository import Repository

from .graph import DependencyGraph
from .node import GraphNode
from .resolver import dependency_edges_for, resolve_exact


Resolved = TypeVar("Resolved", bound=TEOSObject)


def _resolve_many(
    references: tuple[Reference, ...],
    repository: Repository,
    expected_type: type[Resolved],
) -> tuple[Resolved, ...]:
    return tuple(
        cast(
            Resolved,
            resolve_exact(reference, repository.registry, expected_type),
        )
        for reference in references
    )


@dataclass(frozen=True, slots=True)
class CompiledCompetency:
    """A Competency with exact prerequisites and Standards resolved."""

    source: Competency
    prerequisite_competencies: tuple[Competency, ...]
    standards: tuple[Standard, ...]


@dataclass(frozen=True, slots=True)
class CompiledSession:
    """A Session with exact curriculum dependencies resolved."""

    source: Session
    competencies: tuple[Competency, ...]
    prerequisite_sessions: tuple[Session, ...]
    dependent_sessions: tuple[Session, ...]
    prerequisite_competencies: tuple[Competency, ...]


@dataclass(frozen=True, slots=True)
class CompiledInstructionalUnit:
    """An Instructional Unit with exact content and prerequisites resolved."""

    source: InstructionalUnit
    competencies: tuple[Competency, ...]
    sessions: tuple[Session, ...]
    prerequisite_competencies: tuple[Competency, ...]
    prerequisite_instructional_units: tuple[InstructionalUnit, ...]


@dataclass(frozen=True, slots=True)
class CompiledCourse:
    """A Course with exact ordered content and prerequisites resolved."""

    source: Course
    instructional_units: tuple[InstructionalUnit, ...]
    standards: tuple[Standard, ...]
    prerequisite_competencies: tuple[Competency, ...]
    prerequisite_courses: tuple[Course, ...]


@dataclass(frozen=True, slots=True)
class CompiledRepository:
    """A complete immutable compilation result for one validated repository."""

    source: Repository
    graph: DependencyGraph
    dependency_order: tuple[TEOSObject, ...]
    courses: tuple[CompiledCourse, ...]
    instructional_units: tuple[CompiledInstructionalUnit, ...]
    sessions: tuple[CompiledSession, ...]
    competencies: tuple[CompiledCompetency, ...]

    def objects_in_dependency_order(
        self, object_type: type[Resolved]
    ) -> tuple[Resolved, ...]:
        """Return one domain type in stable dependency-first order."""
        return tuple(
            cast(Resolved, obj)
            for obj in self.dependency_order
            if isinstance(obj, object_type)
        )

    @property
    def course_order(self) -> tuple[Course, ...]:
        """Return Courses in stable prerequisite-first order."""
        return self.objects_in_dependency_order(Course)

    @property
    def instructional_unit_order(self) -> tuple[InstructionalUnit, ...]:
        """Return Instructional Units in stable prerequisite-first order."""
        return self.objects_in_dependency_order(InstructionalUnit)

    @property
    def session_order(self) -> tuple[Session, ...]:
        """Return Sessions in stable prerequisite-first order."""
        return self.objects_in_dependency_order(Session)

    @property
    def competency_order(self) -> tuple[Competency, ...]:
        """Return Competencies in stable prerequisite-first order."""
        return self.objects_in_dependency_order(Competency)


class CurriculumCompiler:
    """Resolve, graph, verify, order, and compile one validated repository."""

    def compile(self, repository: Repository) -> CompiledRepository:
        """Compile all maintained object versions without scheduling."""
        objects = tuple(repository.registry)
        nodes = tuple(GraphNode.from_object(obj) for obj in objects)
        edges = tuple(
            edge
            for obj in objects
            for edge in dependency_edges_for(obj, repository.registry)
        )
        graph = DependencyGraph(nodes, edges)
        graph.verify_acyclic()
        dependency_order = tuple(
            node.value for node in graph.topological_order()
        )

        competencies = tuple(
            self._compile_competency(obj, repository)
            for obj in objects
            if isinstance(obj, Competency)
        )
        sessions = tuple(
            self._compile_session(obj, repository)
            for obj in objects
            if isinstance(obj, Session)
        )
        units = tuple(
            self._compile_unit(obj, repository)
            for obj in objects
            if isinstance(obj, InstructionalUnit)
        )
        courses = tuple(
            self._compile_course(obj, repository)
            for obj in objects
            if isinstance(obj, Course)
        )
        return CompiledRepository(
            source=repository,
            graph=graph,
            dependency_order=dependency_order,
            courses=courses,
            instructional_units=units,
            sessions=sessions,
            competencies=competencies,
        )

    @staticmethod
    def _compile_competency(
        obj: Competency, repository: Repository
    ) -> CompiledCompetency:
        return CompiledCompetency(
            source=obj,
            prerequisite_competencies=_resolve_many(
                obj.prerequisite_competency_references,
                repository,
                Competency,
            ),
            standards=_resolve_many(
                obj.standard_references, repository, Standard
            ),
        )

    @staticmethod
    def _compile_session(
        obj: Session, repository: Repository
    ) -> CompiledSession:
        return CompiledSession(
            source=obj,
            competencies=_resolve_many(
                obj.competency_references, repository, Competency
            ),
            prerequisite_sessions=_resolve_many(
                tuple(
                    dependency.session_reference
                    for dependency in obj.prerequisite_session_references
                ),
                repository,
                Session,
            ),
            dependent_sessions=_resolve_many(
                tuple(
                    dependency.session_reference
                    for dependency in obj.dependent_session_references
                ),
                repository,
                Session,
            ),
            prerequisite_competencies=_resolve_many(
                obj.prerequisite_competency_references,
                repository,
                Competency,
            ),
        )

    @staticmethod
    def _compile_unit(
        obj: InstructionalUnit, repository: Repository
    ) -> CompiledInstructionalUnit:
        return CompiledInstructionalUnit(
            source=obj,
            competencies=_resolve_many(
                obj.included_competency_references,
                repository,
                Competency,
            ),
            sessions=_resolve_many(
                obj.session_references, repository, Session
            ),
            prerequisite_competencies=_resolve_many(
                obj.prerequisite_competency_references,
                repository,
                Competency,
            ),
            prerequisite_instructional_units=_resolve_many(
                obj.prerequisite_instructional_unit_references,
                repository,
                InstructionalUnit,
            ),
        )

    @staticmethod
    def _compile_course(
        obj: Course, repository: Repository
    ) -> CompiledCourse:
        return CompiledCourse(
            source=obj,
            instructional_units=_resolve_many(
                obj.instructional_unit_references,
                repository,
                InstructionalUnit,
            ),
            standards=_resolve_many(
                obj.standard_references, repository, Standard
            ),
            prerequisite_competencies=_resolve_many(
                obj.prerequisite_competency_references,
                repository,
                Competency,
            ),
            prerequisite_courses=_resolve_many(
                obj.prerequisite_course_references, repository, Course
            ),
        )


def compile_repository(repository: Repository) -> CompiledRepository:
    """Compile a validated repository with the default curriculum compiler."""
    return CurriculumCompiler().compile(repository)
