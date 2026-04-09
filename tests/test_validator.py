"""Tests for the plugin validation CLI.

Tests each validation rule with valid and invalid fixtures,
cross-reference checks, and fuzzy suggestion output.
"""

from __future__ import annotations

import json
from pathlib import Path

from scripts.validate_plugin import (
    CheckResult,
    _parse_frontmatter,
    _suggest,
    validate_agents,
    validate_cross_references,
    validate_plugin,
    validate_schemas,
    validate_workflows,
)

# ---------------------------------------------------------------------------
# Frontmatter parser
# ---------------------------------------------------------------------------


class TestParseFrontmatter:
    """Tests for YAML frontmatter parsing."""

    def test_parse_valid_frontmatter(self, tmp_path: Path) -> None:
        path = tmp_path / "test.md"
        path.write_text("---\nname: test-agent\ndescription: A test agent\ncolor: red\n---\n")
        fm = _parse_frontmatter(path)
        assert fm is not None
        assert fm["name"] == "test-agent"
        assert fm["description"] == "A test agent"

    def test_parse_frontmatter_with_list(self, tmp_path: Path) -> None:
        path = tmp_path / "test.md"
        path.write_text("---\nname: test\nallowed-tools:\n- Bash\n- Read\n---\n")
        fm = _parse_frontmatter(path)
        assert fm is not None
        assert fm["allowed-tools"] == ["Bash", "Read"]

    def test_parse_frontmatter_with_integer(self, tmp_path: Path) -> None:
        path = tmp_path / "test.md"
        path.write_text("---\nname: test\nmaxTurns: 20\n---\n")
        fm = _parse_frontmatter(path)
        assert fm is not None
        assert fm["maxTurns"] == 20

    def test_parse_multiline_description(self, tmp_path: Path) -> None:
        """Multi-line YAML values must be preserved, not silently truncated."""
        path = tmp_path / "test.md"
        path.write_text(
            "---\nname: test\ndescription: >-\n"
            "  This is a long description that\n"
            "  spans multiple lines\n---\n"
        )
        fm = _parse_frontmatter(path)
        assert fm is not None
        assert "spans multiple lines" in fm["description"]

    def test_parse_quoted_string(self, tmp_path: Path) -> None:
        """Quoted strings should not include the quotes in the value."""
        path = tmp_path / "test.md"
        path.write_text('---\nname: "quoted-value"\n---\n')
        fm = _parse_frontmatter(path)
        assert fm is not None
        assert fm["name"] == "quoted-value"
        assert '"' not in fm["name"]

    def test_no_frontmatter(self, tmp_path: Path) -> None:
        path = tmp_path / "test.md"
        path.write_text("# Just a heading\n\nSome content.")
        assert _parse_frontmatter(path) is None

    def test_unclosed_frontmatter(self, tmp_path: Path) -> None:
        path = tmp_path / "test.md"
        path.write_text("---\nname: test\nNo closing marker")
        assert _parse_frontmatter(path) is None

    def test_invalid_yaml(self, tmp_path: Path) -> None:
        path = tmp_path / "test.md"
        path.write_text("---\n: :\n  - [invalid\n---\n")
        assert _parse_frontmatter(path) is None


# ---------------------------------------------------------------------------
# Fuzzy suggestions
# ---------------------------------------------------------------------------


class TestSuggestions:
    """Tests for typo suggestions."""

    def test_suggest_close_match(self) -> None:
        result = _suggest("modle", {"model", "maxTurns", "name"})
        assert "model" in result

    def test_suggest_case_insensitive(self) -> None:
        """'bash' should suggest 'Bash' despite case difference."""
        result = _suggest("bash", {"Bash", "Glob", "Grep"})
        assert "Bash" in result

    def test_suggest_no_match(self) -> None:
        result = _suggest("zzzzz", {"model", "name"})
        assert result == ""


