---
diataxis_type: how-to
diataxis_goal: Choose effective refactoring scopes for different project sizes and situations
---

# How to Scope Refactoring Effectively

## Overview

This guide shows you how to choose the right refactoring scope to get the best results without wasting time on overly broad runs.

## Prerequisites

- Refactor plugin installed and working (see [Tutorial](../tutorial.md))
- Familiarity with your project's directory structure

## Steps

### 1. Start narrow, then widen

For your first refactor on a project, pick a single module or directory:

```bash
/refactor src/utils/
```

This lets you evaluate the agents' output quality and understand the iteration cycle before committing to a full-codebase run.

### 2. Use file paths for targeted fixes

If you know exactly which files need attention:

```bash
/refactor src/auth/handler.ts
```

Single-file refactors complete faster and produce focused improvements.

### 3. Use descriptions for cross-cutting concerns

If the code you want to refactor spans multiple directories, describe it:

```bash
/refactor "error handling logic"
```

The architect agent will identify relevant files across the codebase.

### 4. Adjust iteration count for scope size

For small scopes (1--3 files), fewer iterations are sufficient:

```bash
/refactor --iterations=2 src/config.ts
```

For large scopes (entire modules), use the default 3 or increase to 5:

```bash
/refactor --iterations=5 src/
```

### 5. Refactor incrementally for large codebases

For a monorepo or large project, run multiple focused refactors rather than one broad pass:

```bash
/refactor src/auth/
/refactor src/api/
/refactor src/models/
```

Review and commit after each run. This gives you finer control over changes and keeps each run's scope manageable.

## When NOT to refactor

- **No test framework** — The test agent can write tests, but it needs a test runner. Set up a testing framework first.
- **Prototype or experimental code** — Refactoring code that may be thrown away wastes effort.
- **During incidents** — Focus on the fix, refactor later.
- **Code scheduled for deletion** — Not worth improving.

## Related

- [Configuration Reference](../reference/configuration.md) — `iterations` field
- [How to Configure Commit Strategies](configure-commits.md) — automate commits between runs
- [Troubleshooting](troubleshooting.md) — when refactors take too long
