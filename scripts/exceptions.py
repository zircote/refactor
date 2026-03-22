"""Custom exception hierarchy for the refactor scripts."""

from __future__ import annotations


class RefactorError(Exception):
    """Base exception for all refactor script errors.

    All subclasses carry structured context via ``error_code`` and
    ``details`` so that callers can programmatically inspect failures
    without parsing message strings.
    """

    def __init__(
        self,
        message: str,
        *,
        error_code: str = "",
        details: dict[str, object] | None = None,
    ) -> None:
        super().__init__(message)
        self.error_code = error_code
        self.details = details or {}


class SubprocessError(RefactorError):
    """A subprocess call failed or could not be found."""

    def __init__(self, message: str, command: str = "", exit_code: int = -1, output: str = ""):
        super().__init__(
            message,
            error_code="SUBPROCESS_FAILED",
            details={"command": command, "exit_code": exit_code},
        )
        self.command = command
        self.exit_code = exit_code
        self.output = output


class UnsupportedLanguageError(RefactorError):
    """The detected or requested language is not supported."""

    def __init__(self, language: str):
        super().__init__(
            f"unsupported language: {language}",
            error_code="UNSUPPORTED_LANGUAGE",
            details={"language": language},
        )
        self.language = language


class CoverageParseError(RefactorError):
    """Coverage tool output could not be parsed."""

    def __init__(self, message: str, raw_output: str = ""):
        super().__init__(
            message,
            error_code="COVERAGE_PARSE_FAILED",
            details={"raw_output_length": len(raw_output)},
        )
        self.raw_output = raw_output


class ProjectDetectionError(RefactorError):
    """Project root or language could not be determined."""

    def __init__(self, message: str, path: str = ""):
        super().__init__(
            message,
            error_code="PROJECT_DETECTION_FAILED",
            details={"path": path},
        )
        self.path = path
