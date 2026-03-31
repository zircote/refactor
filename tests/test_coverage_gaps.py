"""Tests to close coverage gaps in core modules.

Targets:
- coverage_report.py: run_coverage subprocess paths, _read_coverage_file error handling,
  _normalize_coverage TS dispatch, normalizer branch/loop edges
- detect_project.py: Go "." dir case, _find_existing_tests dedup
- run_tests.py: TS failing output, FileNotFoundError/TimeoutExpired in run_tests
- utils.py: find_project_root from file, unbalanced JSON, missing exit_code branch
"""

from __future__ import annotations

import json
import subprocess
from unittest.mock import patch

import pytest

from scripts.coverage_report import (
    _normalize_coverage,
    _normalize_python_coverage,
    _normalize_rust_coverage,
    _normalize_typescript_coverage,
    _read_coverage_file,
    run_coverage,
)
from scripts.detect_project import (
    _find_existing_dirs,
    _find_existing_tests,
    detect_project,
)
from scripts.exceptions import SubprocessError
from scripts.run_tests import _parse_typescript_output, run_tests
from scripts.utils import find_project_root, format_results

# ============================================================
# coverage_report.py gaps
# ============================================================


class TestRunCoverageSubprocess:
    """Cover run_coverage() subprocess execution paths (lines 46-104)."""

    def test_successful_single_step_with_json_file(self, tmp_path, monkeypatch):
        """Run coverage for rust (single command) with a JSON file present."""
        monkeypatch.setenv("REFACTOR_AUDIT_LOG", str(tmp_path / "audit.log"))

        # Create a tarpaulin JSON report
        report = {"files": [{"path": "src/lib.rs", "coverable": 20, "covered": 18, "traces": []}]}
        (tmp_path / "tarpaulin-report.json").write_text(json.dumps(report))

        # Mock subprocess.run to simulate a successful cargo tarpaulin run
        fake_result = subprocess.CompletedProcess(
            args=["cargo", "tarpaulin", "--out", "json"],
            returncode=0,
            stdout="running tests...\n",
            stderr="",
        )
        with patch("scripts.utils.subprocess.run", return_value=fake_result):
            result = run_coverage(str(tmp_path), "rust")

        assert result["exit_code"] == 0
        assert result["coverage"]["total_lines"] == 20
        assert result["coverage"]["covered_lines"] == 18

    def test_multi_step_python_aborts_on_first_failure(self, tmp_path, monkeypatch):
        """Python coverage has 2 steps; abort early if step 1 fails."""
        monkeypatch.setenv("REFACTOR_AUDIT_LOG", str(tmp_path / "audit.log"))

        fake_result = subprocess.CompletedProcess(
            args=["python", "-m", "coverage", "run", "-m", "pytest"],
            returncode=1,
            stdout="ERROR: no tests found\n",
            stderr="",
        )
        with (
            patch("scripts.utils.subprocess.run", return_value=fake_result),
            pytest.raises(SubprocessError, match="command failed"),
        ):
            run_coverage(str(tmp_path), "python")

    def test_file_not_found_raises_subprocess_error(self, tmp_path, monkeypatch):
        """FileNotFoundError when command binary is missing."""
        monkeypatch.setenv("REFACTOR_AUDIT_LOG", str(tmp_path / "audit.log"))

        with (
            patch(
                "scripts.utils.subprocess.run",
                side_effect=FileNotFoundError("cargo"),
            ),
            pytest.raises(SubprocessError, match="command not found"),
        ):
            run_coverage(str(tmp_path), "rust")

    def test_timeout_raises_subprocess_error(self, tmp_path, monkeypatch):
        """TimeoutExpired when coverage takes too long."""
        monkeypatch.setenv("REFACTOR_AUDIT_LOG", str(tmp_path / "audit.log"))

        with (
            patch(
                "scripts.utils.subprocess.run",
                side_effect=subprocess.TimeoutExpired(cmd="cargo tarpaulin", timeout=600),
            ),
            pytest.raises(SubprocessError, match="timed out"),
        ):
            run_coverage(str(tmp_path), "rust")

    def test_fallback_to_parse_coverage_when_no_json_file(self, tmp_path, monkeypatch):
        """When no coverage JSON file exists, parse from output."""
        monkeypatch.setenv("REFACTOR_AUDIT_LOG", str(tmp_path / "audit.log"))

        fake_result = subprocess.CompletedProcess(
            args=["go", "test", "-coverprofile=coverage.out", "./..."],
            returncode=0,
            stdout="ok\tmyproject\t0.5s\ncoverage: 72.3% of statements\n",
            stderr="",
        )
        with patch("scripts.utils.subprocess.run", return_value=fake_result):
            result = run_coverage(str(tmp_path), "go")

        assert result["exit_code"] == 0
        assert result["coverage"]["coverage_pct"] == 72.3

    def test_nonzero_exit_single_step_still_returns_result(self, tmp_path, monkeypatch):
        """Single-step command with nonzero exit still returns (doesn't abort)."""
        monkeypatch.setenv("REFACTOR_AUDIT_LOG", str(tmp_path / "audit.log"))

        fake_result = subprocess.CompletedProcess(
            args=["go", "test", "-coverprofile=coverage.out", "./..."],
            returncode=1,
            stdout="--- FAIL: TestFoo\ncoverage: 50.0% of statements\n",
            stderr="",
        )
        with patch("scripts.utils.subprocess.run", return_value=fake_result):
            result = run_coverage(str(tmp_path), "go")

        assert result["exit_code"] == 1
        assert result["coverage"]["coverage_pct"] == 50.0


