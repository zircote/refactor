"""Typed definitions for workflow runner structures.

Provides TypedDict and enum definitions for workflow nodes, execution
state, and checkpoint records. Zero runtime cost for TypedDicts.
"""

from __future__ import annotations

import enum
from dataclasses import dataclass, field
from typing import TypedDict


class StepStatus(enum.Enum):
    """Execution status of a workflow step."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


class TriggerRule(enum.Enum):
    """When a step should be triggered based on its dependencies."""

    ALL_SUCCESS = "all_success"
    ALL_DONE = "all_done"
    ONE_SUCCESS = "one_success"


class RetryConfig(TypedDict, total=False):
    """Retry configuration for a step."""

    max_attempts: int
    delay_ms: int


class NodeDefinition(TypedDict, total=False):
    """Raw node definition from a workflow YAML/JSON file."""

    node_id: str
    bash: str
    skill: str
    model: str
    max_turns: int
    denied_tools: list[str]
    depends_on: list[str]
    timeout_ms: int
    retry: RetryConfig
    trigger_rule: str


class WorkflowDefinition(TypedDict):
    """Top-level workflow file structure."""

    name: str
    nodes: list[NodeDefinition]


class StepResultDict(TypedDict, total=False):
    """Result of a single step execution."""

    step_id: str
    status: str
    output: str
    exit_code: int
    duration_ms: int
    attempt: int
    error: str


@dataclass
class StepState:
    """Runtime state of a single workflow step."""

    step_id: str
    status: StepStatus = StepStatus.PENDING
    output: str = ""
    exit_code: int = -1
    duration_ms: int = 0
    attempt: int = 0
    error: str = ""

    def to_dict(self) -> StepResultDict:
        """Convert to serializable dictionary."""
        return StepResultDict(
            step_id=self.step_id,
            status=self.status.value,
            output=self.output,
            exit_code=self.exit_code,
            duration_ms=self.duration_ms,
            attempt=self.attempt,
            error=self.error,
        )


@dataclass
class WorkflowState:
    """Full runtime state of a workflow execution."""

    workflow_name: str
    steps: dict[str, StepState] = field(default_factory=dict)
    completed: bool = False
    current_layer: int = 0
