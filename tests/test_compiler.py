"""Curriculum dependency graph and immutable compilation tests."""

from __future__ import annotations

from dataclasses import FrozenInstanceError
from uuid import UUID

import pytest

from src.compiler import (
    CompiledRepository,
    DependencyCycleError,
    DependencyEdge,
    DependencyGraph,
    EdgeKind,
    GraphNode,
    compile_repository,
)
from src.models import Competency, Course, InstructionalUnit, Session, Standard
from src.models.course import CompletionRequirement
from src.models.duration import Duration
from src.models.lifecycle import (
    DurationUnit,
    LifecycleStatus,
    SessionType,
)
from src.models.metadata import LocalizedString, Organization
from src.models.references import (
    AssessmentExpectation,
    CompetencyReference,
    DocumentReference,
    InstructionalUnitReference,
    SessionReference,
    StandardReference,
)
from src.models.session import SessionDependency
from src.repository import ObjectRegistry, Repository


OWNER = Organization(
    identifier="test-owner", name=LocalizedString("Test Owner")
)


def identifier(number: int) -> UUID:
    """Return a readable deterministic fixture UUID."""
    return UUID(int=number)


def competency(
    number: int,
    *,
    prerequisites: tuple[int, ...] = (),
    standards: tuple[int, ...] = (),
) -> Competency:
    """Create a minimal immutable Competency fixture."""
    return Competency(
        competency_id=identifier(number),
        version="1.0.0",
        owner=OWNER,
        title=LocalizedString(f"Competency {number}"),
        description=LocalizedString("Description"),
        learning_outcome=LocalizedString("Observable outcome"),
        performance_criteria=(LocalizedString("Criterion"),),
        assessment_evidence=(
            AssessmentExpectation(LocalizedString("Evidence")),
        ),
        lifecycle_status=LifecycleStatus.APPROVED,
        prerequisite_competency_references=tuple(
            CompetencyReference(identifier=identifier(item), version="1.0.0")
            for item in prerequisites
        ),
        standard_references=tuple(
            StandardReference(identifier=identifier(item), version="1.0.0")
            for item in standards
        ),
    )


def curriculum_repository() -> Repository:
    """Create a complete Course→Unit→Session→Competency→Standard chain."""
    standard = Standard(
        standard_id=identifier(1),
        version="1.0.0",
        title=LocalizedString("Standard"),
        issuer=OWNER,
        source=DocumentReference(
            title=LocalizedString("Authority"), uri="https://example.test"
        ),
        requirements_scope=LocalizedString("Scope"),
        lifecycle_status=LifecycleStatus.APPROVED,
    )
    foundation = competency(2, standards=(1,))
    advanced = competency(3, prerequisites=(2,), standards=(1,))
    first_session = Session(
        session_id=identifier(4),
        version="1.0.0",
        owner=OWNER,
        session_title=LocalizedString("Foundation session"),
        session_type=SessionType.THEORY,
        duration=Duration(1, DurationUnit.HOURS),
        learning_objectives=(LocalizedString("Learn foundation"),),
        competency_references=(
            CompetencyReference(identifier=identifier(2), version="1.0.0"),
        ),
        lifecycle_status=LifecycleStatus.APPROVED,
    )
    second_session = Session(
        session_id=identifier(5),
        version="1.0.0",
        owner=OWNER,
        session_title=LocalizedString("Advanced session"),
        session_type=SessionType.LAB,
        duration=Duration(1, DurationUnit.HOURS),
        learning_objectives=(LocalizedString("Apply foundation"),),
        competency_references=(
            CompetencyReference(identifier=identifier(3), version="1.0.0"),
        ),
        lifecycle_status=LifecycleStatus.APPROVED,
        prerequisite_session_references=(
            SessionDependency(
                SessionReference(identifier=identifier(4), version="1.0.0"),
                "must precede",
            ),
        ),
        prerequisite_competency_references=(
            CompetencyReference(identifier=identifier(2), version="1.0.0"),
        ),
    )
    unit = InstructionalUnit(
        instructional_unit_id=identifier(6),
        version="1.0.0",
        owner=OWNER,
        title=LocalizedString("Unit"),
        description=LocalizedString("Unit scope"),
        included_competency_references=(
            CompetencyReference(identifier=identifier(2), version="1.0.0"),
            CompetencyReference(identifier=identifier(3), version="1.0.0"),
        ),
        learning_objectives=(LocalizedString("Complete sessions"),),
        session_references=(
            SessionReference(identifier=identifier(4), version="1.0.0"),
            SessionReference(identifier=identifier(5), version="1.0.0"),
        ),
        estimated_duration=Duration(2, DurationUnit.HOURS),
        assessment_strategy=(
            AssessmentExpectation(LocalizedString("Observe performance")),
        ),
        lifecycle_status=LifecycleStatus.APPROVED,
    )
    course = Course(
        course_id=identifier(7),
        version="1.0.0",
        owner=OWNER,
        title=LocalizedString("Course"),
        description=LocalizedString("Course scope"),
        instructional_unit_references=(
            InstructionalUnitReference(
                identifier=identifier(6), version="1.0.0"
            ),
        ),
        completion_requirements=(
            CompletionRequirement("completion", LocalizedString("Complete")),
        ),
        estimated_instructional_hours=Duration(2, DurationUnit.HOURS),
        lifecycle_status=LifecycleStatus.APPROVED,
        standard_references=(
            StandardReference(identifier=identifier(1), version="1.0.0"),
        ),
    )
    registry = ObjectRegistry(
        (
            course,
            second_session,
            standard,
            foundation,
            unit,
            advanced,
            first_session,
        )
    )
    return Repository(registry, ())


