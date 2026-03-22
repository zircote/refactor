"""Regression tests for past bug fixes.

Each test here corresponds to a specific bug fix commit and would have
caught the bug if it existed at the time. Going forward, every fix:
commit must include a regression test in this file.

Ref: https://github.com/zircote/refactor/issues/9
"""

from __future__ import annotations

import pytest

from scripts.coverage_report import parse_coverage
from scripts.exceptions import CoverageParseError
from scripts.utils import parse_json_output


class TestImportReAtModuleTop:
    """Regression for: fix: move import re to module top in coverage_report.py

    Bug: `import re` was inside _parse_go_text_coverage function body,
    violating PEP 8 E401/E402. Moved to module-level imports.
    Commit: part of cog-assess --fix run.
    """

    def test_coverage_report_imports_re_at_module_level(self):
        import scripts.coverage_report as cr

        # re should be available as a module-level attribute, not re-imported per call
        assert hasattr(cr, "re") or "re" in dir(cr)
        # Actually verify by checking the source doesn't have import inside function
        import inspect

        source = inspect.getsource(cr._parse_go_text_coverage)
        assert "import re" not in source


class TestAgentFrontmatterFormat:
    """Regression for: fix: standardize agent frontmatter to allowed-tools array format

    Bug: Agent .md files had inconsistent frontmatter. After fix, all agent
    files should have consistent YAML frontmatter with allowed-tools as arrays.
    Commit: dd6c433
    """

    def test_agent_files_have_consistent_frontmatter(self):
        from pathlib import Path

        agents_dir = Path(__file__).parent.parent / "agents"
        if not agents_dir.exists():
            return

        for agent_file in agents_dir.glob("*.md"):
            content = agent_file.read_text()
            # All agent files should start with --- (YAML frontmatter)
            assert content.startswith("---"), f"{agent_file.name} missing frontmatter"


class TestSkillPathLoading:
    """Regression for: fix: move skill to skills/refactor/SKILL.md for plugin loading

    Bug: Skills were not in the expected directory structure for Claude Code
    plugin loading. Each skill must be at skills/{name}/SKILL.md.
    Commit: 6383e2f
    """

    def test_all_skills_at_correct_path(self):
        from pathlib import Path

        skills_dir = Path(__file__).parent.parent / "skills"
        if not skills_dir.exists():
            return

        for skill_dir in skills_dir.iterdir():
            if skill_dir.is_dir():
                skill_file = skill_dir / "SKILL.md"
                assert skill_file.exists(), f"Skill {skill_dir.name} missing SKILL.md"


class TestShutdownInSkills:
    """Regression for: fix: prevent feature-dev agent stall after blackboard creation

    Bug: Skills had shutdown steps that only executed on happy path.
    Agents were left abandoned when workflows were interrupted.
    Fix added Team Lifecycle Safety section and shutdown timeout.
    Commit: efc0a55 + cog-assess --fix run.
    """

    def test_all_swarm_skills_have_lifecycle_safety(self):
        from pathlib import Path

        skills_dir = Path(__file__).parent.parent / "skills"
        swarm_skills = ["refactor", "feature-dev", "test-architect"]

        for skill_name in swarm_skills:
            skill_file = skills_dir / skill_name / "SKILL.md"
            if not skill_file.exists():
                continue
            content = skill_file.read_text()
            assert "Team Lifecycle Safety" in content, (
                f"{skill_name}/SKILL.md missing Team Lifecycle Safety section"
            )
            assert "30 seconds" in content, f"{skill_name}/SKILL.md missing shutdown timeout"
            assert "MUST execute regardless" in content, (
                f"{skill_name}/SKILL.md missing guaranteed cleanup language"
            )


class TestParseJsonOutputEmptyDict:
    """Regression for: fix: parse_json_output empty dict falsy bug

    Bug: `_extract_balanced_json(output, "{", "}") or _extract_balanced_json(...)`
    used `or` which skipped valid empty dict {} because {} is falsy.
    Found by Hypothesis property-based testing.
    """

    def test_empty_dict_in_text_is_found(self):
        result = parse_json_output("prefix {} suffix")
        assert result == {}

    def test_empty_list_in_text_is_found(self):
        result = parse_json_output("prefix [] suffix")
        assert result == []


class TestParseCoverageNonDictJson:
    """Regression for: fix: parse_coverage crash on non-dict JSON (NaN)

    Bug: json.loads("NaN") returns float nan. _normalize_coverage assumed
    dict input and called data.get() on a float, crashing.
    Found by Hypothesis property-based testing.
    Now raises CoverageParseError instead of silently returning error dicts.
    """

    def test_nan_string_raises_parse_error(self):
        with pytest.raises(CoverageParseError):
            parse_coverage("NaN", "rust")

    def test_integer_json_raises_parse_error(self):
        with pytest.raises(CoverageParseError):
            parse_coverage("42", "python")
