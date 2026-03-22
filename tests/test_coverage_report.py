"""Tests for scripts/coverage_report.py — coverage execution and parsing."""

from __future__ import annotations

import pytest

from scripts.coverage_report import _parse_go_text_coverage, parse_coverage
from scripts.exceptions import CoverageParseError, UnsupportedLanguageError


class TestParseCoverage:
    def test_parse_rust_tarpaulin_json(self):
        import json

        data = {
            "files": [
                {
                    "path": "src/main.rs",
                    "coverable": 10,
                    "covered": 8,
                    "traces": [{"line": 5, "hits": 0}],
                }
            ]
        }
        output = json.dumps(data)
        result = parse_coverage(output, "rust")
        assert result is not None
        assert "coverage_pct" in result
        assert result["total_lines"] == 10
        assert result["covered_lines"] == 8

    def test_parse_python_coverage_json(self, sample_coverage_json):
        import json

        output = json.dumps(sample_coverage_json)
        result = parse_coverage(output, "python")
        assert result is not None
        assert result["coverage_pct"] == 80.0

    def test_parse_go_text_coverage(self):
        output = "PASS\ncoverage: 78.5% of statements\nok  \tmyproject\t0.004s"
        result = parse_coverage(output, "go")
        assert result is not None
        assert result["coverage_pct"] == 78.5

    def test_parse_unsupported_raises_coverage_parse_error(self):
        with pytest.raises(CoverageParseError, match="could not parse coverage output"):
            parse_coverage("some output", "fortran")

    def test_parse_empty_output_raises_coverage_parse_error(self):
        with pytest.raises(CoverageParseError, match="could not parse coverage output"):
            parse_coverage("", "python")


class TestParseGoTextCoverage:
    def test_parses_percentage(self):
        output = "coverage: 85.3% of statements"
        result = _parse_go_text_coverage(output)
        assert result["coverage_pct"] == 85.3

    def test_no_match_raises_coverage_parse_error(self):
        with pytest.raises(CoverageParseError, match="could not parse Go coverage output"):
            _parse_go_text_coverage("no coverage info here")

    def test_from_fixture(self, sample_output):
        result = _parse_go_text_coverage(sample_output("go", "coverage"))
        assert result["coverage_pct"] == 78.5


class TestNormalizeCoverage:
    def test_normalize_python_coverage(self):
        from scripts.coverage_report import _normalize_python_coverage

        data = {
            "totals": {"num_statements": 100, "missing_lines": 20, "percent_covered": 80.0},
            "files": {
                "src/main.py": {"missing_lines": [10, 20, 30]},
                "src/utils.py": {"missing_lines": []},
            },
        }
        result = _normalize_python_coverage(data)
        assert result["coverage_pct"] == 80.0
        assert result["total_lines"] == 100
        assert result["covered_lines"] == 80
        assert len(result["uncovered_files"]) == 1
        assert result["uncovered_files"][0]["file"] == "src/main.py"

    def test_normalize_rust_coverage(self):
        from scripts.coverage_report import _normalize_rust_coverage

        data = {
            "files": [
                {
                    "path": "src/main.rs",
                    "coverable": 10,
                    "covered": 8,
                    "traces": [
                        {"line": 5, "hits": 0},
                        {"line": 7, "hits": 1},
                    ],
                }
            ]
        }
        result = _normalize_rust_coverage(data)
        assert result["total_lines"] == 10
        assert result["covered_lines"] == 8
        assert result["coverage_pct"] == 80.0
        assert len(result["uncovered_files"]) == 1

    def test_normalize_typescript_coverage(self):
        from scripts.coverage_report import _normalize_typescript_coverage

        data = {
            "src/main.ts": {
                "statementMap": {"0": {}, "1": {}, "2": {}, "3": {}},
                "s": {"0": 1, "1": 1, "2": 0, "3": 1},
            }
        }
        result = _normalize_typescript_coverage(data)
        assert result["total_lines"] == 4
        assert result["covered_lines"] == 3
        assert result["coverage_pct"] == 75.0
        assert len(result["uncovered_files"]) == 1

    def test_normalize_coverage_dispatches_correctly(self):
        from scripts.coverage_report import _normalize_coverage

        data = {
            "totals": {
                "num_statements": 10,
                "missing_lines": 2,
                "percent_covered": 80.0,
            },
            "files": {},
        }
        result = _normalize_coverage(data, "python")
        assert result["coverage_pct"] == 80.0

    def test_normalize_coverage_unknown_lang_raises(self):
        from scripts.coverage_report import _normalize_coverage

        with pytest.raises(CoverageParseError, match="normalization not implemented"):
            _normalize_coverage({}, "fortran")


class TestReadCoverageFile:
    def test_returns_none_when_no_file(self, tmp_path):
        from scripts.coverage_report import _read_coverage_file

        result = _read_coverage_file(str(tmp_path), "rust")
        assert result is None

    def test_reads_python_coverage_json(self, tmp_path, sample_coverage_json):
        import json

        (tmp_path / "coverage.json").write_text(json.dumps(sample_coverage_json))
        from scripts.coverage_report import _read_coverage_file

        result = _read_coverage_file(str(tmp_path), "python")
        assert result is not None


class TestRunCoverage:
    def test_unsupported_language_raises(self):
        from scripts.coverage_report import run_coverage

        with pytest.raises(UnsupportedLanguageError, match="unsupported language: fortran"):
            run_coverage("/tmp", "fortran")
