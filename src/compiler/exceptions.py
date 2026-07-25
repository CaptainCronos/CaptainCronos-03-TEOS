"""Deterministic diagnostics for curriculum graph construction and compilation."""

from __future__ import annotations

from typing import Iterable


class CompilerError(Exception):
    """Base class for failures that prevent publication of compiled curriculum."""


class ResolutionError(CompilerError):
    """An exact typed relationship cannot be resolved during compilation."""


class GraphError(CompilerError):
    """Base class for dependency graph construction or query failures."""


class DuplicateNodeError(GraphError):
    """Two graph nodes have the same type, UUID, and exact version."""


class MissingNodeError(GraphError):
    """A requested node or edge endpoint is absent from the graph."""


class GraphIntegrityError(GraphError):
    """The immutable graph violates an endpoint or relationship invariant."""


class DependencyCycleError(GraphError):
    """Ordering relationships contain one or more illegal dependency cycles."""

    def __init__(self, components: Iterable[Iterable[object]]) -> None:
        self.components = tuple(tuple(component) for component in components)
        rendered = "; ".join(
            " -> ".join(str(node) for node in component)
            for component in self.components
        )
        super().__init__(f"illegal dependency cycle(s): {rendered}")


class CompilationError(CompilerError):
    """Resolved graph data cannot be materialized as compiled curriculum."""
