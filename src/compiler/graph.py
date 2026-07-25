"""Immutable dependency graph over every maintained TEOS object version."""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Iterable, Mapping
from types import MappingProxyType

from .edges import DependencyEdge
from .exceptions import (
    DependencyCycleError,
    DuplicateNodeError,
    GraphIntegrityError,
    MissingNodeError,
)
from .node import GraphNode, NodeKey
from .ordering import cyclic_components, topological_order
from .traversal import (
    is_reachable,
    reachable_nodes,
    strongly_connected_components,
    transitive_closure,
)


class DependencyGraph:
    """A frozen directed multigraph with deterministic relationship queries."""

    __slots__ = (
        "_nodes",
        "_edges",
        "_outgoing",
        "_incoming",
        "_ordering_outgoing",
        "_ordering_incoming",
    )

    def __init__(
        self,
        nodes: Iterable[GraphNode],
        edges: Iterable[DependencyEdge],
    ) -> None:
        node_index: dict[NodeKey, GraphNode] = {}
        for node in nodes:
            if node.key in node_index:
                raise DuplicateNodeError(f"duplicate graph node {node.key}")
            node_index[node.key] = node

        ordered_edges = tuple(sorted(set(edges), key=DependencyEdge.sort_key))
        outgoing: dict[NodeKey, set[NodeKey]] = defaultdict(set)
        incoming: dict[NodeKey, set[NodeKey]] = defaultdict(set)
        ordering_outgoing: dict[NodeKey, set[NodeKey]] = defaultdict(set)
        ordering_incoming: dict[NodeKey, set[NodeKey]] = defaultdict(set)
        for edge in ordered_edges:
            if edge.source not in node_index or edge.target not in node_index:
                missing = (
                    edge.source if edge.source not in node_index else edge.target
                )
                raise GraphIntegrityError(
                    f"edge {edge.kind.value} references missing node {missing}"
                )
            outgoing[edge.source].add(edge.target)
            incoming[edge.target].add(edge.source)
            if edge.constrains_order:
                ordering_outgoing[edge.source].add(edge.target)
                ordering_incoming[edge.target].add(edge.source)

        keys = tuple(sorted(node_index))
        self._nodes = MappingProxyType(
            {key: node_index[key] for key in keys}
        )
        self._edges = ordered_edges
        self._outgoing = self._freeze_adjacency(keys, outgoing)
        self._incoming = self._freeze_adjacency(keys, incoming)
        self._ordering_outgoing = self._freeze_adjacency(
            keys, ordering_outgoing
        )
        self._ordering_incoming = self._freeze_adjacency(
            keys, ordering_incoming
        )

    @staticmethod
    def _freeze_adjacency(
        keys: tuple[NodeKey, ...],
        adjacency: Mapping[NodeKey, set[NodeKey]],
    ) -> Mapping[NodeKey, tuple[NodeKey, ...]]:
        return MappingProxyType(
            {key: tuple(sorted(adjacency.get(key, ()))) for key in keys}
        )

    @property
    def nodes(self) -> tuple[GraphNode, ...]:
        """Return every exact-version node in stable order."""
        return tuple(self._nodes.values())

    @property
    def edges(self) -> tuple[DependencyEdge, ...]:
        """Return every typed edge in stable order."""
        return self._edges

    def node(self, key: NodeKey) -> GraphNode:
        """Return one node by exact key."""
        try:
            return self._nodes[key]
        except KeyError as error:
            raise MissingNodeError(f"graph does not contain {key}") from error

    def children(self, key: NodeKey) -> tuple[GraphNode, ...]:
        """Return direct targets declared by one node."""
        self.node(key)
        return tuple(self._nodes[child] for child in self._outgoing[key])

    def outgoing_edges(self, key: NodeKey) -> tuple[DependencyEdge, ...]:
        """Return exact typed relationships declared by one node."""
        self.node(key)
        return tuple(edge for edge in self._edges if edge.source == key)

    def parents(self, key: NodeKey) -> tuple[GraphNode, ...]:
        """Return direct referrers of one node."""
        self.node(key)
        return tuple(self._nodes[parent] for parent in self._incoming[key])

    def incoming_edges(self, key: NodeKey) -> tuple[DependencyEdge, ...]:
        """Return exact typed relationships targeting one node."""
        self.node(key)
        return tuple(edge for edge in self._edges if edge.target == key)

    def reverse_dependencies(self, key: NodeKey) -> tuple[GraphNode, ...]:
        """Return direct objects that declare a relationship to one node."""
        return self.parents(key)

    def descendants(self, key: NodeKey) -> tuple[GraphNode, ...]:
        """Return all transitively reachable declared targets."""
        self.node(key)
        return tuple(
            self._nodes[node] for node in reachable_nodes(key, self._outgoing)
        )

    def ancestors(self, key: NodeKey) -> tuple[GraphNode, ...]:
        """Return all transitive referrers of one node."""
        self.node(key)
        return tuple(
            self._nodes[node] for node in reachable_nodes(key, self._incoming)
        )

    def is_reachable(self, source: NodeKey, target: NodeKey) -> bool:
        """Return whether a declared relationship path connects two nodes."""
        self.node(source)
        self.node(target)
        return is_reachable(source, target, self._outgoing)

    def transitive_closure(self) -> tuple[tuple[NodeKey, NodeKey], ...]:
        """Return every reachable ordered node pair."""
        return transitive_closure(tuple(self._nodes), self._outgoing)

    def strongly_connected_components(
        self, *, ordering_only: bool = False
    ) -> tuple[tuple[GraphNode, ...], ...]:
        """Return stable strongly connected components."""
        adjacency = (
            self._ordering_outgoing if ordering_only else self._outgoing
        )
        return tuple(
            tuple(self._nodes[key] for key in component)
            for component in strongly_connected_components(
                tuple(self._nodes), adjacency
            )
        )

    def topological_order(
        self, *, dependencies_first: bool = True
    ) -> tuple[GraphNode, ...]:
        """Return a stable ordering over dependency-constraining edges."""
        adjacency = (
            self._ordering_incoming
            if dependencies_first
            else self._ordering_outgoing
        )
        keys = topological_order(tuple(self._nodes), adjacency)
        return tuple(self._nodes[key] for key in keys)

    def dependency_cycles(self) -> tuple[tuple[GraphNode, ...], ...]:
        """Return all illegal ordering components in stable order."""
        return tuple(
            tuple(self._nodes[key] for key in component)
            for component in cyclic_components(
                tuple(self._nodes), self._ordering_outgoing
            )
        )

    def verify_acyclic(self) -> None:
        """Reject any illegal dependency cycle deterministically."""
        components = self.dependency_cycles()
        if components:
            raise DependencyCycleError(
                tuple(tuple(node.key for node in part) for part in components)
            )

    def orphans(self) -> tuple[GraphNode, ...]:
        """Return nodes with neither incoming nor outgoing relationships."""
        return tuple(
            node
            for key, node in self._nodes.items()
            if not self._outgoing[key] and not self._incoming[key]
        )

    def __len__(self) -> int:
        """Return the number of exact-version graph nodes."""
        return len(self._nodes)
