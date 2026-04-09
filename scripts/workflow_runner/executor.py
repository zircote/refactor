"""DAG-based workflow executor.

Executes workflow nodes in topological order, running independent
nodes within each layer sequentially (parallel execution is left
to the caller or a future async layer). Supports dry-run mode,
retry policies, and checkpoint-based resume.
"""

from __future__ import annotations

import shutil
import subprocess
import time
from collections.abc import Callable
from typing import TYPE_CHECKING

from .checkpoint import CheckpointStore
from .types import StepState, StepStatus, TriggerRule

if TYPE_CHECKING:
    from .dag import WorkflowDAG

if TYPE_CHECKING:
    from .types import NodeDefinition


StepCallback = Callable[[StepState], None]


def _default_timeout(node: NodeDefinition) -> int:
    """Return timeout in ms, defaulting to 120_000 (2 minutes)."""
    return node.get("timeout_ms", 120_000)


def _get_trigger_rule(node: NodeDefinition) -> TriggerRule:
    """Parse trigger rule from node definition."""
    raw = node.get("trigger_rule", "all_success")
    try:
        return TriggerRule(raw)
    except ValueError:
        return TriggerRule.ALL_SUCCESS


def _should_run(
    node: NodeDefinition,
    dep_states: dict[str, StepState],
) -> bool:
    """Determine if a node should run based on its trigger rule and dependency states."""
    deps = node.get("depends_on", [])
    if not deps:
        return True

    rule = _get_trigger_rule(node)
    states = [dep_states[d] for d in deps if d in dep_states]

    if rule == TriggerRule.ALL_SUCCESS:
        return all(s.status == StepStatus.COMPLETED for s in states)
    if rule == TriggerRule.ALL_DONE:
        done = (StepStatus.COMPLETED, StepStatus.FAILED, StepStatus.SKIPPED)
        return all(s.status in done for s in states)
    if rule == TriggerRule.ONE_SUCCESS:
        return any(s.status == StepStatus.COMPLETED for s in states)

    return False  # pragma: no cover


def _resolve_bash() -> str:
    """Resolve the absolute path to bash."""
    path = shutil.which("bash")
    if path is None:
        return "/bin/bash"
    return path


def _execute_bash_step(command: str, timeout_ms: int) -> tuple[str, int]:
    """Run a bash command and return (output, exit_code)."""
    timeout_s = timeout_ms / 1000.0
    bash = _resolve_bash()
    try:
        result = subprocess.run(
            [bash, "-c", command],
            capture_output=True,
            text=True,
            timeout=timeout_s,
        )
        output = result.stdout + result.stderr
        return output.strip(), result.returncode
    except subprocess.TimeoutExpired:
        return "", -1


class WorkflowExecutor:
    """Execute a workflow DAG with checkpointing and retry support.

    Parameters
    ----------
    dag
        The workflow DAG to execute.
    store
        Checkpoint store for persistence. Defaults to in-memory.
    dry_run
        If True, mark all steps as completed without executing.
    on_step_complete
        Optional callback invoked after each step finishes.
    """

    def __init__(
        self,
        dag: WorkflowDAG,
        *,
        store: CheckpointStore | None = None,
        dry_run: bool = False,
        on_step_complete: StepCallback | None = None,
    ) -> None:
        self._dag = dag
        self._store = store or CheckpointStore()
        self._dry_run = dry_run
        self._on_step_complete = on_step_complete
        self._step_states: dict[str, StepState] = {}

    def run(self, *, resume_run_id: str | None = None) -> dict[str, StepState]:
        """Execute the workflow and return final step states.

        Parameters
        ----------
        resume_run_id
            If provided, resume from this run's checkpoint state.

        Returns
        -------
        dict[str, StepState]
            Final state of every step.
        """
        if resume_run_id:
            run_id = resume_run_id
            self._step_states = self._store.load_steps(run_id)
        else:
            run_id = self._store.create_run(self._dag._workflow_name)
            for node_id in self._dag.node_ids:
                self._step_states[node_id] = StepState(step_id=node_id)

        for layer in self._dag.get_layers():
            for node_id in layer:
                state = self._step_states[node_id]

                # Skip already completed steps (resume case)
                if state.status == StepStatus.COMPLETED:
                    continue

                node = self._dag.get_node(node_id)

                if not _should_run(node, self._step_states):
                    state.status = StepStatus.SKIPPED
                    state.error = "dependency not met"
                    self._store.save_step(run_id, state)
                    if self._on_step_complete:
                        self._on_step_complete(state)
                    continue

                self._execute_step(run_id, node, state)

        self._store.mark_completed(run_id)
        return self._step_states

    def _execute_step(
        self,
        run_id: str,
        node: NodeDefinition,
        state: StepState,
    ) -> None:
        """Execute a single step with retry support."""
        retry = node.get("retry", {})
        max_attempts = retry.get("max_attempts", 1)
        delay_ms = retry.get("delay_ms", 0)
        timeout_ms = _default_timeout(node)

        for attempt in range(1, max_attempts + 1):
            state.status = StepStatus.RUNNING
            state.attempt = attempt
            self._store.save_step(run_id, state)

            if self._dry_run:
                state.status = StepStatus.COMPLETED
                state.output = "[dry-run] skipped"
                state.exit_code = 0
                state.duration_ms = 0
                self._store.save_step(run_id, state)
                if self._on_step_complete:
                    self._on_step_complete(state)
                return

            bash_cmd = node.get("bash", "")
            if not bash_cmd:
                # Skill-type nodes are marked completed (execution is external)
                state.status = StepStatus.COMPLETED
                state.output = f"[skill] {node.get('skill', 'unknown')}"
                state.exit_code = 0
                self._store.save_step(run_id, state)
                if self._on_step_complete:
                    self._on_step_complete(state)
                return

            start = time.monotonic()
            output, exit_code = _execute_bash_step(bash_cmd, timeout_ms)
            elapsed_ms = int((time.monotonic() - start) * 1000)

            state.output = output
            state.exit_code = exit_code
            state.duration_ms = elapsed_ms

            if exit_code == -1:
                state.status = StepStatus.FAILED
                state.error = f"timeout after {timeout_ms}ms"
                self._store.save_step(run_id, state)

                if attempt < max_attempts:
                    time.sleep(delay_ms / 1000.0)
                    continue

                if self._on_step_complete:
                    self._on_step_complete(state)
                return

            if exit_code == 0:
                state.status = StepStatus.COMPLETED
                state.error = ""
                self._store.save_step(run_id, state)
                if self._on_step_complete:
                    self._on_step_complete(state)
                return

            # Non-zero exit code
            state.status = StepStatus.FAILED
            state.error = f"exit code {exit_code}"
            self._store.save_step(run_id, state)

            if attempt < max_attempts:
                time.sleep(delay_ms / 1000.0)
                continue

            if self._on_step_complete:
                self._on_step_complete(state)
