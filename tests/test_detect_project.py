"""Tests for scripts/detect_project.py — language and framework detection."""

from __future__ import annotations

from pathlib import Path

import pytest

from scripts.detect_project import detect_language, detect_project, detect_test_framework
from scripts.exceptions import ProjectDetectionError, UnsupportedLanguageError


class TestDetectLanguage:
    def test_detects_rust(self, tmp_project):
        project = tmp_project("rust")
        assert detect_language(str(project)) == "rust"

    def test_detects_python(self, tmp_project):
        project = tmp_project("python")
        assert detect_language(str(project)) == "python"

    def test_detects_typescript(self, tmp_project):
        project = tmp_project("typescript")
        assert detect_language(str(project)) == "typescript"

    def test_detects_go(self, tmp_project):
        project = tmp_project("go")
        assert detect_language(str(project)) == "go"

    def test_returns_none_for_unrecognized_project(self, tmp_path: Path):
        # A directory with only a pom.xml is not recognized (Java not in markers)
        (tmp_path / "pom.xml").write_text("")
        assert detect_language(str(tmp_path)) is None

    def test_returns_none_for_empty_dir(self, tmp_path: Path):
        assert detect_language(str(tmp_path)) is None

    def test_returns_none_for_nonexistent_dir(self):
        assert detect_language("/nonexistent/path") is None

    def test_priority_rust_over_python(self, tmp_path: Path):
        # Rust markers should take priority
        (tmp_path / "Cargo.toml").write_text("")
        (tmp_path / "pyproject.toml").write_text("")
        result = detect_language(str(tmp_path))
        assert result == "rust"


class TestDetectTestFramework:
    def test_rust_framework(self, tmp_path: Path):
        fw = detect_test_framework(str(tmp_path), "rust")
        assert fw["test_runner"] == "cargo test"
        assert fw["coverage_tool"] == "cargo-tarpaulin"

    def test_python_framework(self, tmp_path: Path):
        fw = detect_test_framework(str(tmp_path), "python")
        assert fw["test_runner"] == "pytest"

    def test_unknown_language_raises(self, tmp_path: Path):
        with pytest.raises(UnsupportedLanguageError, match="unsupported language: unknown"):
            detect_test_framework(str(tmp_path), "unknown")


class TestDetectProject:
    def test_full_detection_rust(self, tmp_project):
        project = tmp_project("rust")
        result = detect_project(str(project))
        assert result["language"] == "rust"
        assert "framework" in result
        assert result["framework"]["test_runner"] == "cargo test"

    def test_full_detection_unknown_raises(self, tmp_path: Path):
        with pytest.raises(ProjectDetectionError, match="no supported language detected"):
            detect_project(str(tmp_path))

    def test_nonexistent_path_raises(self):
        with pytest.raises(ProjectDetectionError, match="not a directory"):
            detect_project("/nonexistent/path/to/project")

    def test_result_has_expected_keys(self, tmp_project):
        project = tmp_project("python")
        result = detect_project(str(project))
        assert "language" in result
        assert "framework" in result
        assert "existing_tests" in result
        assert "path" in result
