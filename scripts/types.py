"""Typed return value definitions for the refactor scripts package.

Provides TypedDict definitions for structured return types, replacing
untyped dict[str, Any] returns with self-documenting, statically-checkable
types. Zero runtime cost -- typing annotations only.
"""

from __future__ import annotations

from typing import TypedDict


class TestCounts(TypedDict):
    """Parsed test count results from output parsing."""

    passed: int
    failed: int
    errors: int


class TestResult(TypedDict):
    """Full test execution result."""

    passed: int
    failed: int
    errors: int
    output: str
    exit_code: int


class FrameworkInfo(TypedDict):
    """Test framework information for a language."""

    test_runner: str
    coverage_tool: str
    property_lib: str


class UncoveredFile(TypedDict):
    """A file with uncovered lines."""

    file: str
    uncovered_lines: list[int]


class CoverageData(TypedDict):
    """Normalized coverage data."""

    total_lines: int
    covered_lines: int
    coverage_pct: float
    uncovered_files: list[UncoveredFile]


class CoverageResult(TypedDict):
    """Full coverage execution result."""

    output: str
    exit_code: int
    coverage: CoverageData


class ProjectInfo(TypedDict):
    """Full project detection result."""

    path: str
    language: str
    framework: FrameworkInfo
    source_dirs: list[str]
    test_dirs: list[str]
    existing_tests: list[str]
