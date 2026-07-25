"""Stable dependency ordering and illegal-cycle discovery."""

from __future__ import annotations

import heapq
from collections.abc import Mapping

from .exceptions import DependencyCycleError
from .node import NodeKey
from .traversal import strongly_connected_components


def topological_order(
    nodes: tuple[NodeKey, ...],
    adjacency: Mapping[NodeKey, tuple[NodeKey, ...]],
) -> tuple[NodeKey, ...]:
    """Return a stable source-before-target topological order."""
    indegree = {node: 0 for node in nodes}
    for children in adjacency.values():
        for child in children:
            indegree[child] += 1

    ready = [node for node, degree in indegree.items() if degree == 0]
    heapq.heapify(ready)
    ordered: list[NodeKey] = []
    while ready:
        node = heapq.heappop(ready)
        ordered.append(node)
        for child in adjacency.get(node, ()):
            indegree[child] -= 1
            if indegree[child] == 0:
                heapq.heappush(ready, child)

    if len(ordered) != len(nodes):
        raise DependencyCycleError(cyclic_components(nodes, adjacency))
    return tuple(ordered)


def cyclic_components(
    nodes: tuple[NodeKey, ...],
    adjacency: Mapping[NodeKey, tuple[NodeKey, ...]],
) -> tuple[tuple[NodeKey, ...], ...]:
    """Return stable non-trivial or self-loop strongly connected components."""
    return tuple(
        component
        for component in strongly_connected_components(nodes, adjacency)
        if len(component) > 1
        or component[0] in adjacency.get(component[0], ())
    )
