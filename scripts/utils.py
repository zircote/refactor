"""Shared utilities for the test-architect scripts package.

Provides project root discovery, JSON parsing, and result formatting.
"""

from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Any

from .exceptions import SubprocessError
from .languages import LANGUAGES

# Derive root markers from the language registry to stay in sync.
# Flattened and deduplicated, preserving registry priority order.
_ROOT_MARKERS: tuple[str, ...] = tuple(
    dict.fromkeys(marker for config in LANGUAGES.values() for marker in config.markers)
)


def find_project_root(start_path: str) -> str:
    """Walk up directories from start_path to find the project root.

    The project root is the first ancestor directory containing one of:
    Cargo.toml, pyproject.toml, package.json, or go.mod.

    Args:
        start_path: Starting filesystem path (file or directory).

    Returns:
        Absolute path string to the project root, or the filesystem
        root if no marker is found.
    """
    current = Path(start_path).resolve()
    if current.is_file():
        current = current.parent

    while True:
        for marker in _ROOT_MARKERS:
            if (current / marker).exists():
                return str(current)
        parent = current.parent
        if parent == current:
            # Reached filesystem root without finding a marker
            return str(current)
        current = parent


def run_subprocess(
    cmd: list[str],
    cwd: str,
    timeout: int,
    *,
    output_so_far: str = "",
) -> subprocess.CompletedProcess[str]:
    """Execute a subprocess with standardized error handling.

    Wraps subprocess.run with consistent conversion of FileNotFoundError
    and TimeoutExpired into SubprocessError.

    Args:
        cmd: Command and arguments to execute.
        cwd: Working directory for the command.
        timeout: Maximum execution time in seconds.
        output_so_far: Any output accumulated from prior steps (included
            in the SubprocessError for multi-step command pipelines).

    Returns:
        The completed process result.

    Raises:
        SubprocessError: If the command is not found or times out.
    """
    try:
        return subprocess.run(
            cmd,
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
    except FileNotFoundError as exc:
        raise SubprocessError(
            f"command not found: {exc}",
            command=" ".join(cmd),
            exit_code=-1,
            output=output_so_far,
        ) from exc
    except subprocess.TimeoutExpired as exc:
        raise SubprocessError(
            f"execution timed out after {timeout}s",
            command=" ".join(cmd),
            exit_code=-1,
            output=output_so_far,
        ) from exc


def _extract_balanced_json(output: str, open_char: str, close_char: str) -> dict[str, Any] | None:
    """Find and parse the first balanced JSON block delimited by open/close chars."""
    start = output.find(open_char)
    if start == -1:
        return None
    depth = 0
    for i in range(start, len(output)):
        if output[i] == open_char:
            depth += 1
        elif output[i] == close_char:
            depth -= 1
            if depth == 0:
                try:
                    result: dict[str, Any] = json.loads(output[start : i + 1])
                    return result
                except json.JSONDecodeError:
                    return None
    return None


def parse_json_output(output: str) -> dict[str, Any] | None:
    """Safely parse JSON from command output that may contain mixed text.

    Tries the full output first, then searches for the first { ... }
    or [ ... ] JSON block within the text.

    Args:
        output: Raw command output string, potentially mixed text+JSON.

    Returns:
        Parsed dict/list or None if no valid JSON found.
    """
    output = output.strip()
    if not output:
        return None

    # Try parsing the entire output as JSON
    try:
        parsed: dict[str, Any] = json.loads(output)
        return parsed
    except json.JSONDecodeError:
        pass

    # Try to find JSON object, then JSON array
    # Use `is not None` to avoid falsy empty dict/list being skipped
    result = _extract_balanced_json(output, "{", "}")
    if result is not None:
        return result
    return _extract_balanced_json(output, "[", "]")


def _format_test_results(results: dict[str, Any]) -> list[str]:
    """Format test execution results."""
    lines = [
        "Test Results:",
        f"  Passed:  {results['passed']}",
        f"  Failed:  {results['failed']}",
        f"  Errors:  {results.get('errors', 0)}",
    ]
    if "exit_code" in results:
        status = "SUCCESS" if results["exit_code"] == 0 else "FAILURE"
        lines.append(f"  Status:  {status} (exit code {results['exit_code']})")
    return lines


def _format_coverage_results(results: dict[str, Any]) -> list[str]:
    """Format coverage report results."""
    lines = [
        "Coverage Report:",
        f"  Total lines:   {results.get('total_lines', 'N/A')}",
        f"  Covered lines: {results.get('covered_lines', 'N/A')}",
        f"  Coverage:      {results['coverage_pct']}%",
    ]
    uncovered = results.get("uncovered_files", [])
    if uncovered:
        lines.append(f"  Uncovered files ({len(uncovered)}):")
        for entry in uncovered[:10]:
            file_name = entry.get("file", "unknown")
            count = len(entry.get("uncovered_lines", []))
            lines.append(f"    - {file_name} ({count} uncovered lines)")
        if len(uncovered) > 10:
            lines.append(f"    ... and {len(uncovered) - 10} more")
    return lines


def _format_project_results(results: dict[str, Any]) -> list[str]:
    """Format project detection results."""
    fw = results["framework"]
    tests = results.get("existing_tests", [])
    return [
        "Project Detection:",
        f"  Path:     {results.get('path', 'N/A')}",
        f"  Language: {results['language']}",
        f"  Runner:   {fw.get('test_runner', 'N/A')}",
        f"  Coverage: {fw.get('coverage_tool', 'N/A')}",
        f"  Property: {fw.get('property_lib', 'N/A')}",
        f"  Existing tests: {len(tests)}",
    ]


_FORMATTERS: dict[str, Any] = {
    "test": _format_test_results,
    "coverage": _format_coverage_results,
    "project": _format_project_results,
}


def format_results(results: dict[str, Any], result_type: str | None = None) -> str:
    """Format a results dict as a human-readable summary.

    When result_type is provided, dispatches directly to the matching
    formatter. When None, falls back to key-sniffing for backward
    compatibility.

    Args:
        results: Dict to format.
        result_type: Optional explicit type — "test", "coverage", or "project".

    Returns:
        Multi-line human-readable string.
    """
    lines: list[str] = []

    if result_type is not None:
        formatter = _FORMATTERS.get(result_type)
        if formatter:
            if "error" in results:
                lines.append(f"Error: {results['error']}")
            lines.extend(formatter(results))
            return "\n".join(lines)

    # Fallback: key-sniffing dispatch for backward compatibility
    if "error" in results:
        lines.append(f"Error: {results['error']}")
    if "passed" in results and "failed" in results:
        lines.extend(_format_test_results(results))
    if "coverage_pct" in results:
        lines.extend(_format_coverage_results(results))
    if "language" in results and "framework" in results:
        lines.extend(_format_project_results(results))
    if not lines:
        lines.extend(f"  {key}: {value}" for key, value in results.items())

    return "\n".join(lines)
