"""Project detection logic for multi-language test architecture.

Detects project language, test framework, and directory structure
by inspecting project manifest files and conventions.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any


# Priority order: Rust > Python > TypeScript > Go
_LANGUAGE_MARKERS: list[tuple[str, list[str]]] = [
    ("rust", ["Cargo.toml"]),
    ("python", ["pyproject.toml"]),
    ("typescript", ["package.json", "tsconfig.json"]),
    ("go", ["go.mod"]),
]

_FRAMEWORK_MAP: dict[str, dict[str, str]] = {
    "rust": {
        "test_runner": "cargo test",
        "coverage_tool": "cargo-tarpaulin",
        "property_lib": "proptest",
    },
    "python": {
        "test_runner": "pytest",
        "coverage_tool": "coverage.py",
        "property_lib": "hypothesis",
    },
    "typescript": {
        "test_runner": "vitest",
        "coverage_tool": "c8",
        "property_lib": "fast-check",
    },
    "go": {
        "test_runner": "go test",
        "coverage_tool": "go tool cover",
        "property_lib": "rapid",
    },
}

# Conventional source and test directory names per language
_SOURCE_DIRS: dict[str, list[str]] = {
    "rust": ["src"],
    "python": ["src", "lib"],
    "typescript": ["src", "lib"],
    "go": ["."],
}

_TEST_DIRS: dict[str, list[str]] = {
    "rust": ["tests"],
    "python": ["tests", "test"],
    "typescript": ["tests", "test", "__tests__"],
    "go": ["."],
}

# Common test file glob patterns per language
_TEST_PATTERNS: dict[str, list[str]] = {
    "rust": ["**/tests/**/*.rs", "**/src/**/*_test.rs", "**/*_tests.rs"],
    "python": ["**/test_*.py", "**/*_test.py", "**/tests/**/*.py"],
    "typescript": ["**/*.test.ts", "**/*.spec.ts", "**/*.test.tsx", "**/*.spec.tsx"],
    "go": ["**/*_test.go"],
}


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

    for lang, markers in _LANGUAGE_MARKERS:
        if all((root / marker).exists() for marker in markers):
            return lang

    return None


def detect_test_framework(path: str, lang: str) -> dict[str, str]:
    """Map a detected language to its test runner, coverage tool, and property lib.

    Args:
        path: Filesystem path to the project root (reserved for future use).
        lang: Language identifier from detect_language().

    Returns:
        Dict with keys: test_runner, coverage_tool, property_lib.
        Returns an error dict if the language is unsupported.
    """
    framework = _FRAMEWORK_MAP.get(lang)
    if framework is None:
        return {
            "error": f"unsupported language: {lang}",
            "test_runner": "",
            "coverage_tool": "",
            "property_lib": "",
        }
    return dict(framework)


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
    test_files: list[str] = []
    for pattern in patterns:
        test_files.extend(str(p.relative_to(root)) for p in root.glob(pattern))
    # Deduplicate while preserving order
    seen: set[str] = set()
    unique: list[str] = []
    for f in sorted(test_files):
        if f not in seen:
            seen.add(f)
            unique.append(f)
    return unique


def detect_project(path: str) -> dict[str, Any]:
    """Full project detection: language, framework, directories, and existing tests.

    Args:
        path: Filesystem path to the project root.

    Returns:
        JSON-serializable dict with keys: path, language, framework,
        source_dirs, test_dirs, existing_tests. Returns an error dict
        if the path is invalid or no language is detected.
    """
    root = Path(path).resolve()
    if not root.is_dir():
        return {"error": f"not a directory: {path}", "path": str(root)}

    lang = detect_language(str(root))
    if lang is None:
        return {
            "path": str(root),
            "language": None,
            "error": "no supported language detected",
        }

    framework = detect_test_framework(str(root), lang)
    source_dirs = _find_existing_dirs(root, _SOURCE_DIRS.get(lang, []))
    test_dirs = _find_existing_dirs(root, _TEST_DIRS.get(lang, []))
    existing_tests = _find_existing_tests(root, _TEST_PATTERNS.get(lang, []))

    return {
        "path": str(root),
        "language": lang,
        "framework": framework,
        "source_dirs": source_dirs,
        "test_dirs": test_dirs,
        "existing_tests": existing_tests,
    }
