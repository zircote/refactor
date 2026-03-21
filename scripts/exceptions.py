"""Custom exception hierarchy for the refactor scripts."""

from __future__ import annotations


class RefactorError(Exception):
    """Base exception for all refactor script errors."""


class SubprocessError(RefactorError):
    """A subprocess call failed or could not be found."""

    def __init__(self, message: str, command: str = "", exit_code: int = -1, output: str = ""):
        super().__init__(message)
        self.command = command
        self.exit_code = exit_code
        self.output = output


class UnsupportedLanguageError(RefactorError):
    """The detected or requested language is not supported."""

    def __init__(self, language: str):
        super().__init__(f"unsupported language: {language}")
        self.language = language


class CoverageParseError(RefactorError):
    """Coverage tool output could not be parsed."""

    def __init__(self, message: str, raw_output: str = ""):
        super().__init__(message)
        self.raw_output = raw_output


class ProjectDetectionError(RefactorError):
    """Project root or language could not be determined."""

    def __init__(self, message: str, path: str = ""):
        super().__init__(message)
        self.path = path
