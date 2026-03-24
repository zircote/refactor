"""Tests for the audit logging module."""

from __future__ import annotations

import json
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import pytest

from scripts.audit import _get_audit_path, log_operation


class TestGetAuditPath:
    """Tests for audit log path resolution."""

    def test_default_path(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.delenv("REFACTOR_AUDIT_LOG", raising=False)
        path = _get_audit_path()
        assert path == Path(".refactor") / "audit.log"

    def test_env_override(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("REFACTOR_AUDIT_LOG", "/tmp/custom-audit.log")
        path = _get_audit_path()
        assert path == Path("/tmp/custom-audit.log")


class TestLogOperation:
    """Tests for structured audit log entries."""

    def test_writes_json_entry(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        log_file = tmp_path / "audit.log"
        monkeypatch.setenv("REFACTOR_AUDIT_LOG", str(log_file))

        entry = log_operation(
            action="test_run",
            resource="/project (python)",
            result="success",
            details={"passed": 10, "failed": 0},
        )

        assert entry["action"] == "test_run"
        assert entry["resource"] == "/project (python)"
        assert entry["result"] == "success"
        assert entry["details"] == {"passed": 10, "failed": 0}
        assert "timestamp" in entry
        assert "actor" in entry

        # Verify file was written
        lines = log_file.read_text().strip().split("\n")
        assert len(lines) == 1
        parsed = json.loads(lines[0])
        assert parsed["action"] == "test_run"

    def test_appends_multiple_entries(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        log_file = tmp_path / "audit.log"
        monkeypatch.setenv("REFACTOR_AUDIT_LOG", str(log_file))

        log_operation(action="test_run", resource="proj1", result="success")
        log_operation(action="coverage_analysis", resource="proj2", result="failure")

        lines = log_file.read_text().strip().split("\n")
        assert len(lines) == 2
        assert json.loads(lines[0])["action"] == "test_run"
        assert json.loads(lines[1])["action"] == "coverage_analysis"

    def test_no_details_omitted(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        log_file = tmp_path / "audit.log"
        monkeypatch.setenv("REFACTOR_AUDIT_LOG", str(log_file))

        entry = log_operation(action="detect", resource=".", result="success")
        assert "details" not in entry

        parsed = json.loads(log_file.read_text().strip())
        assert "details" not in parsed

    def test_creates_parent_directory(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        log_file = tmp_path / "nested" / "dir" / "audit.log"
        monkeypatch.setenv("REFACTOR_AUDIT_LOG", str(log_file))

        log_operation(action="test", resource=".", result="success")
        assert log_file.exists()

    def test_actor_from_user_env(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        log_file = tmp_path / "audit.log"
        monkeypatch.setenv("REFACTOR_AUDIT_LOG", str(log_file))
        monkeypatch.setenv("USER", "test-actor")

        entry = log_operation(action="test", resource=".", result="success")
        assert entry["actor"] == "test-actor"

    def test_survives_unwritable_path(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("REFACTOR_AUDIT_LOG", "/nonexistent/readonly/audit.log")

        # Should not raise — logs a warning instead
        entry = log_operation(action="test", resource=".", result="success")
        assert entry["action"] == "test"
