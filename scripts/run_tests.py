"""Test execution for multi-language projects.

Runs language-appropriate test commands via subprocess and parses
the output into a structured result dict.
"""

from __future__ import annotations

import re
import subprocess
from typing import Any


# Test commands per language
_TEST_COMMANDS: dict[str, list[str]] = {
    "rust": ["cargo", "test"],
    "python": ["python", "-m", "pytest", "-v"],
    "typescript": ["npx", "vitest", "run"],
    "go": ["go", "test", "-v", "./..."],
}


def _parse_rust_output(output: str) -> dict[str, int]:
    """Parse cargo test summary line: 'test result: ok. X passed; Y failed; Z ignored'."""
    match = re.search(
        r"test result:.*?(\d+)\s+passed.*?(\d+)\s+failed.*?(\d+)\s+ignored",
        output,
    )
    if match:
        return {
            "passed": int(match.group(1)),
            "failed": int(match.group(2)),
            "errors": 0,
        }
    return {"passed": 0, "failed": 0, "errors": 0}


def _parse_python_output(output: str) -> dict[str, int]:
    """Parse pytest summary line: 'X passed, Y failed, Z error'."""
    passed = failed = errors = 0
    match = re.search(r"(\d+)\s+passed", output)
    if match:
        passed = int(match.group(1))
    match = re.search(r"(\d+)\s+failed", output)
    if match:
        failed = int(match.group(1))
    match = re.search(r"(\d+)\s+error", output)
    if match:
        errors = int(match.group(1))
    return {"passed": passed, "failed": failed, "errors": errors}


def _parse_typescript_output(output: str) -> dict[str, int]:
    """Parse vitest summary: 'Tests  X passed | Y failed'."""
    passed = failed = errors = 0
    match = re.search(r"(\d+)\s+passed", output)
    if match:
        passed = int(match.group(1))
    match = re.search(r"(\d+)\s+failed", output)
    if match:
        failed = int(match.group(1))
    return {"passed": passed, "failed": failed, "errors": errors}


def _parse_go_output(output: str) -> dict[str, int]:
    """Parse go test output: count PASS/FAIL/--- FAIL lines."""
    passed = len(re.findall(r"^---\s+PASS:", output, re.MULTILINE))
    failed = len(re.findall(r"^---\s+FAIL:", output, re.MULTILINE))
    # Also count top-level ok/FAIL lines if no individual test lines found
    if passed == 0 and failed == 0:
        passed = len(re.findall(r"^ok\s+", output, re.MULTILINE))
        failed = len(re.findall(r"^FAIL\s+", output, re.MULTILINE))
    return {"passed": passed, "failed": failed, "errors": 0}


_PARSERS: dict[str, Any] = {
    "rust": _parse_rust_output,
    "python": _parse_python_output,
    "typescript": _parse_typescript_output,
    "go": _parse_go_output,
}


def run_tests(path: str, lang: str) -> dict[str, Any]:
    """Execute language-appropriate test command and parse results.

    Args:
        path: Filesystem path to the project root.
        lang: Language identifier (rust, python, typescript, go).

    Returns:
        Dict with keys: passed, failed, errors, output, exit_code.
        On execution failure, output contains the error message.
    """
    cmd = _TEST_COMMANDS.get(lang)
    if cmd is None:
        return {
            "passed": 0,
            "failed": 0,
            "errors": 0,
            "output": f"unsupported language: {lang}",
            "exit_code": -1,
        }

    try:
        result = subprocess.run(
            cmd,
            cwd=path,
            capture_output=True,
            text=True,
            timeout=300,
        )
    except FileNotFoundError as exc:
        return {
            "passed": 0,
            "failed": 0,
            "errors": 1,
            "output": f"command not found: {exc}",
            "exit_code": -1,
        }
    except subprocess.TimeoutExpired:
        return {
            "passed": 0,
            "failed": 0,
            "errors": 1,
            "output": "test execution timed out after 300s",
            "exit_code": -1,
        }

    combined_output = result.stdout + result.stderr
    parser = _PARSERS.get(lang)
    counts = (
        parser(combined_output) if parser else {"passed": 0, "failed": 0, "errors": 0}
    )

    return {
        **counts,
        "output": combined_output,
        "exit_code": result.returncode,
    }
