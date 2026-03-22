"""Property-based tests for parser functions using Hypothesis."""

from __future__ import annotations

import json

from hypothesis import given, settings
from hypothesis import strategies as st

from scripts.coverage_report import _parse_go_text_coverage, parse_coverage
from scripts.detect_project import detect_language
from scripts.exceptions import CoverageParseError
from scripts.run_tests import (
    _parse_go_output,
    _parse_python_output,
    _parse_rust_output,
    _parse_typescript_output,
)
from scripts.utils import _extract_balanced_json, format_results, parse_json_output

# --- Property: parsers never raise unhandled exceptions on arbitrary input ---


class TestParseJsonOutputProperties:
    @given(st.text(max_size=500))
    @settings(max_examples=100)
    def test_never_crashes_on_arbitrary_text(self, text: str):
        # Should never raise — may return None, dict, list, or other JSON primitives
        result = parse_json_output(text)
        # json.loads can return float (NaN, Infinity), int, str, bool, None, dict, list
        assert result is None or isinstance(result, (dict, list, int, float, str, bool))

    @given(st.dictionaries(st.text(min_size=1, max_size=10), st.integers()))
    def test_roundtrips_valid_json_dicts(self, data: dict):
        output = json.dumps(data)
        result = parse_json_output(output)
        assert result == data

    @given(st.lists(st.integers(), max_size=20))
    def test_roundtrips_valid_json_arrays(self, data: list):
        output = json.dumps(data)
        result = parse_json_output(output)
        assert result == data

    @given(
        st.text(max_size=200),
        st.dictionaries(
            st.from_regex(r"[a-z]{1,5}", fullmatch=True),
            st.integers(),
        ),
    )
    def test_finds_embedded_json(self, prefix: str, data: dict):
        # Restrict keys to alphanumeric to avoid JSON structural chars in keys
        # which confuse the naive brace-depth extraction
        prefix = prefix.replace("{", "").replace("[", "")
        output = f"{prefix} {json.dumps(data)} suffix"
        result = parse_json_output(output)
        assert result == data


class TestExtractBalancedJsonProperties:
    @given(st.text(max_size=300))
    @settings(max_examples=100)
    def test_never_crashes_on_arbitrary_text(self, text: str):
        result = _extract_balanced_json(text, "{", "}")
        assert result is None or isinstance(result, (dict, list))

    @given(st.text(max_size=300))
    def test_never_crashes_with_brackets(self, text: str):
        result = _extract_balanced_json(text, "[", "]")
        assert result is None or isinstance(result, (dict, list))


# --- Property: test output parsers never crash ---


class TestOutputParserProperties:
    @given(st.text(max_size=500))
    @settings(max_examples=50)
    def test_rust_parser_never_crashes(self, text: str):
        result = _parse_rust_output(text)
        assert isinstance(result, dict)
        assert "passed" in result
        assert "failed" in result
        assert isinstance(result["passed"], int)
        assert isinstance(result["failed"], int)
        assert result["passed"] >= 0
        assert result["failed"] >= 0

    @given(st.text(max_size=500))
    @settings(max_examples=50)
    def test_python_parser_never_crashes(self, text: str):
        result = _parse_python_output(text)
        assert isinstance(result, dict)
        assert result["passed"] >= 0
        assert result["failed"] >= 0

    @given(st.text(max_size=500))
    @settings(max_examples=50)
    def test_typescript_parser_never_crashes(self, text: str):
        result = _parse_typescript_output(text)
        assert isinstance(result, dict)
        assert result["passed"] >= 0

    @given(st.text(max_size=500))
    @settings(max_examples=50)
    def test_go_parser_never_crashes(self, text: str):
        result = _parse_go_output(text)
        assert isinstance(result, dict)
        assert result["passed"] >= 0


# --- Property: detect_language never crashes on any path ---


class TestDetectLanguageProperties:
    @given(st.text(min_size=1, max_size=100))
    @settings(max_examples=30)
    def test_never_crashes_on_arbitrary_path(self, path: str):
        result = detect_language(path)
        assert result is None or isinstance(result, str)


# --- Property: format_results always returns a string ---


class TestFormatResultsProperties:
    @given(st.dictionaries(st.text(min_size=1, max_size=10), st.text(max_size=50), max_size=5))
    @settings(max_examples=50)
    def test_always_returns_string(self, data: dict):
        result = format_results(data)
        assert isinstance(result, str)


# --- Property: go text coverage parser never crashes ---


class TestGoTextCoverageProperties:
    @given(st.text(max_size=300))
    @settings(max_examples=50)
    def test_returns_dict_or_raises_parse_error(self, text: str):
        try:
            result = _parse_go_text_coverage(text)
            assert isinstance(result, dict)
            assert "coverage_pct" in result
            assert isinstance(result["coverage_pct"], float)
            assert result["coverage_pct"] >= 0.0
        except CoverageParseError:
            pass  # Expected for unparseable input


# --- Property: parse_coverage never crashes ---


class TestParseCoverageProperties:
    @given(
        st.text(max_size=300),
        st.sampled_from(["rust", "python", "typescript", "go", "unknown", ""]),
    )
    @settings(max_examples=50)
    def test_returns_dict_or_raises_parse_error(self, output: str, lang: str):
        try:
            result = parse_coverage(output, lang)
            assert result is None or isinstance(result, dict)
        except CoverageParseError:
            pass  # Expected for unparseable input
