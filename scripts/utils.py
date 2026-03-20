"""Shared utilities for the test-architect scripts package.

Provides project root discovery, JSON parsing, and result formatting.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


# Manifest files that indicate a project root
_ROOT_MARKERS = ("Cargo.toml", "pyproject.toml", "package.json", "go.mod")


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
        return json.loads(output)
    except json.JSONDecodeError:
        pass

    # Try to find JSON object in the output
    start = output.find("{")
    if start != -1:
        depth = 0
        for i in range(start, len(output)):
            if output[i] == "{":
                depth += 1
            elif output[i] == "}":
                depth -= 1
                if depth == 0:
                    try:
                        return json.loads(output[start : i + 1])
                    except json.JSONDecodeError:
                        break

    # Try to find JSON array in the output
    start = output.find("[")
    if start != -1:
        depth = 0
        for i in range(start, len(output)):
            if output[i] == "[":
                depth += 1
            elif output[i] == "]":
                depth -= 1
                if depth == 0:
                    try:
                        return json.loads(output[start : i + 1])
                    except json.JSONDecodeError:
                        break

    return None


def format_results(results: dict[str, Any]) -> str:
    """Format a results dict as a human-readable summary.

    Handles both test results (passed/failed/errors) and coverage
    results (coverage_pct/uncovered_files). Falls back to a generic
    key-value format for other dicts.

    Args:
        results: Dict to format.

    Returns:
        Multi-line human-readable string.
    """
    lines: list[str] = []

    # Error case
    if "error" in results:
        lines.append(f"Error: {results['error']}")

    # Test results
    if "passed" in results and "failed" in results:
        lines.append("Test Results:")
        lines.append(f"  Passed:  {results['passed']}")
        lines.append(f"  Failed:  {results['failed']}")
        lines.append(f"  Errors:  {results.get('errors', 0)}")
        if "exit_code" in results:
            status = "SUCCESS" if results["exit_code"] == 0 else "FAILURE"
            lines.append(f"  Status:  {status} (exit code {results['exit_code']})")

    # Coverage results
    if "coverage_pct" in results:
        lines.append("Coverage Report:")
        lines.append(f"  Total lines:   {results.get('total_lines', 'N/A')}")
        lines.append(f"  Covered lines: {results.get('covered_lines', 'N/A')}")
        lines.append(f"  Coverage:      {results['coverage_pct']}%")
        uncovered = results.get("uncovered_files", [])
        if uncovered:
            lines.append(f"  Uncovered files ({len(uncovered)}):")
            for entry in uncovered[:10]:
                file_name = entry.get("file", "unknown")
                count = len(entry.get("uncovered_lines", []))
                lines.append(f"    - {file_name} ({count} uncovered lines)")
            if len(uncovered) > 10:
                lines.append(f"    ... and {len(uncovered) - 10} more")

    # Project detection results
    if "language" in results and "framework" in results:
        lines.append("Project Detection:")
        lines.append(f"  Path:     {results.get('path', 'N/A')}")
        lines.append(f"  Language: {results['language']}")
        fw = results["framework"]
        lines.append(f"  Runner:   {fw.get('test_runner', 'N/A')}")
        lines.append(f"  Coverage: {fw.get('coverage_tool', 'N/A')}")
        lines.append(f"  Property: {fw.get('property_lib', 'N/A')}")
        tests = results.get("existing_tests", [])
        lines.append(f"  Existing tests: {len(tests)}")

    # Fallback for unrecognized dicts
    if not lines:
        for key, value in results.items():
            lines.append(f"  {key}: {value}")

    return "\n".join(lines)