class TestReadCoverageFileErrors:
    """Cover _read_coverage_file error paths (lines 124-125)."""

    def test_invalid_json_file_skipped(self, tmp_path):
        """JSONDecodeError in coverage file is caught and returns None."""
        (tmp_path / "coverage.json").write_text("not valid json {{{")
        result = _read_coverage_file(str(tmp_path), "python")
        assert result is None

    def test_key_error_in_normalization_skipped(self, tmp_path):
        """KeyError during normalization is caught and continues."""
        (tmp_path / "coverage.json").write_text('{"totals": {}, "files": {}}')
        with patch(
            "scripts.coverage_report._normalize_coverage",
            side_effect=KeyError("missing_key"),
        ):
            result = _read_coverage_file(str(tmp_path), "python")
        assert result is None

    def test_go_has_no_json_candidates(self, tmp_path):
        """Go has empty candidates list, so always returns None."""
        result = _read_coverage_file(str(tmp_path), "go")
        assert result is None

    def test_reads_typescript_coverage_file(self, tmp_path):
        """TypeScript coverage JSON from c8/istanbul."""
        cov_dir = tmp_path / "coverage"
        cov_dir.mkdir()
        data = {
            "src/index.ts": {
                "statementMap": {"0": {}, "1": {}},
                "s": {"0": 1, "1": 0},
            }
        }
        (cov_dir / "coverage-final.json").write_text(json.dumps(data))
        result = _read_coverage_file(str(tmp_path), "typescript")
        assert result is not None
        assert result["total_lines"] == 2
        assert result["covered_lines"] == 1


class TestNormalizeCoverageDispatch:
    """Cover _normalize_coverage TS dispatch (line 137)."""

    def test_dispatch_to_typescript(self):
        data = {
            "src/app.ts": {
                "statementMap": {"0": {}},
                "s": {"0": 1},
            }
        }
        result = _normalize_coverage(data, "typescript")
        assert result["total_lines"] == 1
        assert result["covered_lines"] == 1

    def test_dispatch_to_rust(self):
        data = {"files": [{"path": "src/lib.rs", "coverable": 5, "covered": 5, "traces": []}]}
        result = _normalize_coverage(data, "rust")
        assert result["coverage_pct"] == 100.0


class TestNormalizerEdgeCases:
    """Cover branch edges in normalizer loops."""

    def test_rust_all_covered(self):
        data = {
            "files": [
                {"path": "src/main.rs", "coverable": 5, "covered": 5, "traces": []},
            ]
        }
        result = _normalize_rust_coverage(data)
        assert result["coverage_pct"] == 100.0
        assert result["uncovered_files"] == []

    def test_rust_zero_lines(self):
        data = {"files": []}
        result = _normalize_rust_coverage(data)
        assert result["coverage_pct"] == 0.0
        assert result["total_lines"] == 0

    def test_python_no_missing_files(self):
        data = {
            "totals": {"num_statements": 50, "missing_lines": 0, "percent_covered": 100.0},
            "files": {"src/main.py": {"missing_lines": []}},
        }
        result = _normalize_python_coverage(data)
        assert result["uncovered_files"] == []
        assert result["covered_lines"] == 50

    def test_typescript_all_covered(self):
        data = {
            "src/app.ts": {
                "statementMap": {"0": {}, "1": {}},
                "s": {"0": 1, "1": 1},
            }
        }
        result = _normalize_typescript_coverage(data)
        assert result["coverage_pct"] == 100.0
        assert result["uncovered_files"] == []

    def test_typescript_zero_statements(self):
        result = _normalize_typescript_coverage({})
        assert result["coverage_pct"] == 0.0
        assert result["total_lines"] == 0


# ============================================================
# detect_project.py gaps
# ============================================================


class TestFindExistingDirs:
    """Cover _find_existing_dirs with Go '.' case (line 115)."""

    def test_dot_dir_for_go(self, tmp_path):
        """Go uses '.' as source/test dir — the root itself."""
        result = _find_existing_dirs(tmp_path, ["."])
        assert "." in result

    def test_mixed_existing_and_missing(self, tmp_path):
        (tmp_path / "src").mkdir()
        result = _find_existing_dirs(tmp_path, ["src", "lib", "pkg"])
        assert result == ["src"]

    def test_empty_candidates(self, tmp_path):
        result = _find_existing_dirs(tmp_path, [])
        assert result == []


