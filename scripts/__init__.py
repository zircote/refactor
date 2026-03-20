"""test-architect scripts package.

Core detection, test execution, coverage analysis, and utilities
for multi-language test architecture.
"""

from .detect_project import detect_language, detect_test_framework, detect_project
from .run_tests import run_tests
from .coverage_report import run_coverage, parse_coverage
from .utils import find_project_root, parse_json_output, format_results

__all__ = [
    "detect_language",
    "detect_test_framework",
    "detect_project",
    "run_tests",
    "run_coverage",
    "parse_coverage",
    "find_project_root",
    "parse_json_output",
    "format_results",
]
