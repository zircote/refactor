"""DAG construction and topological sorting for workflow execution.

Uses graphlib.TopologicalSorter to build a dependency DAG from workflow
node definitions. Provides cycle detection and parallel group extraction
for concurrent execution of independent nodes.
"""

from __future__ import annotations

from graphlib import CycleError, TopologicalSorter
from typing import TYPE_CHECKING

from .exceptions import CyclicDependencyError, WorkflowValidationError

if TYPE_CHECKING:
    from .types import NodeDefinition


class WorkflowDAG:
    """Directed acyclic graph built from workflow node definitions.

    Wraps ``graphlib.TopologicalSorter`` to provide:
    - Cycle detection with clear error messages
    - Parallel layer extraction (groups of nodes that can run concurrently)
    - Dependency validation (no references to undefined nodes)
    """

    def __init__(self, nodes: list[NodeDefinition], *, workflow_name: str = "") -> None:
        self._nodes: dict[str, NodeDefinition] = {}
        self._workflow_name = workflow_name
        self._layers: list[list[str]] | None = None

        self._validate_and_build(nodes)

    def _validate_and_build(self, nodes: list[NodeDefinition]) -> None:
        """Validate node definitions and build the internal graph."""
        issues: list[str] = []
        seen_ids: set[str] = set()

        for node in nodes:
            node_id = node.get("node_id", "")
            if not node_id:
                issues.append("node missing required 'node_id' field")
                continue
            if node_id in seen_ids:
                issues.append(f"duplicate node id: '{node_id}'")
            seen_ids.add(node_id)
            self._nodes[node_id] = node

        # Check dependency references
        for node in nodes:
            node_id = node.get("node_id", "")
            for dep in node.get("depends_on", []):
                if dep not in seen_ids:
                    issues.append(f"node '{node_id}' depends on unknown node '{dep}'")

        if issues:
            raise WorkflowValidationError(
                f"workflow validation failed: {'; '.join(issues)}",
                workflow=self._workflow_name,
                issues=issues,
            )

    @property
    def node_ids(self) -> list[str]:
        """All node IDs in definition order."""
        return list(self._nodes.keys())

    def get_node(self, node_id: str) -> NodeDefinition:
        """Get node definition by ID."""
        return self._nodes[node_id]

    def get_layers(self) -> list[list[str]]:
        """Return nodes grouped into parallel execution layers.

        Each layer contains nodes whose dependencies are all satisfied
        by prior layers. Nodes within a layer can run concurrently.

        Raises ``CyclicDependencyError`` if the graph contains cycles.
        """
        if self._layers is not None:
            return self._layers

        sorter: TopologicalSorter[str] = TopologicalSorter()
        for node_id, node in self._nodes.items():
            deps = node.get("depends_on", [])
            sorter.add(node_id, *deps)

        try:
            sorter.prepare()
        except CycleError as exc:
            raise CyclicDependencyError(
                str(exc),
                workflow=self._workflow_name,
            ) from exc

        layers: list[list[str]] = []
        while sorter.is_active():
            ready = sorted(sorter.get_ready())  # sorted for determinism
            layers.append(ready)
            sorter.done(*ready)

        self._layers = layers
        return layers

    def topological_order(self) -> list[str]:
        """Return all node IDs in topological order (flattened layers)."""
        return [node_id for layer in self.get_layers() for node_id in layer]

    def __len__(self) -> int:
        return len(self._nodes)

    def __contains__(self, node_id: str) -> bool:
        return node_id in self._nodes
