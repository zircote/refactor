---
name: test-plan
description: "Produce a JSON test plan from code or specs without generating test code. Detect → plan → present for approval."
arguments:
  - name: target
    description: "File path, directory, or glob pattern to plan tests for. Defaults to current project root."
    required: false
allowed-tools:
  - Read
  - Glob
  - Grep
  - Agent
---

# /test-plan — Plan-Only Mode

You are invoking the test-architect skill in **plan-only mode**. No test code will be generated.

## Instructions

Load and follow the test-architect skill at `${CLAUDE_PLUGIN_ROOT}/skills/test-architect/SKILL.md`, but stop after the planning phase.

## Pipeline

1. **Detect** — Identify project language, test framework, and directory structure
2. **Analyze** — Read the target code or spec document to identify:
   - Functions and methods under test
   - Input domains and their equivalence classes
   - Boundary values for each partition
   - Invariants suitable for property-based testing
   - Common mutation operators to defend against
3. **Plan** — Produce a structured JSON test plan containing:
   - Test cases organized by equivalence class
   - Boundary value test points
   - Property-based test specifications
   - Mutation-aware assertion strategies
4. **Present** — Display the plan for user review and approval

## Output Format

Present the JSON test plan in a readable format. Do NOT proceed to code generation — this is a planning-only command. The user can run `/test-gen` to execute the plan.

## Target Resolution

- If target is provided, scope analysis to that path
- If target is omitted, detect and analyze the entire project root
- Target can be a file, directory, or glob pattern

## References

Technique reference documents are available at:
- `${CLAUDE_PLUGIN_ROOT}/references/property-testing.md`
- `${CLAUDE_PLUGIN_ROOT}/references/boundary-analysis.md`
- `${CLAUDE_PLUGIN_ROOT}/references/mutation-testing.md`
