"""Unified language configuration registry.

Consolidates all per-language dispatch tables from detect_project,
run_tests, and coverage_report into a single LanguageConfig dataclass.
Adding a new language requires a single entry here instead of
touching 3 modules and 7+ dictionaries.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class LanguageConfig:
    """All per-language configuration in one place."""

    name: str
    markers: list[str]
    test_runner: str
    coverage_tool: str
    property_lib: str
    source_dirs: list[str]
    test_dirs: list[str]
    test_patterns: list[str]
    test_command: list[str]
    coverage_commands: list[list[str]]
    coverage_files: list[str] = field(default_factory=list)


# Registry keyed by language name
LANGUAGES: dict[str, LanguageConfig] = {}

# Priority-ordered list for language detection (first match wins)
LANGUAGE_PRIORITY: list[str] = []


def _register(config: LanguageConfig) -> None:
    """Register a language config and append to priority list."""
    LANGUAGES[config.name] = config
    LANGUAGE_PRIORITY.append(config.name)


def get_config(lang: str) -> LanguageConfig | None:
    """Look up language configuration by name."""
    return LANGUAGES.get(lang)


# Register in priority order: Rust > Python > TypeScript > Go

_register(
    LanguageConfig(
        name="rust",
        markers=["Cargo.toml"],
        test_runner="cargo test",
        coverage_tool="cargo-tarpaulin",
        property_lib="proptest",
        source_dirs=["src"],
        test_dirs=["tests"],
        test_patterns=["**/tests/**/*.rs", "**/src/**/*_test.rs", "**/*_tests.rs"],
        test_command=["cargo", "test"],
        coverage_commands=[["cargo", "tarpaulin", "--out", "json"]],
        coverage_files=["tarpaulin-report.json"],
    )
)

_register(
    LanguageConfig(
        name="python",
        markers=["pyproject.toml"],
        test_runner="pytest",
        coverage_tool="coverage.py",
        property_lib="hypothesis",
        source_dirs=["src", "lib"],
        test_dirs=["tests", "test"],
        test_patterns=["**/test_*.py", "**/*_test.py", "**/tests/**/*.py"],
        test_command=["python", "-m", "pytest", "-v"],
        coverage_commands=[
            ["python", "-m", "coverage", "run", "-m", "pytest"],
            ["python", "-m", "coverage", "json"],
        ],
        coverage_files=["coverage.json"],
    )
)

_register(
    LanguageConfig(
        name="typescript",
        markers=["package.json", "tsconfig.json"],
        test_runner="vitest",
        coverage_tool="c8",
        property_lib="fast-check",
        source_dirs=["src", "lib"],
        test_dirs=["tests", "test", "__tests__"],
        test_patterns=["**/*.test.ts", "**/*.spec.ts", "**/*.test.tsx", "**/*.spec.tsx"],
        test_command=["npx", "vitest", "run"],
        coverage_commands=[["npx", "c8", "--reporter=json", "vitest", "run"]],
        coverage_files=["coverage/coverage-final.json"],
    )
)

_register(
    LanguageConfig(
        name="go",
        markers=["go.mod"],
        test_runner="go test",
        coverage_tool="go tool cover",
        property_lib="rapid",
        source_dirs=["."],
        test_dirs=["."],
        test_patterns=["**/*_test.go"],
        test_command=["go", "test", "-v", "./..."],
        coverage_commands=[["go", "test", "-coverprofile=coverage.out", "./..."]],
    )
)
