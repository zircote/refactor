# How to Use Autonomous Mode

## Basic Usage

### Refactor
```
/refactor --autonomous src/services/
```

### Feature Development
```
/feature-dev --autonomous add a REST endpoint for user preferences
```

## Override Iteration Count

Default max is 20. Override with `--iterations`:

```
/refactor --autonomous --iterations=10 src/api/
/feature-dev --autonomous --iterations=8 implement rate limiting
```

## Combine with Focus (Refactor Only)

```
/refactor --autonomous --focus=security,code src/auth/
```

## Configure Score Weights

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

## Configure Convergence Thresholds

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

## Interpreting Convergence Reports

After the loop completes, the convergence-reporter generates a report with:

### Score Trajectory Table
Shows each iteration's score, best score, and keep/discard action. Look for:
- **Rapid improvement** — most iterations kept, score rose quickly
- **Gradual improvement** — mixed kept/reverted, steady upward trend
- **Plateau** — score stopped improving after initial gains
- **Stuck** — multiple consecutive reverts

### Score Breakdown
Shows how the three components (tests, quality, security) contributed to the composite. If one component is lagging, you know where to focus next.

### Remaining Weaknesses
Lists what's still dragging the score down — useful for deciding whether to run another autonomous pass or switch to manual fixes.

## Tips

- **Start with standard mode** for unfamiliar codebases. Use `--autonomous` after you've validated the agent team works well on your codebase.
- **Check the convergence report** before committing. The loop finds a local optimum, not necessarily the global best.
- **Run again** if the report says "plateau" with low scores — the agents are non-deterministic and may find different improvements on a second pass.
- **Lower max iterations** for small scopes. A single file rarely needs 20 iterations.
