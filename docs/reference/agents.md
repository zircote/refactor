---
diataxis_type: reference
diataxis_describes: refactor plugin agent specifications
---

# Agent Reference

The refactor plugin orchestrates four specialized agents as a swarm team. Each agent has a defined role, tool set, and model assignment.

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
- Phase 1: Initial architecture review
- Phase 2 Step A: Prioritized optimization plan (top 3)
- Phase 3: Final quality assessment framework
- Phase 4: Final scoring (Clean Code + Architecture, 1--10 each)

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
- Phase 2 Step F: Verify simplification preserved functionality
- Phase 3: Final test suite run

## Refactor-Code Agent

| Property | Value |
|----------|-------|
| Name | `refactor-code` |
| Model | `sonnet` |
| Color | yellow |

**Role:** Implementation of refactoring optimizations

**Capabilities:** Clean code refactoring, safe incremental changes, test failure fixing, best practice application

**Tools:** Glob, Grep, Read, Write, Edit, TodoWrite

**Invoked during:**
- Phase 2 Step B: Implement top 3 optimizations
- Phase 2 Step D: Fix test failures

## Simplifier Agent

| Property | Value |
|----------|-------|
| Name | `simplifier` |
| Model | `opus` |
| Color | cyan |

**Role:** Code clarity and consistency

**Capabilities:** Naming improvements, control flow simplification, redundancy removal, cross-file consistency, readability polish

**Tools:** Read, Write, Edit, Glob, Grep, Bash

**Note:** Uses the `opus` model because nuanced clarity decisions benefit from the most capable model.

**Invoked during:**
- Phase 2 Step E: Simplify all code changed in iteration
- Phase 3: Final whole-scope simplification pass

## See Also

- [Architecture: Swarm Orchestration Design](../explanation/architecture.md)
- [Quality Score Reference](quality-scores.md)