# ---------------------------------------------------------------------------
# Agent validation
# ---------------------------------------------------------------------------


class TestValidateAgents:
    """Tests for agent definition validation."""

    def _make_agent(self, tmp_path: Path, name: str, content: str) -> Path:
        agents_dir = tmp_path / "agents"
        agents_dir.mkdir(exist_ok=True)
        path = agents_dir / f"{name}.md"
        path.write_text(content)
        return path

    def test_valid_agent(self, tmp_path: Path) -> None:
        self._make_agent(
            tmp_path,
            "test-agent",
            "---\nname: test-agent\ndescription: Test\ncolor: red\n"
            "allowed-tools:\n- Bash\n- Read\nmodel: sonnet\nmaxTurns: 20\n"
            "effort: high\n---\n",
        )
        results = validate_agents(tmp_path)
        failures = [r for r in results if not r.passed]
        assert failures == [], [f.to_dict() for f in failures]
        # Verify the validator actually checked the fields it should have
        check_names = {r.name for r in results}
        assert "agent:test-agent:name" in check_names
        assert "agent:test-agent:description" in check_names
        assert "agent:test-agent:model" in check_names
        assert "agent:test-agent:maxTurns" in check_names

    def test_missing_required_fields(self, tmp_path: Path) -> None:
        self._make_agent(tmp_path, "bad", "---\ncolor: red\n---\n")
        results = validate_agents(tmp_path)
        failed_names = {r.name for r in results if not r.passed}
        assert "agent:bad:name" in failed_names
        assert "agent:bad:description" in failed_names

    def test_recommended_fields_are_warnings_not_failures(self, tmp_path: Path) -> None:
        """Missing model/maxTurns should pass with a warning, not fail."""
        self._make_agent(
            tmp_path,
            "minimal",
            "---\nname: minimal\ndescription: Test\n---\n",
        )
        results = validate_agents(tmp_path)
        model_checks = [r for r in results if r.name == "agent:minimal:model"]
        assert len(model_checks) == 1
        assert model_checks[0].passed is True
        assert "warning" in model_checks[0].message

    def test_invalid_model(self, tmp_path: Path) -> None:
        self._make_agent(
            tmp_path,
            "bad-model",
            "---\nname: x\ndescription: x\nmodel: gpt4\nmaxTurns: 10\n---\n",
        )
        results = validate_agents(tmp_path)
        model_checks = [r for r in results if "model_valid" in r.name]
        assert len(model_checks) == 1
        assert not model_checks[0].passed

    def test_unknown_tool(self, tmp_path: Path) -> None:
        self._make_agent(
            tmp_path,
            "bad-tool",
            "---\nname: x\ndescription: x\nmodel: sonnet\nmaxTurns: 10\n"
            "allowed-tools:\n- FakeTool\n---\n",
        )
        results = validate_agents(tmp_path)
        tool_checks = [r for r in results if "tool:FakeTool" in r.name]
        assert len(tool_checks) == 1
        assert not tool_checks[0].passed

    def test_tools_as_string_not_list(self, tmp_path: Path) -> None:
        """allowed-tools as a bare string should fail, not silently pass."""
        self._make_agent(
            tmp_path,
            "str-tool",
            "---\nname: x\ndescription: x\nallowed-tools: Bash\n---\n",
        )
        results = validate_agents(tmp_path)
        format_checks = [r for r in results if "allowed-tools_format" in r.name]
        assert len(format_checks) == 1
        assert not format_checks[0].passed

    def test_typo_suggestion(self, tmp_path: Path) -> None:
        self._make_agent(
            tmp_path,
            "typo",
            "---\nname: x\ndescription: x\nmodle: sonnet\n---\n",
        )
        results = validate_agents(tmp_path)
        unknown = [r for r in results if "unknown_key" in r.name]
        assert len(unknown) == 1
        assert "model" in unknown[0].message

    def test_no_agents_dir(self, tmp_path: Path) -> None:
        results = validate_agents(tmp_path)
        assert not results[0].passed

    def test_no_frontmatter(self, tmp_path: Path) -> None:
        self._make_agent(tmp_path, "no-fm", "# Just content\n")
        results = validate_agents(tmp_path)
        fm_checks = [r for r in results if "frontmatter" in r.name]
        assert len(fm_checks) == 1
        assert not fm_checks[0].passed


