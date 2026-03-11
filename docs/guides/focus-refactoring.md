---
diataxis_type: how-to
diataxis_goal: Run targeted refactoring with --focus to constrain analysis to specific disciplines
---

# How to Run Focused Refactoring

## Overview

The `--focus` flag constrains a refactoring run to specific disciplines, spawning only the agents needed for that analysis. This reduces overhead and speeds up targeted reviews.

## Prerequisites

- Refactor plugin installed and working (see [Tutorial](../tutorial.md))
- Familiarity with the agent roles (see [Agent Reference](../reference/agents.md))

## Focus areas

| Value | Agents spawned | Scores produced |
|-------|---------------|-----------------|
| `security` | refactor-test, refactor-code, security-review | Security Posture |
| `architecture` | refactor-test, refactor-code, architect | Clean Code, Architecture |
| `simplification` | refactor-test, refactor-code, simplifier | Simplification |
| `code` | refactor-test, refactor-code, architect | Clean Code, Architecture |
| (none) | all 5 | Clean Code, Architecture, Security Posture |

The refactor-test and refactor-code agents always spawn regardless of focus. They provide the safety net (tests must pass) and fix capability (resolve failures).

## Steps

### 1. Run a security-only refactor

```bash
/refactor --focus=security src/auth/
```

Only the security-review agent analyzes your code. The run defaults to 1 iteration. The final report includes a Security Posture Score.

### 2. Run an architecture-only refactor

```bash
/refactor --focus=architecture src/api/
```

The architect agent reviews structure and the refactor-code agent implements the top 3 optimizations. Produces Clean Code and Architecture scores.

### 3. Run a simplification-only pass

```bash
/refactor --focus=simplification src/utils/
```

The simplifier agent operates directly on the scope (no architect plan). Focuses on naming clarity, control flow, redundancy, and style. Produces a Simplification Score.

### 4. Run a code-only refactor

```bash
/refactor --focus=code src/models/
```

Equivalent to `--focus=architecture` — the architect provides the optimization plan, the code agent implements it. No security review or simplification pass.

### 5. Combine focus areas

```bash
/refactor --focus=security,architecture src/
```

Multiple values are comma-separated. The agent set is the **union** of each focus area's agents. This example spawns: refactor-test, refactor-code, architect, and security-review (4 of 5 agents).

### 6. Override iteration count in focused mode

Focused runs default to 1 iteration. Override with `--iterations`:

```bash
/refactor --focus=security --iterations=3 src/auth/
```

### 7. When to use each focus mode

| Scenario | Recommended focus |
|----------|-------------------|
| Security audit before release | `--focus=security` |
| Design review for architecture discussion | `--focus=architecture` |
| Quick cleanup of messy code | `--focus=simplification` |
| Full refactor with code improvements | `--focus=code` or no flag |
| Pre-merge security + architecture check | `--focus=security,architecture` |

## Related

- [Agent Reference](../reference/agents.md) — agent specifications and focus mode activation
- [Quality Score Reference](../reference/quality-scores.md) — scoring rubrics for each focus mode
- [How to Scope Refactoring Effectively](scope-refactoring.md) — complementary to focus narrowing
- [Troubleshooting](troubleshooting.md) — common focus mode issues
