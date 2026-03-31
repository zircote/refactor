"""Coverage analysis for multi-language projects.

Executes language-specific coverage tools and parses results into
a normalized coverage report.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import TYPE_CHECKING, Any

from .audit import log_operation
from .exceptions import CoverageParseError, SubprocessError, UnsupportedLanguageError
from .languages import get_config
from .utils import parse_json_output, run_subprocess

if TYPE_CHECKING:
    from collections.abc import Callable

    from .types import CoverageData, CoverageResult, UncoveredFile


def run_coverage(path: str, lang: str) -> CoverageResult:
    """Execute coverage tool for the given language and return raw output.

    Args:
        path: Filesystem path to the project root.
        lang: Language identifier (rust, python, typescript, go).

    Returns:
        CoverageResult with keys: output, exit_code, coverage.

    Raises:
        UnsupportedLanguageError: If the language is not supported.
        SubprocessError: If a coverage command fails or is not found.
    """
    config = get_config(lang)
    if config is None:
        raise UnsupportedLanguageError(lang)

    commands = config.coverage_commands
    combined_output = ""
    last_exit_code = 0

    for cmd in commands:
        result = run_subprocess(cmd, cwd=path, timeout=600, output_so_far=combined_output)

        combined_output += result.stdout + result.stderr
        last_exit_code = result.returncode

        # For multi-step commands (Python), abort early if a step fails
        if result.returncode != 0 and len(commands) > 1:
            raise SubprocessError(
                f"command failed: {' '.join(cmd)}",
                command=" ".join(cmd),
                exit_code=result.returncode,
                output=combined_output,
            )

    # Try to read coverage JSON files for languages that produce them
    coverage_data = _read_coverage_file(path, lang)
    if coverage_data is None:
        coverage_data = parse_coverage(combined_output, lang)

    cov_result: CoverageResult = {
        "output": combined_output,
        "exit_code": last_exit_code,
        "coverage": coverage_data,
    }

    total_pct = coverage_data.get("coverage_pct") if coverage_data else None
    log_operation(
        action="coverage_analysis",
        resource=f"{path} ({lang})",
        result="success" if last_exit_code == 0 else "failure",
        details={"coverage_pct": total_pct} if total_pct is not None else None,
    )

    return cov_result


def _read_coverage_file(path: str, lang: str) -> CoverageData | None:
    """Attempt to read a coverage JSON file produced by the tool."""
    root = Path(path)
    config = get_config(lang)
    coverage_files = config.coverage_files if config else []

    for filename in coverage_files:
        filepath = root / filename
        if filepath.exists():
            try:
                raw = filepath.read_text()
                data = json.loads(raw)
                return _normalize_coverage(data, lang)
            except (json.JSONDecodeError, KeyError):
                continue

    return None


def _normalize_rust_coverage(data: dict[str, Any]) -> CoverageData:
    """Normalize tarpaulin JSON output."""
    total_lines = 0
    covered_lines = 0
    uncovered_files: list[UncoveredFile] = []

    for file_entry in data.get("files", []):
        file_total = file_entry.get("coverable", 0)
        file_covered = file_entry.get("covered", 0)
        total_lines += file_total
        covered_lines += file_covered
        if file_covered < file_total:
            uncovered = [
                t.get("line", 0) for t in file_entry.get("traces", []) if t.get("hits", 0) == 0
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


def _normalize_python_coverage(data: dict[str, Any]) -> CoverageData:
    """Normalize coverage.py JSON output."""
    totals = data.get("totals", {})
    total_lines = totals.get("num_statements", 0)
    covered_lines = total_lines - totals.get("missing_lines", 0)
    pct = totals.get("percent_covered", 0.0)

    uncovered_files: list[UncoveredFile] = []
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


def _normalize_typescript_coverage(data: dict[str, Any]) -> CoverageData:
    """Normalize c8/istanbul JSON coverage output."""
    total_lines = 0
    covered_lines = 0
    uncovered_files: list[UncoveredFile] = []

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


_NORMALIZERS: dict[str, Callable[[dict[str, Any]], CoverageData]] = {
    "rust": _normalize_rust_coverage,
    "python": _normalize_python_coverage,
    "typescript": _normalize_typescript_coverage,
}


def _normalize_coverage(data: dict[str, Any], lang: str) -> CoverageData:
    """Normalize parsed coverage data into a common format."""
    normalizer = _NORMALIZERS.get(lang)
    if normalizer is None:
        raise CoverageParseError(
            f"coverage normalization not implemented for language: {lang}",
            raw_output=str(data),
        )
    return normalizer(data)


def parse_coverage(output: str, lang: str) -> CoverageData:
    """Parse coverage from raw command output when no JSON file is available.

    Args:
        output: Combined stdout+stderr from the coverage command.
        lang: Language identifier.

    Returns:
        Normalized CoverageData with total_lines, covered_lines,
        coverage_pct, uncovered_files.

    Raises:
        CoverageParseError: If the output cannot be parsed.
    """
    # Try to extract JSON from the output
    data = parse_json_output(output)
    if isinstance(data, dict):
        return _normalize_coverage(data, lang)

    # Fallback: try to parse Go text coverage profile
    if lang == "go":
        return _parse_go_text_coverage(output)

    raise CoverageParseError(
        "could not parse coverage output",
        raw_output=output,
    )


def _parse_go_text_coverage(output: str) -> CoverageData:
    """Parse Go coverage percentage from 'go test -cover' output."""

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

    raise CoverageParseError(
        "could not parse Go coverage output",
        raw_output=output,
    )
