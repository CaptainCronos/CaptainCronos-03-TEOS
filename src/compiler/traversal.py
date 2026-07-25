"""Pure deterministic traversal algorithms over immutable adjacency indexes."""

from __future__ import annotations

from collections.abc import Mapping

from .node import NodeKey


def reachable_nodes(
    start: NodeKey, adjacency: Mapping[NodeKey, tuple[NodeKey, ...]]
) -> tuple[NodeKey, ...]:
    """Return all nodes reachable from ``start`` in stable depth-first order."""
    visited: set[NodeKey] = set()
    pending = list(reversed(adjacency.get(start, ())))
    while pending:
        current = pending.pop()
        if current in visited:
            continue
        visited.add(current)
        pending.extend(
            reversed(
                tuple(
                    child
                    for child in adjacency.get(current, ())
                    if child not in visited
                )
            )
        )
    return tuple(sorted(visited))


def is_reachable(
    source: NodeKey,
    target: NodeKey,
    adjacency: Mapping[NodeKey, tuple[NodeKey, ...]],
) -> bool:
    """Return whether a directed path connects two exact nodes."""
    return target in reachable_nodes(source, adjacency)


def transitive_closure(
    nodes: tuple[NodeKey, ...],
    adjacency: Mapping[NodeKey, tuple[NodeKey, ...]],
) -> tuple[tuple[NodeKey, NodeKey], ...]:
    """Return every reachable ordered pair in stable order."""
    return tuple(
        (source, target)
        for source in nodes
        for target in reachable_nodes(source, adjacency)
    )


def strongly_connected_components(
    nodes: tuple[NodeKey, ...],
    adjacency: Mapping[NodeKey, tuple[NodeKey, ...]],
) -> tuple[tuple[NodeKey, ...], ...]:
    """Return Tarjan strongly connected components deterministically."""
    index = 0
    indexes: dict[NodeKey, int] = {}
    lowlinks: dict[NodeKey, int] = {}
    stack: list[NodeKey] = []
    on_stack: set[NodeKey] = set()
    components: list[tuple[NodeKey, ...]] = []

    def connect(node: NodeKey) -> None:
        nonlocal index
        indexes[node] = index
        lowlinks[node] = index
        index += 1
        stack.append(node)
        on_stack.add(node)

        for child in adjacency.get(node, ()):
            if child not in indexes:
                connect(child)
                lowlinks[node] = min(lowlinks[node], lowlinks[child])
            elif child in on_stack:
                lowlinks[node] = min(lowlinks[node], indexes[child])

        if lowlinks[node] == indexes[node]:
            component: list[NodeKey] = []
            while True:
                member = stack.pop()
                on_stack.remove(member)
                component.append(member)
                if member == node:
                    break
            components.append(tuple(sorted(component)))

    for node in nodes:
        if node not in indexes:
            connect(node)
    return tuple(sorted(components, key=lambda component: component[0]))
