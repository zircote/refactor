"""Plugin structure validator for the refactor plugin.

Validates agent definitions, JSON schemas, and workflow files.
Outputs a JSON report with pass/fail per check.

Usage:
    python scripts/validate_plugin.py [PLUGIN_ROOT]
"""

from __future__ import annotations

import argparse
import json
import sys
from difflib import get_close_matches
from pathlib import Path
from typing import Any

import yaml

# Valid Claude Code agent frontmatter fields
REQUIRED_AGENT_FIELDS = {"name", "description"}
RECOMMENDED_AGENT_FIELDS = {"model", "maxTurns"}
VALID_MODELS = {"sonnet", "opus", "haiku"}
VALID_TOOLS = {
    "Bash",
    "Glob",
    "Grep",
    "Read",
    "Write",
    "Edit",
    "TodoWrite",
    "NotebookEdit",
    "TaskList",
    "TaskGet",
    "TaskUpdate",
    "TaskCreate",
    "SendMessage",
    "Agent",
    "WebSearch",
    "WebFetch",
    "Skill",
    "ToolSearch",
}
AGENT_FRONTMATTER_FIELDS = {
    "name",
    "description",
    "color",
    "allowed-tools",
    "disallowedTools",
    "model",
    "maxTurns",
    "effort",
}


def _parse_frontmatter(path: Path) -> dict[str, Any] | None:
    """Parse YAML frontmatter from a markdown file using yaml.safe_load.

    Returns the frontmatter as a dict, or None if no frontmatter found.
    """
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---"):
        return None

    end = text.find("\n---", 3)
    if end == -1:
        return None

    fm_text = text[3:end]
    try:
        data = yaml.safe_load(fm_text)
    except yaml.YAMLError:
        return None

    if not isinstance(data, dict):
        return None

    return data


