---
diataxis_type: reference
diataxis_describes: refactor plugin agent specifications
---

# Agent Reference

The refactor plugin orchestrates six specialized agents as a swarm team. Each agent has a defined role, tool set, and model assignment.

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

**Role:** Design and architecture analysis

**Capabilities:** Code structure review, pattern identification, optimization planning, quality scoring

**Tools:** Glob, Grep, Read, TodoWrite, WebFetch

**Invoked during:**
- Phase 1: Initial architecture review (uses code-explorer's codebase map)
- Phase 2 Step A: Prioritized optimization plan (top 3)
- Phase 3: Final quality assessment framework
- Phase 3 Step 4: Final scoring (Clean Code + Architecture, 1--10 each)

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
| Color | yellow |

**Role:** Implementation of refactoring optimizations

**Capabilities:** Clean code refactoring, safe incremental changes, test failure fixing, blocking finding remediation, best practice application

**Tools:** Glob, Grep, Read, Write, Edit, TodoWrite

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

## See Also

- [Architecture: Swarm Orchestration Design](../explanation/architecture.md)
- [Quality Score Reference](quality-scores.md)