class TestFindExistingTests:
    """Cover _find_existing_tests dedup logic (lines 128-130)."""

    def test_deduplicates_test_files(self, tmp_path):
        """Test files matched by multiple patterns are deduplicated."""
        tests_dir = tmp_path / "tests"
        tests_dir.mkdir()
        (tests_dir / "test_main.py").write_text("")
        (tests_dir / "__init__.py").write_text("")

        # Python patterns: test_*.py matches AND tests/**/*.py matches test_main.py
        result = _find_existing_tests(tmp_path, ["**/test_*.py", "**/tests/**/*.py"])
        # test_main.py should appear only once despite matching both patterns
        assert result.count("tests/test_main.py") == 1

    def test_sorted_output(self, tmp_path):
        tests_dir = tmp_path / "tests"
        tests_dir.mkdir()
        (tests_dir / "test_z.py").write_text("")
        (tests_dir / "test_a.py").write_text("")
        result = _find_existing_tests(tmp_path, ["**/test_*.py"])
        assert result == ["tests/test_a.py", "tests/test_z.py"]

    def test_no_matches(self, tmp_path):
        result = _find_existing_tests(tmp_path, ["**/*.rs"])
        assert result == []


class TestDetectProjectGo:
    """Cover Go project detection paths."""

    def test_go_project_has_dot_dirs(self, tmp_project):
        project = tmp_project("go")
        result = detect_project(str(project))
        assert result["language"] == "go"
        # Go uses "." as source dir
        assert "." in result["source_dirs"]
        assert "." in result["test_dirs"]


# ============================================================
# run_tests.py gaps
# ============================================================


class TestParseTypescriptFailingOutput:
    """Cover TS parser with failing output (line 63)."""

    def test_failing_output(self, sample_output):
        result = _parse_typescript_output(sample_output("typescript", "failing"))
        assert result["passed"] >= 1
        assert result["failed"] == 1

    def test_no_match(self):
        result = _parse_typescript_output("no test output")
        assert result == {"passed": 0, "failed": 0, "errors": 0}


class TestRunTestsExceptions:
    """Cover FileNotFoundError and TimeoutExpired in run_tests (lines 109-114)."""

    def test_file_not_found_raises_subprocess_error(self, tmp_path, monkeypatch):
        monkeypatch.setenv("REFACTOR_AUDIT_LOG", str(tmp_path / "audit.log"))
        with (
            patch(
                "scripts.utils.subprocess.run",
                side_effect=FileNotFoundError("cargo"),
            ),
            pytest.raises(SubprocessError, match="command not found"),
        ):
            run_tests(str(tmp_path), "rust")

    def test_timeout_raises_subprocess_error(self, tmp_path, monkeypatch):
        monkeypatch.setenv("REFACTOR_AUDIT_LOG", str(tmp_path / "audit.log"))
        with (
            patch(
                "scripts.utils.subprocess.run",
                side_effect=subprocess.TimeoutExpired(cmd="cargo test", timeout=300),
            ),
            pytest.raises(SubprocessError, match="timed out"),
        ):
            run_tests(str(tmp_path), "rust")


# ============================================================
# utils.py gaps
# ============================================================


class TestExtractBalancedJsonInvalidContent:
    """Cover _extract_balanced_json with balanced braces but invalid JSON."""

    def test_balanced_braces_but_invalid_json(self):
        from scripts.utils import _extract_balanced_json

        # Braces are balanced but content is not valid JSON
        result = _extract_balanced_json("{not: valid, json}", "{", "}")
        assert result is None

    def test_balanced_brackets_but_invalid_json(self):
        from scripts.utils import _extract_balanced_json

        result = _extract_balanced_json("[not valid json]", "[", "]")
        assert result is None


class TestFindProjectRootFromFile:
    """Cover find_project_root starting from a file path (line 31)."""

    def test_from_file_path(self, tmp_path):
        (tmp_path / "pyproject.toml").write_text("")
        test_file = tmp_path / "src" / "main.py"
        test_file.parent.mkdir()
        test_file.write_text("")
        result = find_project_root(str(test_file))
        assert result == str(tmp_path)


class TestFormatResultsMissingExitCode:
    """Cover _format_test_results branch when exit_code is absent (line 103->106)."""

    def test_test_results_without_exit_code(self):
        result = format_results({"passed": 5, "failed": 0, "errors": 0})
        assert "Test Results:" in result
        assert "Passed:  5" in result
        # No Status line when exit_code is missing
        assert "Status:" not in result

    def test_test_results_with_exit_code(self):
        result = format_results({"passed": 5, "failed": 0, "errors": 0, "exit_code": 0})
        assert "SUCCESS" in result
