# Autonomous Convergence Loop Algorithm

This document specifies the complete algorithm for the autonomous convergence mode (`--autonomous`) in the refactor and feature-dev skills. It adapts the [Karpathy autoresearch pattern](https://github.com/karpathy/autoresearch) from skill improvement to source code improvement.

## Key Adaptations from Autoresearch

| Dimension | Autoresearch | Autonomous Convergence |
|-----------|-------------|----------------------|
| Artifact | SKILL.md (text) | Source code (git-tracked) |
| Metric | `mean(pass_rate)` from eval grading | Weighted composite: tests + quality + security |
| Snapshot | File-system copy with SHA-256 | Git branches (`autoresearch/v0`, `v1`, ...) |
| Evaluator | Eval cases + grader agent | Test suite + code-reviewer Mode 5 |
| Test freeze | Evals always frozen | Frozen for refactor, mutable for feature-dev |

## Initialization

```
INPUTS:
  scope           = files/directories to refactor or feature to implement
  max_iterations  = config.autonomous.maxIterations (default: 20)
  weights         = config.autonomous.scoreWeights (default: {tests: 0.50, quality: 0.25, security: 0.25})
  convergence     = config.autonomous.convergence

PRECONDITIONS:
  - Phase 0 (team init) and Phase 0.5 (discovery) have completed
  - Phase 1 (foundation: tests + architecture review + security baseline) has completed
  - For feature-dev: Phases 1-4 (elicitation through architecture selection) have completed

INIT:
  workspace = {scope-slug}-autonomous/

  # Detect stale branches from prior aborted runs
  scripts/git_snapshot.sh detect-stale
  # If found: warn user, offer cleanup

  # Create immutable baseline
  scripts/git_snapshot.sh baseline
  # Creates branch autoresearch/v0 at current HEAD

  # Establish baseline score
  score_0 = evaluate(workspace, 0)
  best = {version: 0, score: score_0}

  # Initialize results log
  scripts/results_log.sh append results.tsv 0 score_0 score_0 "baseline" "Initial evaluation"
```

## Evaluation Procedure

Evaluation scores the current working tree state using three signals:

```
FUNCTION evaluate(workspace, iteration):
  iter_dir = workspace/iteration-{iteration}/
  mkdir -p iter_dir

  # 1. Run tests via refactor-test agent
  #    Agent writes standardized output:
  #    iter_dir/test-results.json = {"passed": N, "failed": M, "total": T, "pass_rate": F}
  spawn refactor-test(
    mode = "run-and-report",
    output_path = iter_dir/test-results.json
  )

  # 2. Run code-reviewer in Mode 5 (autonomous scoring)
  #    Agent writes structured output:
  #    iter_dir/review-scores.json = {"quality_score": Q, "security_score": S, ...}
  spawn code-reviewer(
    mode = 5,  # Autonomous scoring
    output_path = iter_dir/review-scores.json
  )

  # 3. Compute weighted composite
  score = scripts/score.sh workspace iteration
  # score = test_rate * 0.50 + (quality/10) * 0.25 + (security/10) * 0.25

  RETURN score
```

## Main Loop

```
FOR i IN 1..max_iterations:

  # ─── MODIFY ───────────────────────────────────────────────
  # Execute one iteration's improvement sub-steps.
  # These are the same sub-steps as the standard Phase 2, but
  # with test-creation constraints.

  # Refactor mode: tests are FROZEN
  #   - architect: create/update optimization plan
  #   - refactor-code: implement top optimizations
  #   - refactor-test: run tests ONLY (no creation/modification)
  #   - refactor-code: fix test failures if any
  #   - code-reviewer: Mode 2 iteration review (narrative feedback)
  #   - simplifier: polish changed code

  # Feature-dev mode: tests are MUTABLE
  #   - feature-code: implement next iteration of feature
  #   - refactor-test: write new tests + run all tests (creation allowed)
  #   - feature-code: fix test failures if any
  #   - code-reviewer: Mode 2 iteration review (narrative feedback)

  changelog = summary of changes made in this iteration

  # ─── EVALUATE ─────────────────────────────────────────────
  score_i = evaluate(workspace, i)

  # ─── KEEP or DISCARD ──────────────────────────────────────
  IF score_i > best.score:
    # Keep: snapshot the improved version
    scripts/git_snapshot.sh create {i}
    # Creates branch autoresearch/v{i}
    best = {version: i, score: score_i}
    action = "kept"
  ELSE:
    # Discard: restore working tree from best snapshot
    scripts/git_snapshot.sh restore {best.version}
    action = "reverted"

  # ─── LOG ──────────────────────────────────────────────────
  scripts/results_log.sh append results.tsv i score_i best.score action changelog

  # ─── CONVERGENCE CHECK ────────────────────────────────────
  IF best.score >= convergence.perfectScore:
    BREAK  # Perfect score achieved

  IF scripts/results_log.sh check-stuck results.tsv convergence.maxConsecutiveReverts:
    BREAK  # Stuck — N consecutive reverts

  IF scripts/results_log.sh check-plateau results.tsv convergence.plateauWindow convergence.plateauDelta:
    BREAK  # Plateau — score not improving

  # Otherwise: continue to next iteration
```

## Finalization

```
FINALIZE:
  # Ensure best version is on the working tree
  scripts/git_snapshot.sh restore {best.version}

  # Spawn convergence reporter agent
  spawn convergence-reporter(
    workspace     = workspace,
    best_version  = best.version,
    best_score    = best.score,
    total_iters   = i,
    reason        = convergence_reason  # "perfect" | "stuck" | "plateau" | "max_iterations"
  )
  # Reporter writes workspace/convergence-report.md
  # Reporter writes to blackboard key: convergence_report

  # Clean up snapshot branches
  scripts/git_snapshot.sh cleanup
  # Deletes all autoresearch/v* branches

  # Proceed to Phase 3 (Final Assessment) as normal
```

## Composite Score

The composite score is a weighted sum of three normalized signals:

```
score = test_pass_rate * W_tests
      + (quality_score / 10) * W_quality
      + (security_score / 10) * W_security

Where:
  test_pass_rate  = passed / total (0.0–1.0) from test-results.json
  quality_score   = 0–10 from review-scores.json (Clean Code rubric)
  security_score  = 0–10 from review-scores.json (Security Posture rubric)
  W_tests         = 0.50 (default)
  W_quality       = 0.25 (default)
  W_security      = 0.25 (default)

Special case: if blocking_findings is true in review-scores.json,
both quality and security scores are capped at 5.0 (0.5 normalized).
```

## Convergence Criteria

| Condition | Check | Default Threshold |
|-----------|-------|-------------------|
| **Perfect** | `best.score >= perfectScore` | 1.0 |
| **Stuck** | Last N actions all "reverted" | N = 3 |
| **Plateau** | Score delta < threshold for M iterations | delta = 0.01, M = 3 |
| **Max iterations** | `i >= max_iterations` | 20 |

Checked in order. First matching condition stops the loop.

## Workspace Layout

```
{scope-slug}-autonomous/
├── results.tsv                    # Append-only score log
├── convergence-report.md          # Generated at finalization
├── iteration-0/                   # Baseline evaluation
│   ├── test-results.json
│   └── review-scores.json
├── iteration-1/                   # First iteration
│   ├── test-results.json
│   └── review-scores.json
├── iteration-2/
│   └── ...
└── ...
```

Git branches (ephemeral, cleaned up at finalization):
```
autoresearch/v0    — Immutable baseline (HEAD at loop start)
autoresearch/v1    — Snapshot of first kept iteration (if kept)
autoresearch/v3    — Snapshot of third iteration (if kept; v2 was reverted)
```

## Safety Invariants

1. **Baseline is immutable** — `autoresearch/v0` is never modified after creation
2. **Kept snapshots are immutable** — once `autoresearch/v{N}` is created, it is never modified
3. **Revert restores exactly** — `git checkout autoresearch/v{best} -- .` restores the full working tree
4. **Tests frozen for refactor** — refactor-test only runs tests during the autonomous loop, never creates or modifies them
5. **Tests mutable for feature-dev** — refactor-test can create/modify tests (new functionality needs new tests)
6. **Regression abort** — N consecutive reverts stops the loop (default: 3)
7. **Score monotonically increases** — `best.score` can only increase or stay the same
8. **Branches cleaned up** — all `autoresearch/v*` branches deleted at finalization
9. **No human gates during loop** — fully autonomous; user reviews final result only

## Refactor vs Feature-Dev Differences

| Aspect | Refactor | Feature-Dev |
|--------|----------|-------------|
| Phase replaced | Phase 2 (Iteration Loop) | Phase 5 (Implementation) |
| Implementing agent | refactor-code | feature-code |
| Test creation | Frozen (run only) | Mutable (create + run) |
| Optimization source | architect's plan | architecture blueprint |
| Baseline taken | After Phase 1 (foundation) | After Phase 4 (architecture chosen) |
| Standard sub-steps | architect → code → test → review → simplify | code → test → review |
