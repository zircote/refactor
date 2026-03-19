---
diataxis_type: how-to
diataxis_goal: Diagnose and resolve common problems during refactoring
---

# Troubleshooting

## Tests keep failing

**Problem:** Tests fail repeatedly after the refactor-code agent applies fixes.

**Steps to resolve:**

1. Check the test failure report for patterns — are the same tests failing, or different ones each time?
2. If the same tests keep failing, the refactoring may have exposed a pre-existing issue. Verify the tests passed before the refactor started.
3. Reduce scope to isolate the problem:
   ```bash
   /refactor src/problematic-module/specific-file.ts
   ```
4. If the code has hidden dependencies (global state, external services), the test agent may not detect them. Check for:
   - Shared mutable state between tests
   - Tests that depend on execution order
   - External service calls without mocks
5. After 3 failed fix attempts, the plugin asks for your guidance. Provide context about the failing tests.

## Iterations take too long

**Problem:** Each iteration is very slow, making the full run impractical.

**Steps to resolve:**

1. Reduce scope — refactor specific files or directories instead of the entire codebase
2. Check your test suite speed — slow integration tests dominate iteration time. If your project supports it, configure the test runner to skip slow tests:
   ```bash
   # Example: skip slow tests during refactoring
   export SKIP_SLOW_TESTS=true
   ```
3. Reduce iteration count for iterative improvement over multiple runs:
   ```bash
   /refactor --iterations=2 src/
   ```
4. Check for performance bottlenecks in the codebase itself (e.g., large file counts, circular dependencies that slow analysis)

## An agent gets stuck

**Problem:** An agent does not complete its task and the refactor stalls.

**Steps to resolve:**

1. The team lead automatically sends a status check after a timeout
2. If the agent still does not respond, cancel the refactor and restart with a smaller scope
3. If the problem persists, it may be a bug in the agent instructions — report it as an issue

## PR creation fails

**Problem:** The refactor completes but the PR is not created.

**Steps to resolve:**

1. Verify `gh` is installed and authenticated:
   ```bash
   gh auth status
   ```
2. Verify your repository has a remote configured:
   ```bash
   git remote -v
   ```
3. If on a default branch (`main`/`master`/`develop`), verify the plugin can create branches:
   ```bash
   git branch
   ```
4. PR creation failures are non-blocking — your refactored code and report file are still available locally

## Report publishing fails

**Problem:** The refactor report is not published to GitHub Issues or Discussions.

**Steps to resolve:**

1. Verify `gh` authentication (same as PR creation above)
2. For issues: verify the target repository exists and you have write access
3. For discussions: verify Discussions are enabled on the target repository and the configured category exists
4. If publishing to a different repository (`reportRepository`), verify the `owner/repo` format is correct
5. Publishing failures are non-blocking — the report is always saved locally as `refactor-result-{timestamp}.md`

## Focused run still spawns unexpected agents

**Problem:** You used `--focus=security` but see refactor-test and refactor-code agents running.

**Explanation:** This is by design. The refactor-test and refactor-code agents always spawn regardless of `--focus` value. They provide the safety net (tests must pass after any changes) and fix capability (resolve test failures or security findings). Only the discipline-specific agents (code-explorer, architect, simplifier, code-reviewer) are gated by `--focus`.

## Focused run defaults to 1 iteration

**Problem:** A focused refactor completes after only 1 iteration when you expected more.

**Explanation:** Focused runs default to 1 iteration to optimize for speed. Override with `--iterations=N`:

```bash
/refactor --focus=security --iterations=3 src/auth/
```

The full iteration default from your config file (typically 3) only applies to unfocused runs.

## Feature-dev: Stuck in elicitation loop

**Problem:** The `/feature-dev` skill keeps asking clarifying questions and does not proceed to exploration.

**Steps to resolve:**

1. Provide more detail in your initial feature description — include what the feature should do, which existing code it touches, and any technical constraints
2. If the skill keeps asking questions after 2 rounds, type "proceed" to force advancement
3. For very simple features (e.g., adding a single endpoint), describe it fully: method, path, response format, auth requirements. The 95% confidence check will pass immediately

## Feature-dev: Architecture proposals don't fit

**Problem:** All three architecture proposals miss the mark or feel too similar.

**Steps to resolve:**

1. When prompted to choose, select the closest one and note what needs to change
2. The skill accepts free-text feedback — explain what's wrong and the architect instances will be re-prompted
3. If the proposals are too similar, check whether your clarifying answers were specific enough about constraints and preferences

## Feature-dev: Too many agents for a simple feature

**Problem:** The skill spawns 3 explorers, 3 architects, and 3 reviewers for a trivial feature.

**Explanation:** The skill scales agent counts based on feature complexity (assessed during Phase 1). If your feature was assessed as complex despite being simple, the 95% confidence check may have identified uncertainty that inflated the complexity assessment. For truly simple features, the skill should reduce to 1 instance each. If this does not happen, reduce `explorerCount`, `architectCount`, and `reviewerCount` in `.claude/refactor.config.json` under the `featureDev` key.

## Related

- [Configuration Reference](../reference/configuration.md) — config options affecting behavior
- [How to Scope Refactoring Effectively](scope-refactoring.md) — reducing scope to avoid problems
- [How to Develop Features](use-feature-dev.md) — practical guide to `/feature-dev` scenarios
