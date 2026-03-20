"""Coverage analysis for multi-language projects.

Executes language-specific coverage tools and parses results into
a normalized coverage report.
"""

from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Any

from .utils import parse_json_output


# Coverage commands per language
_COVERAGE_COMMANDS: dict[str, list[list[str]]] = {
    "rust": [["cargo", "tarpaulin", "--out", "json"]],
    "python": [
        ["python", "-m", "coverage", "run", "-m", "pytest"],
        ["python", "-m", "coverage", "json"],
    ],
    "typescript": [["npx", "c8", "--reporter=json", "vitest", "run"]],
    "go": [["go", "test", "-coverprofile=coverage.out", "./..."]],
}


def run_coverage(path: str, lang: str) -> dict[str, Any]:
    """Execute coverage tool for the given language and return raw output.

    Args:
        path: Filesystem path to the project root.
        lang: Language identifier (rust, python, typescript, go).

    Returns:
        Dict with keys: output, exit_code, coverage (parsed coverage dict).
        On failure, includes an error key.
    """
    commands = _COVERAGE_COMMANDS.get(lang)
    if commands is None:
        return {
            "error": f"unsupported language: {lang}",
            "output": "",
            "exit_code": -1,
        }

    combined_output = ""
    last_exit_code = 0

    for cmd in commands:
        try:
            result = subprocess.run(
                cmd,
                cwd=path,
                capture_output=True,
                text=True,
                timeout=600,
            )
        except FileNotFoundError as exc:
            return {
                "error": f"command not found: {exc}",
                "output": combined_output,
                "exit_code": -1,
            }
        except subprocess.TimeoutExpired:
            return {
                "error": "coverage execution timed out after 600s",
                "output": combined_output,
                "exit_code": -1,
            }

        combined_output += result.stdout + result.stderr
        last_exit_code = result.returncode

        # For multi-step commands (Python), abort early if a step fails
        if result.returncode != 0 and len(commands) > 1:
            return {
                "error": f"command failed: {' '.join(cmd)}",
                "output": combined_output,
                "exit_code": result.returncode,
            }

    # Try to read coverage JSON files for languages that produce them
    coverage_data = _read_coverage_file(path, lang)
    if coverage_data is None:
        coverage_data = parse_coverage(combined_output, lang)

    return {
        "output": combined_output,
        "exit_code": last_exit_code,
        "coverage": coverage_data,
    }


def _read_coverage_file(path: str, lang: str) -> dict[str, Any] | None:
    """Attempt to read a coverage JSON file produced by the tool."""
    root = Path(path)
    candidates: dict[str, list[str]] = {
        "rust": ["tarpaulin-report.json"],
        "python": ["coverage.json"],
        "typescript": ["coverage/coverage-final.json"],
        "go": [],  # Go uses coverage.out (text), not JSON
    }

    for filename in candidates.get(lang, []):
        filepath = root / filename
        if filepath.exists():
            try:
                raw = filepath.read_text()
                data = json.loads(raw)
                return _normalize_coverage(data, lang)
            except (json.JSONDecodeError, KeyError):
                continue

    return None


def _normalize_coverage(data: dict[str, Any], lang: str) -> dict[str, Any]:
    """Normalize parsed coverage data into a common format."""
    if lang == "rust":
        return _normalize_rust_coverage(data)
    elif lang == "python":
        return _normalize_python_coverage(data)
    elif lang == "typescript":
        return _normalize_typescript_coverage(data)
    return {"error": "normalization not implemented", "raw": data}


