---
diataxis_type: reference
diataxis_describes: refactor plugin agent specifications
---

# Agent Reference

The refactor plugin provides eight specialized agents shared between the `/refactor` and `/feature-dev` skills. Each agent has a defined role, tool set, and model assignment.

The `/refactor` skill uses 6 agents (+ convergence-reporter in autonomous mode): code-explorer, architect, code-reviewer, refactor-test, refactor-code, simplifier.
The `/feature-dev` skill uses 5 agents (+ convergence-reporter in autonomous mode): code-explorer, architect, code-reviewer, feature-code, refactor-test (plus simplifier and refactor-code for fix-ups).

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
| refactor-test | No | `refactor-test` | Both skills |
| simplifier | No | `simplifier` | /refactor Phase 2-3 |
| convergence-reporter | No | `convergence-reporter` | Both skills (autonomous mode) |

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
- Refactor `--autonomous`: Tests are frozen (run only)
- Feature-dev `--autonomous`: Tests are mutable (create + run)

## See Also

- [Architecture: Swarm Orchestration Design](../explanation/architecture.md)
- [Quality Score Reference](quality-scores.md)
- [How to Develop Features](../guides/use-feature-dev.md)
