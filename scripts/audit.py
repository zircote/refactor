"""Structured audit logging for plugin operations.

Captures administrative and operational actions with actor, action,
resource, timestamp, and result for audit trail compliance (GOV-004).
"""

from __future__ import annotations

import getpass
import json
import logging
import os
import time
from pathlib import Path
from typing import Any

_AUDIT_LOG_ENV = "REFACTOR_AUDIT_LOG"
_DEFAULT_AUDIT_DIR = ".refactor"
_DEFAULT_AUDIT_FILE = "audit.log"

logger = logging.getLogger("refactor.audit")


def _get_audit_path() -> Path:
    """Resolve audit log file path from environment or default."""
    env_path = os.environ.get(_AUDIT_LOG_ENV)
    if env_path:
        return Path(env_path)
    return Path(_DEFAULT_AUDIT_DIR) / _DEFAULT_AUDIT_FILE


def _get_actor() -> str:
    """Get current actor identity."""
    return os.environ.get("USER", getpass.getuser())


def log_operation(
    action: str,
    resource: str,
    result: str,
    details: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Log a structured audit entry.

    Args:
        action: The operation performed (e.g., "test_run", "coverage_analysis").
        resource: The target resource (e.g., project path, language).
        result: Outcome — "success", "failure", or "error".
        details: Optional additional context.

    Returns:
        The audit entry dict that was logged.
    """
    entry: dict[str, Any] = {
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "actor": _get_actor(),
        "action": action,
        "resource": resource,
        "result": result,
    }
    if details:
        entry["details"] = details

    audit_path = _get_audit_path()
    try:
        audit_path.parent.mkdir(parents=True, exist_ok=True)
        with open(audit_path, "a") as f:
            f.write(json.dumps(entry, separators=(",", ":")) + "\n")
    except OSError as exc:
        logger.warning("Failed to write audit log to %s: %s", audit_path, exc)

    return entry
