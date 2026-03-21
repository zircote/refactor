"""Tests for scripts/utils.py — JSON parsing, result formatting, project root discovery."""

from __future__ import annotations

import json
from pathlib import Path

from scripts.utils import (
    _extract_balanced_json,
    find_project_root,
    format_results,
    parse_json_output,
)

# --- parse_json_output ---


class TestParseJsonOutput:
    def test_valid_json_object(self):
        result = parse_json_output('{"key": "value"}')
        assert result == {"key": "value"}

    def test_valid_json_array(self):
        result = parse_json_output("[1, 2, 3]")
        assert result == [1, 2, 3]

    def test_empty_string(self):
        assert parse_json_output("") is None

    def test_whitespace_only(self):
        assert parse_json_output("   \n  ") is None

    def test_json_embedded_in_text(self):
        output = 'some text before {"result": 42} some text after'
        result = parse_json_output(output)
        assert result == {"result": 42}

    def test_json_array_embedded_in_text(self):
        output = "prefix [1, 2, 3] suffix"
        result = parse_json_output(output)
        assert result == [1, 2, 3]

    def test_nested_json(self):
        nested = {"outer": {"inner": [1, 2, {"deep": True}]}}
        output = f"log output\n{json.dumps(nested)}\nmore log"
        result = parse_json_output(output)
        assert result == nested

    def test_invalid_json_returns_none(self):
        assert parse_json_output("not json at all") is None

    def test_malformed_json_returns_none(self):
        assert parse_json_output('{"key": "value"') is None

    def test_prefers_full_parse_over_extraction(self):
        full_json = '{"a": 1}'
        result = parse_json_output(full_json)
        assert result == {"a": 1}


# --- _extract_balanced_json ---


class TestExtractBalancedJson:
    def test_extracts_object(self):
        result = _extract_balanced_json('text {"a": 1} more', "{", "}")
        assert result == {"a": 1}

    def test_extracts_array(self):
        result = _extract_balanced_json("text [1, 2] more", "[", "]")
        assert result == [1, 2]

    def test_no_match_returns_none(self):
        assert _extract_balanced_json("no json here", "{", "}") is None

    def test_unbalanced_returns_none(self):
        assert _extract_balanced_json("{unclosed", "{", "}") is None

    def test_nested_braces(self):
        result = _extract_balanced_json('{"a": {"b": 1}}', "{", "}")
        assert result == {"a": {"b": 1}}


# --- format_results ---


class TestFormatResults:
    def test_error_format(self):
        result = format_results({"error": "something failed"})
        assert "Error: something failed" in result

    def test_test_results_format(self):
        result = format_results({"passed": 10, "failed": 2, "errors": 1, "exit_code": 1})
        assert "Test Results:" in result
        assert "Passed:  10" in result
        assert "Failed:  2" in result
        assert "FAILURE" in result

    def test_test_results_success(self):
        result = format_results({"passed": 5, "failed": 0, "errors": 0, "exit_code": 0})
        assert "SUCCESS" in result

    def test_coverage_format(self):
        result = format_results(
            {
                "coverage_pct": 85.5,
                "total_lines": 100,
                "covered_lines": 85,
                "uncovered_files": [],
            }
        )
        assert "Coverage Report:" in result
        assert "85.5%" in result

    def test_coverage_with_uncovered_files(self):
        result = format_results(
            {
                "coverage_pct": 70.0,
                "uncovered_files": [
                    {"file": "src/main.py", "uncovered_lines": [1, 2, 3]},
                ],
            }
        )
        assert "src/main.py" in result
        assert "3 uncovered lines" in result

    def test_project_detection_format(self):
        result = format_results(
            {
                "language": "rust",
                "framework": {
                    "test_runner": "cargo test",
                    "coverage_tool": "tarpaulin",
                    "property_lib": "proptest",
                },
                "existing_tests": ["test1.rs", "test2.rs"],
            }
        )
        assert "Project Detection:" in result
        assert "rust" in result
        assert "Existing tests: 2" in result

    def test_fallback_generic_format(self):
        result = format_results({"custom_key": "custom_value"})
        assert "custom_key: custom_value" in result

    def test_uncovered_files_truncated_at_10(self):
        files = [{"file": f"file{i}.py", "uncovered_lines": [1]} for i in range(15)]
        result = format_results({"coverage_pct": 50.0, "uncovered_files": files})
        assert "and 5 more" in result


# --- find_project_root ---


class TestFindProjectRoot:
    def test_finds_root_with_cargo_toml(self, tmp_path: Path):
        (tmp_path / "Cargo.toml").write_text("")
        sub = tmp_path / "src"
        sub.mkdir()
        result = find_project_root(str(sub))
        assert result == str(tmp_path)

    def test_finds_root_with_pyproject_toml(self, tmp_path: Path):
        (tmp_path / "pyproject.toml").write_text("")
        result = find_project_root(str(tmp_path))
        assert result == str(tmp_path)

    def test_finds_root_with_package_json(self, tmp_path: Path):
        (tmp_path / "package.json").write_text("")
        result = find_project_root(str(tmp_path))
        assert result == str(tmp_path)

    def test_returns_path_when_no_root_markers_found(self, tmp_path: Path):
        sub = tmp_path / "orphan"
        sub.mkdir()
        result = find_project_root(str(sub))
        # May return the input or walk up to a parent that has a marker file
        assert isinstance(result, str)
        assert len(result) > 0