def _normalize_rust_coverage(data: dict[str, Any]) -> dict[str, Any]:
    """Normalize tarpaulin JSON output."""
    total_lines = 0
    covered_lines = 0
    uncovered_files: list[dict[str, Any]] = []

    for file_entry in data.get("files", []):
        file_total = file_entry.get("coverable", 0)
        file_covered = file_entry.get("covered", 0)
        total_lines += file_total
        covered_lines += file_covered
        if file_covered < file_total:
            uncovered = [
                t.get("line", 0)
                for t in file_entry.get("traces", [])
                if t.get("hits", 0) == 0
            ]
            uncovered_files.append(
                {
                    "file": file_entry.get("path", "unknown"),
                    "uncovered_lines": uncovered,
                }
            )

    pct = (covered_lines / total_lines * 100) if total_lines > 0 else 0.0
    return {
        "total_lines": total_lines,
        "covered_lines": covered_lines,
        "coverage_pct": round(pct, 2),
        "uncovered_files": uncovered_files,
    }


def _normalize_python_coverage(data: dict[str, Any]) -> dict[str, Any]:
    """Normalize coverage.py JSON output."""
    totals = data.get("totals", {})
    total_lines = totals.get("num_statements", 0)
    covered_lines = total_lines - totals.get("missing_lines", 0)
    pct = totals.get("percent_covered", 0.0)

    uncovered_files: list[dict[str, Any]] = []
    for filename, file_data in data.get("files", {}).items():
        missing = file_data.get("missing_lines", [])
        if missing:
            uncovered_files.append(
                {
                    "file": filename,
                    "uncovered_lines": missing,
                }
            )

    return {
        "total_lines": total_lines,
        "covered_lines": covered_lines,
        "coverage_pct": round(pct, 2),
        "uncovered_files": uncovered_files,
    }


def _normalize_typescript_coverage(data: dict[str, Any]) -> dict[str, Any]:
    """Normalize c8/istanbul JSON coverage output."""
    total_lines = 0
    covered_lines = 0
    uncovered_files: list[dict[str, Any]] = []

    for filename, file_data in data.items():
        stmt_map = file_data.get("statementMap", {})
        stmt_hits = file_data.get("s", {})
        file_total = len(stmt_map)
        file_covered = sum(1 for v in stmt_hits.values() if v > 0)
        total_lines += file_total
        covered_lines += file_covered

        if file_covered < file_total:
            uncovered = [int(k) for k, v in stmt_hits.items() if v == 0]
            uncovered_files.append(
                {
                    "file": filename,
                    "uncovered_lines": uncovered,
                }
            )

    pct = (covered_lines / total_lines * 100) if total_lines > 0 else 0.0
    return {
        "total_lines": total_lines,
        "covered_lines": covered_lines,
        "coverage_pct": round(pct, 2),
        "uncovered_files": uncovered_files,
    }


def parse_coverage(output: str, lang: str) -> dict[str, Any]:
    """Parse coverage from raw command output when no JSON file is available.

    Args:
        output: Combined stdout+stderr from the coverage command.
        lang: Language identifier.

    Returns:
        Normalized coverage dict with total_lines, covered_lines,
        coverage_pct, uncovered_files. Returns error dict on failure.
    """
    # Try to extract JSON from the output
    data = parse_json_output(output)
    if data and not isinstance(data, str):
        return _normalize_coverage(data, lang)

    # Fallback: try to parse Go text coverage profile
    if lang == "go":
        return _parse_go_text_coverage(output)

    return {
        "error": "could not parse coverage output",
        "total_lines": 0,
        "covered_lines": 0,
        "coverage_pct": 0.0,
        "uncovered_files": [],
    }


def _parse_go_text_coverage(output: str) -> dict[str, Any]:
    """Parse Go coverage percentage from 'go test -cover' output."""
    import re

    # Look for "coverage: XX.X% of statements"
    match = re.search(r"coverage:\s+([\d.]+)%\s+of\s+statements", output)
    if match:
        pct = float(match.group(1))
        return {
            "total_lines": 0,
            "covered_lines": 0,
            "coverage_pct": round(pct, 2),
            "uncovered_files": [],
        }

    return {
        "error": "could not parse Go coverage output",
        "total_lines": 0,
        "covered_lines": 0,
        "coverage_pct": 0.0,
        "uncovered_files": [],
    }
