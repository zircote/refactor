# Autonomous Convergence Mode

## What Is It?

Autonomous convergence mode (`--autonomous`) applies the [Karpathy autoresearch pattern](https://github.com/karpathy/autoresearch) to code refactoring and feature development. Instead of running a fixed number of iterations and always moving forward, the system:

1. **Scores** each iteration with a composite metric
2. **Keeps** improvements and **discards** regressions
3. **Stops** when convergence is detected

The core insight: autonomous agents can iterate on code while humans sleep, as long as there's a reliable evaluation metric guiding improvement.

## How Composite Scoring Works

Each iteration produces a score from three signals:

| Signal | Source | Weight | Range |
|--------|--------|--------|-------|
| **Test pass rate** | refactor-test agent | 50% | 0.0–1.0 |
| **Code quality** | code-reviewer Mode 5 | 25% | 0.0–1.0 (from 0–10 scale) |
| **Security posture** | code-reviewer Mode 5 | 25% | 0.0–1.0 (from 0–10 scale) |

```
composite = test_rate * 0.50 + (quality / 10) * 0.25 + (security / 10) * 0.25
```

Weights are configurable in `.claude/refactor.config.json` under `autonomous.scoreWeights`.

**Blocking findings**: If the code-reviewer detects Critical or High severity security findings, both quality and security scores are capped at 5.0 (0.5 normalized). This ensures blocking issues drag the composite score down even if tests pass.

## The Keep/Discard Gate

After each iteration, the composite score is compared to the best score seen so far:

- **Score improved** → Keep the changes. Create a git branch snapshot (`autoresearch/v{N}`). Update best.
- **Score didn't improve** → Discard. Restore the working tree from the best snapshot.

This means `best_score` can only increase or stay flat. Bad experiments are free — they get reverted automatically.

## Convergence Detection

The loop stops when any of these conditions are met:

| Condition | Meaning | Default Threshold |
|-----------|---------|-------------------|
| **Perfect** | Score reached maximum | `>= 1.0` |
| **Stuck** | Consecutive reverts | 3 in a row |
| **Plateau** | Score stopped improving | delta < 0.01 for 3 iterations |
| **Max iterations** | Budget exhausted | 20 |

"Stuck" doesn't mean failure — it means the agents, given current context and eval signal, can't find better approaches. This is valuable information.

## Refactor vs Feature-Dev

The autonomous loop works in both skills but with one key difference:

| Aspect | `/refactor --autonomous` | `/feature-dev --autonomous` |
|--------|------------------------|---------------------------|
| **Tests** | **Frozen** — run only, no creation | **Mutable** — create + modify allowed |
| **Rationale** | Tests are the fixed evaluation metric | New functionality needs new tests |
| **Phase replaced** | Phase 2 (Iteration Loop) | Phase 5 (Implementation) |
| **Implementing agent** | refactor-code | feature-code |

For refactoring, freezing tests prevents "moving the goalposts" — if tests change alongside code, you can't tell whether the score improved because the code got better or because the tests got easier.

For feature development, new tests are part of the deliverable. The feature doesn't exist yet, so tests must evolve with the implementation.

## When to Use Autonomous Mode

**Good fit**:
- Large refactors where you want maximum quality without babysitting
- Well-specified features where Phases 1-4 have produced a clear architecture
- Overnight or unattended runs where you'll review results later
- When you want quantitative evidence that code quality improved

**Consider standard mode instead**:
- Quick fixes or small changes (overhead of scoring isn't worth it)
- Exploratory work where you want interactive feedback between iterations
- When you need to control exactly what changes in each iteration

## Git Branch Snapshots

Instead of filesystem copies (used by the original autoresearch), autonomous mode uses git branches:

- `autoresearch/v0` — Immutable baseline at loop start
- `autoresearch/v1`, `v2`, ... — Snapshots of kept iterations

Branches are local only (never pushed) and automatically cleaned up when the loop completes. If the loop is interrupted, stale branches are detected and cleaned on the next run.
