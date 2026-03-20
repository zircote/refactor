---
diataxis_type: reference
diataxis_describes: refactor plugin agent specifications
---

# Agent Reference

The refactor plugin provides twelve specialized agents shared between the `/refactor`, `/feature-dev`, and `/test-architect` skills. Each agent has a defined role, tool set, and model assignment.

The `/refactor` skill uses 6 agents (+ convergence-reporter in autonomous mode): code-explorer, architect, code-reviewer, refactor-test, refactor-code, simplifier.
The `/feature-dev` skill uses 8 agents (+ convergence-reporter in autonomous mode): code-explorer, architect, test-planner, feature-code, test-writer, code-reviewer, test-rigor-reviewer, coverage-analyst (plus simplifier and refactor-code for fix-ups).
The `/test-architect` skill uses 4 agents: test-planner, test-writer, test-rigor-reviewer, coverage-analyst.

## Code-Explorer Agent

| Property | Value |
|----------|-------|
| Name | `code-explorer` |
| Model | `sonnet` |
| Color | yellow |

**Role:** Deep codebase discovery (Phase 0.5)

**Capabilities:** Entry point tracing, execution flow mapping, architecture layer identification, dependency cataloging, pattern recognition, structured codebase map generation

**Tools:** Glob, Grep, Read, Write, Edit, Bash, TodoWrite

**Invoked during:**
- Phase 0.5: Deep codebase discovery (runs first, before all other agents)

**Output:** Structured codebase map distributed via blackboard (or inline) to all downstream agents

**Focus mode:** Activated by `--focus=discovery`

## Architect Agent

| Property | Value |
|----------|-------|
| Name | `architect` |
| Model | `sonnet` |
| Color | green |

**Role:** Design and architecture analysis (refactoring) + feature architecture design (feature-dev)

**Capabilities:** Code structure review, pattern identification, optimization planning, quality scoring, feature architecture blueprints with implementation maps

**Tools:** Bash, Glob, Grep, Read, TodoWrite