def test_graph_construction_and_exact_reference_resolution() -> None:
    """Compilation creates nodes for all objects and typed exact edges."""
    compiled = compile_repository(curriculum_repository())

    assert len(compiled.graph) == 7
    assert len(compiled.graph.edges) == 13
    course_edge = next(
        edge
        for edge in compiled.graph.edges
        if edge.kind is EdgeKind.COURSE_INSTRUCTIONAL_UNIT
    )
    assert course_edge.source.identifier == identifier(7)
    assert course_edge.target.identifier == identifier(6)
    assert course_edge.target.version == "1.0.0"


def test_ancestors_descendants_reverse_lookup_and_reachability() -> None:
    """Graph traversal follows declared parent-to-target relationships."""
    graph = compile_repository(curriculum_repository()).graph
    course = next(
        node for node in graph.nodes if node.key.identifier == identifier(7)
    )
    standard = next(
        node for node in graph.nodes if node.key.identifier == identifier(1)
    )

    assert standard in graph.descendants(course.key)
    assert course in graph.ancestors(standard.key)
    assert course in graph.reverse_dependencies(
        next(node for node in graph.nodes if node.key.identifier == identifier(6)).key
    )
    assert graph.is_reachable(course.key, standard.key)
    assert (course.key, standard.key) in graph.transitive_closure()


def test_dependency_order_is_stable_and_dependencies_first() -> None:
    """Topological ordering puts exact targets before their dependents."""
    first = compile_repository(curriculum_repository())
    second = compile_repository(curriculum_repository())
    first_ids = tuple(item.teos_id for item in first.dependency_order)

    assert first_ids == tuple(item.teos_id for item in second.dependency_order)
    assert first_ids.index(identifier(1)) < first_ids.index(identifier(3))
    assert first_ids.index(identifier(4)) < first_ids.index(identifier(5))
    assert first_ids.index(identifier(6)) < first_ids.index(identifier(7))
    assert tuple(item.teos_id for item in first.session_order) == (
        identifier(4),
        identifier(5),
    )
    assert tuple(item.teos_id for item in first.competency_order) == (
        identifier(2),
        identifier(3),
    )


def test_strong_components_and_cycle_diagnostic_are_deterministic() -> None:
    """Illegal prerequisite cycles report stable exact node identities."""
    first = competency(10, prerequisites=(11,))
    second = competency(11, prerequisites=(10,))
    repository = Repository(ObjectRegistry((second, first)), ())

    with pytest.raises(DependencyCycleError) as first_error:
        compile_repository(repository)
    with pytest.raises(DependencyCycleError) as second_error:
        compile_repository(repository)

    assert str(first_error.value) == str(second_error.value)
    assert "competency:00000000-0000-0000-0000-00000000000a@1.0.0" in str(
        first_error.value
    )


def test_orphan_detection() -> None:
    """A node with no declared incoming or outgoing relationship is an orphan."""
    standalone = competency(20)
    node = GraphNode.from_object(standalone)
    graph = DependencyGraph((node,), ())

    assert graph.orphans() == (node,)
    assert graph.strongly_connected_components() == ((node,),)


def test_graph_is_immutable() -> None:
    """Graph collections and node/edge values cannot be mutated."""
    graph = compile_repository(curriculum_repository()).graph

    with pytest.raises(AttributeError):
        graph.nodes.append(graph.nodes[0])  # type: ignore[attr-defined]
    with pytest.raises(FrozenInstanceError):
        graph.edges[0].ordinal = 99  # type: ignore[misc]


def test_compiler_output_contains_resolved_immutable_views() -> None:
    """Compiled views retain exact objects and declared sequence."""
    compiled = compile_repository(curriculum_repository())

    assert isinstance(compiled, CompiledRepository)
    assert compiled.courses[0].instructional_units[0].teos_id == identifier(6)
    assert tuple(
        session.teos_id
        for session in compiled.instructional_units[0].sessions
    ) == (identifier(4), identifier(5))
    assert (
        compiled.sessions[1].prerequisite_sessions[0].teos_id
        == identifier(4)
    )
    assert (
        compiled.competencies[1].prerequisite_competencies[0].teos_id
        == identifier(2)
    )
    with pytest.raises(FrozenInstanceError):
        compiled.courses[0].source = compiled.courses[0].source  # type: ignore[misc]


def test_graph_rejects_missing_edge_endpoint() -> None:
    """Graph integrity rejects an edge whose exact target is absent."""
    node = GraphNode.from_object(competency(30))
    missing = GraphNode.from_object(competency(31))
    edge = DependencyEdge(
        source=node.key,
        target=missing.key,
        kind=EdgeKind.COMPETENCY_PREREQUISITE_COMPETENCY,
    )

    with pytest.raises(Exception, match="missing node"):
        DependencyGraph((node,), (edge,))
