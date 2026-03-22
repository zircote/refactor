"""test-architect scripts package.

Core detection, test execution, coverage analysis, and utilities
for multi-language test architecture.
"""

from .audit import log_operation
from .coverage_report import parse_coverage, run_coverage
from .detect_project import detect_language, detect_project, detect_test_framework
from .exceptions import (
    CoverageParseError,
    ProjectDetectionError,
    RefactorError,
    SubprocessError,
    UnsupportedLanguageError,
)
from .run_tests import run_tests
from .utils import find_project_root, format_results, parse_json_output

__all__ = [
    "log_operation",
    "detect_language",
    "detect_test_framework",
    "detect_project",
    "run_tests",
    "run_coverage",
    "parse_coverage",
    "find_project_root",
    "parse_json_output",
    "format_results",
    "RefactorError",
    "SubprocessError",
    "UnsupportedLanguageError",
    "CoverageParseError",
    "ProjectDetectionError",
]
