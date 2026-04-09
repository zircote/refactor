"""Exception hierarchy for the workflow runner."""

from __future__ import annotations

from scripts.exceptions import RefactorError


class WorkflowError(RefactorError):
    """Base exception for workflow runner errors."""

    def __init__(self, message: str, *, workflow: str = "") -> None:
        super().__init__(
            message,
            error_code="WORKFLOW_ERROR",
            details={"workflow": workflow},
        )
        self.workflow = workflow


class CyclicDependencyError(WorkflowError):
    """Workflow DAG contains a cycle."""

    def __init__(self, message: str, *, workflow: str = "") -> None:
        super().__init__(message, workflow=workflow)
        self.error_code = "CYCLIC_DEPENDENCY"


class StepTimeoutError(WorkflowError):
    """A workflow step exceeded its timeout."""

    def __init__(self, step_id: str, timeout_ms: int, *, workflow: str = "") -> None:
        super().__init__(
            f"step '{step_id}' exceeded timeout of {timeout_ms}ms",
            workflow=workflow,
        )
        self.error_code = "STEP_TIMEOUT"
        self.details = {"step_id": step_id, "timeout_ms": timeout_ms, "workflow": workflow}
        self.step_id = step_id
        self.timeout_ms = timeout_ms


class StepFailedError(WorkflowError):
    """A workflow step failed execution."""

    def __init__(self, step_id: str, reason: str, *, workflow: str = "") -> None:
        super().__init__(
            f"step '{step_id}' failed: {reason}",
            workflow=workflow,
        )
        self.error_code = "STEP_FAILED"
        self.details = {"step_id": step_id, "reason": reason, "workflow": workflow}
        self.step_id = step_id
        self.reason = reason


class WorkflowValidationError(WorkflowError):
    """Workflow definition failed validation."""

    def __init__(
        self, message: str, *, workflow: str = "", issues: list[str] | None = None
    ) -> None:
        super().__init__(message, workflow=workflow)
        self.error_code = "WORKFLOW_VALIDATION"
        self.issues = issues or []
        self.details = {"workflow": workflow, "issues": self.issues}