# ---------------------------------------------------------------------------
# Schema validation
# ---------------------------------------------------------------------------


class TestValidateSchemas:
    """Tests for JSON Schema validation."""

    def test_valid_schema(self, tmp_path: Path) -> None:
        schemas_dir = tmp_path / "schemas"
        schemas_dir.mkdir()
        schema = {
            "$schema": "http://json-schema.org/draft-07/schema#",
            "title": "Test",
            "type": "object",
        }
        (schemas_dir / "test.json").write_text(json.dumps(schema))
        results = validate_schemas(tmp_path)
        failures = [r for r in results if not r.passed]
        assert failures == []
        # Verify specific checks ran
        check_names = {r.name for r in results}
        assert "schema:test:valid_json" in check_names
        assert "schema:test:has_schema" in check_names
        assert "schema:test:has_title" in check_names

    def test_invalid_json(self, tmp_path: Path) -> None:
        schemas_dir = tmp_path / "schemas"
        schemas_dir.mkdir()
        (schemas_dir / "bad.json").write_text("{invalid")
        results = validate_schemas(tmp_path)
        json_checks = [r for r in results if "valid_json" in r.name]
        assert len(json_checks) == 1
        assert not json_checks[0].passed

    def test_missing_schema_field(self, tmp_path: Path) -> None:
        schemas_dir = tmp_path / "schemas"
        schemas_dir.mkdir()
        (schemas_dir / "no-schema.json").write_text(json.dumps({"title": "Test"}))
        results = validate_schemas(tmp_path)
        schema_checks = [r for r in results if "has_schema" in r.name]
        assert len(schema_checks) == 1
        assert not schema_checks[0].passed

    def test_no_schemas_dir(self, tmp_path: Path) -> None:
        results = validate_schemas(tmp_path)
        assert not results[0].passed


# ---------------------------------------------------------------------------
# Workflow validation
# ---------------------------------------------------------------------------


class TestValidateWorkflows:
    """Tests for workflow file validation."""

    def test_valid_workflow(self, tmp_path: Path) -> None:
        wf_dir = tmp_path / "workflows"
        wf_dir.mkdir(parents=True)
        wf = {
            "name": "test",
            "nodes": [{"id": "a", "bash": "echo a"}],
        }
        (wf_dir / "test.json").write_text(json.dumps(wf))
        results = validate_workflows(tmp_path)
        failures = [r for r in results if not r.passed]
        assert failures == [], [f.to_dict() for f in failures]
        # Verify a specific workflow check ran with node count
        wf_checks = [r for r in results if "workflow:test:valid" in r.name]
        assert len(wf_checks) == 1
        assert "1 node" in wf_checks[0].message

    def test_cyclic_workflow(self, tmp_path: Path) -> None:
        wf_dir = tmp_path / "workflows"
        wf_dir.mkdir(parents=True)
        wf = {
            "name": "cyclic",
            "nodes": [
                {"id": "a", "bash": "echo a", "depends_on": ["b"]},
                {"id": "b", "bash": "echo b", "depends_on": ["a"]},
            ],
        }
        (wf_dir / "cyclic.json").write_text(json.dumps(wf))
        results = validate_workflows(tmp_path)
        wf_checks = [r for r in results if "valid" in r.name and "workflow:" in r.name]
        assert len(wf_checks) == 1
        assert not wf_checks[0].passed

    def test_no_workflows_dir(self, tmp_path: Path) -> None:
        results = validate_workflows(tmp_path)
        assert not results[0].passed


