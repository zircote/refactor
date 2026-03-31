"""Protocol definitions for domain boundaries.

Defines structural interfaces (PEP 544) between the plugin's layers:
- Command execution (subprocess I/O)
- Output parsing (text -> structured data)
- Coverage analysis (raw data -> normalized report)

Using Protocol enables structural subtyping -- implementations don't need
to inherit or register, they just need to match the signature.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from .types import CoverageData, CoverageResult, ProjectInfo, TestCounts, TestResult


class TestRunner(Protocol):
    """Execute tests for a given project and language."""

    def __call__(self, path: str, lang: str) -> TestResult:
        """Run tests and return results with passed/failed/errors/output/exit_code."""
        ...


class OutputParser(Protocol):
    """Parse raw test output into structured counts."""

    def __call__(self, output: str) -> TestCounts:
        """Parse output and return dict with passed, failed, errors keys."""
        ...


class CoverageAnalyzer(Protocol):
    """Execute coverage analysis for a given project and language."""

    def __call__(self, path: str, lang: str) -> CoverageResult:
        """Run coverage tool and return output/exit_code/coverage dict."""
        ...


class CoverageParser(Protocol):
    """Parse raw coverage output into a normalized report."""

    def __call__(self, output: str, lang: str) -> CoverageData:
        """Parse coverage data and return normalized dict."""
        ...


class ProjectDetector(Protocol):
    """Detect project language and test framework."""

    def __call__(self, path: str) -> ProjectInfo:
        """Detect project info and return language/framework/path dict."""
        ...
