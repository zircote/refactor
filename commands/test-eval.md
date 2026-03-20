---
name: test-eval
description: "Evaluate existing test suite quality and coverage. Runs rigor review and coverage analysis on current tests."
arguments:
  - name: target
    description: "File path, directory, or glob pattern to evaluate. Defaults to current project root."
    required: false
allowed-tools:
  - Read
  - Bash
  - Glob
  - Grep
  - Agent
---

# /test-eval — Evaluate Existing Tests

You are invoking the test-architect skill in **evaluation mode**. This analyzes existing tests for quality and coverage without generating new test code.

## Instructions

Load and follow the test-architect skill at `${CLAUDE_PLUGIN_ROOT}/skills/test-architect/SKILL.md`, using the evaluation agents.

## Pipeline

1. **Detect** — Identify project language, test framework, and existing test files
2. **Rigor Review** — Run the test-rigor-reviewer agent to evaluate:
   - Assertion strength (exact values vs. loose checks)
   - Boundary coverage (both sides of each boundary tested?)
   - Tautological assertions (tests that can never fail)
   - Missing negative test cases
   - Property-based test opportunities
   - Mutation resilience (would common mutants survive?)
3. **Coverage Analysis** — Run the coverage-analyst agent to:
   - Execute the language-appropriate coverage tool
   - Parse and normalize coverage results
   - Identify uncovered files, functions, and branches
   - Map coverage gaps to specific missing test scenarios
4. **Report** — Present a combined quality report with:
   - Per-file rigor scores
   - Overall coverage percentage and gap list
   - Prioritized recommendations for test improvements
   - Specific test cases to add for maximum impact

## Target Resolution

- If target is provided, scope evaluation to that path
- If target is omitted, evaluate the entire project's test suite
- Target can be a file, directory, or glob pattern

## References

Technique reference documents are available at:
- `${CLAUDE_PLUGIN_ROOT}/references/property-testing.md`
- `${CLAUDE_PLUGIN_ROOT}/references/boundary-analysis.md`
- `${CLAUDE_PLUGIN_ROOT}/references/mutation-testing.md`