**Invoked during (/refactor):**
- Phase 1: Initial architecture review (uses code-explorer's codebase map)
- Phase 2 Step A: Prioritized optimization plan (top 3)
- Phase 3: Final quality assessment framework
- Phase 3 Step 4: Final scoring (Clean Code + Architecture, 1--10 each)

**Invoked during (/feature-dev):**
- Phase 4: Architecture design (spawned as N parallel instances with different design philosophies)

**Blackboard protocol:** Reads `codebase_context`, `feature_spec`, `clarifications`. Writes `architect_plan` (refactor) or `architect_{i}_design` (feature-dev).

**Focus mode:** Activated by `--focus=architecture` or `--focus=code`

## Code-Reviewer Agent

| Property | Value |
|----------|-------|
| Name | `code-reviewer` |
| Model | `sonnet` |
| Color | red |

**Role:** Unified quality and security review gate

**Capabilities:** Bug detection with confidence scoring (>=80 threshold), project guidelines compliance, security regression detection, OWASP pattern validation, secrets/PII scanning, dependency vulnerability audit, severity classification (Critical/High = blocking), Security Posture Score assignment

**Tools:** Glob, Grep, Read, Write, Edit, Bash, TodoWrite

**Review modes:**
1. **Combined Baseline** (Phase 1): Establishes quality + security baseline for regression detection
2. **Iteration Review** (Phase 2): Confidence-scored quality review + severity-classified security review of changed files
3. **Final Assessment** (Phase 3): Comprehensive review with Security Posture Score (1-10)

**Invoked during:**
- Phase 1: Establish quality + security baseline
- Phase 2 Step E: Per-iteration quality + security review of changes
- Phase 2 Step E.1: Verify fix effectiveness for blocking findings
- Phase 3: Final comprehensive review and Security Posture Score

**Focus mode:** Activated by `--focus=security` or `--focus=code`

## Refactor-Test Agent

| Property | Value |
|----------|-------|
| Name | `refactor-test` |
| Model | `sonnet` |
| Color | blue |

**Role:** Quality assurance through testing

**Capabilities:** Coverage analysis, test case generation, test execution, failure diagnosis

**Tools:** Glob, Grep, Read, Write, Edit, Bash, TodoWrite

**Invoked during:**
- Phase 1: Coverage analysis and test generation
- Phase 2 Step C: Full test suite run
- Phase 2 Step D: Re-run after failure fixes
- Phase 2 Step G: Verify simplification preserved functionality
- Phase 3: Final test suite run

**Focus mode:** Always active regardless of `--focus` value

## Refactor-Code Agent

| Property | Value |
|----------|-------|
| Name | `refactor-code` |
| Model | `sonnet` |
| Color | magenta |

**Role:** Implementation of refactoring optimizations

**Capabilities:** Clean code refactoring, safe incremental changes, test failure fixing, blocking finding remediation, best practice application

**Tools:** Bash, Glob, Grep, Read, Write, Edit, TodoWrite

**Blackboard protocol:** Reads `codebase_context`, `architect_plan`. Writes `implementation_report`.

**Invoked during:**
- Phase 2 Step B: Implement top 3 optimizations
- Phase 2 Step D: Fix test failures
- Phase 2 Step E.1: Fix blocking code review findings

**Focus mode:** Always active regardless of `--focus` value

## Simplifier Agent

| Property | Value |
|----------|-------|
| Name | `simplifier` |
| Model | `sonnet` |
| Color | cyan |

**Role:** Code clarity and consistency

**Capabilities:** Naming improvements, control flow simplification, redundancy removal, cross-file consistency, readability polish

**Tools:** Read, Write, Edit, Glob, Grep, Bash

**Invoked during:**
- Phase 2 Step F: Simplify all code changed in iteration
- Phase 3: Final whole-scope simplification pass

**Focus mode:** Activated by `--focus=simplification`

## Feature-Code Agent

| Property | Value |
|----------|-------|
| Name | `feature-code` |
| Model | `sonnet` |
| Color | white |

**Role:** Implementation of new features from architecture blueprints

**Capabilities:** Feature implementation from blueprints, codebase convention matching, clean code creation, integration point wiring, implementation reporting

**Tools:** Bash, Glob, Grep, Read, Write, Edit, TodoWrite

**Invoked during (/feature-dev only):**
- Phase 5: Implement the chosen architecture blueprint
- Phase 5 (fix-up): Address issues from quality review

**Not used by /refactor.** The refactor workflow uses refactor-code instead (which restructures existing code rather than creating new functionality).

**Blackboard protocol:** Reads `codebase_context`, `chosen_architecture`, `clarifications`, `feature_spec`. Writes `implementation_report`.

## Multi-Instance Spawning

Some agents support multi-instance parallel spawning, where the same agent definition is spawned multiple times with unique names and different focus areas. This enables parallel exploration, design, and review.

| Agent | Multi-Instance? | Naming Pattern | Used By |
|-------|----------------|----------------|---------|
| code-explorer | Yes | `code-explorer-1`, `code-explorer-2`, ... | /feature-dev Phase 2 |
| architect | Yes | `architect-1`, `architect-2`, ... | /feature-dev Phase 4 |
| code-reviewer | Yes | `code-reviewer-1`, `code-reviewer-2`, ... | /feature-dev Phase 6 |
| feature-code | No | `feature-code` | /feature-dev Phase 5 |
| refactor-code | No | `refactor-code` | /refactor Phase 2 |
| refactor-test | No | `refactor-test` | /refactor |
| simplifier | No | `simplifier` | /refactor Phase 2-3 |
| convergence-reporter | No | `convergence-reporter` | Both skills (autonomous mode) |
| test-planner | Yes | `test-planner-1`, `test-planner-2`, ... | /feature-dev Phase 4.5, /test-architect (multi-module) |
| test-writer | No | `test-writer` | /feature-dev Phase 5, /test-architect |
| test-rigor-reviewer | No | `test-rigor-reviewer` | /feature-dev Phase 6, /test-architect |
| coverage-analyst | No | `coverage-analyst` | /feature-dev Phase 6, /test-architect |

Instance counts are configurable via `config.featureDev.explorerCount`, `.architectCount`, `.reviewerCount` (default: 3 each). The skill scales counts based on feature complexity — simple features may use 1 instance instead of 3.

## Blackboard Protocol

All agents share context through the Atlatl blackboard. Each agent has documented read/write keys:

| Agent | Reads | Writes |
|-------|-------|--------|
| code-explorer | `feature_spec` | `codebase_context`, `explorer_{i}_findings` |
| architect | `codebase_context`, `feature_spec`, `clarifications` | `architect_plan`, `architect_{i}_design` |
| code-reviewer | `codebase_context`, `feature_spec`, `chosen_architecture` | `reviewer_baseline`, `reviewer_{i}_findings` |
| feature-code | `codebase_context`, `chosen_architecture`, `clarifications`, `feature_spec` | `implementation_report` |
| refactor-code | `codebase_context`, `architect_plan` | `implementation_report` |
| refactor-test | `codebase_context` | `test_report` |
| simplifier | `codebase_context` | `simplification_report` |
| convergence-reporter | `convergence_data` | `convergence_report` |
| test-planner | `codebase_context`, `feature_spec` | `test_plan` |
| test-writer | `codebase_context`, `test_plan` | `test_generation_report` |
| test-rigor-reviewer | `codebase_context`, `test_plan` | `test_rigor_report` |
| coverage-analyst | `codebase_context`, `test_plan` | `coverage_report` |

The blackboard enables write-once, read-many context sharing — the code-explorer writes the codebase map once and all downstream agents read it as needed.

## Convergence-Reporter Agent

| Property | Value |
|----------|-------|
| Name | `convergence-reporter` |
| Model | `sonnet` |
| Color | cyan |

**Role:** Analyzes autonomous convergence loop results and produces reports

**Capabilities:** Score trajectory computation, git diff generation, weakness analysis, convergence pattern classification, recommendation generation

**Tools:** Bash, Glob, Grep, Read

**Invoked during:**
- Autonomous loop finalization (Phase 2 Step 2.2 in refactor, Phase 5 Step 5.3-auto in feature-dev)
- Only when `--autonomous` flag is active

**Output:** Convergence report (score trajectory, diff, weaknesses, recommendation) written to workspace and blackboard

**Spawn timing:** Deferred — not spawned with the initial team, only when the convergence loop completes

## Test-Planner Agent

| Property | Value |
|----------|-------|
| Name | `test-planner` |
| Model | `sonnet` |
| Color | gold |

**Role:** Read-only analysis producing JSON test plans from source code using formal techniques

**Capabilities:** Equivalence class partitioning, boundary value analysis, state transition coverage, property-based test identification, JSON test plan generation

**Tools:** Bash, Glob, Grep, Read, TodoWrite

**Invoked during (/test-architect):**
- Phase 1: Analyze target code and produce structured JSON test plan
- Modes: `full`, `plan`

**Invoked during (/feature-dev):**
- Phase 4.5: Produce formal test plan against the chosen architecture blueprint

**Output:** JSON test plan with test_cases, property_tests, coverage_targets, and technique_summary

**Blackboard protocol:** Reads `codebase_context`, `feature_spec`, `chosen_architecture` (feature-dev). Writes `test_plan`.

## Test-Writer Agent

| Property | Value |
|----------|-------|
| Name | `test-writer` |
| Model | `sonnet` |
| Color | orange |

**Role:** TDD red-phase test code generation from JSON test plans

**Capabilities:** Idiomatic test code generation across Rust/Python/TypeScript/Go, mutation-aware assertions, property-based test implementation, framework-specific conventions

**Tools:** Bash, Glob, Grep, Read, Write, Edit, TodoWrite

**Invoked during (/test-architect):**
- Phase 2: Generate test files implementing all planned test cases
- Mode: `full` only

**Invoked during (/feature-dev):**
- Phase 5: Generate test code from the Phase 4.5 test plan

**Output:** Test files following language conventions (Rust: `#[cfg(test)]` modules, Python: `test_*.py`, TypeScript: `*.test.ts`, Go: `*_test.go`)

**Blackboard protocol:** Reads `codebase_context`, `test_plan`. Writes `test_generation_report`.

## Test-Rigor-Reviewer Agent

| Property | Value |
|----------|-------|
| Name | `test-rigor-reviewer` |
| Model | `sonnet` |
| Color | amber |

**Role:** Read-only test quality auditor scoring tests against formal rigor criteria

**Capabilities:** Anti-pattern detection (tautological assertions, weak generators, mutation-susceptible patterns), per-test 0.0-1.0 scoring, test plan cross-referencing, verdict assignment (PASS/NEEDS IMPROVEMENT/FAIL)

**Tools:** Bash, Glob, Grep, Read, TodoWrite

**Invoked during (/test-architect):**
- Phase 3: Rigor review of generated or existing test suites
- Modes: `full`, `eval`

**Invoked during (/feature-dev):**
- Phase 6: Mandatory rigor review of feature tests (runs in parallel with code-reviewers)

**Scoring rubric:** 1.0 (excellent, mutation-resistant) → 0.0 (useless, tautological)

**Verdict criteria:**
- PASS: Overall rigor >= 0.70, zero tautological tests
- NEEDS IMPROVEMENT: Rigor 0.50-0.69 or 1-2 weak tests
- FAIL: Rigor < 0.50 or any tautological assertions

**Blackboard protocol:** Reads `codebase_context`, `test_plan`. Writes `test_rigor_report`.

## Coverage-Analyst Agent

| Property | Value |
|----------|-------|
| Name | `coverage-analyst` |
| Model | `sonnet` |
| Color | teal |

**Role:** Coverage measurement, gap identification, and targeted test case recommendation

**Capabilities:** Native coverage tool execution (cargo-tarpaulin, coverage.py, c8, go tool cover), coverage parsing, gap severity classification (critical/important/nice-to-have), test plan correlation, targeted test recommendations

**Tools:** Bash, Glob, Grep, Read, TodoWrite

**Invoked during (/test-architect):**
- Phase 3: Coverage analysis (parallel with rigor review)
- Phase 4: Standalone coverage analysis
- Modes: `full`, `eval`, `coverage`

**Invoked during (/feature-dev):**
- Phase 6: Mandatory coverage analysis of feature code (runs in parallel with code-reviewers)

**Verdict criteria:**
- MEETS TARGET: Line >= 90% AND Branch >= 85% AND zero critical gaps
- BELOW TARGET: Line or Branch below target but no critical gaps
- CRITICAL GAPS: Any critical-severity uncovered regions

**Blackboard protocol:** Reads `codebase_context`, `test_plan`. Writes `coverage_report`.

## Code-Reviewer Mode 5: Autonomous Scoring

In addition to Modes 1-4, the code-reviewer supports Mode 5 for the autonomous convergence loop.

**Trigger:** Task description contains "Mode 5" or "autonomous scoring"

**Purpose:** Produce machine-readable quality and security scores consumed by the composite scoring system

**Output:** JSON file (`review-scores.json`) with:
- `quality_score` (0-10): Clean Code rubric
- `security_score` (0-10): Security Posture rubric
- `quality_findings_count`: Issues with confidence >= 80
- `security_findings_count`: All severity levels
- `blocking_findings`: true if Critical/High exist
- `summary`: 1-2 sentence narrative

**Blocking penalty:** If `blocking_findings` is true, both scores are capped at 5.0

## Refactor-Test: Autonomous Mode Output

When running in autonomous mode, refactor-test writes a standardized `test-results.json`:
- `passed`, `failed`, `total` (integers)
- `pass_rate` (float 0.0-1.0)

**Test freeze behavior:**
- Refactor `--autonomous`: Tests are frozen (run only, via refactor-test)
- Feature-dev `--autonomous`: Test plan is fixed from Phase 4.5 (via test-writer). Tests are NOT rewritten per iteration — the plan is the stable fitness function.

## See Also

- [Architecture: Swarm Orchestration Design](../explanation/architecture.md)
- [Quality Score Reference](quality-scores.md)
- [How to Develop Features](../guides/use-feature-dev.md)
- [Quality Score Reference: Rigor Scores](quality-scores.md#test-rigor-score) — rigor scoring rubric for test quality
- [Tutorial: Your First Test Architecture](../tutorials/tutorial-test-architect.md) — see the test-architect in action
