"""Tests for scripts/exceptions.py — custom exception hierarchy."""

from __future__ import annotations

from scripts.exceptions import (
    CoverageParseError,
    ProjectDetectionError,
    RefactorError,
    SubprocessError,
    UnsupportedLanguageError,
)


class TestExceptionHierarchy:
    def test_all_inherit_from_refactor_error(self):
        assert issubclass(SubprocessError, RefactorError)
        assert issubclass(UnsupportedLanguageError, RefactorError)
        assert issubclass(CoverageParseError, RefactorError)
        assert issubclass(ProjectDetectionError, RefactorError)

    def test_refactor_error_inherits_from_exception(self):
        assert issubclass(RefactorError, Exception)


class TestRefactorErrorBase:
    def test_structured_context_defaults(self):
        err = RefactorError("base error")
        assert err.error_code == ""
        assert err.details == {}

    def test_structured_context_explicit(self):
        err = RefactorError("msg", error_code="TEST", details={"key": "val"})
        assert err.error_code == "TEST"
        assert err.details == {"key": "val"}


class TestSubprocessError:
    def test_stores_command_and_exit_code(self):
        err = SubprocessError("failed", command="cargo test", exit_code=1, output="error output")
        assert str(err) == "failed"
        assert err.command == "cargo test"
        assert err.exit_code == 1
        assert err.output == "error output"

    def test_defaults(self):
        err = SubprocessError("failed")
        assert err.command == ""
        assert err.exit_code == -1
        assert err.output == ""

    def test_has_structured_context(self):
        err = SubprocessError("failed", command="cargo test", exit_code=1)
        assert err.error_code == "SUBPROCESS_FAILED"
        assert err.details["command"] == "cargo test"
        assert err.details["exit_code"] == 1


class TestUnsupportedLanguageError:
    def test_stores_language(self):
        err = UnsupportedLanguageError("fortran")
        assert err.language == "fortran"
        assert "unsupported language: fortran" in str(err)

    def test_has_structured_context(self):
        err = UnsupportedLanguageError("fortran")
        assert err.error_code == "UNSUPPORTED_LANGUAGE"
        assert err.details["language"] == "fortran"


class TestCoverageParseError:
    def test_stores_raw_output(self):
        err = CoverageParseError("parse failed", raw_output="garbage data")
        assert err.raw_output == "garbage data"

    def test_has_structured_context(self):
        err = CoverageParseError("parse failed", raw_output="garbage data")
        assert err.error_code == "COVERAGE_PARSE_FAILED"
        assert err.details["raw_output_length"] == len("garbage data")


class TestProjectDetectionError:
    def test_stores_path(self):
        err = ProjectDetectionError("not found", path="/some/path")
        assert err.path == "/some/path"

    def test_has_structured_context(self):
        err = ProjectDetectionError("not found", path="/some/path")
        assert err.error_code == "PROJECT_DETECTION_FAILED"
        assert err.details["path"] == "/some/path"
