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
from .languages import LANGUAGES, LanguageConfig, get_config
from .protocols import (
    CoverageAnalyzer,
    CoverageParser,
    OutputParser,
    ProjectDetector,
    TestRunner,
)
from .run_tests import run_tests
from .types import (
    CoverageData,
    CoverageResult,
    FrameworkInfo,
    ProjectInfo,
    TestCounts,
    TestResult,
    UncoveredFile,
)
from .utils import find_project_root, format_results, parse_json_output, run_subprocess

__all__ = [
    # Protocols
    "TestRunner",
    "OutputParser",
    "CoverageAnalyzer",
    "CoverageParser",
    "ProjectDetector",
    # TypedDicts
    "TestCounts",
    "TestResult",
    "FrameworkInfo",
    "CoverageData",
    "CoverageResult",
    "ProjectInfo",
    "UncoveredFile",
    # Language registry
    "LanguageConfig",
    "LANGUAGES",
    "get_config",
    # Functions
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
    "run_subprocess",
    # Exceptions
    "RefactorError",
    "SubprocessError",
    "UnsupportedLanguageError",
    "CoverageParseError",
    "ProjectDetectionError",
]
