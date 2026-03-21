"""Shared fixtures for refactor plugin tests."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

FIXTURES_DIR = Path(__file__).parent / "fixtures"


@pytest.fixture()
def fixtures_dir() -> Path:
    """Return the path to the test fixtures directory."""
    return FIXTURES_DIR


@pytest.fixture()
def sample_output(fixtures_dir: Path):
    """Factory fixture: returns test output content by language and variant."""

    def _factory(language: str, variant: str = "passing") -> str:
        path = fixtures_dir / f"{language}_{variant}.txt"
        return path.read_text()

    return _factory


@pytest.fixture()
def tmp_project(tmp_path: Path):
    """Factory fixture: creates a minimal project directory for a given language."""

    def _factory(language: str) -> Path:
        project = tmp_path / f"test-{language}-project"
        project.mkdir()
        markers: dict[str, list[str]] = {
            "rust": ["Cargo.toml"],
            "python": ["pyproject.toml"],
            "typescript": ["package.json", "tsconfig.json"],
            "go": ["go.mod"],
        }
        for marker in markers.get(language, []):
            (project / marker).write_text("")
        return project

    return _factory


@pytest.fixture()
def sample_coverage_json() -> dict[str, Any]:
    """Sample coverage.py JSON output."""
    return {
        "meta": {"version": "7.4"},
        "totals": {"covered_lines": 80, "num_statements": 100, "percent_covered": 80.0},
        "files": {
            "src/main.py": {
                "summary": {
                    "covered_lines": 40,
                    "num_statements": 50,
                    "percent_covered": 80.0,
                },
                "missing_lines": [10, 20, 30, 40, 50, 60, 70, 80, 90, 100],
            }
        },
    }
