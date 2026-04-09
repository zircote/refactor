"""Workflow definition loader.

Loads workflow definitions from YAML or JSON files and validates
their basic structure before constructing a DAG.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .dag import WorkflowDAG
from .exceptions import WorkflowValidationError
from .types import NodeDefinition, WorkflowDefinition

try:
    import yaml

    _HAS_YAML = True
except ImportError:  # pragma: no cover
    _HAS_YAML = False


def _load_raw(path: Path) -> dict[str, Any]:
    """Load a file as a dictionary, supporting JSON and YAML."""
    content = path.read_text(encoding="utf-8")

    if path.suffix in (".yaml", ".yml"):
        if not _HAS_YAML:
            raise WorkflowValidationError(
                "pyyaml is required to load YAML workflow files; "
                "install it with: pip install pyyaml",
                workflow=str(path),
            )
        data = yaml.safe_load(content)
    elif path.suffix == ".json":
        data = json.loads(content)
    else:
        raise WorkflowValidationError(
            f"unsupported file extension: {path.suffix} (expected .yaml, .yml, or .json)",
            workflow=str(path),
        )

    if not isinstance(data, dict):
        raise WorkflowValidationError(
            "workflow file must contain a mapping at the top level",
            workflow=str(path),
        )
    return data


def _validate_structure(data: dict[str, Any], path: str) -> WorkflowDefinition:
    """Validate raw data against the expected workflow structure."""
    issues: list[str] = []

    name = data.get("name")
    if not isinstance(name, str) or not name:
        issues.append("missing or empty 'name' field")

    nodes_raw = data.get("nodes")
    if not isinstance(nodes_raw, list):
        issues.append("missing or non-list 'nodes' field")
        raise WorkflowValidationError(
            f"workflow structure invalid: {'; '.join(issues)}",
            workflow=path,
            issues=issues,
        )

    nodes: list[NodeDefinition] = []
    for i, node_raw in enumerate(nodes_raw):
        if not isinstance(node_raw, dict):
            issues.append(f"node at index {i} is not a mapping")
            continue
        node_id = node_raw.get("id")
        if not isinstance(node_id, str) or not node_id:
            issues.append(f"node at index {i} missing 'id' field")
            continue

        has_bash = "bash" in node_raw
        has_skill = "skill" in node_raw
        if not has_bash and not has_skill:
            issues.append(f"node '{node_id}' must have either 'bash' or 'skill'")

        # Build NodeDefinition with 'id' remapped to 'node_id'
        node_def = NodeDefinition(node_id=node_id)
        if "bash" in node_raw:
            node_def["bash"] = str(node_raw["bash"])
        if "skill" in node_raw:
            node_def["skill"] = str(node_raw["skill"])
        if "model" in node_raw:
            node_def["model"] = str(node_raw["model"])
        if "max_turns" in node_raw:
            node_def["max_turns"] = int(node_raw["max_turns"])
        if "denied_tools" in node_raw:
            node_def["denied_tools"] = list(node_raw["denied_tools"])
        if "depends_on" in node_raw:
            node_def["depends_on"] = list(node_raw["depends_on"])
        if "timeout_ms" in node_raw:
            node_def["timeout_ms"] = int(node_raw["timeout_ms"])
        if "retry" in node_raw:
            node_def["retry"] = node_raw["retry"]
        if "trigger_rule" in node_raw:
            node_def["trigger_rule"] = str(node_raw["trigger_rule"])
        if "when" in node_raw:
            node_def["when"] = str(node_raw["when"])
        nodes.append(node_def)

    if issues:
        raise WorkflowValidationError(
            f"workflow structure invalid: {'; '.join(issues)}",
            workflow=path,
            issues=issues,
        )

    return WorkflowDefinition(name=name or "", nodes=nodes)


def load_workflow(path: str | Path) -> WorkflowDAG:
    """Load a workflow file and return a validated DAG.

    Parameters
    ----------
    path
        Path to a ``.yaml``, ``.yml``, or ``.json`` workflow file.

    Returns
    -------
    WorkflowDAG
        A validated DAG ready for execution.

    Raises
    ------
    WorkflowValidationError
        If the file is malformed or fails structural checks.
    """
    file_path = Path(path)
    if not file_path.exists():
        raise WorkflowValidationError(
            f"workflow file not found: {file_path}",
            workflow=str(file_path),
        )

    raw = _load_raw(file_path)
    definition = _validate_structure(raw, str(file_path))
    return WorkflowDAG(definition["nodes"], workflow_name=definition["name"])
