---
diataxis_type: how-to
diataxis_goal: Perform common git workflows using the plugin's workflow commands
---

# How to Use Git Workflow Commands

## Overview

This guide covers common git workflows using the plugin's built-in commands. Each section walks through a specific scenario -- commit and push, create a PR, fix review feedback, sync your branch, and review PR comments.

## Prerequisites

- The refactor plugin loaded via `--plugin-dir`
- Git installed and available on your PATH
- [GitHub CLI](https://cli.github.com/) (`gh`) installed and authenticated (required for PR commands)
- A git repository with a remote configured

## Steps

### 1. Commit and push your work

Use `/cp` to stage all changes, generate a conventional commit message, and push to the remote.

**Auto-generate a commit message from the diff:**

```bash
/cp
```

The command reviews your changes, generates a message following conventional commit format, stages files individually (never `git add -A`), and pushes to the current branch's remote.

**Provide your own commit message:**

```bash
/cp "fix: resolve null pointer in webhook handler"
```

The command uses your message verbatim. It must follow conventional commit format.

**What happens if you have confidential files:**

The command detects `.env`, `*.pem`, `*.key`, and similar files. It warns you and excludes them from staging automatically.

**What happens if the remote has new commits:**

The command fetches and rebases before pushing. If the rebase has conflicts, the push pipeline halts and presents resolution options.

### 2. Create a pull request

Use `/pr` to create a draft PR targeting a branch.

**Create a draft PR to the default branch:**

```bash
/pr
```

**Create a PR targeting a specific branch:**

```bash
/pr develop
```

**Create a non-draft PR:**

```bash
/pr --no-draft
```

The command rebases your branch onto the target, pushes, generates a PR title and body (with Summary, Changes, and Test Plan sections), and creates the PR via `gh pr create`.

**Convert a draft PR to ready for review:**

```bash
/pr --ready
```

**Push new commits to an existing PR:**

```bash
/pr --update
```

If a PR already exists for the branch, the create workflow stops and suggests `--update` instead.

### 3. Fix PR review feedback

Use `/pr-fix` to address all review comments on a PR -- fetch, triage, fix, reply, push, and resolve threads.

**Fix comments on the current branch's PR:**

```bash
/pr-fix
```

When no PR number is given, the command discovers all open PRs and processes them.

**Fix a specific PR:**

```bash
/pr-fix 42
```

**Fix a range of PRs:**

```bash
/pr-fix 10..15
```

**Preview what would change without modifying anything:**

```bash
/pr-fix --dry-run
```

**Lower the confidence threshold to accept more fixes automatically:**

```bash
/pr-fix --confidence=85
```

By default, only fixes with 95%+ confidence are auto-accepted. Others are skipped in auto mode or prompted in `--interactive` mode.

Every comment receives a reply (fixed, rejected with explanation, answered, or acknowledged). Every thread is resolved after push.

### 4. Review PR comments without fixing

Use `/review-comments` to triage and score PR comments without necessarily applying fixes.

**Score comments without taking action:**

```bash
/review-comments --score-only
```

This fetches, categorizes, and scores all comments, then stops. You can follow up with specific instructions.

**Interactively review and remediate comments:**

```bash
/review-comments 42
```

**Auto-accept comments meeting a confidence threshold:**

```bash
/review-comments --auto --confidence=75
```

### 5. Sync your branch with remote

Three commands cover different sync scenarios:

**Fast-forward only (safest -- no rewrite):**

```bash
/ff
```

Use when you have no local commits. The command fetches and fast-forwards. If fast-forward is not possible (you have local commits), it stops and suggests `/fr` instead.

**Fetch and rebase (no push):**

```bash
/fr
```

Fetches from origin and rebases your branch onto the upstream tracking branch. Does not push -- use `/sync` for the full cycle.

**Full sync -- fetch, rebase, and push:**

```bash
/sync
```

Fetches, rebases, shows what will be pushed, asks for confirmation, and pushes. Uses `--force-with-lease` after rebase (safe because it just rebased onto the latest upstream).

**Sync with a specific remote and branch:**

```bash
/sync origin main
```

### 6. Clean up stale branches

Use `/prune` to find local branches whose remote tracking branch has been deleted.

**List stale branches (dry-run, default):**

```bash
/prune
```

**Delete stale branches (with confirmation):**

```bash
/prune --force
```

Protected branches (`main`, `master`, `develop`, `development`, and the current branch) are never deleted.

### 7. Review a pull request

Use `/pr-review` to perform a comprehensive code review on a PR.

**Review a specific PR:**

```bash
/pr-review 42
```

**Review with only high-severity findings:**

```bash
/pr-review 42 --severity=high
```

**Preview the review without posting:**

```bash
/pr-review 42 --dry-run
```

The review covers PR hygiene (title, description, commits, CI), code quality (correctness, security, performance, maintainability), and submits findings as a single batched GitHub review.

### 8. Sweep PRs to merge

Use `/pr-sweep` to drive all eligible PRs through a strict quality pipeline and auto-merge.

**Sweep all open PRs:**

```bash
/pr-sweep
```

**Sweep specific PRs without merging (readiness report only):**

```bash
/pr-sweep 10..15 --no-merge
```

**Preview the sweep plan:**

```bash
/pr-sweep --dry-run
```

Draft PRs are skipped automatically. Each PR passes through Copilot review, comment remediation, rebase, CI green gate, and merge.

### 9. Set up git hooks

Use `/git-hooks` to analyze your project and install tailored hooks.

**Interactive analysis and setup:**

```bash
/git-hooks
```

**Zero-touch provisioning (for bulk repo setup):**

```bash
/git-hooks --auto
```

**Preview what hooks would be recommended:**

```bash
/git-hooks --dry-run
```

## Related

- [Git Workflow Commands Reference](../reference/git-commands.md) -- full syntax, flags, and behavior details
- [Configuration Reference](../reference/configuration.md) -- project settings
- [Troubleshooting](troubleshooting.md) -- diagnose common problems
