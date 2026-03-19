---
diataxis_type: tutorial
diataxis_learning_goals:
  - Install and configure the refactor plugin
  - Run a refactor on a codebase
  - Read and interpret the refactor report
  - Understand the iterative improvement cycle
---

# Tutorial: Your First Refactor

In this tutorial, we will install the refactor plugin, run it against a codebase, and walk through the results. By the end, you will understand the full refactoring lifecycle and how to interpret quality scores.

## What you'll learn

- How to install the refactor plugin
- How to run a refactor with different scopes
- How the six agents collaborate through the iteration cycle (plus the `/feature-dev` skill)
- How to read the final quality report

## Prerequisites

- [Claude Code](https://github.com/anthropics/claude-code) CLI installed
- A git repository with source code to refactor
- Git installed and available on your PATH
- (Optional) [GitHub CLI](https://cli.github.com/) (`gh`) for PR and issue features

## Steps

### Step 1: Install the plugin

Point Claude Code at the refactor plugin directory:

```bash
claude --plugin-dir /path/to/refactor
```

You should see Claude Code start normally. The `/refactor` command is now available.

### Step 2: Prepare your repository

Navigate to the project you want to refactor and ensure you have a clean git state:

```bash
cd your-project
git status
```

The output should show no uncommitted changes. If there are changes, commit or stash them first. The refactor plugin modifies files, so starting from a clean state lets you review all changes with `git diff` afterward.

### Step 3: Run your first refactor

Start with a focused scope. Pick a single directory or file:

```bash
/refactor src/utils/
```

The plugin will ask you configuration questions on first run:

1. **Iterations** — Choose "3 (Recommended)" to start
2. **Commits** — Choose "Don't commit (I'll handle it)" so you can review changes first
3. **Pull Request** — Choose "No"
4. **Report** — Choose "Local file only"

Your answers are saved to `.claude/refactor.config.json` and reused on future runs.

### Step 3b: Try a focused refactor

Now run a focused refactor to see how `--focus` constrains the agents:

```bash
/refactor --focus=security src/utils/
```

This time, only three agents spawn: refactor-test (always), refactor-code (always), and code-reviewer (the focused discipline for security). The run defaults to 1 iteration instead of 3.

You will see the same phase structure, but steps that require inactive agents are skipped. The final report includes only a Security Posture Score — no Architecture or Clean Code scores are produced.

To override the iteration default in focused mode:

```bash
/refactor --focus=security --iterations=3 src/utils/
```

### Step 4: Watch the phases

After configuration, the plugin creates a swarm team and begins working. You will see progress messages as each phase completes:

**Phase 0.5 (Discovery)** runs the code-explorer agent first. It traces entry points, maps execution flows, catalogs dependencies, and produces a structured codebase map. This map is shared with all downstream agents via the blackboard so they start with full context rather than each independently exploring.

You will see: "Phase 0.5 complete. Codebase discovery finished."

**Phase 1 (Foundation)** runs agents in parallel:
- The refactor-test agent analyzes test coverage and adds missing tests
- The architect agent reviews your code's architecture
- The code-reviewer agent establishes a quality + security baseline

All three read the code-explorer's codebase map from the blackboard. You will see: "Phase 1 complete. Test coverage established. Architecture reviewed. Quality + security baseline recorded."

**Phase 2 (Iteration Loop)** runs three times by default. Each iteration:
1. The architect creates an optimization plan (top 3 priorities)
2. The refactor-code agent implements the optimizations
3. The refactor-test agent runs all tests
4. If tests fail, the refactor-code agent fixes them
5. The simplifier polishes the changed code
6. Tests run again to verify simplification

You will see: "Iteration 1 of 3 complete." after each cycle.

**Phase 3 (Final Assessment)** runs the simplifier and architect in parallel for a final polish and quality evaluation.

**Phase 4 (Report)** generates the results file.

### Step 5: Review the report

When the refactor completes, you will see a summary with quality scores:

```
Refactoring complete!

Summary:
- Iterations: 3
- Tests: All passing
- Report: refactor-result-20260228-143022.md

Quality Scores:
- Clean Code: 8/10
- Architecture: 7/10
```

Open the report file to see the full assessment, including per-criteria justifications, improvements achieved, and recommendations for future work.

### Step 6: Review the code changes

Use git to see what the agents changed:

```bash
git diff
```

Review the modifications. The refactor plugin preserves all existing functionality — only code quality and structure are improved. If you are satisfied with the changes, commit them:

```bash
git add -u
git commit -m "refactor: improve code quality in src/utils/"
```

If you want to discard the changes, reset:

```bash
git checkout -- .
```

## What you've accomplished

You have:
- Installed the refactor plugin and configured it for your project
- Run a scoped refactor with the default 3-iteration cycle
- Observed six agents collaborating through parallel and sequential phases
- Run a focused refactor constrained to a single discipline
- Read a quality assessment report with Clean Code, Architecture, and Security Posture scores
- Reviewed and committed (or discarded) the changes

## Next steps

- [Tutorial: Your First Feature Development](tutorial-feature-dev.md) — build a new feature with `/feature-dev`
- [How to Configure Commit Strategies](guides/configure-commits.md) — automate commits and PRs
- [How to Scope Refactoring Effectively](guides/scope-refactoring.md) — strategies for large codebases
- [How to Run Focused Refactoring](guides/focus-refactoring.md) — constrain runs to specific disciplines
- [How to Develop Features](guides/use-feature-dev.md) — practical guide to `/feature-dev` scenarios
- [Configuration Reference](reference/configuration.md) — all config options
- [Architecture: Swarm Orchestration Design](explanation/architecture.md) — understand why the plugin works this way
