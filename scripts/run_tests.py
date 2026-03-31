"""Test execution for multi-language projects.

Runs language-appropriate test commands via subprocess and parses
the output into a structured result dict.
"""

from __future__ import annotations

import re
from typing import TYPE_CHECKING

from .audit import log_operation
from .exceptions import UnsupportedLanguageError
from .languages import get_config
from .utils import run_subprocess

if TYPE_CHECKING:
    from collections.abc import Callable

    from .types import TestCounts, TestResult


def _parse_regex_counts(output: str, patterns: dict[str, str]) -> TestCounts:
    """Parse test counts from output using per-field regex patterns.

    Generic extraction helper that eliminates duplication between
    language parsers sharing the same "N passed / N failed" format.

    Args:
        output: Combined stdout+stderr from the test command.
        patterns: Mapping of field name to regex with a single capture group.

    Returns:
        TestCounts with parsed values (0 for unmatched fields).
    """
    counts: dict[str, int] = {}
    for field_name, pattern in patterns.items():
        match = re.search(pattern, output)
        counts[field_name] = int(match.group(1)) if match else 0
    return {
        "passed": counts.get("passed", 0),
        "failed": counts.get("failed", 0),
        "errors": counts.get("errors", 0),
    }


# Shared regex patterns for pytest-style and vitest-style output
_PYTHON_PATTERNS: dict[str, str] = {
    "passed": r"(\d+)\s+passed",
    "failed": r"(\d+)\s+failed",
    "errors": r"(\d+)\s+error",
}

_TYPESCRIPT_PATTERNS: dict[str, str] = {
    "passed": r"(\d+)\s+passed",
    "failed": r"(\d+)\s+failed",
}


def _parse_rust_output(output: str) -> TestCounts:
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


def _parse_python_output(output: str) -> TestCounts:
    """Parse pytest summary line: 'X passed, Y failed, Z error'."""
    return _parse_regex_counts(output, _PYTHON_PATTERNS)


def _parse_typescript_output(output: str) -> TestCounts:
    """Parse vitest summary: 'Tests  X passed | Y failed'."""
    return _parse_regex_counts(output, _TYPESCRIPT_PATTERNS)


def _parse_go_output(output: str) -> TestCounts:
    """Parse go test output: count PASS/FAIL/--- FAIL lines."""
    passed = len(re.findall(r"^---\s+PASS:", output, re.MULTILINE))
    failed = len(re.findall(r"^---\s+FAIL:", output, re.MULTILINE))
    # Also count top-level ok/FAIL lines if no individual test lines found
    if passed == 0 and failed == 0:
        passed = len(re.findall(r"^ok\s+", output, re.MULTILINE))
        failed = len(re.findall(r"^FAIL\s+", output, re.MULTILINE))
    return {"passed": passed, "failed": failed, "errors": 0}


_PARSERS: dict[str, Callable[[str], TestCounts]] = {
    "rust": _parse_rust_output,
    "python": _parse_python_output,
    "typescript": _parse_typescript_output,
    "go": _parse_go_output,
}


def run_tests(path: str, lang: str) -> TestResult:
    """Execute language-appropriate test command and parse results.

    Args:
        path: Filesystem path to the project root.
        lang: Language identifier (rust, python, typescript, go).

    Returns:
        TestResult with keys: passed, failed, errors, output, exit_code.

    Raises:
        UnsupportedLanguageError: If the language is not supported.
        SubprocessError: If the test command cannot be found or times out.
    """
    config = get_config(lang)
    if config is None:
        raise UnsupportedLanguageError(lang)

    cmd = config.test_command
    result = run_subprocess(cmd, cwd=path, timeout=300)

    combined_output = result.stdout + result.stderr
    parser = _PARSERS.get(lang)
    counts = parser(combined_output) if parser else {"passed": 0, "failed": 0, "errors": 0}

    test_result: TestResult = {
        "passed": counts["passed"],
        "failed": counts["failed"],
        "errors": counts["errors"],
        "output": combined_output,
        "exit_code": result.returncode,
    }

    log_operation(
        action="test_run",
        resource=f"{path} ({lang})",
        result="success" if result.returncode == 0 else "failure",
        details={
            "passed": counts["passed"],
            "failed": counts["failed"],
            "errors": counts["errors"],
        },
    )

    return test_result
