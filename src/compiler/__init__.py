"""Immutable curriculum dependency graph and compilation engine."""

from .compiler import (
    CompiledCompetency,
    CompiledCourse,
    CompiledInstructionalUnit,
    CompiledRepository,
    CompiledSession,
    CurriculumCompiler,
    compile_repository,
)
from .edges import DependencyEdge, EdgeKind
from .exceptions import (
    CompilationError,
    CompilerError,
    DependencyCycleError,
    DuplicateNodeError,
    GraphError,
    GraphIntegrityError,
    MissingNodeError,
    ResolutionError,
)
from .graph import DependencyGraph
from .node import GraphNode, NodeKey
from .resolver import dependency_edges_for, resolve_exact

__all__ = [
    "CompilationError",
    "CompiledCompetency",
    "CompiledCourse",
    "CompiledInstructionalUnit",
    "CompiledRepository",
    "CompiledSession",
    "CompilerError",
    "CurriculumCompiler",
    "DependencyCycleError",
    "DependencyEdge",
    "DependencyGraph",
    "DuplicateNodeError",
    "EdgeKind",
    "GraphError",
    "GraphIntegrityError",
    "GraphNode",
    "MissingNodeError",
    "NodeKey",
    "ResolutionError",
    "compile_repository",
    "dependency_edges_for",
    "resolve_exact",
]