# ---------------------------------------------------------------------------
# Cross-reference validation
# ---------------------------------------------------------------------------


class TestValidateCrossReferences:
    """Tests for cross-reference validation between agents and workflows."""

    def test_valid_cross_reference(self, tmp_path: Path) -> None:
        agents_dir = tmp_path / "agents"
        agents_dir.mkdir()
        (agents_dir / "code-reviewer.md").write_text(
            "---\nname: code-reviewer\ndescription: Test\n---\n"
        )
        wf_dir = tmp_path / "workflows"
        wf_dir.mkdir()
        wf = {
            "name": "test",
            "nodes": [{"id": "a", "skill": "refactor:code-reviewer"}],
        }
        (wf_dir / "test.json").write_text(json.dumps(wf))
        results = validate_cross_references(tmp_path)
        failures = [r for r in results if not r.passed]
        assert failures == []

    def test_invalid_cross_reference(self, tmp_path: Path) -> None:
        agents_dir = tmp_path / "agents"
        agents_dir.mkdir()
        (agents_dir / "code-reviewer.md").write_text(
            "---\nname: code-reviewer\ndescription: Test\n---\n"
        )
        wf_dir = tmp_path / "workflows"
        wf_dir.mkdir()
        wf = {
            "name": "test",
            "nodes": [{"id": "a", "skill": "refactor:nonexistent-agent"}],
        }
        (wf_dir / "test.json").write_text(json.dumps(wf))
        results = validate_cross_references(tmp_path)
        failures = [r for r in results if not r.passed]
        assert len(failures) == 1
        assert "nonexistent-agent" in failures[0].message

    def test_no_agents_returns_empty(self, tmp_path: Path) -> None:
        results = validate_cross_references(tmp_path)
        assert results == []


# ---------------------------------------------------------------------------
# Full plugin validation
# ---------------------------------------------------------------------------


class TestValidatePlugin:
    """Tests for the full plugin validation report."""

    def test_empty_dir_reports_failures(self, tmp_path: Path) -> None:
        report = validate_plugin(tmp_path)
        assert report["status"] == "fail"
        assert report["failed"] > 0

    def test_valid_plugin(self, tmp_path: Path) -> None:
        # Create minimal valid plugin structure
        agents_dir = tmp_path / "agents"
        agents_dir.mkdir()
        (agents_dir / "test.md").write_text(
            "---\nname: test\ndescription: Test\nmodel: sonnet\nmaxTurns: 10\n---\n"
        )

        schemas_dir = tmp_path / "schemas"
        schemas_dir.mkdir()
        (schemas_dir / "test.json").write_text(
            json.dumps({"$schema": "http://json-schema.org/draft-07/schema#", "title": "T"})
        )

        wf_dir = tmp_path / "workflows"
        wf_dir.mkdir(parents=True)
        (wf_dir / "test.json").write_text(
            json.dumps({"name": "t", "nodes": [{"id": "a", "bash": "echo"}]})
        )

        report = validate_plugin(tmp_path)
        assert report["status"] == "pass"
        assert report["failed"] == 0
        # Verify the report contains checks from all validation phases
        check_names = {c["name"] for c in report["checks"]}
        assert any("agent:" in n for n in check_names)
        assert any("schema:" in n for n in check_names)
        assert any("workflow:" in n for n in check_names)


# ---------------------------------------------------------------------------
# CheckResult
# ---------------------------------------------------------------------------


class TestCheckResult:
    """Tests for CheckResult serialization."""

    def test_to_dict_pass(self) -> None:
        r = CheckResult("test", True)
        d = r.to_dict()
        assert d["name"] == "test"
        assert d["passed"] is True
        assert "message" not in d

    def test_to_dict_fail_with_message(self) -> None:
        r = CheckResult("test", False, "something wrong")
        d = r.to_dict()
        assert d["passed"] is False
        assert d["message"] == "something wrong"