class CheckResult:
    """Result of a single validation check."""

    def __init__(self, name: str, passed: bool, message: str = "") -> None:
        self.name = name
        self.passed = passed
        self.message = message

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dictionary."""
        d: dict[str, Any] = {"name": self.name, "passed": self.passed}
        if self.message:
            d["message"] = self.message
        return d


def _suggest(value: str, valid: set[str]) -> str:
    """Return a 'did you mean?' suggestion if a close match exists."""
    # Use case-insensitive matching for short strings
    matches = get_close_matches(value.lower(), [v.lower() for v in sorted(valid)], n=1, cutoff=0.5)
    if matches:
        # Find the original-cased version
        for v in valid:
            if v.lower() == matches[0]:
                return f" (did you mean '{v}'?)"
    return ""


def validate_agents(root: Path) -> list[CheckResult]:
    """Validate all agent definition files."""
    results: list[CheckResult] = []
    agents_dir = root / "agents"

    if not agents_dir.is_dir():
        results.append(CheckResult("agents_dir_exists", False, "agents/ directory not found"))
        return results

    results.append(CheckResult("agents_dir_exists", True))

    agent_files = sorted(agents_dir.glob("*.md"))
    if not agent_files:
        results.append(CheckResult("agents_found", False, "no .md files in agents/"))
        return results

    results.append(CheckResult("agents_found", True, f"{len(agent_files)} agent(s)"))

    for path in agent_files:
        prefix = f"agent:{path.stem}"
        fm = _parse_frontmatter(path)

        if fm is None:
            results.append(CheckResult(f"{prefix}:frontmatter", False, "no frontmatter"))
            continue

        results.append(CheckResult(f"{prefix}:frontmatter", True))

        # Required fields
        for field in REQUIRED_AGENT_FIELDS:
            if field in fm:
                results.append(CheckResult(f"{prefix}:{field}", True))
            else:
                suggest = _suggest(field, set(fm.keys()))
                results.append(
                    CheckResult(f"{prefix}:{field}", False, f"missing '{field}'{suggest}")
                )

        # Recommended fields — warnings, not hard failures
        for field in RECOMMENDED_AGENT_FIELDS:
            if field in fm:
                results.append(CheckResult(f"{prefix}:{field}", True))
            else:
                results.append(
                    CheckResult(f"{prefix}:{field}", True, f"warning: '{field}' not set")
                )

        # Model validation
        if "model" in fm and fm["model"] not in VALID_MODELS:
            suggest = _suggest(str(fm["model"]), VALID_MODELS)
            results.append(
                CheckResult(
                    f"{prefix}:model_valid",
                    False,
                    f"invalid model '{fm['model']}'{suggest}",
                )
            )

        # Unknown frontmatter keys
        for key in fm:
            if key not in AGENT_FRONTMATTER_FIELDS:
                suggest = _suggest(str(key), AGENT_FRONTMATTER_FIELDS)
                results.append(
                    CheckResult(
                        f"{prefix}:unknown_key",
                        False,
                        f"unknown frontmatter key '{key}'{suggest}",
                    )
                )

        # Tool validation for allowed-tools
        tools = fm.get("allowed-tools", [])
        if isinstance(tools, list):
            for tool in tools:
                if tool not in VALID_TOOLS:
                    suggest = _suggest(str(tool), VALID_TOOLS)
                    results.append(
                        CheckResult(
                            f"{prefix}:tool:{tool}",
                            False,
                            f"unknown tool '{tool}'{suggest}",
                        )
                    )
        elif tools:
            results.append(
                CheckResult(
                    f"{prefix}:allowed-tools_format",
                    False,
                    f"'allowed-tools' must be a list, got {type(tools).__name__}",
                )
            )

        # Tool validation for disallowedTools
        dtools = fm.get("disallowedTools", [])
        if isinstance(dtools, list):
            for tool in dtools:
                if tool not in VALID_TOOLS:
                    suggest = _suggest(str(tool), VALID_TOOLS)
                    results.append(
                        CheckResult(
                            f"{prefix}:disallowed_tool:{tool}",
                            False,
                            f"unknown disallowed tool '{tool}'{suggest}",
                        )
                    )
        elif dtools:
            results.append(
                CheckResult(
                    f"{prefix}:disallowedTools_format",
                    False,
                    f"'disallowedTools' must be a list, got {type(dtools).__name__}",
                )
            )

    return results


def validate_schemas(root: Path) -> list[CheckResult]:
    """Validate JSON Schema files."""
    results: list[CheckResult] = []
    schemas_dir = root / "schemas"

    if not schemas_dir.is_dir():
        results.append(CheckResult("schemas_dir_exists", False, "schemas/ directory not found"))
        return results

    results.append(CheckResult("schemas_dir_exists", True))

    schema_files = sorted(schemas_dir.glob("*.json"))
    if not schema_files:
        results.append(CheckResult("schemas_found", False, "no .json files in schemas/"))
        return results

    results.append(CheckResult("schemas_found", True, f"{len(schema_files)} schema(s)"))

    for path in schema_files:
        prefix = f"schema:{path.stem}"
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            results.append(CheckResult(f"{prefix}:valid_json", False, str(exc)))
            continue

        results.append(CheckResult(f"{prefix}:valid_json", True))

        if "$schema" not in data:
            results.append(CheckResult(f"{prefix}:has_schema", False, "missing '$schema' field"))
        else:
            results.append(CheckResult(f"{prefix}:has_schema", True))

        if "title" not in data:
            results.append(CheckResult(f"{prefix}:has_title", False, "missing 'title' field"))
        else:
            results.append(CheckResult(f"{prefix}:has_title", True))

    return results


def validate_workflows(root: Path) -> list[CheckResult]:
    """Validate workflow YAML/JSON files."""
    results: list[CheckResult] = []
    workflows_dir = root / "workflows"

    if not workflows_dir.is_dir():
        results.append(CheckResult("workflows_dir_exists", False, "workflows/ directory not found"))
        return results

    results.append(CheckResult("workflows_dir_exists", True))

    wf_files = sorted(
        list(workflows_dir.glob("*.yaml"))
        + list(workflows_dir.glob("*.yml"))
        + list(workflows_dir.glob("*.json"))
    )

    if not wf_files:
        results.append(CheckResult("workflows_found", False, "no workflow files"))
        return results

    results.append(CheckResult("workflows_found", True, f"{len(wf_files)} workflow(s)"))

    for path in wf_files:
        prefix = f"workflow:{path.stem}"
        try:
            from scripts.workflow_runner.loader import load_workflow

            dag = load_workflow(path)
            dag.get_layers()  # triggers cycle check
            results.append(CheckResult(f"{prefix}:valid", True, f"{len(dag)} node(s)"))
        except ImportError as exc:
            results.append(
                CheckResult(f"{prefix}:valid", False, f"workflow_runner import failed: {exc}")
            )
        except Exception as exc:  # noqa: BLE001
            results.append(CheckResult(f"{prefix}:valid", False, str(exc)))

    return results


def validate_cross_references(root: Path) -> list[CheckResult]:
    """Validate cross-references between agents, workflows, and schemas."""
    results: list[CheckResult] = []

    agents_dir = root / "agents"
    workflows_dir = root / "workflows"

    # Collect known agent and skill names
    known_agents: set[str] = set()
    if agents_dir.is_dir():
        for path in agents_dir.glob("*.md"):
            fm = _parse_frontmatter(path)
            if fm and "name" in fm:
                known_agents.add(fm["name"])

    # Skills are also valid references (skills/<name>/SKILL.md)
    skills_dir = root / "skills"
    known_skills: set[str] = set()
    if skills_dir.is_dir():
        for skill_path in skills_dir.iterdir():
            if skill_path.is_dir() and (skill_path / "SKILL.md").exists():
                known_skills.add(skill_path.name)

    known_refs = known_agents | known_skills

    if not known_refs:
        return results

    results.append(
        CheckResult(
            "xref:refs_found",
            True,
            f"{len(known_agents)} agent(s), {len(known_skills)} skill(s) indexed",
        )
    )

    # Check workflow skill references against known agents
    if workflows_dir.is_dir():
        wf_files = (
            list(workflows_dir.glob("*.yaml"))
            + list(workflows_dir.glob("*.yml"))
            + list(workflows_dir.glob("*.json"))
        )
        for path in wf_files:
            try:
                text = path.read_text(encoding="utf-8")
                if path.suffix in (".yaml", ".yml"):
                    data = yaml.safe_load(text)
                else:
                    data = json.loads(text)
                if not isinstance(data, dict):
                    continue
                for node in data.get("nodes", []):
                    if not isinstance(node, dict):
                        continue
                    skill = node.get("skill", "")
                    if not skill:
                        continue
                    # skill format is "plugin:agent-name"
                    parts = skill.split(":", 1)
                    if len(parts) == 2:
                        agent_ref = parts[1]
                        if agent_ref not in known_refs:
                            suggest = _suggest(agent_ref, known_refs)
                            results.append(
                                CheckResult(
                                    f"xref:{path.stem}:{agent_ref}",
                                    False,
                                    f"workflow '{path.stem}' references unknown agent "
                                    f"'{agent_ref}'{suggest}",
                                )
                            )
            except (json.JSONDecodeError, yaml.YAMLError):
                continue

    return results


def validate_plugin(root: Path) -> dict[str, Any]:
    """Run all validation checks and return a report."""
    all_results: list[CheckResult] = []
    all_results.extend(validate_agents(root))
    all_results.extend(validate_schemas(root))
    all_results.extend(validate_workflows(root))
    all_results.extend(validate_cross_references(root))

    passed = sum(1 for r in all_results if r.passed)
    failed = sum(1 for r in all_results if not r.passed)

    return {
        "passed": passed,
        "failed": failed,
        "total": passed + failed,
        "status": "pass" if failed == 0 else "fail",
        "checks": [r.to_dict() for r in all_results],
    }


def main() -> int:
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Validate refactor plugin structure",
    )
    parser.add_argument(
        "root",
        nargs="?",
        default=".",
        help="Plugin root directory (default: current directory)",
    )
    parser.add_argument(
        "--json",
        dest="json_output",
        action="store_true",
        help="Output as JSON",
    )
    args = parser.parse_args()

    root = Path(args.root).resolve()
    report = validate_plugin(root)

    if args.json_output:
        print(json.dumps(report, indent=2))
    else:
        for check in report["checks"]:
            status = "PASS" if check["passed"] else "FAIL"
            msg = f"  — {check.get('message', '')}" if check.get("message") else ""
            print(f"  [{status}] {check['name']}{msg}")
        print(f"\n{report['passed']}/{report['total']} checks passed ({report['status']})")

    return 0 if report["status"] == "pass" else 1


if __name__ == "__main__":
    sys.exit(main())
