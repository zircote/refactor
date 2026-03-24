"""Tests verifying Protocol structural subtyping compliance.

Ensures existing implementations satisfy Protocol interfaces
without requiring inheritance — pure structural matching.
"""

from __future__ import annotations

from scripts.coverage_report import parse_coverage, run_coverage  # noqa: TC001
from scripts.detect_project import detect_project  # noqa: TC001
from scripts.protocols import (  # noqa: TC001
    CoverageAnalyzer,
    CoverageParser,
    OutputParser,
    ProjectDetector,
    TestRunner,
)
from scripts.run_tests import (  # noqa: TC001
    _parse_go_output,
    _parse_python_output,
    _parse_rust_output,
    _parse_typescript_output,
    run_tests,
)


def test_run_tests_satisfies_test_runner() -> None:
    """run_tests matches the TestRunner protocol signature."""
    runner: TestRunner = run_tests
    assert callable(runner)


def test_parsers_satisfy_output_parser() -> None:
    """All language parsers match the OutputParser protocol."""
    parsers: list[OutputParser] = [
        _parse_rust_output,
        _parse_python_output,
        _parse_typescript_output,
        _parse_go_output,
    ]
    for parser in parsers:
        assert callable(parser)


def test_run_coverage_satisfies_coverage_analyzer() -> None:
    """run_coverage matches the CoverageAnalyzer protocol."""
    analyzer: CoverageAnalyzer = run_coverage
    assert callable(analyzer)


def test_parse_coverage_satisfies_coverage_parser() -> None:
    """parse_coverage matches the CoverageParser protocol."""
    parser: CoverageParser = parse_coverage
    assert callable(parser)


def test_detect_project_satisfies_project_detector() -> None:
    """detect_project matches the ProjectDetector protocol."""
    detector: ProjectDetector = detect_project
    assert callable(detector)


def _custom_runner(path: str, lang: str) -> dict[str, object]:
    return {
        "passed": 0,
        "failed": 0,
        "errors": 0,
        "output": "",
        "exit_code": 0,
    }


def test_protocol_structural_subtyping_with_function() -> None:
    """A plain function satisfying the signature matches the protocol."""
    runner: TestRunner = _custom_runner
    result = runner("/tmp", "python")
    assert result["passed"] == 0
