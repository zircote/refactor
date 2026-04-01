"""Tests for scripts/run_tests.py — test execution and output parsing."""

from __future__ import annotations

import pytest

from scripts.exceptions import UnsupportedLanguageError
from scripts.run_tests import (
    _parse_go_output,
    _parse_python_output,
    _parse_rust_output,
    _parse_typescript_output,
    run_tests,
)

# --- Output Parsers ---


class TestParseRustOutput:
    def test_passing(self, sample_output):
        result = _parse_rust_output(sample_output("rust", "passing"))
        assert result["passed"] == 5
        assert result["failed"] == 0

    def test_failing(self, sample_output):
        result = _parse_rust_output(sample_output("rust", "failing"))
        assert result["passed"] == 2
        assert result["failed"] == 1

    def test_no_match(self):
        result = _parse_rust_output("no test output here")
        assert result == {"passed": 0, "failed": 0, "errors": 0}


class TestParsePythonOutput:
    def test_passing(self, sample_output):
        result = _parse_python_output(sample_output("python", "passing"))
        assert result["passed"] == 10
        assert result["failed"] == 0

    def test_failing(self, sample_output):
        result = _parse_python_output(sample_output("python", "failing"))
        assert result["passed"] == 5
        assert result["failed"] == 2
        assert result["errors"] == 1

    def test_no_match(self):
        result = _parse_python_output("")
        assert result == {"passed": 0, "failed": 0, "errors": 0}


class TestParseTypescriptOutput:
    def test_passing(self, sample_output):
        result = _parse_typescript_output(sample_output("typescript", "passing"))
        assert result["passed"] == 3
        assert result["failed"] == 0

    def test_vitest_prefers_tests_line_over_test_files(self):
        """Regression: parser must read the 'Tests' summary, not 'Test Files'.

        Vitest emits two lines: 'Test Files  1 passed' and 'Tests  42 passed'.
        A naive first-match regex returns 1 instead of 42.
        """
        output = (
            " ✓ tests/api.test.ts (42)\n"
            "\n"
            " Test Files  1 passed (1)\n"
            "      Tests  42 passed (42)\n"
            "   Start at  10:30:15\n"
            "   Duration  2.34s\n"
        )
        result = _parse_typescript_output(output)
        assert result["passed"] == 42
        assert result["failed"] == 0

    def test_vitest_mixed_pass_fail(self):
        """Tests line with both passed and failed counts."""
        output = " Test Files  2 passed | 1 failed (3)\n      Tests  15 passed | 3 failed (18)\n"
        result = _parse_typescript_output(output)
        assert result["passed"] == 15
        assert result["failed"] == 3

    def test_no_tests_line_falls_back_to_first_match(self):
        """If no 'Tests' summary line exists, fall back to generic regex."""
        output = "5 passed, 2 failed\n"
        result = _parse_typescript_output(output)
        assert result["passed"] == 5
        assert result["failed"] == 2


class TestParseGoOutput:
    def test_passing(self, sample_output):
        result = _parse_go_output(sample_output("go", "passing"))
        assert result["passed"] == 3
        assert result["failed"] == 0

    def test_fallback_to_ok_lines(self):
        output = "ok  \tmyproject\t0.003s\n"
        result = _parse_go_output(output)
        assert result["passed"] == 1
        assert result["failed"] == 0


# --- run_tests ---


class TestRunTests:
    def test_unsupported_language_raises(self):
        with pytest.raises(UnsupportedLanguageError, match="unsupported language: fortran"):
            run_tests("/tmp", "fortran")

    def test_another_unsupported_language_raises(self):
        with pytest.raises(UnsupportedLanguageError):
            run_tests("/tmp", "cobol")

    def test_python_runs_pytest(self, tmp_path):
        # This will likely fail (no tests to find) but should not raise SubprocessError
        # It should return a result dict with exit_code != 0
        result = run_tests(str(tmp_path), "python")
        assert "exit_code" in result
        assert "output" in result
        assert isinstance(result["passed"], int)
