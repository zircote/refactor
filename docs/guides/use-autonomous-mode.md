---
diataxis_type: how-to
diataxis_goal: Use autonomous convergence mode for unattended refactoring and feature development
---

# How to Use Autonomous Mode

## Overview

The `--autonomous` flag replaces the fixed iteration loop with a Karpathy autoresearch-style convergence loop. Each iteration is scored, improvements are kept, regressions are discarded, and the loop stops automatically when convergence is detected.

## Prerequisites

- Refactor plugin v4.0.0+ installed and working (see [Tutorial](../tutorial.md))
- A git repository with source code (autonomous mode uses git branches for snapshots)
- Familiarity with the standard `/refactor` or `/feature-dev` workflow

## Steps

### 1. Run an autonomous refactor

```bash
/refactor --autonomous src/services/
```

The plugin proceeds through Phases 0-1 (discovery, foundation) normally, then enters the autonomous convergence loop instead of the standard Phase 2 iteration loop.

### 2. Run an autonomous feature build

```bash
/feature-dev --autonomous add a REST endpoint for user preferences
```

Phases 1-4 (elicitation, exploration, clarification, architecture selection) run normally with interactive gates. Phase 5 (implementation) uses the convergence loop instead of the standard implementation flow.

### 3. Override the iteration count

Default max is 20. Override with `--iterations`:

```bash
/refactor --autonomous --iterations=10 src/api/
/feature-dev --autonomous --iterations=8 implement rate limiting
```

### 4. Combine with focus (refactor only)

```bash
/refactor --autonomous --focus=security,code src/auth/
```

### 5. Configure score weights

Edit `.claude/refactor.config.json`:

```json
{
  "autonomous": {
    "scoreWeights": {
      "tests": 0.60,
      "quality": 0.20,
      "security": 0.20
    }
  }
}
```

Increase test weight when test coverage is your priority. Increase security weight for auth-sensitive code.

### 6. Configure convergence thresholds

```json
{
  "autonomous": {
    "convergence": {
      "perfectScore": 1.0,
      "plateauDelta": 0.01,
      "plateauWindow": 3,
      "maxConsecutiveReverts": 3
    }
  }
}
```

- **plateauDelta**: How small a score improvement counts as "no improvement". Increase (e.g., 0.05) for earlier stopping.
- **plateauWindow**: How many flat iterations before declaring plateau. Increase for more patience.
- **maxConsecutiveReverts**: How many bad iterations in a row before stopping. Increase for more persistence.

### 7. Interpret the convergence report

After the loop completes, the convergence-reporter generates a report with:

**Score Trajectory Table** — Shows each iteration's score, best score, and keep/discard action. Look for:
- **Rapid improvement** — most iterations kept, score rose quickly
- **Gradual improvement** — mixed kept/reverted, steady upward trend
- **Plateau** — score stopped improving after initial gains
- **Stuck** — multiple consecutive reverts

**Score Breakdown** — Shows how the three components (tests, quality, security) contributed to the composite. If one component is lagging, you know where to focus next.

**Remaining Weaknesses** — Lists what's still dragging the score down. Useful for deciding whether to run another autonomous pass or switch to manual fixes.

## Verification

After the loop completes:
1. Review the convergence report at `{scope-slug}-autonomous/convergence-report.md`
2. Check the score trajectory — did the score improve meaningfully?
3. Review the code changes with `git diff`
4. Commit if satisfied, or discard with `git checkout -- .`

## Tips

- **Start with standard mode** for unfamiliar codebases. Use `--autonomous` after you've validated the agent team works well on your codebase.
- **Check the convergence report** before committing. The loop finds a local optimum, not necessarily the global best.
- **Run again** if the report says "plateau" with low scores — the agents are non-deterministic and may find different improvements on a second pass.
- **Lower max iterations** for small scopes. A single file rarely needs 20 iterations.

## Related

- [Understanding Autonomous Convergence](../explanation/autonomous-convergence.md) — how the pattern works and why
- [Configuration Reference](../reference/configuration.md) — all autonomous config options
- [Agent Reference](../reference/agents.md) — convergence-reporter agent and code-reviewer Mode 5
- [Troubleshooting](troubleshooting.md) — common autonomous mode issues
