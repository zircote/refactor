"""Project detection logic for multi-language test architecture.

Detects project language, test framework, and directory structure
by inspecting project manifest files and conventions.
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from .exceptions import ProjectDetectionError, UnsupportedLanguageError
from .languages import LANGUAGE_PRIORITY, LANGUAGES, get_config

if TYPE_CHECKING:
    from .types import FrameworkInfo, ProjectInfo


def detect_language(path: str) -> str | None:
    """Detect the primary project language from manifest files.

    Checks for language-specific manifest files in priority order:
    Rust > Python > TypeScript > Go.

    Args:
        path: Filesystem path to the project root.

    Returns:
        Language identifier string or None if no language detected.
    """
    root = Path(path)
    if not root.is_dir():
        return None

    for lang_name in LANGUAGE_PRIORITY:
        config = LANGUAGES[lang_name]
        if all((root / marker).exists() for marker in config.markers):
            return lang_name

    return None


def detect_test_framework(lang_or_path: str, lang: str | None = None) -> FrameworkInfo:
    """Map a detected language to its test runner, coverage tool, and property lib.

    Supports two call forms for backward compatibility:
        detect_test_framework(lang)            — current API
        detect_test_framework(path, lang)      — deprecated, path is ignored

    Args:
        lang_or_path: Language identifier, or a filesystem path (deprecated).
        lang: Language identifier when first arg is a path (deprecated form).

    Returns:
        Dict with keys: test_runner, coverage_tool, property_lib.

    Raises:
        UnsupportedLanguageError: If the language is not in the registry.
    """
    # Backward-compat shim: if called as detect_test_framework(path, lang),
    # the second argument is the actual language; ignore the path.
    effective_lang = lang if lang is not None else lang_or_path

    config = get_config(effective_lang)
    if config is None:
        raise UnsupportedLanguageError(effective_lang)
    return {
        "test_runner": config.test_runner,
        "coverage_tool": config.coverage_tool,
        "property_lib": config.property_lib,
    }


def _find_existing_dirs(root: Path, candidates: list[str]) -> list[str]:
    """Return candidate directory names that actually exist under root."""
    found = []
    for name in candidates:
        candidate = root / name if name != "." else root
        if candidate.is_dir():
            found.append(name)
    return found


def _find_existing_tests(root: Path, patterns: list[str]) -> list[str]:
    """Glob for test files matching language-specific patterns."""
    test_files: set[str] = set()
    for pattern in patterns:
        test_files.update(str(p.relative_to(root)) for p in root.glob(pattern))
    return sorted(test_files)


def detect_project(path: str) -> ProjectInfo:
    """Full project detection: language, framework, directories, and existing tests.

    Args:
        path: Filesystem path to the project root.

    Returns:
        ProjectInfo dict with keys: path, language, framework,
        source_dirs, test_dirs, existing_tests.

    Raises:
        ProjectDetectionError: If the path is invalid or no language is detected.
    """
    root = Path(path).resolve()
    if not root.is_dir():
        raise ProjectDetectionError(f"not a directory: {path}", path=str(root))

    lang = detect_language(str(root))
    if lang is None:
        raise ProjectDetectionError("no supported language detected", path=str(root))

    config = LANGUAGES[lang]
    framework = detect_test_framework(lang)
    source_dirs = _find_existing_dirs(root, config.source_dirs)
    test_dirs = _find_existing_dirs(root, config.test_dirs)
    existing_tests = _find_existing_tests(root, config.test_patterns)

    return {
        "path": str(root),
        "language": lang,
        "framework": framework,
        "source_dirs": source_dirs,
        "test_dirs": test_dirs,
        "existing_tests": existing_tests,
    }
