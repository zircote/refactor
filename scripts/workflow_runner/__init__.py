"""Declarative workflow runner for the refactor plugin.

Provides DAG-based workflow execution with checkpoint persistence,
retry policies, and dry-run support. Workflow definitions are loaded
from YAML or JSON files.
"""

from __future__ import annotations

from .checkpoint import CheckpointStore
from .dag import WorkflowDAG
from .exceptions import (
    CyclicDependencyError,
    StepFailedError,
    StepTimeoutError,
    WorkflowError,
    WorkflowValidationError,
)
from .executor import WorkflowExecutor
from .loader import load_workflow
from .types import (
    NodeDefinition,
    StepResultDict,
    StepState,
    StepStatus,
    TriggerRule,
    WorkflowDefinition,
    WorkflowState,
)

__all__ = [
    # Core classes
    "WorkflowDAG",
    "WorkflowExecutor",
    "CheckpointStore",
    # Loader
    "load_workflow",
    # Types
    "NodeDefinition",
    "StepState",
    "StepStatus",
    "StepResultDict",
    "TriggerRule",
    "WorkflowDefinition",
    "WorkflowState",
    # Exceptions
    "WorkflowError",
    "CyclicDependencyError",
    "StepFailedError",
    "StepTimeoutError",
    "WorkflowValidationError",
]
