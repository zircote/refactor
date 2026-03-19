---
diataxis_type: tutorial
diataxis_learning_goals:
  - Run an autonomous refactor and observe the convergence loop
  - Understand composite scoring (tests, quality, security)
  - Interpret keep/discard decisions and convergence detection
  - Read a convergence report and decide next steps
---

# Tutorial: Your First Autonomous Refactor

In this tutorial, we will run a refactor in autonomous mode and walk through the convergence loop. By the end, you will understand how the keep/discard gate works, how to read composite scores, and how to interpret convergence reports.

## What you'll learn

- How `--autonomous` changes the refactoring loop
- How the composite score is computed from tests, quality, and security
- What keep/discard decisions look like as the loop progresses
- How to read the convergence report and decide whether to apply changes

## Prerequisites

- [Claude Code](https://github.com/anthropics/claude-code) CLI installed
- The refactor plugin (v4.0.0+) loaded via `--plugin-dir`
- A git repository with source code and existing tests
- Git installed and available on your PATH

## Steps

### Step 1: Start an autonomous refactor

Navigate to your project and pick a directory with existing tests:

```bash
/refactor --autonomous src/utils/
```

The plugin runs Phase 0 (team creation) and Phase 0.5 (discovery) as normal. Phase 1 (foundation) establishes test coverage, architecture review, and security baseline -- also as normal.

The difference begins at Phase 2.

### Step 2: Watch the autonomous loop initialize

Instead of the standard "Iteration 1 of 3" message, you will see:

```
Autonomous mode initialized. Baseline score: 0.625. Starting convergence loop (max 20 iterations).
```

The baseline score is a composite of three signals:
- **Test pass rate** (weight: 50%) — what fraction of tests pass
- **Code quality** (weight: 25%) — Clean Code score (0-10) from code-reviewer Mode 5
- **Security posture** (weight: 25%) — Security Posture score (0-10) from code-reviewer Mode 5

A baseline of 0.625 means: tests mostly pass, quality is decent, and security is acceptable -- but there is room to improve.

### Step 3: Observe keep/discard decisions

As each iteration completes, you will see one of two outcomes:

**Kept iteration** — the composite score improved:
```
Iteration 1: score 0.712 (improved from 0.625). KEPT -- snapshot v1 created.
```

**Reverted iteration** — the composite score did not improve:
```
Iteration 2: score 0.680 (no improvement over 0.712). REVERTED to v1.
```

When an iteration is reverted, the working tree is restored from the best snapshot. The agents then try a different approach on the next iteration, building on the best version -- not the failed one.

### Step 4: Watch for convergence

The loop stops automatically when one of these conditions is met:

- **Perfect score** (1.0) — all tests pass, quality and security are 10/10
- **Stuck** — 3 consecutive reverts (agents cannot find improvements)
- **Plateau** — score improvement < 0.01 for 3 iterations
- **Max iterations** — reached the cap (default: 20)

You will see a message like:
```
Convergence: Score plateau detected (delta < 0.01 for 3 iterations). Stopping loop.
```

### Step 5: Read the convergence report

After the loop completes, the convergence-reporter agent produces a report. You will see a summary:

```
Autonomous convergence loop complete. 7 iterations, 4 kept, 3 reverted.
Best score: 0.843. Reason: plateau. Proceeding to final assessment.
```

The full report is saved to `{scope-slug}-autonomous/convergence-report.md`. It contains:

**Score trajectory table** — every iteration's score, best score, action, and what changed:

```
| Iteration | Score | Best  | Action   | Summary                         |
|-----------|-------|-------|----------|---------------------------------|
| 0         | 0.625 | 0.625 | baseline | Initial evaluation              |
| 1         | 0.712 | 0.712 | kept     | Restructured error handling     |
| 2         | 0.680 | 0.712 | reverted | Regression in auth module       |
| 3         | 0.790 | 0.790 | kept     | Simplified validation logic     |
| 4         | 0.843 | 0.843 | kept     | Extracted shared utilities      |
| 5         | 0.831 | 0.843 | reverted | Minor quality regression        |
```

**Score breakdown** — how each component contributed:

```
| Component | Raw        | Normalized | Weight | Contribution |
|-----------|------------|------------|--------|-------------|
| Tests     | 45/45      | 1.000      | 50%    | 0.500       |
| Quality   | 7.2/10     | 0.720      | 25%    | 0.180       |
| Security  | 6.5/10     | 0.650      | 25%    | 0.163       |
| Composite |            |            |        | 0.843       |
```

**Remaining weaknesses** — what is still dragging the score down.

**Recommendation** — whether to apply changes, run again, or investigate.

### Step 6: Review and commit

The plugin proceeds to Phase 3 (Final Assessment) and Phase 4 (Report) as normal. Review the changes:

```bash
git diff
```

If satisfied, commit. If not, discard with `git checkout -- .`.

## What you've accomplished

You have:

- Run an autonomous refactor with convergence detection
- Observed the keep/discard gate in action (kept improvements, discarded regressions)
- Seen automatic convergence detection stop the loop when progress plateaued
- Read a convergence report with score trajectory, breakdown, and recommendations
- Understood how the composite score balances tests, quality, and security

## Next steps

- [How to Use Autonomous Mode](guides/use-autonomous-mode.md) — configure weights, thresholds, and iteration counts
- [Understanding Autonomous Convergence](explanation/autonomous-convergence.md) — the design rationale behind the pattern
- [Tutorial: Your First Refactor](tutorial.md) — learn the standard (non-autonomous) workflow
- [Configuration Reference](reference/configuration.md) — all autonomous config options
