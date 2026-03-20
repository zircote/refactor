---
name: test-gen
description: "Generate scientifically grounded test suites from code, specs, or design documents. Full pipeline: detect → plan → write → review → coverage. Use --coverage for coverage-only mode."
arguments:
  - name: target
    description: "File path, directory, or glob pattern to generate tests for. Defaults to current project root."
    required: false
  - name: --coverage
    description: "Run coverage analysis only — skip test generation."
    required: false
allowed-tools:
  - Read
  - Write
  - Bash
  - Glob
  - Grep
  - Agent
---

# /test-gen — Full Test Generation Pipeline

You are invoking the test-architect skill to generate scientifically grounded test suites.

## Mode Selection

- If `--coverage` flag is present: run **coverage-only** mode (detect → coverage analysis → gap report).
- Otherwise: run **full pipeline** (detect → plan → write → review → coverage → capture).

## Instructions

Load and follow the test-architect skill at `${CLAUDE_PLUGIN_ROOT}/skills/test-architect/SKILL.md`.

The skill will orchestrate specialist agents through these phases:

### Full Pipeline (default)
1. **Detect** — Identify project language, test framework, and directory structure
2. **Plan** — Produce a JSON test plan using equivalence class partitioning and boundary value analysis
3. **Write** — Generate idiomatic test code designed to FAIL (TDD red phase)
4. **Review** — Verify scientific rigor: mutation-aware assertions, boundary coverage, property-based tests
5. **Coverage** — Run coverage analysis and identify remaining gaps
6. **Capture** — Store reusable patterns and decisions to Atlatl memory

### Coverage-Only Mode (--coverage)
1. **Detect** — Identify project language and coverage tool
2. **Coverage** — Run coverage tool and parse results
3. **Gap Analysis** — Identify uncovered files, functions, and branches
4. **Recommendations** — Suggest specific test cases for uncovered paths

## Target Resolution

- If target is provided, scope analysis to that path
- If target is omitted, detect and analyze the entire project root
- Target can be a file (`src/lib.rs`), directory (`src/`), or glob (`src/**/*.py`)

## References

Technique reference documents are available at:
- `${CLAUDE_PLUGIN_ROOT}/references/property-testing.md`
- `${CLAUDE_PLUGIN_ROOT}/references/boundary-analysis.md`
- `${CLAUDE_PLUGIN_ROOT}/references/mutation-testing.md`
