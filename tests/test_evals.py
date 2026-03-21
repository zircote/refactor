"""Bridge eval JSON files to automated pytest assertions.

Loads all *-evals.json files and runs deterministic validation:
1. Structural integrity: required fields present, types correct
2. Skill trigger matching: expected_skill maps to an actual skill directory
3. Assertion quality: assertions are non-empty and descriptive
4. Negative cases: null expected_skill entries have anti-trigger assertions
5. Cross-referencing: no duplicate eval names across files

Non-deterministic assertions (LLM behavior quality) are documented but
not executable in CI — they require an AI evaluator.

Ref: https://github.com/zircote/refactor/issues/3
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

EVALS_DIR = Path(__file__).parent.parent / "evals"
SKILLS_DIR = Path(__file__).parent.parent / "skills"


def _normalize_entry(entry: dict, source_skill: str | None = None) -> dict:
    """Normalize an eval entry to a common schema."""
    # Format A: {name, input, expected_skill, assertions}
    if "name" in entry and "input" in entry:
        return entry
    # Format B: {id, prompt, expected_output, expectations}
    if "id" in entry and "prompt" in entry:
        return {
            "name": entry["id"],
            "input": entry["prompt"],
            "expected_skill": source_skill,
            "assertions": entry.get("expectations", []),
            "expected_output": entry.get("expected_output"),
            "files": entry.get("files"),
            "_format": "B",
        }
    return entry


def _load_all_evals() -> list[tuple[str, dict]]:
    """Load all eval entries with their source file name."""
    entries = []
    for eval_file in sorted(EVALS_DIR.glob("*-evals.json")):
        raw = json.loads(eval_file.read_text())

        if isinstance(raw, list):
            # Format A: top-level array of entries
            for entry in raw:
                normalized = _normalize_entry(entry)
                entries.append((f"{eval_file.stem}/{normalized['name']}", normalized))
        elif isinstance(raw, dict) and "evals" in raw:
            # Format B: {skill_name, evals: [...]}
            skill_name = raw.get("skill_name")
            for entry in raw["evals"]:
                normalized = _normalize_entry(entry, source_skill=skill_name)
                entries.append((f"{eval_file.stem}/{normalized['name']}", normalized))
    return entries


ALL_EVALS = _load_all_evals()
EVAL_IDS = [e[0] for e in ALL_EVALS]
AVAILABLE_SKILLS = {d.name for d in SKILLS_DIR.iterdir() if d.is_dir()}


# --- Structural Integrity ---


class TestEvalStructure:
    @pytest.mark.parametrize("eval_id,entry", ALL_EVALS, ids=EVAL_IDS)
    def test_has_required_fields(self, eval_id: str, entry: dict):
        assert "name" in entry, f"{eval_id}: missing 'name'"
        assert "input" in entry, f"{eval_id}: missing 'input'"
        assert "expected_skill" in entry, f"{eval_id}: missing 'expected_skill'"
        assert "assertions" in entry, f"{eval_id}: missing 'assertions'"

    @pytest.mark.parametrize("eval_id,entry", ALL_EVALS, ids=EVAL_IDS)
    def test_name_is_valid_identifier(self, eval_id: str, entry: dict):
        name = entry["name"]
        assert isinstance(name, (str, int))
        if isinstance(name, str):
            assert len(name) > 0
            # Allow snake_case, kebab-case, and numeric IDs
            assert all(c.isalnum() or c in ("_", "-") for c in name), (
                f"{eval_id}: name '{name}' contains invalid characters"
            )

    @pytest.mark.parametrize("eval_id,entry", ALL_EVALS, ids=EVAL_IDS)
    def test_input_is_nonempty_string(self, eval_id: str, entry: dict):
        assert isinstance(entry["input"], str)
        assert len(entry["input"].strip()) > 0

    @pytest.mark.parametrize("eval_id,entry", ALL_EVALS, ids=EVAL_IDS)
    def test_assertions_are_nonempty_list(self, eval_id: str, entry: dict):
        assertions = entry["assertions"]
        assert isinstance(assertions, list)
        assert len(assertions) > 0, f"{eval_id}: assertions list is empty"

    @pytest.mark.parametrize("eval_id,entry", ALL_EVALS, ids=EVAL_IDS)
    def test_each_assertion_is_descriptive(self, eval_id: str, entry: dict):
        for i, assertion in enumerate(entry["assertions"]):
            assert isinstance(assertion, str)
            assert len(assertion) >= 10, f"{eval_id}: assertion[{i}] too short: '{assertion}'"

    @pytest.mark.parametrize("eval_id,entry", ALL_EVALS, ids=EVAL_IDS)
    def test_expected_skill_type(self, eval_id: str, entry: dict):
        skill = entry["expected_skill"]
        assert skill is None or isinstance(skill, str)


# --- Skill Trigger Matching ---


class TestSkillMapping:
    @pytest.mark.parametrize(
        "eval_id,entry",
        [(eid, e) for eid, e in ALL_EVALS if e["expected_skill"] is not None],
        ids=[eid for eid, e in ALL_EVALS if e["expected_skill"] is not None],
    )
    def test_expected_skill_exists_or_is_external(self, eval_id: str, entry: dict):
        """Positive evals should reference a known skill or an explicitly external one."""
        skill = entry["expected_skill"]
        # The eval file stem tells us which skill this file tests
        eval_file_skill = eval_id.split("/")[0].replace("-evals", "")
        if skill == eval_file_skill:
            # This is the primary skill — it must exist
            assert skill in AVAILABLE_SKILLS, (
                f"{eval_id}: expected_skill '{skill}' not found in skills/"
            )
        # Negative/redirect cases (skill != file's own skill) are allowed
        # to reference external skills not in this plugin

    def test_every_skill_has_at_least_one_eval(self):
        """Each skill directory should have at least one positive eval entry."""
        skills_with_evals = {
            entry["expected_skill"] for _, entry in ALL_EVALS if entry["expected_skill"] is not None
        }
        # Skills that are tested through evals
        for skill in AVAILABLE_SKILLS:
            eval_file = EVALS_DIR / f"{skill}-evals.json"
            if eval_file.exists():
                assert skill in skills_with_evals, (
                    f"Skill '{skill}' has eval file but no positive eval entries"
                )


# --- Negative Case Validation ---


class TestNegativeCases:
    @pytest.mark.parametrize(
        "eval_id,entry",
        [(eid, e) for eid, e in ALL_EVALS if e["expected_skill"] is None],
        ids=[eid for eid, e in ALL_EVALS if e["expected_skill"] is None],
    )
    def test_negative_cases_have_anti_trigger_assertions(self, eval_id: str, entry: dict):
        """Negative eval entries should assert the skill does NOT trigger."""
        assertions_text = " ".join(entry["assertions"]).lower()
        has_negation = any(
            keyword in assertions_text
            for keyword in ["not trigger", "does not", "should not", "not match"]
        )
        assert has_negation, (
            f"{eval_id}: negative case (expected_skill=null) should have "
            f"assertions about what should NOT happen"
        )


# --- Uniqueness ---


class TestUniqueness:
    def test_no_duplicate_eval_names_within_file(self):
        """Each eval file should have unique names within itself."""
        by_file: dict[str, list[str]] = {}
        for eval_id, entry in ALL_EVALS:
            file_stem = eval_id.split("/")[0]
            by_file.setdefault(file_stem, []).append(str(entry["name"]))
        for file_stem, names in by_file.items():
            duplicates = [n for n in names if names.count(n) > 1]
            assert not duplicates, f"{file_stem}: duplicate names: {set(duplicates)}"

    def test_no_duplicate_qualified_eval_ids(self):
        """Fully qualified eval IDs (file/name) should be unique."""
        seen: set[str] = set()
        for eval_id, _ in ALL_EVALS:
            assert eval_id not in seen, f"Duplicate eval ID: {eval_id}"
            seen.add(eval_id)


# --- Eval Count ---


class TestEvalCoverage:
    def test_minimum_eval_count(self):
        """Sanity check: we should have a reasonable number of evals."""
        assert len(ALL_EVALS) >= 20, (
            f"Only {len(ALL_EVALS)} eval entries found — expected at least 20"
        )

    def test_each_eval_file_has_entries(self):
        """No empty eval files."""
        for eval_file in EVALS_DIR.glob("*-evals.json"):
            raw = json.loads(eval_file.read_text())
            if isinstance(raw, list):
                assert len(raw) > 0, f"{eval_file.name} is empty"
            elif isinstance(raw, dict) and "evals" in raw:
                assert len(raw["evals"]) > 0, f"{eval_file.name} has empty evals"

    def test_negative_cases_exist(self):
        """At least some evals should test anti-triggers."""
        negative_count = sum(1 for _, entry in ALL_EVALS if entry["expected_skill"] is None)
        assert negative_count >= 5, f"Only {negative_count} negative eval cases — need at least 5"
